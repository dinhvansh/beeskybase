#!/usr/bin/env python3
"""v0.32.0 test — the two core additions behind the Flutter views.

1. `beesky tickets --dir DIR --json` (read-only listing verb):
   report.write_tickets' output parsed back by report.list_tickets
   — one JSON document, newest first, ip/model/problems/text
   round-tripping the ticket format; a missing dir is an empty
   history (exit 0), never an error.

2. `beesky scan --json --events-state FILE`: the pass diffs
   through the core EventEngine with watch --state semantics —
   pass 1 seeds baselines (no events), a miner vanishing in
   pass 2 fires exactly one OFFLINE, pass 3 stays latched
   (anti-flap), and a flagless bridge scan's payload carries NO
   "events" key (the pre-v0.32 byte contract).

Prints PASS lines; exit 1 on failure.
"""

import argparse
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from beesky import cli  # noqa: E402
from beesky.core import report  # noqa: E402

FAILURES: list[str] = []


def check(label: str, condition: bool, extra: str = "") -> None:
    if condition:
        print(f"PASS: {label}")
    else:
        FAILURES.append(label)
        print(f"FAIL: {label} {extra}")


def run_cli(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "beesky", *argv],
        capture_output=True, text=True, cwd=ROOT, timeout=60)


def _record(ip: str, model: str, temp: float, power=None) -> dict:
    return report.build_record_from_boards(
        ip, model=model, elapsed_s=4000,
        ths_realtime=110.0, ths_average=110.0,
        chains=[{"index": 0, "chips_total": 114, "chips_alive": 114,
                 "dead_positions": [], "temp_c": temp}],
        fans_rpm=[4100], source="vnish", power_w=power)


# ----------------------------------------------------------------------
# tickets verb
# ----------------------------------------------------------------------

def test_tickets() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        outdir = Path(tmp) / "tickets"
        hot = report.build_record_from_boards(
            "192.168.2.103", model="Antminer Z15", elapsed_s=4000,
            ths_realtime=1101.0, ths_average=1101.0,
            chains=[{"index": 1, "chips_total": 24, "chips_alive": 24,
                     "dead_positions": [], "temp_c": 88.0}],
            fans_rpm=[3900], source="cgminer")
        sick = report.build_record_from_boards(
            "192.168.2.102", model="Antminer L9", elapsed_s=4000,
            ths_realtime=14.0, ths_average=14.0,
            chains=[{"index": 1, "chips_total": 123, "chips_alive": 84,
                     "dead_positions": [85, 86], "temp_c": 59.0}],
            fans_rpm=[4500], source="cgminer")
        healthy = _record("192.168.2.101", "Antminer S19 Pro", 65.0)
        written = report.write_tickets([hot, sick, healthy], outdir)
        check("write_tickets writes problem miners only",
              len(written) == 2, f"got {len(written)}")

        # Stagger mtimes so the newest-first order is deterministic.
        older = time.time() - 3600
        os.utime(outdir / "ticket-192_168_2_103.txt", (older, older))

        proc = run_cli("tickets", "--dir", str(outdir), "--json")
        check("tickets --json exits 0", proc.returncode == 0,
              proc.stderr[:200])
        payload = json.loads(proc.stdout)  # ONE document or this raises
        tickets = payload["tickets"]
        check("tickets lists both files", len(tickets) == 2)
        check("tickets newest first (mtime desc)",
              tickets[0]["ip"] == "192.168.2.102"
              and tickets[1]["ip"] == "192.168.2.103",
              f"order: {[t['ip'] for t in tickets]}")
        z15 = tickets[1]
        check("ticket ip round-trips the filename encoding",
              z15["file"] == "ticket-192_168_2_103.txt")
        check("ticket model parsed from the Model: line",
              z15["model"] == "Antminer Z15", z15["model"])
        check("ticket problems parsed from the problem section",
              z15["problems"] == [
                  "Board 1: nhiệt độ cao 88°C (ngưỡng 85°C)"],
              f"got {z15['problems']}")
        check("ticket text carries the full ticket",
              z15["text"].startswith(
                  "PHIẾU KIỂM TRA / SỬA CHỮA MÁY ĐÀO")
              and "Gợi ý kiểm tra:" in z15["text"])
        check("ticket modified is an ISO local stamp",
              len(z15["modified"]) == 19 and z15["modified"][4] == "-",
              z15["modified"])
        l9 = tickets[0]
        check("missing-chips problem line parsed (vi)",
              len(l9["problems"]) == 1
              and l9["problems"][0].startswith("Board 1: thiếu 39 chip"),
              f"got {l9['problems']}")

        plain = run_cli("tickets", "--dir", str(outdir))
        check("tickets human mode exits 0 and names the miners",
              plain.returncode == 0
              and "192.168.2.102" in plain.stdout
              and "192.168.2.103" in plain.stdout)

        missing = run_cli("tickets", "--dir", str(Path(tmp) / "nope"),
                          "--json")
        check("missing dir -> empty list, exit 0",
              missing.returncode == 0
              and json.loads(missing.stdout) == {"tickets": []},
              f"rc={missing.returncode} out={missing.stdout[:80]}")


# ----------------------------------------------------------------------
# scan --events-state
# ----------------------------------------------------------------------

def _run_bridge_scan(records: list[dict], state: str | None) -> dict:
    args = argparse.Namespace(
        target="10.0.0.0/24", json="-", tickets=None, group=None,
        groups_file=None, events_state=state)
    original = cli._scan_records
    cli._scan_records = lambda _args: records  # noqa: E731
    try:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = cli.cmd_scan(args)
    finally:
        cli._scan_records = original
    assert rc == 0, f"cmd_scan rc={rc}"
    return json.loads(buf.getvalue())


def test_events_state() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        state = str(Path(tmp) / "events-state.json")
        miner_a = _record("10.0.0.11", "Antminer S19 Pro", 65.0)
        miner_b = _record("10.0.0.12", "Antminer S19 Pro", 66.0)

        plain = _run_bridge_scan([miner_a, miner_b], None)
        check("flagless bridge payload has NO events key",
              "events" not in plain)

        first = _run_bridge_scan([miner_a, miner_b], state)
        check("pass 1 seeds baselines: events key present, empty",
              first.get("events") == [], f"got {first.get('events')}")
        check("pass 1 wrote the engine state file",
              Path(state).exists())

        second = _run_bridge_scan([miner_a], state)
        events = second.get("events") or []
        check("pass 2: the vanished miner fires exactly one event",
              len(events) == 1, f"got {events}")
        if events:
            ev = events[0]
            check("the event is OFFLINE / critical for miner B",
                  ev["type"] == "OFFLINE"
                  and ev["severity"] == "critical"
                  and ev["ip"] == "10.0.0.12",
                  f"got {ev}")
            check("event carries the engine's time + detail fields",
                  bool(ev["time"]) and bool(ev["detail"])
                  and ev["model"] == "Antminer S19 Pro")

        third = _run_bridge_scan([miner_a], state)
        check("pass 3: anti-flap latch — no second OFFLINE",
              third.get("events") == [], f"got {third.get('events')}")

        back = _run_bridge_scan([miner_a, miner_b], state)
        back_types = [e["type"] for e in back.get("events") or []]
        check("pass 4: miner B's return fires BACK_ONLINE",
              back_types == ["BACK_ONLINE"], f"got {back_types}")


def main() -> int:
    test_tickets()
    test_events_state()
    print(f"\nmock_views_test: {len(FAILURES)} FAIL")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
