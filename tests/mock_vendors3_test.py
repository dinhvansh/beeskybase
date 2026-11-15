#!/usr/bin/env python3
"""v0.36.0 test — Braiins + IceRiver adapters from open-source
implementations (docs/vendor-oss-mapping.md).

No hardware. Loopback mocks, one per contract:

  * tests/mock_braiins.py on 127.0.0.1:14030 — a BOSMiner on the
    cgminer-compatible TCP API (version Description "BOSminer+
    0.2.0-ea64aec8e", the Academy's string; summary MHS 1m,
    fans/temps/tunerstatus/devdetails in the Academy's shapes;
    pause/resume with PAUSE/RESUME sections).
  * tests/mock_iceriver.py on 127.0.0.1:18082 — an IceRiver KS0
    Ultra (the HackMD captured packet, verbatim: softver1
    ICM168_3_2_14_ks0ultra_miner, rtpow 359G, one board of 18
    chips, three pools, mac 00:0a:66:30:00:6d).
  * tests/mock_miner.py on 127.0.0.1:4028 — the established
    Antminer cgminer fixture (non-collision witness).
  * tests/mock_luxos.py on 127.0.0.1:14029 — the LUXminer
    fixture (non-collision witness: luxos must stay luxos,
    never braiins).

Asserts: Braiins detection + reads + pause/resume + the TUNER
problem path; IceRiver detection (title + shape gates) + reads
in both response shapes + find_miner; non-collision of both
fingerprints against every other family; Jasminer stays an
honest gap. Prints PASS lines; exit 1 on failure.
"""

import argparse
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
from beesky.core.braiins import (BraiinsClient, BraiinsError,  # noqa: E402
                                 is_braiins_version)
from beesky.core.discover import CRED_TYPES, probe_host  # noqa: E402
from beesky.core.iceriver import (IceRiverClient, IceRiverError,  # noqa: E402
                                  is_iceriver_panel, parse_model,
                                  parse_runtime)

BOS_HOST, BOS_PORT = "127.0.0.1", 14030
ICE_HOST, ICE_PORT = "127.0.0.1", 18082
CG_HOST, CG_PORT = "127.0.0.1", 4028
LUX_HOST, LUX_PORT = "127.0.0.1", 14029
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


