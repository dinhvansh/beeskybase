#!/usr/bin/env python3
"""v0.38.0 test — Auradine + SealMiner adapters from the vendors'
own material (docs/vendor-docs2-mapping.md), Pit-Bit stays a gap.

No hardware. Loopback mocks, one per contract:

  * tests/mock_auradine.py on 127.0.0.1:14034 (RPC) + :8080
    (web) — a Teraflux AT1500: the asic-rs test-JSON fixtures
    verbatim (GCMiner 0.5 / FluxOS, 3 boards x 132 chips,
    token auth admin/admin on :8080, the vendor's real web
    port — the suite binds it, so the client's default is
    exercised). The token-expiry retry is tested by
    poisoning the client's token (one mock, no second
    instance).
  * tests/mock_sealminer.py on 127.0.0.1:14035 (RPC) + :18086
    (web) — a SealMiner A2: the asic-rs test-JSON fixtures
    verbatim (BDMiner 4.11.1, 3 boards x 153 chips, cookie
    auth seal/seal on :80 CGI). A second instance on
    :14036/:18087 runs with MOCK_SEALMINER_MODEL=A3 (the
    low_power gate), a third on :14037/:18088 with
    MOCK_SEALMINER_PM_STATE=Stopped (the resume restart path).
  * tests/mock_miner.py on 127.0.0.1:4028 — the established
    Antminer cgminer fixture (non-collision witness).
  * tests/mock_luxos.py on 127.0.0.1:14029, mock_braiins.py
    on :14030, mock_whatsminer.py on :14028, mock_epic.py on
    :14031, mock_iceriver.py on :18082 — non-collision
    witnesses for every family BeeSky already detects.

Asserts: detection (fingerprints + probe claims + the
non-collision rerun against every witness) + reads
(native MH/s, boards/chips, temps, fans, power, pools,
hostname/MAC/serial) + every wired control with its exact
request body + the honest refusals (wrong password,
missing params, slot bounds, SealMiner restart_mining
unsupported, low_power A2-only, token-expiry retry).
Prints PASS lines; exit 1 on failure.
"""

import importlib.util
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from beesky import cli as cli_mod  # noqa: E402
from beesky.core import actions, inspect as inspect_mod  # noqa: E402
from beesky.core.auradine import (AuradineClient,  # noqa: E402
                                  is_auradine_version)
from beesky.core.discover import CRED_TYPES, probe_host  # noqa: E402
from beesky.core.sealminer import (SealMinerClient,  # noqa: E402
                                   is_sealminer_version)

AU_HOST, AU_RPC, AU_WEB = "127.0.0.1", 14034, 8080
SE_HOST, SE_RPC, SE_WEB = "127.0.0.1", 14035, 18086
SE3_HOST, SE3_RPC, SE3_WEB = "127.0.0.1", 14036, 18087
SEP_HOST, SEP_RPC, SEP_WEB = "127.0.0.1", 14037, 18088
CG_HOST, CG_PORT = "127.0.0.1", 4028
LUX_HOST, LUX_PORT = "127.0.0.1", 14029
BOS_HOST, BOS_PORT = "127.0.0.1", 14030
WM_HOST, WM_PORT = "127.0.0.1", 14028
EPIC_HOST, EPIC_PORT = "127.0.0.1", 14031
ICE_HOST, ICE_PORT = "127.0.0.1", 18082
CLOSED_HTTP, CLOSED_RPC = 18997, 18998

FAILURES: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        print(f"PASS {name}")
    else:
        print(f"FAIL {name} :: {detail}")
        FAILURES.append(name)


def _wait_port(host: str, port: int, timeout: float = 15.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.3):
                return True
        except OSError:
            time.sleep(0.1)
    return False


