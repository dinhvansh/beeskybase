#!/usr/bin/env python3
"""v0.35.0 test — MAC addresses from the local ARP table.

The grid's MAC column (a named DATA-GAP since v0.25) finally has
a data source that needs no miner cooperation: the host's own ARP
cache, read once per scan (beesky/core/arp.py) and attached to
records in cli._fetch_record. docs/parity-audit.md row 15.

Asserts:
  * normalise_mac: dash/colon/lower forms all normalise to
    upper-case colon form; broadcast, short, and garbage inputs
    return None;
  * parse_arp_table: Windows `arp -a`, Linux `ip neigh`, and
    BSD/macOS `arp -an` dumps all parse; incomplete/broadcast
    entries are skipped; lines without a MAC are skipped; a
    repeated IP keeps the LAST entry;
  * read_arp_table never raises: a failing subprocess (or a
    failing command) yields {};
  * live scan (mock dashd, in-process): with a canned ARP table
    the record carries the miner's MAC; with an empty table the
    record has no "mac" key at all — and the scan still succeeds.

Prints PASS lines; exit 1 on failure.
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

from beesky import cli  # noqa: E402
from beesky.core import arp as arp_mod  # noqa: E402

FAILURES: list[str] = []

DASHD_PORT = 18831


def check(label: str, condition: bool, extra: str = "") -> None:
    if condition:
        print(f"PASS: {label}")
    else:
        FAILURES.append(label)
        print(f"FAIL: {label} {extra}")


WIN_ARP = """\
Interface: 192.168.2.10 --- 0x4
  Internet Address      Physical Address      Type
  192.168.2.1           aa-bb-cc-dd-ee-01     dynamic
  192.168.2.38          00-1a-2b-3c-4d-5e     dynamic
  192.168.2.255         ff-ff-ff-ff-ff-ff     static
