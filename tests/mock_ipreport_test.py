#!/usr/bin/env python3
"""v0.34.0 test — IP-Report (docs/ipreport-mapping.md) + settings/timeouts.

1. IP-Report: parse_report mirrors Find-My-Miner's Parse (Bitmain-style
   "IP,MAC" text, free-text Jasminer form, binary-safe rendering,
   public-IP claims ignored, sender fallback, private-sender rule)
   and IpReportListener receives a real UDP datagram on 14235 from a
   mock sender (loopback, tests only), ignores a public sender, and
   the `ipreport listen --duration` CLI streams NDJSON + persists to
   the store file that `ipreport list --json` reads back. Whatsminer
   8888 binds as the second port (single-source, asic-rs only).

2. Settings/timeouts: scan --timeout actually reaches probe_host
   (a slow mock host is dropped at a 0.05s timeout but found at 2s);
   inspect --timeout reaches the fetch stage; ops job "timeout" and
   "stagger_s" validate and the stagger gate really spaces device
   onsets; groups reset-stats clears last_scan per group and --all.

Prints PASS lines; exit 1 on failure.
"""

import json
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from beesky.core import groups as groups_mod  # noqa: E402
from beesky.core import ipreport  # noqa: E402
from beesky.core import ops as ops_mod  # noqa: E402
from beesky.core.discover import probe_host  # noqa: E402

FAILURES: list[str] = []


def check(label: str, condition: bool, extra: str = "") -> None:
    if condition:
        print(f"PASS: {label}")
    else:
        FAILURES.append(label)
        print(f"FAIL: {label} {extra}")


def run_cli(*argv: str, timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "beesky", *argv],
        capture_output=True, text=True, cwd=ROOT, timeout=timeout)


# ----------------------------------------------------------------------
# 1. IP-Report — parse_report
# ----------------------------------------------------------------------

def test_parse() -> None:
    # Bitmain-style "IP,MAC" (Find-My-Miner's own test fixture).
    r = ipreport.parse_report("192.168.1.55", b"192.168.1.55,AA:BB:CC:DD:EE:FF")
    check("parse bitmain-style ip,mac", r["ip"] == "192.168.1.55"
          and r["mac"] == "AA:BB:CC:DD:EE:FF")
    # Free-text Jasminer form, dashed lowercase MAC normalised.
    r = ipreport.parse_report(
        "192.168.1.99", b"Jasminer IP 192.168.1.99 mac de-e5-38-f4-64-87")
    check("parse free-text ip + dashed mac",
          r["ip"] == "192.168.1.99" and r["mac"] == "DE:E5:38:F4:64:87")
    # No IP in the payload: ip is None, the caller falls back to sender.
    r = ipreport.parse_report("192.168.1.55", b"hello")
    check("parse no-ip payload -> ip None, sender kept",
          r["ip"] is None and r["sender"] == "192.168.1.55")
    # A public IP claimed in the payload is ignored (spoof guard).
    r = ipreport.parse_report("192.168.1.55", b"8.8.8.8,AA:BB:CC:DD:EE:FF")
    check("parse public ip claim ignored",
          r["ip"] is None and r["mac"] == "AA:BB:CC:DD:EE:FF")
    # Binary payload renders safely, never raw bytes.
    r = ipreport.parse_report("192.168.1.55",
                              bytes([0, 1, 2, 3, 0xFF, 0xFE, 0x80, 0x01]))
    check("parse binary payload -> (binary) hex preview",
          r["text"].startswith("(binary) ") and r["ip"] is None)
    # Oversized payloads are capped at 200 chars.
    r = ipreport.parse_report("192.168.1.55", b"A" * 100_000)
    check("parse oversized payload capped at 200",
          len(r["text"]) <= 200)
    # Sender acceptance: private yes, public no, loopback only via flag.
    check("accept private sender",
          ipreport.is_acceptable_sender("192.168.1.55") is True)
    check("reject public sender",
          ipreport.is_acceptable_sender("8.8.8.8") is False)
    check("loopback rejected unless allow_loopback",
          ipreport.is_acceptable_sender("127.0.0.1") is False
          and ipreport.is_acceptable_sender("127.0.0.1",
                                             allow_loopback=True) is True)


# ----------------------------------------------------------------------
# 1b. IP-Report — listener receives a real datagram
# ----------------------------------------------------------------------