def _args() -> argparse.Namespace:
    return argparse.Namespace(timeout=1.5, api_key=None, token=None)


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="beesky-vendors3-"))
    bos_log = tmp / "bos.log"
    ice_log = tmp / "ice.log"
    procs = [
        _spawn(["tests/mock_braiins.py", BOS_HOST, str(BOS_PORT)],
               {"MOCK_BRAIINS_LOG": str(bos_log)}),
        _spawn(["tests/mock_iceriver.py", ICE_HOST, str(ICE_PORT)],
               {"MOCK_ICERIVER_LOG": str(ice_log)}),
        _spawn(["tests/mock_miner.py"], {}),
        _spawn(["tests/mock_luxos.py", LUX_HOST, str(LUX_PORT)], {}),
    ]
    try:
        for host, port in ((BOS_HOST, BOS_PORT), (ICE_HOST, ICE_PORT),
                           (CG_HOST, CG_PORT), (LUX_HOST, LUX_PORT)):
            if not _wait_port(host, port):
                check(f"mock up {host}:{port}", False, "timeout")
                return 1

        # ------------------------------------------------ braiins detect
        bos = BraiinsClient(BOS_HOST, port=BOS_PORT, timeout=2.0)
        version = bos.version()
        check("braiins version carries BOSminer+ Description",
              "BOSminer+" in str(
                  version.get("STATUS", [{}])[0].get("Description")),
              repr(version.get("STATUS")))
        check("is_braiins_version true on bosminer reply",
              is_braiins_version(version))
        check("is_braiins_version false on stock cgminer reply",
              not is_braiins_version(
                  {"STATUS": [{"STATUS": "S", "Description":
                               "cgminer 4.9.2"}],
                   "VERSION": [{"CGMiner": "4.9.2", "API": "3.7",
                                "Miner": "cgminer"}]}))
        check("is_braiins_version false on luxos reply",
              not is_braiins_version(
                  {"STATUS": [{"STATUS": "S", "Description":
                               "LUXminer 2024.5.1.155432-f2badc0f"}],
                   "VERSION": [{"Miner": "LUXminer 2024.5.1"}]}))
        check("is_braiins_version false on whatsminer summary",
              not is_braiins_version(
                  {"SUMMARY": [{"MHS 5s": 100.0}],
                   "STATUS": [{"STATUS": "S",
                               "Description": "WhatsMiner"}]}))

        bos_cand = probe_host(BOS_HOST, timeout=1.5,
                              http_port=CLOSED_HTTP,
                              cgminer_port=BOS_PORT)
        check("probe claims braiins",
              bos_cand is not None and bos_cand.source == "braiins",
              repr(bos_cand and bos_cand.source))
        lux_cand = probe_host(LUX_HOST, timeout=1.5,
                              http_port=CLOSED_HTTP,
                              cgminer_port=LUX_PORT)
        check("probe keeps luxos luxos (not braiins)",
              lux_cand is not None and lux_cand.source == "luxos",
              repr(lux_cand and lux_cand.source))
        cg_cand = probe_host(CG_HOST, timeout=1.5,
                             http_port=CLOSED_HTTP,
                             cgminer_port=CG_PORT)
        check("probe keeps stock cgminer (not braiins)",
              cg_cand is not None and cg_cand.source == "cgminer",
              repr(cg_cand and cg_cand.source))

        # -------------------------------------------------- braiins record
        bos_rec = cli_mod._fetch_record(bos_cand, _args())
        check("cli fetch braiins record",
              bos_rec["source"] == "braiins"
              and bos_rec["model"] == "Bitmain Antminer S19 Pro"
              and bos_rec["status"] == "OK",
              repr({k: bos_rec.get(k) for k in
                    ("source", "model", "status")}))
        check("braiins native rate 110.5 TH/s from MHS 1m",
              abs(bos_rec["rate_value"] - 110.5) < 1e-9
              and bos_rec["rate_unit"] == "TH/s",
              repr((bos_rec.get("rate_value"),
                    bos_rec.get("rate_unit"))))
        check("braiins elapsed 90000 s",
              bos_rec["elapsed_s"] == 90000, repr(bos_rec.get("elapsed_s")))
        check("braiins power 3250 W from tunerstatus",
              bos_rec["power_w"] == 3250.0, repr(bos_rec.get("power_w")))
        check("braiins 3 boards, 342 chips, temps 71/73/69",
              len(bos_rec["chains"]) == 3
              and bos_rec["chips_total"] == 342
              and bos_rec["chips_alive"] == 342
              and [c["temp_c"] for c in bos_rec["chains"]]
              == [71.0, 73.0, 69.0],
              repr(bos_rec.get("chains")))
        check("braiins fans 5340/4620/0/0",
              bos_rec["fans_rpm"] == [5340, 4620, 0, 0],
              repr(bos_rec.get("fans_rpm")))
        check("braiins pool enriched, Alive",
              len(bos_rec.get("pools") or []) == 1
              and bos_rec["pools"][0]["status"] == "Alive"
              and bos_rec["pools"][0]["worker"] == "braiinsuser.001",
              repr(bos_rec.get("pools")))
        check("reads never pause/resume",
              "pause" not in _log_lines(bos_log)
              and "resume" not in _log_lines(bos_log),
              repr(_log_lines(bos_log)))

        # -------------------------------------------- braiins pause/resume
        ok, msg = actions.execute(
            BOS_HOST, "braiins", "pause_mining",
            creds={"cgminer_port": BOS_PORT, "timeout": 2.0})
        check("braiins pause_mining accepted", ok, msg)
        ok, msg = actions.execute(
            BOS_HOST, "braiins", "resume_mining",
            creds={"cgminer_port": BOS_PORT, "timeout": 2.0})
        check("braiins resume_mining accepted", ok, msg)
        check("pause/resume reached the mock",
              "pause" in _log_lines(bos_log)
              and "resume" in _log_lines(bos_log),
              repr(_log_lines(bos_log)))
        ok, msg = actions.execute(
            BOS_HOST, "braiins", "reboot",
            creds={"cgminer_port": BOS_PORT, "timeout": 2.0})
        check("braiins reboot honestly unsupported",
              not ok and "unknown miner source" in msg, msg)

        doc = inspect_mod.inspect_device(
            BOS_HOST, timeout=2.0, http_port=CLOSED_HTTP,
            cgminer_port=BOS_PORT)
        check("inspect braiins boards supported, 3 x 114 chips",
              doc.get("boards", {}).get("supported") is True
              and len(doc["boards"]["boards"]) == 3
              and all(b["chips_total"] == 114
                      for b in doc["boards"]["boards"]),
              repr(doc.get("boards")))
        check("inspect braiins pools+fans supported",
              doc.get("pools", {}).get("supported") is True
              and doc.get("fans", {}).get("supported") is True,
              repr({k: doc.get(k) for k in ("pools", "fans")}))

        # ------------------------------------------------- iceriver detect
        ice = IceRiverClient(ICE_HOST, port=ICE_PORT, timeout=2.0)
        check("iceriver console title gate",
              ice.has_console_title())
        panel = ice.userpanel()
        check("is_iceriver_panel true on captured packet",
              is_iceriver_panel(panel))
        check("is_iceriver_panel true on wrapped shape",
              is_iceriver_panel(
                  {"error": 0,
                   "userpanel": {"data": {"softver1": "x_ks0_miner"}}}))
        check("is_iceriver_panel false on stock/dashd payloads",
              not is_iceriver_panel({"miner": {"miner_type": "S19"}})
              and not is_iceriver_panel(
                  {"STATUS": [{"Description": "cgminer 4.9.2"}]})
              and not is_iceriver_panel({"error": 1, "data": {}}))
        check("parse_model KS0ULTRA",
              parse_model("ICM168_3_2_14_ks0ultra_miner") == "KS0ULTRA",
              parse_model("ICM168_3_2_14_ks0ultra_miner"))
        check("parse_runtime 00:01:15:16 -> 4516 s",
              parse_runtime("00:01:15:16") == 4516,
              repr(parse_runtime("00:01:15:16")))

        ice_cand = probe_host(ICE_HOST, timeout=1.5,
                              http_port=ICE_PORT,
                              cgminer_port=CLOSED_RPC)
        check("probe claims iceriver, model KS0ULTRA, default pwd",
              ice_cand is not None and ice_cand.source == "iceriver"
              and ice_cand.model == "KS0ULTRA"
              and ice_cand.iceriver_password == "12345678",
              repr(ice_cand and (ice_cand.source, ice_cand.model,
                                 ice_cand.iceriver_password)))
        ice_cand2 = probe_host(
            ICE_HOST, timeout=1.5, http_port=ICE_PORT,
            cgminer_port=CLOSED_RPC,
            creds=[{"label": "ice", "user": "admin",
                    "password": "hunter2", "type": "iceriver"}])
        check("probe tries iceriver-tagged password first",
              ice_cand2 is not None
              and ice_cand2.iceriver_password == "hunter2",
              repr(ice_cand2 and ice_cand2.iceriver_password))

        # ------------------------------------------------- iceriver record
        ice_rec = cli_mod._fetch_record(ice_cand, _args())
        check("cli fetch iceriver record",
              ice_rec["source"] == "iceriver"
              and ice_rec["model"] == "KS0ULTRA"
              and ice_rec["status"] == "OK",
              repr({k: ice_rec.get(k) for k in
                    ("source", "model", "status")}))
        check("iceriver native rate 359 GH/s from rtpow+unit",
              ice_rec["rate_value"] == 359.0
              and ice_rec["rate_unit"] == "GH/s",
              repr((ice_rec.get("rate_value"),
                    ice_rec.get("rate_unit"))))
        check("iceriver elapsed 4516 s, power unreported",
              ice_rec["elapsed_s"] == 4516
              and ice_rec["power_w"] is None,
              repr((ice_rec.get("elapsed_s"),
                    ice_rec.get("power_w"))))
        check("iceriver 1 board, 18/18 chips, temp 48",
              len(ice_rec["chains"]) == 1
              and ice_rec["chips_total"] == 18
              and ice_rec["chips_alive"] == 18
              and ice_rec["chains"][0]["temp_c"] == 48.0,
              repr(ice_rec.get("chains")))
        check("iceriver fans 6079/6079/0/0",
              ice_rec["fans_rpm"] == [6079, 6079, 0, 0],
              repr(ice_rec.get("fans_rpm")))
        check("iceriver pools: 3, one Alive with 281 accepted",
              len(ice_rec.get("pools") or []) == 3
              and ice_rec["pools"][1]["status"] == "Alive"
              and ice_rec["pools"][1]["accepted"] == 281.0,
              repr(ice_rec.get("pools")))
        check("iceriver pools never carry passwords",
              all("pass" not in p and "password" not in p
                  for p in (ice_rec.get("pools") or [])),
              repr(ice_rec.get("pools")))
        check("iceriver mac from panel, upper-case",
              ice_rec.get("mac") == "00:0A:66:30:00:6D",
              repr(ice_rec.get("mac")))
        check("login before panel, cookie forwarded, no writes",
              any("loginpost" in line for line in _log_lines(ice_log))
              and any("cookie=yes" in line
                      for line in _log_lines(ice_log)
                      if "userpanel" in line)
              and not any("machineconfig" in line
                          for line in _log_lines(ice_log)),
              repr(_log_lines(ice_log)))

        # -------------------------------------------- iceriver find_miner
        ok, msg = actions.execute(
            ICE_HOST, "iceriver", "find_miner",
            creds={"http_port": ICE_PORT, "timeout": 2.0,
                   "password": "12345678"})
        check("iceriver find_miner accepted", ok, msg)
        check("find_miner sent locate post=5",
              any("post=5" in line for line in _log_lines(ice_log)),
              repr(_log_lines(ice_log)))
        ok, msg = actions.execute(
            ICE_HOST, "iceriver", "reboot",
            creds={"http_port": ICE_PORT, "timeout": 2.0})
        check("iceriver reboot honestly unsupported",
              not ok and "unknown miner source" in msg, msg)

        doc = inspect_mod.inspect_device(
            ICE_HOST, timeout=2.0, http_port=ICE_PORT,
            cgminer_port=CLOSED_RPC)
        check("inspect iceriver boards supported, 1 x 18 chips",
              doc.get("boards", {}).get("supported") is True
              and len(doc["boards"]["boards"]) == 1
              and doc["boards"]["boards"][0]["chips_total"] == 18,
              repr(doc.get("boards")))
        check("inspect iceriver pools+fans supported",
              doc.get("pools", {}).get("supported") is True
              and doc.get("fans", {}).get("supported") is True,
              repr({k: doc.get(k) for k in ("pools", "fans")}))

        # --------------------------------------------- jasminer stays a gap
        check("no jasminer adapter module exists",
              importlib.util.find_spec("beesky.core.jasminer") is None)
        check("jasminer is a cred tag only",
              "jasminer" in CRED_TYPES)
    finally:
        for proc in procs:
            _stop(proc)

    # ---- respawns: TUNER-bad braiins + wrapped iceriver shape --------
    # (separate runs so the main assertions above see the default
    # fixtures; each respawn is stopped before returning.)
    bos_bad = _spawn(["tests/mock_braiins.py", BOS_HOST, str(BOS_PORT)],
                     {"MOCK_BRAIINS_TUNER_BAD": "1"})
    try:
        if not _wait_port(BOS_HOST, BOS_PORT):
            check("tuner-bad mock up", False, "timeout")
        else:
            bad_cand = probe_host(BOS_HOST, timeout=1.5,
                                  http_port=CLOSED_HTTP,
                                  cgminer_port=BOS_PORT)
            bad_rec = cli_mod._fetch_record(bad_cand, _args())
            check("tuner error chain -> TUNER problem, CHECK",
                  bad_rec["status"] == "CHECK"
                  and any(p.get("code") == "TUNER"
                          and p.get("chain") == 3
                          for p in bad_rec["problems"]),
                  repr(bad_rec.get("problems")))
    finally:
        _stop(bos_bad)

    ice_wrapped = _spawn(
        ["tests/mock_iceriver.py", ICE_HOST, str(ICE_PORT)],
        {"MOCK_ICERIVER_WRAPPED": "1"})
    try:
        if not _wait_port(ICE_HOST, ICE_PORT):
            check("wrapped mock up", False, "timeout")
        else:
            w_cand = probe_host(ICE_HOST, timeout=1.5,
                                http_port=ICE_PORT,
                                cgminer_port=CLOSED_RPC)
            w_rec = cli_mod._fetch_record(w_cand, _args())
            check("wrapped userpanel shape parses identically",
                  w_rec["source"] == "iceriver"
                  and w_rec["model"] == "KS0ULTRA"
                  and w_rec["rate_value"] == 359.0
                  and w_rec["rate_unit"] == "GH/s",
                  repr({k: w_rec.get(k) for k in
                        ("source", "model", "rate_value",
                         "rate_unit")}))
    finally:
        _stop(ice_wrapped)

    print()
    print(f"vendors3: {len(FAILURES)} failures")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
