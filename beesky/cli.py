"""BeeSky command-line interface.

    python -m beesky scan <target> [--json out.json] [--tickets dir/]
                                   [--timeout 1.5] [--workers 64]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import report
from .core.cgminer import CgminerClient, CgminerError
from .core.discover import discover


def _fetch_record(ip: str, timeout: float) -> dict:
    """Pull summary+stats from one miner and build its status record."""
    client = CgminerClient(ip, timeout=max(timeout, 2.0))
    try:
        summary = client.summary()
        stats = client.stats()
    except CgminerError as exc:
        return report.error_record(ip, str(exc))
    return report.build_record(ip, summary, stats)


def _print_table(records: list[dict]) -> None:
    headers = ["IP", "Model", "TH/s", "Chips", "MaxTemp", "Fans", "Status"]
    rows: list[list[str]] = []
    for rec in records:
        ths = f"{rec['ths']:.2f}" if rec["ths"] is not None else "-"
        chips = f"{rec['chips_alive']}/{rec['chips_total']}" if rec["chips_total"] else "-"
        temp = f"{rec['max_temp_c']:.0f}" if rec["max_temp_c"] is not None else "-"
        fans = "/".join(str(f) for f in rec["fans_rpm"]) or "-"
        rows.append([rec["ip"], str(rec["model"]), ths, chips, temp, fans, rec["status"]])
    widths = [max(len(headers[i]), *(len(r[i]) for r in rows)) if rows else len(headers[i])
              for i in range(len(headers))]
    fmt = " | ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers))
    print("-+-".join("-" * w for w in widths))
    for row in rows:
        print(fmt.format(*row))


def cmd_scan(args: argparse.Namespace) -> int:
    candidates = discover(args.target, timeout=args.timeout, workers=args.workers)
    records = [_fetch_record(c.ip, args.timeout) for c in candidates]

    if not records:
        print("No miners found.")
    else:
        _print_table(records)
        bad = sum(1 for r in records if r["status"] != "OK")
        print(f"\nFound {len(records)} miner(s), {bad} need(s) checking.")

    if args.json:
        Path(args.json).write_text(
            json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"JSON written to {args.json}")
    if args.tickets:
        written = report.write_tickets(records, args.tickets)
        for path in written:
            print(f"Ticket written to {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="beesky", description="BeeSky — ASIC miner LAN scanner & repair diagnostics")
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="scan a target for miners and report health")
    scan.add_argument("target",
                      help="IP, CIDR (192.168.1.0/24) or range (192.168.1.10-192.168.1.60)")
    scan.add_argument("--json", metavar="FILE", help="write status records as JSON")
    scan.add_argument("--tickets", metavar="DIR",
                      help="write one repair ticket per problem miner into DIR")
    scan.add_argument("--timeout", type=float, default=1.5,
                      help="per-probe timeout in seconds (default 1.5)")
    scan.add_argument("--workers", type=int, default=64,
                      help="max concurrent probes (default 64)")
    scan.set_defaults(func=cmd_scan)

    args = parser.parse_args(argv)
    return args.func(args)
