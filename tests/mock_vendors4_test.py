#!/usr/bin/env python3
"""v0.37.0 test — ePIC adapter from Epic's own published material
(docs/epic-mapping.md).

No hardware. Loopback mocks, one per contract:

  * tests/mock_epic.py on 127.0.0.1:14031 — an ePIC SC200
    (doc-shaped /summary + /capabilities; the control bodies
    are the dashboard's own handleApi shapes; the factory
    password is README's "letmein").
  * tests/mock_miner.py on 127.0.0.1:4028 — the established
    Antminer cgminer fixture (non-collision witness).
  * tests/mock_luxos.py on 127.0.0.1:14029 — the LUXminer
    fixture (non-collision witness).
  * tests/mock_braiins.py on 127.0.0.1:14030 — the BOSMiner
    fixture (non-collision witness).
  * tests/mock_whatsminer.py on 127.0.0.1:14028 — the
    Whatsminer fixture (non-collision witness).

Asserts: ePIC detection (structural gate + non-collision
against every other family) + reads (native MH/s, boards,
power, fan %, pools, hostname/coin) + every wired control
(reboot, restart, pause, find, preset, pool, password,
power, shutdown temp, fan speed, tune) + the honest
refusals (resume has no verified /miner value, wrong
password, out-of-range fan speed, missing tune params).
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
from beesky.core.discover import CRED_TYPES, probe_host  # noqa: E402
from beesky.core.epic import (EpicClient, EpicError,  # noqa: E402
                              is_epic_summary)

EPIC_HOST, EPIC_PORT = "127.0.0.1", 14031
CG_HOST, CG_PORT = "127.0.0.1", 4028
LUX_HOST, LUX_PORT = "127.0.0.1", 14029
BOS_HOST, BOS_PORT = "127.0.0.1", 14030
WM_HOST, WM_PORT = "127.0.0.1", 14028
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


class _Args:
    timeout = 1.5
    api_key = None
    token = None


EPIC_SUMMARY = {
    "Hostname": "epicminer30032518",
    "Session": {"Average MHs": 8500.5, "Uptime": 90000},
    "HBs": [{"Index": 0, "Temperature": 62}],
}


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="beesky-vendors4-"))
    epic_log = tmp / "epic.log"
    procs = [
        _spawn(["tests/mock_epic.py", EPIC_HOST, str(EPIC_PORT)],
               {"MOCK_EPIC_LOG": str(epic_log)}),
        _spawn(["tests/mock_miner.py"], {}),
        _spawn(["tests/mock_luxos.py", LUX_HOST, str(LUX_PORT)], {}),
        _spawn(["tests/mock_braiins.py", BOS_HOST, str(BOS_PORT)], {}),
        _spawn(["tests/mock_whatsminer.py", WM_HOST, str(WM_PORT)],
               {}),
    ]
    try:
        for host, port in ((EPIC_HOST, EPIC_PORT), (CG_HOST, CG_PORT),
                           (LUX_HOST, LUX_PORT), (BOS_HOST, BOS_PORT),
                           (WM_HOST, WM_PORT)):
            if not _wait_port(host, port):
                check(f"mock up {host}:{port}", False, "timeout")
                return 1

        # ------------------------------------------------- epic detection
        epic = EpicClient(EPIC_HOST, port=EPIC_PORT, timeout=2.0)
        summary = epic.summary()
        check("epic summary has Hostname + Session + HBs",
              summary.get("Hostname") == "epicminer30032518"
              and isinstance(summary.get("Session"), dict)
              and len(summary.get("HBs") or []) == 3,
              repr({k: summary.get(k) for k in
                    ("Hostname", "Session", "HBs")}))
        check("is_epic_summary true on the mock summary",
              is_epic_summary(summary))
        check("is_epic_summary false on stock cgminer shape",
              not is_epic_summary(
                  {"STATUS": [{"Description": "cgminer 4.9.2"}],
                   "SUMMARY": [{"GHS 5s": 100.0}]}))
        check("is_epic_summary false on dashd shape",
              not is_epic_summary({"miner": {"miner_type": "S19"}}))
        check("is_epic_summary false on near-misses",
              not is_epic_summary({})
              and not is_epic_summary(
                  {"Hostname": "epicminer1", "Session": {},
                   "HBs": []})
              and not is_epic_summary(
                  {"Hostname": "", "Session": {"Average MHs": 1.0},
                   "HBs": []})
              and not is_epic_summary(
                  {"Hostname": "epicminer1",
                   "Session": {"Average MHs": 1.0}, "HBs": {}}))
        check("is_epic_summary true on the bare gate shape",
              is_epic_summary(EPIC_SUMMARY))
        caps = epic.capabilities()
        check("capabilities Model SC200, presets + coins",
              (caps or {}).get("Model") == "SC200"
              and "Balanced" in (caps or {}).get("Presets", [])
              and "BTC" in (caps or {}).get("Coins", []),
              repr(caps))
        check("epic is a cred tag",
              "epic" in CRED_TYPES)

        epic_cand = probe_host(EPIC_HOST, timeout=1.5,
                               http_port=CLOSED_HTTP,
                               cgminer_port=EPIC_PORT)
        check("probe claims epic",
              epic_cand is not None and epic_cand.source == "epic",
              repr(epic_cand and epic_cand.source))
        cg_cand = probe_host(CG_HOST, timeout=1.5,
                             http_port=CLOSED_HTTP,
                             cgminer_port=CG_PORT)
        check("probe keeps stock cgminer (not epic)",
              cg_cand is not None and cg_cand.source == "cgminer",
              repr(cg_cand and cg_cand.source))
        lux_cand = probe_host(LUX_HOST, timeout=1.5,
                              http_port=CLOSED_HTTP,
                              cgminer_port=LUX_PORT)
        check("probe keeps luxos luxos (not epic)",
              lux_cand is not None and lux_cand.source == "luxos",
              repr(lux_cand and lux_cand.source))
        bos_cand = probe_host(BOS_HOST, timeout=1.5,
                              http_port=CLOSED_HTTP,
                              cgminer_port=BOS_PORT)
        check("probe keeps braiins braiins (not epic)",
              bos_cand is not None and bos_cand.source == "braiins",
              repr(bos_cand and bos_cand.source))
        wm_cand = probe_host(WM_HOST, timeout=1.5,
                             http_port=CLOSED_HTTP,
                             cgminer_port=WM_PORT)
        check("probe keeps whatsminer whatsminer (not epic)",
              wm_cand is not None and wm_cand.source == "whatsminer",
              repr(wm_cand and wm_cand.source))

        # --------------------------------------------------- epic record
        epic_rec = cli_mod._fetch_record(epic_cand, _Args())
        check("cli fetch epic record",
              epic_rec["source"] == "epic"
              and epic_rec["model"] == "SC200"
              and epic_rec["status"] == "OK",
              repr({k: epic_rec.get(k) for k in
                    ("source", "model", "status")}))
        check("epic native rate 8500.5 MH/s",
              epic_rec["rate_value"] == 8500.5
              and epic_rec["rate_unit"] == "MH/s",
              repr((epic_rec.get("rate_value"),
                    epic_rec.get("rate_unit"))))
        check("epic elapsed 90000 s, power 3300 W",
              epic_rec["elapsed_s"] == 90000
              and epic_rec["power_w"] == 3300.0,
              repr((epic_rec.get("elapsed_s"),
                    epic_rec.get("power_w"))))
        check("epic 3 boards, chips 0/0, temps 62/68/65",
              len(epic_rec["chains"]) == 3
              and epic_rec["chips_total"] == 0
              and epic_rec["chips_alive"] == 0
              and [c["temp_c"] for c in epic_rec["chains"]]
              == [62.0, 68.0, 65.0],
              repr(epic_rec.get("chains")))
        check("epic fans: no rpm, fan_speed_pct 80",
              epic_rec["fans_rpm"] == []
              and epic_rec.get("fan_speed_pct") == 80,
              repr((epic_rec.get("fans_rpm"),
                    epic_rec.get("fan_speed_pct"))))
        check("epic pools: 2, first Alive, no passwords",
              len(epic_rec.get("pools") or []) == 2
              and epic_rec["pools"][0]["status"] == "Alive"
              and epic_rec["pools"][1]["status"] == "Dead"
              and epic_rec["pools"][0]["worker"]
              == "wallet123.worker001"
              and all("pass" not in p and "password" not in p
                      for p in (epic_rec.get("pools") or [])),
              repr(epic_rec.get("pools")))
        check("epic hostname + coin on the record",
              epic_rec.get("hostname") == "epicminer30032518"
              and epic_rec.get("coin") == "BTC",
              repr({k: epic_rec.get(k) for k in
                    ("hostname", "coin")}))
        check("reads never POST",
              all(line.startswith("GET ")
                  for line in _log_lines(epic_log)),
              repr(_log_lines(epic_log)))

        # --------------------------------------------------- epic actions
        creds = {"cgminer_port": EPIC_PORT, "timeout": 2.0}
        ok, msg = actions.execute(
            EPIC_HOST, "epic", "reboot", creds=creds)
        check("epic reboot accepted", ok, msg)
        ok, msg = actions.execute(
            EPIC_HOST, "epic", "restart_mining", creds=creds)
        check("epic restart_mining accepted (softreboot)", ok, msg)
        ok, msg = actions.execute(
            EPIC_HOST, "epic", "pause_mining", creds=creds)
        check("epic pause_mining accepted (/miner stop)", ok, msg)
        ok, msg = actions.execute(
            EPIC_HOST, "epic", "resume_mining", creds=creds)
        check("epic resume_mining honestly unsupported",
              not ok and "not supported" in msg, msg)
        ok, msg = actions.execute(
            EPIC_HOST, "epic", "find_miner", creds=creds)
        check("epic find_miner accepted (/identify on)", ok, msg)
        ok, msg = actions.execute(
            EPIC_HOST, "epic", "set_preset",
            payload={"preset": "Balanced", "power_target": 3300},
            creds=creds)
        check("epic set_preset accepted (/mode)", ok, msg)
        ok, msg = actions.execute(
            EPIC_HOST, "epic", "switch_pool",
            payload={"url": "stratum+tcp://new.example.com:3333",
                     "user": "wallet123.worker002", "pool_id": 0},
            creds=creds)
        check("epic switch_pool accepted (/coin)", ok, msg)
        ok, msg = actions.execute(
            EPIC_HOST, "epic", "change_password",
            payload={"new_password": "hunter2"}, creds=creds)
        check("epic change_password accepted (/password)", ok, msg)
        ok, msg = actions.execute(
            EPIC_HOST, "epic", "set_power_target",
            payload={"watts": 2000}, creds=creds)
        check("epic set_power_target accepted (/power)", ok, msg)
        ok, msg = actions.execute(
            EPIC_HOST, "epic", "set_shutdown_temp",
            payload={"temp_c": 80}, creds=creds)
        check("epic set_shutdown_temp accepted", ok, msg)
        ok, msg = actions.execute(
            EPIC_HOST, "epic", "set_fan_speed",
            payload={"speed": 90}, creds=creds)
        check("epic set_fan_speed accepted", ok, msg)
        ok, msg = actions.execute(
            EPIC_HOST, "epic", "tune",
            payload={"clock_mhz": 550, "voltage_mv": 12500},
            creds=creds)
        check("epic tune accepted", ok, msg)

        lines = _log_lines(epic_log)
        check("control bodies match the dashboard shapes",
              any("POST /reboot param=0" in line for line in lines)
              and any("POST /softreboot param=0" in line
                      for line in lines)
              and any('POST /miner param="stop"' in line
                      for line in lines)
              and any("POST /identify param=true" in line
                      for line in lines)
              and any("POST /fanspeed param=90" in line
                      for line in lines)
              and any("POST /tune param=" in line
                      and "clks" in line and "voltage" in line
                      for line in lines)
              and any("POST /coin param=" in line
                      and "pool_url" in line for line in lines),
              repr(lines))
        get_idx = [i for i, line in enumerate(lines)
                   if "GET /summary" in line]
        post_idx = [i for i, line in enumerate(lines)
                    if "POST /coin" in line]
        check("switch_pool read /summary first, then POSTed /coin",
              bool(get_idx) and bool(post_idx)
              and min(get_idx) < min(post_idx),
              repr(lines))

        bad_creds = {"cgminer_port": EPIC_PORT, "timeout": 2.0,
                     "password": "wrong"}
        ok, msg = actions.execute(
            EPIC_HOST, "epic", "reboot", creds=bad_creds)
        check("epic wrong password refused",
              not ok and "wrong password" in msg, msg)
        ok, msg = actions.execute(
            EPIC_HOST, "epic", "set_fan_speed",
            payload={"speed": 0}, creds=creds)
        check("epic fan speed 0 refused client-side",
              not ok, msg)
        ok, msg = actions.execute(
            EPIC_HOST, "epic", "tune",
            payload={"clock_mhz": 550}, creds=creds)
        check("epic tune without voltage refused client-side",
              not ok, msg)
        ok, msg = actions.execute(
            EPIC_HOST, "epic", "set_preset",
            payload={}, creds=creds)
        check("epic set_preset without preset refused",
              not ok, msg)
        ok, msg = actions.execute(
            EPIC_HOST, "epic", "switch_pool",
            payload={"pool_id": 0}, creds=creds)
        check("epic switch_pool without url/user refused",
              not ok, msg)

        # --------------------------------------------------- epic inspect
        doc = inspect_mod.inspect_device(
            EPIC_HOST, timeout=2.0, http_port=CLOSED_HTTP,
            cgminer_port=EPIC_PORT)
        check("inspect epic boards supported, 3 boards, temps",
              doc.get("boards", {}).get("supported") is True
              and len(doc["boards"]["boards"]) == 3
              and [b["temp_c"] for b in doc["boards"]["boards"]]
              == [62.0, 68.0, 65.0]
              and all(b["chips_total"] == 0
                      for b in doc["boards"]["boards"]),
              repr(doc.get("boards")))
        check("inspect epic pools supported, 2 pools",
              doc.get("pools", {}).get("supported") is True
              and len(doc["pools"]["pools"]) == 2,
              repr(doc.get("pools")))
        check("inspect epic fans: pct 80, no rpm pretence",
              doc.get("fans", {}).get("supported") is True
              and doc["fans"].get("fan_speed_pct") == 80
              and doc["fans"].get("fans") == [],
              repr(doc.get("fans")))

        # --------------------------------------------- jasminer stays a gap
        check("no jasminer adapter module exists",
              importlib.util.find_spec("beesky.core.jasminer") is None)
        check("jasminer is a cred tag only",
              "jasminer" in CRED_TYPES)
    finally:
        for proc in procs:
            _stop(proc)

    print()
    print(f"vendors4: {len(FAILURES)} failures")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
