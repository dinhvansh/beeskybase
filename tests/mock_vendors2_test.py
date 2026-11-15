#!/usr/bin/env python3
"""v0.33.0 test — docs-based vendor adapters (docs/vendor-docs-mapping.md).

No hardware. Loopback mocks, one per contract:

  * tests/mock_whatsminer.py on 127.0.0.1:14028 — the MicroBT
    dialect WITH the token flow (get_token returns the manuals'
    own worked-example salts; privileged commands accept only
    the openssl-derived sign for password "admin").
  * tests/mock_luxos.py on 127.0.0.1:14029 — a LUXminer on the
    cgminer-compatible TCP API (version Description "LUXminer
    2024.5.1.155432-f2badc0f", logon/logoff/curtail/rebootdevice).
  * tests/mock_miner.py on 127.0.0.1:4028 — the established
    Antminer cgminer fixture (non-collision witness).
  * tests/mock_avalon.py on 127.0.0.2:14028 — the Avalon
    refinement witness (still refined, never luxos).

Asserts: the md5crypt implementation against the manuals' worked
example + independent openssl vectors; the Whatsminer token flow
end-to-end (G-W1 closed); LuxOS detection + reads + session
actions; reads never mint tokens/sessions; Braiins/IceRiver/
Jasminer stay honest gaps. Prints PASS lines; exit 1 on failure.
"""

import argparse
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
from beesky.core import actions, inspect as inspect_mod, ops  # noqa: E402
from beesky.core.discover import probe_host  # noqa: E402
from beesky.core.luxos import (LuxosClient, LuxosError,  # noqa: E402
                               is_luxos_version)
from beesky.core.md5crypt import md5crypt, md5crypt_checksum  # noqa: E402
from beesky.core.whatsminer import (WhatsminerClient,  # noqa: E402
                                    WhatsminerError, whatsminer_token)

WM_HOST, WM_PORT = "127.0.0.1", 14028
LUX_HOST, LUX_PORT = "127.0.0.1", 14029
CG_HOST, CG_PORT = "127.0.0.1", 4028
AV_HOST, AV_PORT = "127.0.0.2", 14028
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