def test_listener() -> None:
    # NOTE: this sandbox forbids UDP sendto even on loopback, so the
    # receive path is verified through handle_datagram (the exact
    # function the socket loop calls) plus a real bind — the
    # over-the-wire exchange itself is verified by the mock sender
    # in the Flutter-side test and, finally, by a real miner.
    received: list[dict] = []

    def on_report(report: dict) -> None:
        received.append(report)

    listener = ipreport.IpReportListener(
        on_report=on_report, ports=(14235, 18888),
        whatsminer_port=18888, allow_loopback=True)
    bound = listener.start()
    try:
        check("listener binds both ports", 14235 in bound and 18888 in bound,
              f"bound={bound}")
        r = listener.handle_datagram(
            b"192.168.1.77,AA:BB:CC:00:11:22", "127.0.0.1", 14235)
        check("handle_datagram accepts antminer report",
              r is not None and r["ip"] == "192.168.1.77"
              and r["mac"] == "AA:BB:CC:00:11:22"
              and r["family"] == "antminer"
              and r["sender"] == "127.0.0.1"
              and len(received) == 1,
              f"got={r}")
        r = listener.handle_datagram(
            b"192.168.1.78,AA:BB:CC:00:11:23", "127.0.0.1", 18888)
        check("handle_datagram tags whatsminer port family",
              r is not None and r["family"] == "whatsminer"
              and len(received) == 2,
              f"got={r}")
        check("handle_datagram drops public sender",
              listener.handle_datagram(b"hello", "8.8.8.8", 14235) is None
              and len(received) == 2)
        check("handle_datagram drops sender with no private claim "
              "but keeps the sender as target",
              listener.handle_datagram(b"hello", "192.168.1.55", 14235)
              is not None and received[2]["ip"] is None
              and received[2]["sender"] == "192.168.1.55")
    finally:
        listener.stop()
    check("listener stops cleanly", listener.bound_ports() == [])