"""

IP_NEIGH = """\
192.168.2.38 dev eth0 lladdr 00:1a:2b:3c:4d:5e REACHABLE
192.168.2.39 dev eth0 lladdr AA:BB:CC:DD:EE:FF STALE
192.168.2.40 dev eth0  FAILED
"""

BSD_ARP = """\
? (192.168.2.38) at 0:1a:2b:3c:4d:5e on en0 ifscope [ethernet]
? (192.168.2.41) at (incomplete) on en0 ifscope [ethernet]
garbage line with no addresses at all
"""


def test_normalise() -> None:
    check("mac: dash form normalises to upper colon form",
          arp_mod.normalise_mac("aa-bb-cc-dd-ee-ff") == "AA:BB:CC:DD:EE:FF")
    check("mac: lower colon form normalises",
          arp_mod.normalise_mac("aa:bb:cc:dd:ee:ff") == "AA:BB:CC:DD:EE:FF")
    check("mac: mixed-case colon form normalises",
          arp_mod.normalise_mac("Aa:Bb:Cc:Dd:Ee:Ff") == "AA:BB:CC:DD:EE:FF")
    check("mac: unpadded BSD octets pad out",
          arp_mod.normalise_mac("0:1a:2b:3c:4d:5e") == "00:1A:2B:3C:4D:5E")
    check("mac: broadcast is rejected",
          arp_mod.normalise_mac("ff-ff-ff-ff-ff-ff") is None)
    check("mac: short input is rejected",
          arp_mod.normalise_mac("aa:bb:cc:dd:ee") is None)
    check("mac: garbage is rejected",
          arp_mod.normalise_mac("not-a-mac") is None)
    check("mac: non-string is rejected",
          arp_mod.normalise_mac(None) is None)


def test_parse() -> None:
    win = arp_mod.parse_arp_table(WIN_ARP)
    check("parse: Windows arp -a yields both real entries",
          win == {"192.168.2.1": "AA:BB:CC:DD:EE:01",
                  "192.168.2.38": "00:1A:2B:3C:4D:5E"},
          f"got {win}")
    check("parse: Windows broadcast entry is skipped",
          "192.168.2.255" not in win)
    neigh = arp_mod.parse_arp_table(IP_NEIGH)
    check("parse: ip neigh yields REACHABLE + STALE, skips FAILED",
          neigh == {"192.168.2.38": "00:1A:2B:3C:4D:5E",
                    "192.168.2.39": "AA:BB:CC:DD:EE:FF"},
          f"got {neigh}")
    bsd = arp_mod.parse_arp_table(BSD_ARP)
    check("parse: BSD arp -an yields the one complete entry",
          bsd == {"192.168.2.38": "00:1A:2B:3C:4D:5E"}, f"got {bsd}")
    check("parse: non-string input yields an empty table",
          arp_mod.parse_arp_table(None) == {})
    check("parse: a repeated IP keeps the LAST entry",
          arp_mod.parse_arp_table(
              "192.168.2.5 dev eth0 lladdr aa:aa:aa:aa:aa:aa REACHABLE\n"
              "192.168.2.5 dev eth0 lladdr bb:bb:bb:bb:bb:bb REACHABLE\n")
          == {"192.168.2.5": "BB:BB:BB:BB:BB:BB"})


def test_read_never_raises() -> None:
    real_run = subprocess.run

    def boom(*args, **kwargs):
        raise OSError("no arp here")

    subprocess.run = boom  # type: ignore[assignment]
    try:
        check("read: a failing subprocess yields {} (never raises)",
              arp_mod.read_arp_table() == {})
    finally:
        subprocess.run = real_run

    def rc1(*args, **kwargs):
        class P:
            returncode = 1
            stdout = b""
        return P()

    subprocess.run = rc1  # type: ignore[assignment]
    try:
        check("read: a non-zero exit yields {}",
              arp_mod.read_arp_table() == {})
    finally:
        subprocess.run = real_run


def _wait_port(port: int, timeout_s: float = 15.0) -> bool:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.2)
    return False


def test_live_scan(tmp: str) -> None:
    creds_path = Path(tmp) / "creds.json"
    creds_path.write_text(json.dumps([
        {"label": "test", "user": "root", "password": "dashd-pw",
         "type": "vnish"},
    ]), encoding="utf-8")
    env = dict(os.environ)
    env["BEESKY_MOCK_CREDS_LOG"] = str(Path(tmp) / "dashd.log")
    proc = subprocess.Popen(
        [sys.executable, str(ROOT / "tests" / "mock_creds_miner.py"),
         "127.0.0.1", str(DASHD_PORT), "dashd"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
    try:
        if not _wait_port(DASHD_PORT):
            check("live: mock dashd came up", False)
            return
        args = argparse.Namespace(
            target="127.0.0.1", timeout=1.5, workers=4,
            http_port=DASHD_PORT, cgminer_port=4028,
            user="root", password="root", api_key=None, token=None,
            creds_file=str(creds_path))
        real_read = arp_mod.read_arp_table
        try:
            cli.arp_mod.read_arp_table = (  # type: ignore[method-assign]
                lambda: {"127.0.0.1": "AA:BB:CC:DD:EE:FF"})
            records = cli._scan_records(args)
            check("live: a canned ARP table puts the MAC on the record",
                  len(records) == 1
                  and records[0].get("mac") == "AA:BB:CC:DD:EE:FF",
                  f"records={records}")
            cli.arp_mod.read_arp_table = lambda: {}  # type: ignore[method-assign]
            records = cli._scan_records(args)
            check("live: an empty ARP table leaves the record mac-free",
                  len(records) == 1 and "mac" not in records[0],
                  f"records={records}")
        finally:
            cli.arp_mod.read_arp_table = real_read  # type: ignore[method-assign]
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def main() -> int:
    test_normalise()
    test_parse()
    test_read_never_raises()
    with tempfile.TemporaryDirectory() as tmp:
        test_live_scan(tmp)
    print()
    if FAILURES:
        print(f"ARP TEST FAILED: {len(FAILURES)} assertion(s): {FAILURES}")
        return 1
    print(f"ARP TEST PASSED: all assertions green")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
