#!/usr/bin/env python3
"""v0.30.0 test — vendor coverage (docs/vendor-coverage-mapping.md).

No hardware. Loopback mocks, one per contract:

  * tests/mock_whatsminer.py on 127.0.0.1:14028 — the MicroBT
    socket dialect ({"cmd": ...} envelopes, Msg payloads, the
    Fan Speed In/Out fingerprint, board 2 at 87 C, privileged
    commands refusing without a token). Logs every request to
    MOCK_WM_LOG so the suite can prove get_token is NEVER sent.
  * tests/mock_avalon.py on 127.0.0.2:14028 — a cgminer-envelope
    device whose STATS carries the Avalon "MM ID<n>" module keys;
    its privileged `restart` is accepted + logged.
  * tests/mock_miner.py on 127.0.0.1:4028 — the established
    Antminer cgminer fixture (non-collision witness both ways).
  * tests/mock_dashd.py on 127.0.0.3:18093 + tests/mock_stock_fw.py
    on 127.0.0.3:18094 — the chain-regression witnesses.

Asserts: per-vendor detection + record fields + native units;
non-collision in every direction (dialect vs envelope, Avalon
refinement vs plain cgminer, dashd/stock unchanged); the cred
family extension (all six new tags round-trip, family-first
ordering); per-vendor actions (avalon reboot rides the cgminer
RPC and lands; whatsminer writes are the honest gap — the mock's
token refusal is never even triggered by the scanner); inspect
sections for whatsminer. Prints PASS lines; exit 1 on failure.
"""

import argparse
import json
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
from beesky.core.cgminer import CgminerClient, CgminerError  # noqa: E402
from beesky.core.discover import (CRED_TYPES, cred_type,  # noqa: E402
                                  ordered_creds, probe_host)
from beesky.core.groups import normalise_group  # noqa: E402
from beesky.core.whatsminer import (WhatsminerClient,  # noqa: E402
                                    WhatsminerError,
                                    is_whatsminer_summary)

