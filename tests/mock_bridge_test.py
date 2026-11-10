#!/usr/bin/env python3
"""v0.21.0 test — the scan/sysinfo JSON bridge for the Flutter shell.

Programme stage 1: the Flutter app drives the Python exe as a
sidecar, so `beesky scan <target> --json` (no FILE) must print ONE
JSON document on stdout — {"records": [...], "scanned": N,
"found": M, "elapsed_s": X} — with NO human noise on stdout (the
table, the ticket notes: stderr or gone), while the legacy
`--json FILE` mode keeps its exact old behaviour. Records are the
same dicts the cloud/agent path serialises (keys: ip, model,
source, rate_value, rate_unit, problems, chains, ...).

Asserts:
  * bridge mode with a stubbed scan: the WHOLE stdout parses as a
    single JSON document; the envelope counts are right (scanned =
    the target's host count, found = len(records)); crafted
    S19 / L9 (14.54 MH/s) / Z15 (1101.00 ksol/s) records keep their
    native rate fields through the bridge; an arg after --json is
    not swallowed as its value;
  * bridge mode + --tickets: tickets are still written and stdout
    stays a single pure JSON document (notes moved to stderr);
  * legacy --json FILE mode unchanged: the file holds the bare
    records list and stdout says where it went;
  * sysinfo --json: {"version": <running version>,
    "default_target": <stubbed helper value>}; unstubbed, the
    returned target still parses;
  * end-to-end: a real subprocess scan of the mock dashd server
    through `python -m beesky scan ... --json` parses and finds
    the sick S19 Pro with its problems attached.

Prints PASS lines; exit 1 on failure.
"""

import contextlib
import io
import json
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import beesky  # noqa: E402
from beesky import cli  # noqa: E402
from beesky.core.discover import parse_targets  # noqa: E402

FAILURES: list[str] = []


def check(label: str, condition: bool, extra: str = "") -> None:
    if condition:
        print(f"PASS: {label}")
    else:
        FAILURES.append(label)
        print(f"FAIL: {label} {extra}")


def _record(ip, model, rate_value, rate_unit, problems=()):
    return {
        "ip": ip, "model": model, "source": "cgminer", "elapsed_s": 3600,
        "ghs_5s": None, "ghs_av": None, "ths": None,
        "rate_value": rate_value, "rate_unit": rate_unit, "power_w": None,
        "chains": [], "fans_rpm": [4000], "chips_alive": 100,
        "chips_total": 100, "max_temp_c": 65.0,
        "problems": list(problems),
        "status": "CHECK" if problems else "OK",
    }


RECORDS = [
    _record("192.0.2.11", "Antminer S19 Pro", 109.13, "TH/s"),
    _record("192.0.2.12", "Antminer L9", 14.54, "MH/s",
            problems=[{"code": "MISSING_CHIPS", "chain": 1, "missing": 39,
                       "dead_positions": [],
                       "detail": "chain 1: missing 39 chip(s)"}]),
    _record("192.0.2.13", "Antminer Z15", 1101.0, "ksol/s"),
    # a tuple leaf + a set leaf: the bridge sanitiser must cope
    dict(_record("192.0.2.14", "Antminer S21", 200.0, "TH/s"),
         chains=[{"index": 1, "dead_positions": (3, 4)}],
         odd_leaf={"a", "b"}),
]