def _spawn(args: list[str], env_extra: dict) -> subprocess.Popen:
    env = dict(os.environ)
    env.update(env_extra)
    return subprocess.Popen(
        [sys.executable] + args, cwd=ROOT, env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _stop(proc: subprocess.Popen) -> None:
    try:
        proc.terminate()
        proc.wait(timeout=5)
    except Exception:  # noqa: BLE001 — teardown must not fail the run
        try:
            proc.kill()
        except Exception:  # noqa: BLE001
            pass


def _log_lines(path: Path) -> list[str]:
    return path.read_text().splitlines() if path.exists() else []


def _close(a: float | None, b: float, tol: float = 0.01) -> bool:
    return a is not None and abs(a - b) <= tol


class _Args:
    timeout = 1.5
    api_key = None
    token = None


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="beesky-vendors5-"))
    au_log = tmp / "au.log"
    se_log = tmp / "se.log"
    se3_log = tmp / "se3.log"
    sep_log = tmp / "sep.log"
    procs = [
        _spawn(["tests/mock_auradine.py", AU_HOST, str(AU_RPC),
                str(AU_WEB)], {"MOCK_AURADINE_LOG": str(au_log)}),
        _spawn(["tests/mock_sealminer.py", SE_HOST, str(SE_RPC),
                str(SE_WEB)], {"MOCK_SEALMINER_LOG": str(se_log)}),
        _spawn(["tests/mock_sealminer.py", SE3_HOST, str(SE3_RPC),
                str(SE3_WEB)],
               {"MOCK_SEALMINER_LOG": str(se3_log),
                "MOCK_SEALMINER_MODEL": "A3"}),
        _spawn(["tests/mock_sealminer.py", SEP_HOST, str(SEP_RPC),
                str(SEP_WEB)],
               {"MOCK_SEALMINER_LOG": str(sep_log),
                "MOCK_SEALMINER_PM_STATE": "Stopped"}),
        _spawn(["tests/mock_miner.py"], {}),
        _spawn(["tests/mock_luxos.py", LUX_HOST, str(LUX_PORT)], {}),
        _spawn(["tests/mock_braiins.py", BOS_HOST, str(BOS_PORT)], {}),
        _spawn(["tests/mock_whatsminer.py", WM_HOST, str(WM_PORT)],
               {}),
        _spawn(["tests/mock_epic.py", EPIC_HOST, str(EPIC_PORT)], {}),
        _spawn(["tests/mock_iceriver.py", ICE_HOST, str(ICE_PORT)],
               {}),
    ]
    try:
        for host, port in ((AU_HOST, AU_RPC), (AU_HOST, AU_WEB),
                           (SE_HOST, SE_RPC), (SE_HOST, SE_WEB),
                           (SE3_HOST, SE3_RPC), (SE3_HOST, SE3_WEB),
                           (SEP_HOST, SEP_RPC), (SEP_HOST, SEP_WEB),
                           (CG_HOST, CG_PORT), (LUX_HOST, LUX_PORT),
                           (BOS_HOST, BOS_PORT), (WM_HOST, WM_PORT),
                           (EPIC_HOST, EPIC_PORT),
                           (ICE_HOST, ICE_PORT)):
            if not _wait_port(host, port):
                check(f"mock up {host}:{port}", False, "timeout")
                return 1

        # ------------------------------------------- fingerprint units
        au_client = AuradineClient(AU_HOST, port=AU_RPC,
                                   web_port=AU_WEB, timeout=2.0)
        se_client = SealMinerClient(SE_HOST, port=SE_RPC,
                                    web_port=SE_WEB, timeout=2.0)
        au_version = au_client.version()
        se_version = se_client.version()
        check("auradine version carries GCMiner 0.5",
              au_version.get("VERSION", [{}])[0].get("GCMiner")
              == "0.5", repr(au_version))
        check("sealminer version carries BDMiner 4.11.1",
              se_version.get("VERSION", [{}])[0].get("BDMiner")
              == "4.11.1", repr(se_version))
        check("is_auradine_version true on GCMiner reply",
              is_auradine_version(au_version))
        check("is_auradine_version true on FluxOS-only reply",
              is_auradine_version(
                  {"VERSION": [{"Miner": "FluxOS-2023-12.27"}]}))
        check("is_auradine_version false on cgminer reply",
              not is_auradine_version(
                  {"VERSION": [{"Miner": "cgminer 4.11.1"}]})
              and not is_auradine_version(se_version)
              and not is_auradine_version({}))
        check("is_sealminer_version true on BDMiner reply",
              is_sealminer_version(se_version))
        check("is_sealminer_version true on lowercase bdminer",
              is_sealminer_version(
                  {"STATUS": [{"Description": "bdminer 4.11.1"}]}))
        check("is_sealminer_version false on other families",
              not is_sealminer_version(au_version)
              and not is_sealminer_version(
                  {"VERSION": [{"Miner": "LUXminer 2024.5.1"}]})
              and not is_sealminer_version(
                  {"VERSION": [{"Miner": "BOSminer+ 0.2.0"}]})
              and not is_sealminer_version({}))
        check("auradine + sealminer are cred tags",
              "auradine" in CRED_TYPES and "sealminer" in CRED_TYPES)

        # --------------------------------------------- probe claims
        au_cand = probe_host(AU_HOST, timeout=1.5,
                             http_port=CLOSED_HTTP, cgminer_port=AU_RPC)
        check("probe claims auradine",
              au_cand is not None and au_cand.source == "auradine",
              repr(au_cand and au_cand.source))
        se_cand = probe_host(SE_HOST, timeout=1.5,
                             http_port=SE_WEB, cgminer_port=SE_RPC)
        check("probe claims sealminer",
              se_cand is not None and se_cand.source == "sealminer",
              repr(se_cand and se_cand.source))

        # ------------------------------- non-collision rerun (v0.30 rule)
        witnesses = [
            ("stock cgminer", CG_HOST, CG_PORT, CLOSED_HTTP, "cgminer"),
            ("luxos", LUX_HOST, LUX_PORT, CLOSED_HTTP, "luxos"),
            ("braiins", BOS_HOST, BOS_PORT, CLOSED_HTTP, "braiins"),
            ("whatsminer", WM_HOST, WM_PORT, CLOSED_HTTP, "whatsminer"),
            ("epic", EPIC_HOST, EPIC_PORT, CLOSED_HTTP, "epic"),
            ("iceriver", ICE_HOST, CLOSED_RPC, ICE_PORT, "iceriver"),
        ]
        for label, host, rpc_port, http_port, want in witnesses:
            cand = probe_host(host, timeout=1.5,
                              http_port=http_port, cgminer_port=rpc_port)
            check(f"probe keeps {label} {want} (not auradine/sealminer)",
                  cand is not None and cand.source == want,
                  repr(cand and cand.source))
        check("probe still claims auradine after the witnesses",
              (lambda c: c is not None and c.source == "auradine")(
                  probe_host(AU_HOST, timeout=1.5,
                             http_port=CLOSED_HTTP,
                             cgminer_port=AU_RPC)))
        check("probe still claims sealminer after the witnesses",
              (lambda c: c is not None and c.source == "sealminer")(
                  probe_host(SE_HOST, timeout=1.5, http_port=SE_WEB,
                             cgminer_port=SE_RPC)))

        # ---------------------------------------------- auradine record
        au_mark = len(_log_lines(au_log))
        au_rec = cli_mod._fetch_record(au_cand, _Args())
        check("cli fetch auradine record",
              au_rec["source"] == "auradine"
              and au_rec["model"] == "AT1500"
              and au_rec["status"] == "OK",
              repr({k: au_rec.get(k) for k in
                    ("source", "model", "status")}))
        check("auradine native rate 7.97 TH/s (MHS av / 1e6)",
              _close(au_rec.get("rate_value"), 7.97063)
              and au_rec.get("rate_unit") == "TH/s"
              and _close(au_rec.get("ghs_5s"), 20599.77)
              and _close(au_rec.get("ghs_av"), 7970.63),
              repr((au_rec.get("rate_value"), au_rec.get("rate_unit"),
                    au_rec.get("ghs_5s"), au_rec.get("ghs_av"))))
        check("auradine elapsed 56696 s, power 58.94 W (PSU PowerIn)",
              au_rec.get("elapsed_s") == 56696
              and _close(au_rec.get("power_w"), 58.94),
              repr((au_rec.get("elapsed_s"), au_rec.get("power_w"))))
        check("auradine 3 boards, 132 chips each, temps 28.25/29.06/30.12",
              len(au_rec["chains"]) == 3
              and au_rec["chips_total"] == 396
              and au_rec["chips_alive"] == 396
              and [c["chips_total"] for c in au_rec["chains"]]
              == [132, 132, 132]
              and [c["temp_c"] for c in au_rec["chains"]]
              == [28.25, 29.06, 30.12],
              repr(au_rec.get("chains")))
        check("auradine board temp spread 20.5-47.5 C",
              au_rec.get("board_temp_min_c") == 20.5
              and au_rec.get("board_temp_max_c") == 47.5,
              repr((au_rec.get("board_temp_min_c"),
                    au_rec.get("board_temp_max_c"))))
        check("auradine fans 7080/7020/7100/7020 rpm",
              au_rec["fans_rpm"] == [7080, 7020, 7100, 7020],
              repr(au_rec.get("fans_rpm")))
        check("auradine pools: 3, first Alive, no passwords",
              len(au_rec.get("pools") or []) == 3
              and au_rec["pools"][0]["status"] == "Alive"
              and au_rec["pools"][0]["url"]
              == "stratum+tcp://btc.viabtc.io:3333"
              and au_rec["pools"][0]["worker"] == "username.suffix"
              and all("pass" not in p and "password" not in p
                      for p in (au_rec.get("pools") or [])),
              repr(au_rec.get("pools")))
        check("auradine hostname + mac + serial on the record",
              au_rec.get("hostname") == "teraflux-01"
              and au_rec.get("mac") == "1c:00:00:0e:3b:2b"
              and au_rec.get("serial") == "AU23200006",
              repr({k: au_rec.get(k) for k in
                    ("hostname", "mac", "serial")}))
        check("auradine accepted 3310 / rejected 1",
              au_rec.get("accepted") == 3310
              and au_rec.get("rejected") == 1,
              repr((au_rec.get("accepted"), au_rec.get("rejected"))))
        au_new = _log_lines(au_log)[au_mark:]
        check("auradine reads never POST a write (only /token)",
              all(not line.startswith("WEB POST")
                  or "POST /token" in line for line in au_new)
              and any("WEB GET /ipreport" in line for line in au_new)
              and any("WEB GET /temperature" in line
                      for line in au_new),
              repr(au_new))

        # --------------------------------------------- sealminer record
        se_mark = len(_log_lines(se_log))
        se_rec = cli_mod._fetch_record(se_cand, _Args())
        check("cli fetch sealminer record",
              se_rec["source"] == "sealminer"
              and se_rec["model"] == "A2"
              and se_rec["status"] == "OK",
              repr({k: se_rec.get(k) for k in
                    ("source", "model", "status")}))
        check("sealminer native rate 206.86 TH/s (MHS av / 1e6)",
              _close(se_rec.get("rate_value"), 206.86047)
              and se_rec.get("rate_unit") == "TH/s"
              and _close(se_rec.get("ghs_5s"), 368479.43)
              and _close(se_rec.get("ghs_av"), 206860.47),
              repr((se_rec.get("rate_value"), se_rec.get("rate_unit"),
                    se_rec.get("ghs_5s"), se_rec.get("ghs_av"))))
        check("sealminer elapsed 2481 s, power 3504 W",
              se_rec.get("elapsed_s") == 2481
              and se_rec.get("power_w") == 3504.0,
              repr((se_rec.get("elapsed_s"), se_rec.get("power_w"))))
        check("sealminer 3 boards, 153 chips each, temps 70/70/70",
              len(se_rec["chains"]) == 3
              and se_rec["chips_total"] == 459
              and se_rec["chips_alive"] == 459
              and [c["chips_total"] for c in se_rec["chains"]]
              == [153, 153, 153]
              and [c["temp_c"] for c in se_rec["chains"]]
              == [70, 70, 70],
              repr(se_rec.get("chains")))
        check("sealminer intake min 55, outlet max 69",
              se_rec.get("board_temp_min_c") == 55
              and se_rec.get("board_temp_max_c") == 69,
              repr((se_rec.get("board_temp_min_c"),
                    se_rec.get("board_temp_max_c"))))
        check("sealminer fans 3723/3723/3753/3723 rpm (Fan Count 4)",
              se_rec["fans_rpm"] == [3723, 3723, 3753, 3723],
              repr(se_rec.get("fans_rpm")))
        check("sealminer pools: 1 Alive, worker Dow_Mining.SealMinerA2",
              len(se_rec.get("pools") or []) == 1
              and se_rec["pools"][0]["status"] == "Alive"
              and se_rec["pools"][0]["worker"]
              == "Dow_Mining.SealMinerA2"
              and se_rec["pools"][0]["url"]
              == "stratum+tcp://stratum.braiins.com:3333",
              repr(se_rec.get("pools")))
        check("sealminer mac + serial on the record",
              se_rec.get("mac") == "50:d4:48:4b:86:78"
              and se_rec.get("serial") == "S127200252001850",
              repr({k: se_rec.get(k) for k in ("mac", "serial")}))
        check("sealminer accepted 1421 / rejected 3",
              se_rec.get("accepted") == 1421
              and se_rec.get("rejected") == 3,
              repr((se_rec.get("accepted"), se_rec.get("rejected"))))
        se_new = _log_lines(se_log)[se_mark:]
        check("sealminer reads never write (no ascset/updatepools/restart)",
              all("RPC ascset" not in line
                  and "RPC updatepools" not in line
                  and "RPC restart" not in line
                  and "led_conf" not in line
                  and "reboot.php" not in line
                  for line in se_new)
              and any("RPC summary" in line for line in se_new)
              and any("WEB GET /cgi-bin/get_system_info.php" in line
                      for line in se_new),
              repr(se_new))

        # --------------------------------------------- auradine actions
        au_creds = {"cgminer_port": AU_RPC, "timeout": 2.0}
        ok, msg = actions.execute(
            AU_HOST, "auradine", "reboot", creds=au_creds)
        check("auradine reboot accepted", ok, msg)
        ok, msg = actions.execute(
            AU_HOST, "auradine", "restart_mining", creds=au_creds)
        check("auradine restart_mining accepted (restart gcminer)",
              ok, msg)
        ok, msg = actions.execute(
            AU_HOST, "auradine", "pause_mining", creds=au_creds)
        check("auradine pause_mining accepted (mode sleep on)", ok, msg)
        ok, msg = actions.execute(
            AU_HOST, "auradine", "resume_mining", creds=au_creds)
        check("auradine resume_mining accepted (mode sleep off)",
              ok, msg)
        ok, msg = actions.execute(
            AU_HOST, "auradine", "find_miner", creds=au_creds)
        check("auradine find_miner accepted (led code 3)", ok, msg)
        ok, msg = actions.execute(
            AU_HOST, "auradine", "set_power_target",
            payload={"watts": 2000}, creds=au_creds)
        check("auradine set_power_target accepted (mode custom/power)",
              ok, msg)
        ok, msg = actions.execute(
            AU_HOST, "auradine", "switch_pool",
            payload={"url": "stratum+tcp://new.example.com:3333",
                     "user": "newuser.001", "pool_id": 0},
            creds=au_creds)
        check("auradine switch_pool accepted (updatepools)", ok, msg)

        au_lines = _log_lines(au_log)
        check("auradine reboot body is bare restart (no parameter)",
              any('WEB POST /restart {"command": "restart"}' in line
                  for line in au_lines),
              repr(au_lines))
        check("auradine restart_mining body carries parameter gcminer",
              any('"parameter": "gcminer"' in line
                  and "POST /restart" in line for line in au_lines),
              repr(au_lines))
        check("auradine sleep bodies are mode sleep on/off",
              any('"sleep": "on"' in line and "POST /mode" in line
                  for line in au_lines)
              and any('"sleep": "off"' in line and "POST /mode" in line
                      for line in au_lines),
              repr(au_lines))
        check("auradine find_miner body is led code 3",
              any('"code": 3' in line and "POST /led" in line
                  for line in au_lines),
              repr(au_lines))
        check("auradine power body is mode custom/tune power 2000",
              any('"mode": "custom"' in line
                  and '"tune": "power"' in line
                  and '"power": 2000' in line for line in au_lines),
              repr(au_lines))
        check("auradine updatepools replaces slot 0, keeps 1-2, pass x",
              any("POST /updatepools" in line
                  and "new.example.com:3333" in line
                  and "newuser.001" in line
                  and line.count("stratum.slushpool.com:3333") == 2
                  and line.count('"pass": "x"') == 3
                  and "btc.viabtc.io" not in line
                  for line in au_lines),
              repr(au_lines))
        rpc_idx = [i for i, line in enumerate(au_lines)
                   if line.startswith("RPC pools")]
        up_idx = [i for i, line in enumerate(au_lines)
                  if "POST /updatepools" in line]
        check("auradine switch_pool read RPC pools before updatepools",
              bool(rpc_idx) and bool(up_idx)
              and max(rpc_idx) < min(up_idx),
              repr(au_lines))

        au_bad = {"cgminer_port": AU_RPC, "timeout": 2.0,
                  "password": "wrong"}
        ok, msg = actions.execute(
            AU_HOST, "auradine", "reboot", creds=au_bad)
        check("auradine wrong password refused at /token",
              not ok and "401" in msg, msg)
        ok, msg = actions.execute(
            AU_HOST, "auradine", "set_power_target",
            payload={}, creds=au_creds)
        check("auradine set_power_target without watts refused",
              not ok, msg)
        ok, msg = actions.execute(
            AU_HOST, "auradine", "switch_pool",
            payload={"pool_id": 0}, creds=au_creds)
        check("auradine switch_pool without url/user refused",
              not ok, msg)
        ok, msg = actions.execute(
            AU_HOST, "auradine", "switch_pool",
            payload={"url": "stratum+tcp://x.example.com:3333",
                     "user": "u.1", "pool_id": 3}, creds=au_creds)
        check("auradine switch_pool pool_id 3 refused (3 slots)",
              not ok, msg)

        # ------------------------------ auradine token-expiry re-auth
        # Poison the token: the next web call answers 401, the
        # client re-authenticates once and retries (asic-rs
        # web.rs) — no second mock needed.
        au2_mark = len(_log_lines(au_log))
        au2_client = AuradineClient(AU_HOST, port=AU_RPC,
                                    web_port=AU_WEB, timeout=2.0)
        au2_client._token = "stale-token"
        fan = au2_client.web_get("fan")
        check("auradine stale token re-authenticates and retries",
              isinstance(fan, dict)
              and len(fan.get("Fan") or []) == 4
              and au2_client._token == "mock-token",
              repr(fan))
        au2_new = _log_lines(au_log)[au2_mark:]
        check("auradine re-auth POSTed /token exactly once more",
              sum(1 for line in au2_new
                  if "POST /token" in line) == 1,
              repr(au2_new))

        # -------------------------------------------- sealminer actions
        # The web CGI lives on the HTTP port, so the action creds
        # carry the mock's web port (80 on a real miner).
        se_creds = {"cgminer_port": SE_RPC, "http_port": SE_WEB,
                    "timeout": 2.0}
        ok, msg = actions.execute(
            SE_HOST, "sealminer", "reboot", creds=se_creds)
        check("sealminer reboot accepted (web reboot.php)", ok, msg)
        ok, msg = actions.execute(
            SE_HOST, "sealminer", "pause_mining", creds=se_creds)
        check("sealminer pause_mining accepted (ascset 0,suspend)",
              ok, msg)
        ok, msg = actions.execute(
            SE_HOST, "sealminer", "resume_mining", creds=se_creds)
        check("sealminer resume_mining no-op when already Running",
              ok and "already hashing" in msg, msg)
        ok, msg = actions.execute(
            SE_HOST, "sealminer", "restart_mining", creds=se_creds)
        check("sealminer restart_mining honestly unsupported",
              not ok and "not supported" in msg, msg)
        ok, msg = actions.execute(
            SE_HOST, "sealminer", "find_miner", creds=se_creds)
        check("sealminer find_miner accepted (led_conf on)", ok, msg)
        ok, msg = actions.execute(
            SE_HOST, "sealminer", "set_power_target",
            payload={"watts": 3000}, creds=se_creds)
        check("sealminer set_power_target accepted (ascset powerlimit)",
              ok, msg)
        ok, msg = actions.execute(
            SE_HOST, "sealminer", "set_mining_mode",
            payload={"mode": "normal"}, creds=se_creds)
        check("sealminer set_mining_mode normal accepted", ok, msg)
        ok, msg = actions.execute(
            SE_HOST, "sealminer", "set_mining_mode",
            payload={"mode": "low_power"}, creds=se_creds)
        check("sealminer set_mining_mode low_power accepted on A2",
              ok, msg)
        ok, msg = actions.execute(
            SE_HOST, "sealminer", "switch_pool",
            payload={"url": "stratum+tcp://new.example.com:3333",
                     "user": "newuser.001", "pool_id": 0},
            creds=se_creds)
        check("sealminer switch_pool accepted (updatepools + reboot)",
              ok, msg)

        se_lines = _log_lines(se_log)
        check("sealminer pause body is ascset 0,suspend",
              any('RPC ascset "0,suspend"' in line
                  for line in se_lines),
              repr(se_lines))
        check("sealminer powerlimit body is 0,powerlimit,{value:3000}",
              any('RPC ascset "0,powerlimit,{\\"value\\":\\"3000\\"}"'
                  in line for line in se_lines),
              repr(se_lines))
        check("sealminer workmode bodies are ascset 0,workmode,{mode}",
              any('RPC ascset "0,workmode,{\\"mode\\":\\"normal\\"}"'
                  in line for line in se_lines)
              and any('RPC ascset "0,workmode,{\\"mode\\":\\"low_power\\"}"'
                      in line for line in se_lines),
              repr(se_lines))
        check("sealminer updatepools parameter is a JSON string",
              any(line.startswith("RPC updatepools")
                  and 'pools' in line
                  and "new.example.com:3333" in line
                  and "newuser.001" in line
                  and "stratum.braiins.com" not in line
                  for line in se_lines),
              repr(se_lines))
        up_idx = [i for i, line in enumerate(se_lines)
                  if line.startswith("RPC updatepools")]
        rb_idx = [i for i, line in enumerate(se_lines)
                  if "GET /cgi-bin/reboot.php" in line]
        check("sealminer switch_pool reboots after updatepools",
              bool(up_idx) and bool(rb_idx)
              and max(up_idx) < max(rb_idx),
              repr(se_lines))
        check("sealminer find_miner body is led_conf on",
              any('WEB POST /cgi-bin/led_conf.php {"key": "led", '
                  '"value": "on"}' in line for line in se_lines),
              repr(se_lines))

        se_bad = {"cgminer_port": SE_RPC, "http_port": SE_WEB,
                  "timeout": 2.0, "password": "wrong"}
        ok, msg = actions.execute(
            SE_HOST, "sealminer", "reboot", creds=se_bad)
        check("sealminer wrong password refused at login",
              not ok and "cookie" in msg, msg)
        ok, msg = actions.execute(
            SE_HOST, "sealminer", "set_mining_mode",
            payload={"mode": "bogus"}, creds=se_creds)
        check("sealminer set_mining_mode bogus refused client-side",
              not ok, msg)
        ok, msg = actions.execute(
            SE_HOST, "sealminer", "set_power_target",
            payload={"watts": -5}, creds=se_creds)
        check("sealminer set_power_target negative watts refused",
              not ok, msg)
        ok, msg = actions.execute(
            SE_HOST, "sealminer", "set_power_target",
            payload={}, creds=se_creds)
        check("sealminer set_power_target without watts refused",
              not ok, msg)
        ok, msg = actions.execute(
            SE_HOST, "sealminer", "switch_pool",
            payload={"pool_id": 0}, creds=se_creds)
        check("sealminer switch_pool without url/user refused",
              not ok, msg)

        # ------------------------- sealminer low_power gate + resume path
        se3_creds = {"cgminer_port": SE3_RPC, "http_port": SE3_WEB,
                     "timeout": 2.0}
        ok, msg = actions.execute(
            SE3_HOST, "sealminer", "set_mining_mode",
            payload={"mode": "low_power"}, creds=se3_creds)
        check("sealminer low_power refused on non-A2 (A3 mock)",
              not ok and "only supported on SealMiner A2" in msg, msg)
        ok, msg = actions.execute(
            SE3_HOST, "sealminer", "set_mining_mode",
            payload={"mode": "normal"}, creds=se3_creds)
        check("sealminer normal mode accepted on A3 mock", ok, msg)

        sep_creds = {"cgminer_port": SEP_RPC, "http_port": SEP_WEB,
                     "timeout": 2.0}
        ok, msg = actions.execute(
            SEP_HOST, "sealminer", "resume_mining", creds=sep_creds)
        check("sealminer resume_mining restarts when not Running",
              ok and "RPC restart" in msg, msg)
        check("sealminer stopped mock saw the RPC restart",
              any(line == "RPC restart" for line in
                  _log_lines(sep_log)),
              repr(_log_lines(sep_log)))

        # ------------------------------------------------------ inspect
        doc = inspect_mod.inspect_device(
            AU_HOST, timeout=2.0, http_port=CLOSED_HTTP,
            cgminer_port=AU_RPC)
        check("inspect auradine boards supported, 3 boards, 132 chips",
              doc.get("boards", {}).get("supported") is True
              and len(doc["boards"]["boards"]) == 3
              and [b["chips_total"] for b in doc["boards"]["boards"]]
              == [132, 132, 132]
              and [b["temp_c"] for b in doc["boards"]["boards"]]
              == [28.25, 29.06, 30.12],
              repr(doc.get("boards")))
        check("inspect auradine pools supported, 3 pools",
              doc.get("pools", {}).get("supported") is True
              and len(doc["pools"]["pools"]) == 3,
              repr(doc.get("pools")))
        check("inspect auradine fans supported, 4 rpm values",
              doc.get("fans", {}).get("supported") is True
              and [f["rpm"] for f in doc["fans"]["fans"]]
              == [7080, 7020, 7100, 7020],
              repr(doc.get("fans")))
        doc = inspect_mod.inspect_device(
            SE_HOST, timeout=2.0, http_port=SE_WEB,
            cgminer_port=SE_RPC)
        check("inspect sealminer boards supported, 3 boards, 153 chips",
              doc.get("boards", {}).get("supported") is True
              and len(doc["boards"]["boards"]) == 3
              and [b["chips_total"] for b in doc["boards"]["boards"]]
              == [153, 153, 153]
              and [b["temp_c"] for b in doc["boards"]["boards"]]
              == [70, 70, 70],
              repr(doc.get("boards")))
        check("inspect sealminer pools supported, 1 pool",
              doc.get("pools", {}).get("supported") is True
              and len(doc["pools"]["pools"]) == 1,
              repr(doc.get("pools")))
        check("inspect sealminer fans supported, 4 rpm values",
              doc.get("fans", {}).get("supported") is True
              and [f["rpm"] for f in doc["fans"]["fans"]]
              == [3723, 3723, 3753, 3723],
              repr(doc.get("fans")))

        # --------------------------------------------- pit-bit stays a gap
        check("no pit-bit adapter module exists",
              importlib.util.find_spec("beesky.core.pitbit") is None)
        check("no pit-bit cred tag exists (stock covers its protocol)",
              "pit-bit" not in CRED_TYPES)
    finally:
        for proc in procs:
            _stop(proc)

    print()
    print(f"vendors5: {len(FAILURES)} failures")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