WM_HOST, WM_PORT = "127.0.0.1", 14028
AV_HOST, AV_PORT = "127.0.0.2", 14028
CG_HOST, CG_PORT = "127.0.0.1", 4028
HTTP_HOST, DASHD_PORT, STOCK_PORT = "127.0.0.3", 18093, 18094
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


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="beesky-vendors-"))
    wm_log = tmp / "wm.log"
    av_log = tmp / "avalon.log"
    procs = [
        _spawn(["tests/mock_whatsminer.py", WM_HOST, str(WM_PORT)],
               {"MOCK_WM_LOG": str(wm_log)}),
        _spawn(["tests/mock_avalon.py", AV_HOST, str(AV_PORT)],
               {"MOCK_AVALON_LOG": str(av_log)}),
        _spawn(["tests/mock_miner.py"], {}),
        _spawn(["tests/mock_dashd.py", HTTP_HOST, str(DASHD_PORT)], {}),
        _spawn(["tests/mock_stock_fw.py", HTTP_HOST, str(STOCK_PORT)], {}),
    ]
    try:
        for host, port in ((WM_HOST, WM_PORT), (AV_HOST, AV_PORT),
                           (CG_HOST, CG_PORT), (HTTP_HOST, DASHD_PORT),
                           (HTTP_HOST, STOCK_PORT)):
            if not _wait_port(host, port):
                check(f"mock up {host}:{port}", False, "timeout")
                return 1

        # ------------------------------------------------ whatsminer client
        wm = WhatsminerClient(WM_HOST, port=WM_PORT, timeout=2.0)
        item = wm.summary_item()
        check("wm summary item type", item.get("Type") == "WhatsMiner M30S",
              repr(item.get("Type")))
        check("wm fingerprint positive", is_whatsminer_summary(item))
        check("wm fingerprint negative on cgminer summary",
              not is_whatsminer_summary(
                  {"Type": "Antminer S19 Pro", "GHS av": 1.0}))
        check("wm fingerprint negative on refusal envelope",
              not is_whatsminer_summary({}))

        record = wm.fetch_record(WM_HOST)
        check("wm record source", record["source"] == "whatsminer",
              record["source"])
        check("wm record model", record["model"] == "WhatsMiner M30S",
              record["model"])
        # MHS 5s = 111,800,000 -> native TH/s display 111.8 (mapping §1.5)
        check("wm record native rate",
              record["rate_unit"] == "TH/s"
              and abs(record["rate_value"] - 111.8) < 1e-6,
              f"{record['rate_value']} {record['rate_unit']}")
        check("wm record ths agrees",
              abs(record["ths"] - 111.8) < 1e-6, str(record["ths"]))
        check("wm record fans", record["fans_rpm"] == [4560, 4620],
              repr(record["fans_rpm"]))
        check("wm record chains temps only",
              [c["temp_c"] for c in record["chains"]] == [62.0, 87.0, 65.0]
              and all(c["chips_total"] == 0 for c in record["chains"]),
              repr(record["chains"]))
        check("wm record over-temp diagnosis",
              any(p["code"] == "OVER_TEMP" and p["chain"] == 2
                  for p in record["problems"]),
              repr(record["problems"]))
        check("wm record no invented chips",
              record["chips_total"] == 0 and record["chips_alive"] == 0)
        check("wm record power unread (G-W4)", record["power_w"] is None)
        pools = record.get("pools") or []
        check("wm record pools verbatim",
              len(pools) == 1
              and pools[0]["url"] == "stratum+tcp://btc.pool.example:3333"
              and pools[0]["worker"] == "wmworker.001"
              and pools[0]["status"] == "Alive",
              repr(pools))

        # The dialect boundary, both directions: the cgminer envelope
        # must NOT read a Whatsminer, and the token refusal is real.
        try:
            foreign = CgminerClient(WM_HOST, port=WM_PORT,
                                    timeout=2.0).summary()
        except CgminerError:
            foreign = {}
        check("cgminer envelope cannot read whatsminer", not foreign,
              repr(foreign))
        try:
            wm.command("restart_btminer")
            refusal = ""
        except WhatsminerError as exc:
            refusal = str(exc)
        check("wm privileged refusal surfaces verbatim",
              "token required" in refusal, refusal)

        # ------------------------------------------------------- probing
        wm_cand = probe_host(WM_HOST, timeout=1.5,
                             http_port=CLOSED_HTTP, cgminer_port=WM_PORT)
        check("probe claims whatsminer",
              wm_cand is not None and wm_cand.source == "whatsminer",
              repr(wm_cand and wm_cand.source))
        cg_cand = probe_host(CG_HOST, timeout=1.5,
                             http_port=CLOSED_HTTP, cgminer_port=CG_PORT)
        check("probe keeps antminer cgminer (no dialect/av mis-claim)",
              cg_cand is not None and cg_cand.source == "cgminer",
              repr(cg_cand and cg_cand.source))
        av_cand = probe_host(AV_HOST, timeout=1.5,
                             http_port=CLOSED_HTTP, cgminer_port=AV_PORT)
        check("probe refines avalon",
              av_cand is not None and av_cand.source == "avalon",
              repr(av_cand and av_cand.source))
        vn_cand = probe_host(HTTP_HOST, timeout=1.5,
                             http_port=DASHD_PORT, cgminer_port=CLOSED_RPC)
        check("probe keeps vnish", vn_cand is not None
              and vn_cand.source == "vnish",
              repr(vn_cand and vn_cand.source))
        st_cand = probe_host(HTTP_HOST, timeout=1.5,
                             http_port=STOCK_PORT, cgminer_port=CLOSED_RPC)
        check("probe keeps stock", st_cand is not None
              and st_cand.source == "stock",
              repr(st_cand and st_cand.source))

        # get_token discipline: after EVERY read path above (client
        # fetch, probes, and the fetch stages below run later), the
        # mock must have seen reads only. Checked here for the probe
        # + client stage; the fetch-stage stage re-checks at the end.
        wm_cmds = wm_log.read_text().split() if wm_log.exists() else []
        check("scanner never sends get_token",
              "get_token" not in wm_cmds, repr(wm_cmds))
        check("scanner used the dialect reads",
              "summary" in wm_cmds and "devs" in wm_cmds
              and "pools" in wm_cmds, repr(wm_cmds))

        # --------------------------------------------------- fetch stages
        args = argparse.Namespace(timeout=1.5, api_key=None, token=None)
        cli_rec = cli_mod._fetch_record(wm_cand, args)
        check("cli fetch whatsminer record",
              cli_rec["source"] == "whatsminer"
              and cli_rec["model"] == "WhatsMiner M30S",
              repr(cli_rec.get("source")))
        ops_rec = ops._fetch_record(wm_cand, 1.5)
        check("ops fetch whatsminer record",
              ops_rec["source"] == "whatsminer",
              repr(ops_rec.get("source")))
        av_rec = cli_mod._fetch_record(av_cand, args)
        check("cli fetch avalon record source",
              av_rec["source"] == "avalon", repr(av_rec.get("source")))
        check("avalon record native rate",
              av_rec["rate_unit"] == "TH/s"
              and abs(av_rec["rate_value"] - 89.8) < 1e-6,
              f"{av_rec['rate_value']} {av_rec['rate_unit']}")
        check("avalon record no invented boards/chips",
              av_rec["chains"] == [] and av_rec["chips_total"] == 0,
              repr(av_rec["chains"]))
        check("avalon record pools enrichment",
              (av_rec.get("pools") or [{}])[0].get("worker")
              == "avalonworker.001", repr(av_rec.get("pools")))

        # --------------------------------------------------------- inspect
        doc = inspect_mod.inspect_device(
            WM_HOST, timeout=1.5, http_port=CLOSED_HTTP,
            cgminer_port=WM_PORT)
        check("inspect whatsminer source", doc.get("source") == "whatsminer",
              repr(doc.get("source")))
        check("inspect whatsminer boards",
              doc["boards"].get("supported") is True
              and len(doc["boards"]["boards"]) == 3
              and doc["boards"]["boards"][1]["temp_c"] == 87.0
              and doc["boards"]["boards"][1]["chips_total"] == 0,
              repr(doc.get("boards")))
        check("inspect whatsminer pools",
              doc["pools"].get("supported") is True
              and doc["pools"]["pools"][0]["status"] == "Alive",
              repr(doc.get("pools")))
        check("inspect whatsminer fans",
              doc["fans"].get("supported") is True
              and [f["rpm"] for f in doc["fans"]["fans"]] == [4560, 4620],
              repr(doc.get("fans")))

        # --------------------------------------------------------- actions
        ok, msg = actions.execute(
            AV_HOST, "avalon", "reboot",
            creds={"cgminer_port": AV_PORT, "timeout": 2.0})
        check("avalon reboot rides cgminer restart", ok, msg)
        av_cmds = av_log.read_text().split() if av_log.exists() else []
        check("avalon mock recorded the restart", "restart" in av_cmds,
              repr(av_cmds))
        ok, msg = actions.execute(
            WM_HOST, "whatsminer", "reboot",
            creds={"cgminer_port": WM_PORT, "timeout": 2.0})
        check("whatsminer reboot is the honest gap (G-W1)",
              not ok and "not supported" in msg, msg)
        ok, msg = actions.execute(
            WM_HOST, "whatsminer", "switch_pool", {"pool_id": 1},
            creds={"cgminer_port": WM_PORT, "timeout": 2.0})
        check("whatsminer switch_pool honest gap",
              not ok and "not supported" in msg, msg)
        ok, msg = actions.execute(
            AV_HOST, "avalon", "switch_pool", {"pool_id": 1},
            creds={"cgminer_port": AV_PORT, "timeout": 2.0})
        check("avalon switch_pool keeps cgminer family gap",
              not ok and "not supported" in msg, msg)

        # ------------------------------------------- cred family extension
        for tag in ("whatsminer", "avalon", "iceriver", "jasminer",
                    "braiins", "luxos"):
            check(f"cred_type round-trips {tag}",
                  tag in CRED_TYPES and cred_type({"type": tag}) == tag)
        check("cred_type unknown still any",
              cred_type({"type": "nope"}) == "any"
              and cred_type({}) == "any")

        def _set(label, type_):
            return {"label": label, "user": "u", "password": "p",
                    "api_key": None, "type": type_}

        sets = [_set("stockset", "stock"), _set("wmset", "whatsminer"),
                _set("anyset", "any"), _set("avset", "avalon")]
        wm_order = [c["label"] for c in ordered_creds(sets, "whatsminer")]
        check("ordered_creds whatsminer family first",
              wm_order == ["wmset", "anyset", "stockset", "avset"],
              repr(wm_order))
        av_order = [c["label"] for c in ordered_creds(sets, "avalon")]
        check("ordered_creds avalon family first",
              av_order == ["avset", "anyset", "stockset", "wmset"],
              repr(av_order))

        raw = [{"label": "ice", "user": "u", "password": "p",
                "type": "iceriver"}]
        check("cli normalise keeps iceriver tag",
              cli_mod._normalise_creds(raw, "test")[0]["type"] == "iceriver")
        raw2 = [{"label": "jas", "user": "u", "password": "p",
                 "type": "jasminer"}]
        check("ops normalise keeps jasminer tag",
              ops._normalise_creds(raw2, "test")[0]["type"] == "jasminer")
        group = normalise_group({
            "name": "Trại B", "targets": "192.168.9.0/24",
            "creds": [{"label": "bos", "user": "u", "password": "p",
                       "type": "braiins"}]})
        check("group creds keep braiins tag verbatim",
              group["creds"][0]["type"] == "braiins",
              repr(group["creds"]))

        # Final get_token re-check: the fetch stages + inspect above
        # must not have minted one either.
        wm_cmds = wm_log.read_text().split() if wm_log.exists() else []
        check("get_token still never sent after all stages",
              "get_token" not in wm_cmds, repr(wm_cmds))
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