def _log_lines(path: Path) -> list[str]:
    return path.read_text().split() if path.exists() else []


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="beesky-vendors2-"))
    wm_log = tmp / "wm.log"
    lux_log = tmp / "lux.log"
    procs = [
        _spawn(["tests/mock_whatsminer.py", WM_HOST, str(WM_PORT)],
               {"MOCK_WM_LOG": str(wm_log)}),
        _spawn(["tests/mock_luxos.py", LUX_HOST, str(LUX_PORT)],
               {"MOCK_LUXOS_LOG": str(lux_log)}),
        _spawn(["tests/mock_miner.py"], {}),
        _spawn(["tests/mock_avalon.py", AV_HOST, str(AV_PORT)], {}),
    ]
    try:
        for host, port in ((WM_HOST, WM_PORT), (LUX_HOST, LUX_PORT),
                           (CG_HOST, CG_PORT), (AV_HOST, AV_PORT)):
            if not _wait_port(host, port):
                check(f"mock up {host}:{port}", False, "timeout")
                return 1

        # ------------------------------------------------- md5crypt gold
        # The manuals' worked example (V2.0.5 §3): time 5626,
        # salt BQ5hoXV9, newsalt jbzkfQls, password admin — values
        # generated with the manuals' own reference implementation
        # (openssl passwd -1). If either differs, the token flow
        # is wrong, not the test.
        check("md5crypt key vector (manual example)",
              md5crypt_checksum("admin", "BQ5hoXV9")
              == "RxmaDUO33TS7O26yeMHZ81",
              md5crypt_checksum("admin", "BQ5hoXV9"))
        check("md5crypt sign vector (manual example)",
              md5crypt_checksum("RxmaDUO33TS7O26yeMHZ81" + "5626",
                                "jbzkfQls") == "w.BNbkCV6n1aNWgiBWLzT/",
              md5crypt_checksum("RxmaDUO33TS7O26yeMHZ81" + "5626",
                                "jbzkfQls"))
        check("md5crypt full string shape",
              md5crypt("admin", "BQ5hoXV9")
              == "$1$BQ5hoXV9$RxmaDUO33TS7O26yeMHZ81")
        # Independent openssl cross-check (a different salt/pw).
        check("md5crypt openssl cross-check",
              md5crypt("hello", "test1234")
              == "$1$test1234$qbJVC/fSdpCHTWhsSFR2/1",
              md5crypt("hello", "test1234"))
        check("md5crypt empty password",
              md5crypt("", "abcd1234")
              == "$1$abcd1234$Ue16.AjYlcqaFMJ2JWtBS0",
              md5crypt("", "abcd1234"))
        key, sign = whatsminer_token("admin", "5626",
                                     "BQ5hoXV9", "jbzkfQls")
        check("whatsminer_token worked example",
              (key, sign) == ("RxmaDUO33TS7O26yeMHZ81",
                              "w.BNbkCV6n1aNWgiBWLzT/"),
              f"{key} / {sign}")
        # Only the last four chars of time enter the sign.
        check("whatsminer_token uses last4(time)",
              whatsminer_token("admin", "99995626",
                               "BQ5hoXV9", "jbzkfQls") == (key, sign))

        # -------------------------------------------------- whatsminer flow
        wm = WhatsminerClient(WM_HOST, port=WM_PORT, timeout=2.0)
        token_resp = wm.command("get_token")
        fields = token_resp.get("Msg") or {}
        check("wm get_token returns manual example fields",
              fields.get("time") == "5626"
              and fields.get("salt") == "BQ5hoXV9"
              and fields.get("newsalt") == "jbzkfQls",
              repr(fields))
        check("wm mint_token reproduces worked-example sign",
              wm.mint_token("admin") == "w.BNbkCV6n1aNWgiBWLzT/")
        wm.privileged("restart_btminer", "admin")
        check("wm privileged restart_btminer accepted", True)
        try:
            wm.privileged("restart_btminer", "wrong-password")
            refusal = ""
        except WhatsminerError as exc:
            refusal = str(exc)
        check("wm wrong password refused with Code 135 text",
              "check token error" in refusal, refusal)
        try:
            wm.command("restart_btminer")
            refusal2 = ""
        except WhatsminerError as exc:
            refusal2 = str(exc)
        check("wm bare privileged call refused without token",
              "check token error" in refusal2, refusal2)

        # Reads must never mint a token: snapshot the mint count
        # (the direct client calls above already minted 4) and
        # prove probe + fetch add none.
        wm_tokens_before_reads = _log_lines(wm_log).count("get_token")
        wm_cand = probe_host(WM_HOST, timeout=1.5,
                             http_port=CLOSED_HTTP, cgminer_port=WM_PORT)
        check("probe claims whatsminer (unchanged)",
              wm_cand is not None and wm_cand.source == "whatsminer",
              repr(wm_cand and wm_cand.source))
        args = argparse.Namespace(timeout=1.5, api_key=None, token=None)
        wm_rec = cli_mod._fetch_record(wm_cand, args)
        check("cli fetch whatsminer record (unchanged)",
              wm_rec["source"] == "whatsminer"
              and abs(wm_rec["rate_value"] - 111.8) < 1e-6,
              repr(wm_rec.get("rate_value")))
        check("reads never send get_token",
              _log_lines(wm_log).count("get_token")
              == wm_tokens_before_reads,
              repr(_log_lines(wm_log)))

        # ------------------------------------------- whatsminer actions
        # Each action mints exactly one token; count them at the end.
        ok, msg = actions.execute(
            WM_HOST, "whatsminer", "reboot",
            creds={"cgminer_port": WM_PORT, "timeout": 2.0,
                   "password": "admin"})
        check("whatsminer reboot (G-W1 closed)", ok, msg)
        ok, msg = actions.execute(
            WM_HOST, "whatsminer", "restart_mining",
            creds={"cgminer_port": WM_PORT, "timeout": 2.0,
                   "password": "admin"})
        check("whatsminer restart_mining rides restart_btminer", ok, msg)
        ok, msg = actions.execute(
            WM_HOST, "whatsminer", "pause_mining",
            creds={"cgminer_port": WM_PORT, "timeout": 2.0,
                   "password": "admin"})
        check("whatsminer pause_mining rides power_off", ok, msg)
        ok, msg = actions.execute(
            WM_HOST, "whatsminer", "resume_mining",
            creds={"cgminer_port": WM_PORT, "timeout": 2.0,
                   "password": "admin"})
        check("whatsminer resume_mining rides power_on", ok, msg)
        ok, msg = actions.execute(
            WM_HOST, "whatsminer", "find_miner",
            creds={"cgminer_port": WM_PORT, "timeout": 2.0,
                   "password": "admin"})
        check("whatsminer find_miner rides set_led auto", ok, msg)
        ok, msg = actions.execute(
            WM_HOST, "whatsminer", "switch_pool",
            {"pool_id": 1, "url": "stratum+tcp://new.pool:3333",
             "user": "newworker.001", "password": "x"},
            creds={"cgminer_port": WM_PORT, "timeout": 2.0,
                   "password": "admin"})
        check("whatsminer switch_pool rewrites slot 1", ok, msg)
        wm_cmds = _log_lines(wm_log)
        check("mock saw update_pools payload shape",
              "update_pools:pool1=:worker1=:pool2=stratum+tcp://new.pool:3333"
              ":worker2=newworker.001:pool3=:worker3=" in wm_cmds,
              repr(wm_cmds))
        ok, msg = actions.execute(
            WM_HOST, "whatsminer", "switch_pool", {"pool_id": 1},
            creds={"cgminer_port": WM_PORT, "timeout": 2.0,
                   "password": "admin"})
        check("whatsminer switch_pool needs url+user (honest)",
              not ok and "url" in msg and "user" in msg, msg)
        ok, msg = actions.execute(
            WM_HOST, "whatsminer", "switch_pool",
            {"pool_id": 5, "url": "stratum+tcp://p:3333", "user": "u"},
            creds={"cgminer_port": WM_PORT, "timeout": 2.0,
                   "password": "admin"})
        check("whatsminer switch_pool rejects pool_id 5",
              not ok and "0-2" in msg, msg)
        ok, msg = actions.execute(
            WM_HOST, "whatsminer", "reboot",
            creds={"cgminer_port": WM_PORT, "timeout": 2.0})
        check("whatsminer reboot falls back to default admin",
              ok and "default admin password" in msg, msg)
        # Token mint count: get_token (1) + mint_token (1) +
        # privileged restart (1) + wrong-password attempt (1) +
        # 6 action calls + default-password reboot (1) = 11.
        # (The bare command() call and the two failing
        # switch_pool calls mint nothing.)
        check("one token mint per privileged call, nothing else",
              _log_lines(wm_log).count("get_token") == 11,
              repr(_log_lines(wm_log).count("get_token")))

        # -------------------------------------------- luxos fingerprint
        lux = LuxosClient(LUX_HOST, port=LUX_PORT, timeout=2.0)
        check("luxos version fingerprint positive",
              is_luxos_version(lux.version()))
        check("luxos fingerprint negative on stock description",
              not is_luxos_version(
                  {"STATUS": [{"Description": "cgminer 4.11.1"}]}))
        check("luxos fingerprint negative on bmminer description",
              not is_luxos_version(
                  {"STATUS": [{"Description": "bmminer 2.0.0"}]}))
        check("luxos fingerprint negative on empty reply",
              not is_luxos_version({})
              and not is_luxos_version({"STATUS": []}))
        check("luxos client is_luxos()", lux.is_luxos())
        try:
            lux.curtail("bogus")
            curtail_bad = ""
        except LuxosError as exc:
            curtail_bad = str(exc)
        check("luxos curtail rejects unknown action",
              "unknown curtail action" in curtail_bad, curtail_bad)

        # ------------------------------------------------ luxos probing
        lux_cand = probe_host(LUX_HOST, timeout=1.5,
                              http_port=CLOSED_HTTP, cgminer_port=LUX_PORT)
        check("probe claims luxos",
              lux_cand is not None and lux_cand.source == "luxos",
              repr(lux_cand and lux_cand.source))
        cg_cand = probe_host(CG_HOST, timeout=1.5,
                             http_port=CLOSED_HTTP, cgminer_port=CG_PORT)
        check("probe keeps antminer cgminer (no luxos mis-claim)",
              cg_cand is not None and cg_cand.source == "cgminer",
              repr(cg_cand and cg_cand.source))
        av_cand = probe_host(AV_HOST, timeout=1.5,
                             http_port=CLOSED_HTTP, cgminer_port=AV_PORT)
        check("probe still refines avalon, not luxos",
              av_cand is not None and av_cand.source == "avalon",
              repr(av_cand and av_cand.source))

        # Reads must not logon: snapshot the lux log after probe
        # + fetch, before any action.
        lux_rec = cli_mod._fetch_record(lux_cand, args)
        check("cli fetch luxos record source",
              lux_rec["source"] == "luxos", repr(lux_rec.get("source")))
        check("luxos record model",
              lux_rec["model"] == "Antminer S19 Pro",
              repr(lux_rec.get("model")))
        check("luxos record native rate",
              lux_rec["rate_unit"] == "TH/s"
              and abs(lux_rec["rate_value"] - 109.13) < 1e-6,
              f"{lux_rec['rate_value']} {lux_rec['rate_unit']}")
        check("luxos record ths agrees",
              abs(lux_rec["ths"] - 109.13) < 1e-6, str(lux_rec["ths"]))
        check("luxos record chains temps",
              [c["temp_c"] for c in lux_rec["chains"]] == [61.0, 87.0, 63.0],
              repr(lux_rec["chains"]))
        check("luxos record board 2 chips 112/114",
              lux_rec["chains"][1]["chips_total"] == 114
              and lux_rec["chains"][1]["chips_alive"] == 112
              and lux_rec["chains"][1]["dead_positions"] == [61, 113],
              repr(lux_rec["chains"][1]))
        check("luxos record over-temp diagnosis",
              any(p["code"] == "OVER_TEMP" and p["chain"] == 2
                  for p in lux_rec["problems"]),
              repr(lux_rec["problems"]))
        check("luxos record pools verbatim",
              (lux_rec.get("pools") or [{}])[0].get("worker")
              == "luxosworker.001", repr(lux_rec.get("pools")))
        check("luxos record power unread (no power field)",
              lux_rec["power_w"] is None)
        ops_rec = ops._fetch_record(lux_cand, 1.5)
        check("ops fetch luxos record",
              ops_rec["source"] == "luxos"
              and ops_rec["model"] == "Antminer S19 Pro",
              repr(ops_rec.get("source")))
        check("luxos reads never logon",
              "logon" not in _log_lines(lux_log),
              repr(_log_lines(lux_log)))

        # ------------------------------------------------ luxos inspect
        doc = inspect_mod.inspect_device(
            LUX_HOST, timeout=1.5, http_port=CLOSED_HTTP,
            cgminer_port=LUX_PORT)
        check("inspect luxos source", doc.get("source") == "luxos",
              repr(doc.get("source")))
        check("inspect luxos boards",
              doc["boards"].get("supported") is True
              and len(doc["boards"]["boards"]) == 3
              and doc["boards"]["boards"][1]["temp_c"] == 87.0,
              repr(doc.get("boards")))
        check("inspect luxos pools",
              doc["pools"].get("supported") is True
              and doc["pools"]["pools"][0]["status"] == "Alive",
              repr(doc.get("pools")))
        check("inspect luxos fans",
              doc["fans"].get("supported") is True
              and [f["rpm"] for f in doc["fans"]["fans"]] == [4320, 4380],
              repr(doc.get("fans")))

        # ------------------------------------------------ luxos actions
        ok, msg = actions.execute(
            LUX_HOST, "luxos", "reboot",
            creds={"cgminer_port": LUX_PORT, "timeout": 2.0})
        check("luxos reboot rides rebootdevice", ok, msg)
        ok, msg = actions.execute(
            LUX_HOST, "luxos", "pause_mining",
            creds={"cgminer_port": LUX_PORT, "timeout": 2.0})
        check("luxos pause_mining rides curtail sleep", ok, msg)
        check("luxos pause message names the wakeup-only rule",
              "ONLY" in msg and "resume_mining" in msg, msg)
        ok, msg = actions.execute(
            LUX_HOST, "luxos", "resume_mining",
            creds={"cgminer_port": LUX_PORT, "timeout": 2.0})
        check("luxos resume_mining rides curtail wakeup", ok, msg)
        lux_cmds = _log_lines(lux_log)
        check("luxos session flow is logon -> curtail -> logoff",
              lux_cmds.count("logon") == 2
              and lux_cmds.count("curtail") == 2
              and lux_cmds.count("logoff") == 2
              and lux_cmds.index("logon") < lux_cmds.index("curtail")
              < lux_cmds.index("logoff"),
              repr(lux_cmds))
        check("luxos mock saw rebootdevice",
              "rebootdevice" in lux_cmds, repr(lux_cmds))

        # --------------------------------------------- remaining gaps
        for family in ("braiins", "iceriver", "jasminer"):
            ok, msg = actions.execute(
                LUX_HOST, family, "reboot",
                creds={"cgminer_port": LUX_PORT, "timeout": 2.0})
            check(f"{family} reboot stays the honest gap",
                  not ok and "unknown miner source" in msg, msg)
    finally:
        for proc in procs:
            proc.terminate()
        for proc in procs:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURES: {FAILURES}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