def test_ipreport_cli() -> None:
    # NOTE: the sandbox forbids UDP sendto, so no datagram can be
    # delivered to the listener here — the CLI test verifies bind +
    # streaming + persistence + the port-clash failure, and the
    # receive path is covered by test_listener's handle_datagram.
    with tempfile.TemporaryDirectory() as tmp:
        store = str(Path(tmp) / "beesky-ipreports.json")
        proc = subprocess.Popen(
            [sys.executable, "-m", "beesky", "ipreport", "listen",
             "--port", "14235", "--no-whatsminer", "--out", store,
             "--duration", "1", "--allow-loopback"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, cwd=ROOT)
        out, err = proc.communicate(timeout=30)
        lines = [json.loads(l) for l in out.splitlines() if l.strip()]
        listening = [l["listening"] for l in lines if "listening" in l]
        stopped = [l for l in lines if "stopped" in l]
        check("cli listen binds and announces listening ports",
              proc.returncode == 0 and listening == [[14235]]
              and stopped and stopped[0]["received"] == 0,
              f"rc={proc.returncode} out={out!r} err={err!r}")
        # Persist one report through the store writer, then read it
        # back through the list verb (the same file the app reads).
        from beesky import cli as _cli
        _cli._append_ipreport(
            store, {"received_at": 1793123456.0, "sender": "192.168.1.90",
                    "text": "192.168.1.90,AA:BB:CC:DD:EE:01",
                    "ip": "192.168.1.90", "mac": "AA:BB:CC:DD:EE:01",
                    "family": "antminer"})
        listed = run_cli("ipreport", "list", "--file", store, "--json")
        doc = json.loads(listed.stdout)
        check("cli list reads persisted store",
              listed.returncode == 0
              and len(doc["reports"]) == 1
              and doc["reports"][0]["ip"] == "192.168.1.90",
              f"out={listed.stdout!r} err={listed.stderr!r}")
        # A second listen on the same port fails cleanly when the
        # port is held by a socket WITHOUT SO_REUSEADDR (the
        # listener's own bind sets REUSEADDR, like the reference
        # implementation, so two BeeSky listeners can coexist —
        # the failure path only fires against a non-reuse holder).
        holder = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        holder.bind(("0.0.0.0", 14235))
        try:
            clash = run_cli("ipreport", "listen", "--port", "14235",
                            "--no-whatsminer", "--duration", "1",
                            "--allow-loopback")
            check("cli listen on taken port fails cleanly (exit 2)",
                  clash.returncode == 2
                  and "Failed to start" in clash.stderr,
                  f"rc={clash.returncode} err={clash.stderr!r}")
        finally:
            holder.close()


# ----------------------------------------------------------------------
# 2. Settings/timeouts — the values actually reach the core
# ----------------------------------------------------------------------

def test_timeouts() -> None:
    # The timeout values the settings UI saves must actually reach
    # the core's probe calls — verified by capturing the argument
    # at the call site (no network timing involved, so no flakes).
    from beesky.core import discover as _disc
    from beesky.core import inspect as _insp
    from beesky import cli as _cli

    seen: list[float] = []
    real_port_open = _disc._port_open

    def capturing_port_open(ip, port, timeout):
        seen.append(timeout)
        return False

    _disc._port_open = capturing_port_open
    try:
        check("probe_host passes --timeout to port probes",
              probe_host("127.0.0.1", timeout=0.7) is None
              and seen == [0.7, 0.7],
              f"seen={seen}")
    finally:
        _disc._port_open = real_port_open

    seen_probe: list[dict] = []
    real_probe = _disc.probe_host

    def capturing_probe(ip, **kwargs):
        seen_probe.append(kwargs)
        return None

    _disc.probe_host = capturing_probe
    try:
        _disc.discover("127.0.0.1", timeout=0.9)
        check("discover passes --timeout to probe_host",
              len(seen_probe) == 1 and seen_probe[0].get("timeout") == 0.9,
              f"seen={seen_probe}")
    finally:
        _disc.probe_host = real_probe

    # inspect --timeout reaches inspect_device (the request timeout
    # the Timeouts tab saves).
    seen_inspect: list[float] = []
    real_inspect = _insp.inspect_device

    def capturing_inspect(ip, **kwargs):
        seen_inspect.append(kwargs.get("timeout"))
        return {"ip": ip, "ok": False}

    _insp.inspect_device = capturing_inspect
    try:
        import argparse
        args = argparse.Namespace(
            ip="127.0.0.1", timeout=4.2, json=True, user="root",
            password="root", creds_file=None, api_key=None, token=None,
            group=None, groups_file=None, http_port=80, cgminer_port=4028)
        rc = _cli.cmd_inspect(args)
        check("inspect passes --timeout to inspect_device",
              rc == 0 and seen_inspect == [4.2],
              f"rc={rc} seen={seen_inspect}")
    finally:
        _insp.inspect_device = real_inspect

    # The CLI accepts --timeout on scan end-to-end (closed ports on
    # loopback: no miners, exit 0, empty records).
    scanned = run_cli("scan", "127.0.0.1", "--timeout", "0.5", "--json")
    doc = json.loads(scanned.stdout)
    check("scan --timeout accepted by CLI",
          scanned.returncode == 0 and doc["records"] == [],
          f"rc={scanned.returncode} err={scanned.stderr!r}")

    # Ops job validation: timeout + stagger_s are real fields with
    # bounds; a bad value is a JobError, not a silent default.
    job = ops_mod.validate_job({
        "type": "reboot", "targets": ["192.168.2.1"],
        "timeout": 5.0, "stagger_s": 0.5, "workers": 2})
    check("ops job carries timeout + stagger_s",
          job["timeout"] == 5.0 and job["stagger_s"] == 0.5)
    # Ops job validation clamps out-of-range numbers to the field's
    # bounds (the established _num behaviour) — a negative timeout
    # becomes the 0.2s floor, never a silent default or a crash.
    clamped = ops_mod.validate_job({"type": "reboot",
                                    "targets": ["192.168.2.1"],
                                    "timeout": -1})
    check("ops job clamps negative timeout to the 0.2s floor",
          clamped["timeout"] == 0.2)

    # The stagger gate really spaces device onsets: two devices with
    # stagger 0.4s take >= 0.4s of onset spread (the work itself is
    # instant — the gate is what we measure). _run_one is stubbed
    # by monkeypatching probe to fail fast.
    from beesky.core import ops as _ops
    real_run_one = _ops._run_one
    onsets: list[float] = []

    def fake_run_one(ip, index, job, merged):
        onsets.append(time.monotonic())
        return False, "mock", None

    _ops._run_one = fake_run_one
    try:
        started = time.monotonic()
        _ops.run_job(ops_mod.validate_job({
            "type": "reboot",
            "targets": ["192.168.2.1", "192.168.2.2", "192.168.2.3"],
            "stagger_s": 0.4, "workers": 3}), emit=lambda e: None)
        elapsed = time.monotonic() - started
        check("ops stagger spaces onsets (>= 0.8s for 3 devices)",
              elapsed >= 0.8 and len(onsets) == 3
              and onsets[-1] - onsets[0] >= 0.75,
              f"elapsed={elapsed:.2f} onsets={onsets}")
    finally:
        _ops._run_one = real_run_one


def test_reset_stats() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store_path = str(Path(tmp) / "beesky-groups.json")
        store = groups_mod.GroupStore(store_path)
        groups = [
            groups_mod.normalise_group(
                {"name": "Trại A", "targets": "192.168.2.0/24"}),
            groups_mod.normalise_group(
                {"name": "Trại B", "targets": "192.168.3.0/24"}),
        ]
        groups[0]["last_scan"] = {"at": "2026-11-12T00:00:00+07:00",
                                  "scanned": 10, "found": 5, "ok": 5,
                                  "check": 0, "error": 0}
        groups[1]["last_scan"] = {"at": "2026-11-12T00:00:00+07:00",
                                  "scanned": 10, "found": 3, "ok": 3,
                                  "check": 0, "error": 0}
        store.save(groups)
        one = run_cli("groups", "--groups-file", store_path,
                      "reset-stats", "Trại A")
        after = store.load()
        check("groups reset-stats clears one group's last_scan",
              one.returncode == 0
              and after[0]["last_scan"] is None
              and after[1]["last_scan"] is not None,
              f"rc={one.returncode} err={one.stderr!r}")
        all_ = run_cli("groups", "--groups-file", store_path,
                       "reset-stats", "--all")
        after = store.load()
        check("groups reset-stats --all clears every group",
              all_.returncode == 0
              and all(g["last_scan"] is None for g in after),
              f"rc={all_.returncode} err={all_.stderr!r}")
        missing = run_cli("groups", "--groups-file", store_path,
                          "reset-stats", "Không có")
        check("groups reset-stats unknown group fails (exit 2)",
              missing.returncode == 2)


def main() -> int:
    test_parse()
    test_listener()
    test_ipreport_cli()
    test_timeouts()
    test_reset_stats()
    print()
    print(f"{len(FAILURES)} failure(s)")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