def _run_cli(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = cli.main(argv)
    return rc, out.getvalue()


def test_bridge_document() -> None:
    with mock.patch.object(cli, "_scan_records", lambda args: RECORDS):
        rc, out = _run_cli(["scan", "192.0.2.0/24", "--json"])
    check("bridge: exit 0", rc == 0)
    try:
        doc = json.loads(out)
    except json.JSONDecodeError as exc:
        check("bridge: stdout is ONE pure JSON document", False, str(exc))
        return
    check("bridge: stdout is ONE pure JSON document", True)
    check("bridge: envelope keys",
          set(doc) == {"records", "scanned", "found", "elapsed_s"},
          f"got {sorted(doc)}")
    check("bridge: scanned = /24 host count",
          doc["scanned"] == len(parse_targets("192.0.2.0/24")) == 254)
    check("bridge: found = record count",
          doc["found"] == len(RECORDS))
    check("bridge: elapsed_s is a non-negative number",
          isinstance(doc["elapsed_s"], (int, float))
          and doc["elapsed_s"] >= 0)
    recs = doc["records"]
    check("bridge: record keys survive (ip/model/rate/problems)",
          all({"ip", "model", "rate_value", "rate_unit", "problems"}
              <= set(r) for r in recs))
    l9 = next(r for r in recs if r["model"] == "Antminer L9")
    check("bridge: L9 native rate intact (14.54 MH/s)",
          l9["rate_value"] == 14.54 and l9["rate_unit"] == "MH/s")
    z15 = next(r for r in recs if r["model"] == "Antminer Z15")
    check("bridge: Z15 native rate intact (1101 ksol/s)",
          z15["rate_value"] == 1101.0 and z15["rate_unit"] == "ksol/s")
    odd = next(r for r in recs if r["ip"] == "192.0.2.14")
    check("bridge: sanitiser coerces tuple/set leaves",
          odd["chains"][0]["dead_positions"] == [3, 4]
          and sorted(odd["odd_leaf"]) == ["a", "b"])


def test_bridge_flag_not_greedy() -> None:
    captured = {}

    def fake_scan(args):
        captured["user"] = args.user
        return []

    with mock.patch.object(cli, "_scan_records", fake_scan):
        rc, out = _run_cli(["scan", "192.0.2.50", "--json",
                            "--user", "alice"])
    check("bridge: --json does not swallow the next flag",
          rc == 0 and captured.get("user") == "alice")
    doc = json.loads(out)
    check("bridge: empty scan still a valid document",
          doc["found"] == 0 and doc["records"] == []
          and doc["scanned"] == 1)


def test_bridge_tickets_keep_stdout_pure() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        with mock.patch.object(cli, "_scan_records", lambda args: RECORDS):
            rc, out = _run_cli(["scan", "192.0.2.0/24", "--json",
                                "--tickets", tmp])
        written = list(Path(tmp).glob("*.txt"))
    check("bridge+tickets: exit 0", rc == 0)
    try:
        json.loads(out)
        pure = True
    except json.JSONDecodeError:
        pure = False
    check("bridge+tickets: stdout still ONE JSON document", pure)
    check("bridge+tickets: ticket files written for problem miners",
          len(written) >= 1, f"got {len(written)}")


def test_legacy_json_file_mode() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "out.json"
        # legacy mode dumps records raw (no bridge sanitiser), so it
        # gets the clean records only — real adapters never emit the
        # exotic leaves the bridge test crafts.
        clean = RECORDS[:3]
        with mock.patch.object(cli, "_scan_records", lambda args: clean):
            rc, out = _run_cli(["scan", "192.0.2.0/24",
                                "--json", str(path)])
        data = json.loads(path.read_text(encoding="utf-8"))
    check("legacy: exit 0 + human note on stdout",
          rc == 0 and "JSON written to" in out)
    check("legacy: file holds the bare records list",
          isinstance(data, list) and len(data) == len(clean)
          and data[1]["rate_unit"] == "MH/s")


def test_sysinfo() -> None:
    with mock.patch.object(cli, "default_scan_target",
                           lambda: "192.0.2.0/24"):
        rc, out = _run_cli(["sysinfo", "--json"])
    doc = json.loads(out)
    check("sysinfo: version is the running version",
          rc == 0 and doc["version"] == beesky.__version__)
    check("sysinfo: default_target comes from the helper",
          doc["default_target"] == "192.0.2.0/24")
    rc, out = _run_cli(["sysinfo", "--json"])
    doc = json.loads(out)
    try:
        hosts = parse_targets(doc["default_target"])
        parseable = len(hosts) >= 1
    except ValueError:
        parseable = False
    check("sysinfo: unstubbed target parses", rc == 0 and parseable)


def _wait_port(port: int, timeout_s: float = 15.0) -> bool:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.2)
    return False


def test_end_to_end_mock_dashd() -> None:
    port = 18777
    server = subprocess.Popen(
        [sys.executable, str(ROOT / "tests" / "mock_dashd.py"),
         "127.0.0.1", str(port)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        if not _wait_port(port):
            check("e2e: mock dashd came up", False)
            return
        proc = subprocess.run(
            [sys.executable, "-m", "beesky", "scan", "127.0.0.1",
             "--http-port", str(port), "--json"],
            cwd=ROOT, capture_output=True, text=True, timeout=120)
        try:
            doc = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            check("e2e: subprocess stdout is ONE JSON document", False,
                  f"{exc}; stdout head: {proc.stdout[:120]!r}")
            return
        check("e2e: subprocess stdout is ONE JSON document", True)
        check("e2e: found the mock miner",
              doc["found"] == 1 and doc["scanned"] == 1,
              f"doc counts: found={doc.get('found')} "
              f"scanned={doc.get('scanned')}")
        rec = doc["records"][0]
        check("e2e: record is the sick S19 Pro via VNish",
              "S19" in str(rec["model"]) and rec["source"] == "vnish",
              f"model={rec.get('model')} source={rec.get('source')}")
        check("e2e: problems + native rate attached",
              len(rec["problems"]) >= 1
              and rec["rate_unit"] == "TH/s"
              and rec["rate_value"] is not None)
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()


def main() -> int:
    test_bridge_document()
    test_bridge_flag_not_greedy()
    test_bridge_tickets_keep_stdout_pure()
    test_legacy_json_file_mode()
    test_sysinfo()
    test_end_to_end_mock_dashd()
    print()
    if FAILURES:
        print(f"BRIDGE TEST FAILED: {len(FAILURES)} assertion(s): "
              f"{FAILURES}")
        return 1
    print("BRIDGE TEST PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
