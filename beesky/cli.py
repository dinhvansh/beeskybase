"""BeeSky command-line interface.

    python -m beesky scan <target> [--json out.json] [--tickets dir/]
                                   [--timeout 1.5] [--workers 64]
                                   [--user root] [--password root]
                                   [--api-key KEY] [--token JWT]
                                   [--http-port 80] [--cgminer-port 4028]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import report
from .core.bitmain import BitmainClient, BitmainError
from .core.cgminer import CgminerClient, CgminerError
from .core.dashd import DashdClient, DashdError
from .core.discover import Candidate, discover


def _fetch_record(cand: Candidate, args: argparse.Namespace) -> dict:
    """Pull full health data for one candidate via its claiming adapter."""
    ip, timeout = cand.ip, max(args.timeout, 2.0)
    if cand.source == "vnish":
        client = DashdClient(ip, port=cand.http_port, timeout=timeout,
                             api_key=args.api_key, token=args.token)
        try:
            return client.fetch_record(ip)
        except DashdError as exc:
            return report.error_record(ip, str(exc), source="vnish")
    if cand.source == "stock":
        client = BitmainClient(ip, port=cand.http_port, timeout=timeout,
                               username=args.user, password=args.password)
        try:
            return client.fetch_record(ip, status_data=cand.status_data or None)
        except BitmainError as exc:
            return report.error_record(ip, str(exc), source="stock")
    # cgminer RPC (also the fallback for port-open-but-silent candidates).
    client = CgminerClient(ip, port=cand.cgminer_port, timeout=timeout)
    try:
        summary = client.summary()
        stats = client.stats()
    except CgminerError as exc:
        return report.error_record(ip, str(exc), source="cgminer")
    return report.build_record(ip, summary, stats, source="cgminer")


def _print_table(records: list[dict]) -> None:
    headers = ["IP", "Model", "Source", "TH/s", "Chips", "MaxTemp", "Fans", "Status"]
    rows: list[list[str]] = []
    for rec in records:
        ths = f"{rec['ths']:.2f}" if rec["ths"] is not None else "-"
        chips = f"{rec['chips_alive']}/{rec['chips_total']}" if rec["chips_total"] else "-"
        temp = f"{rec['max_temp_c']:.0f}" if rec["max_temp_c"] is not None else "-"
        fans = "/".join(str(f) for f in rec["fans_rpm"]) or "-"
        rows.append([rec["ip"], str(rec["model"]), str(rec.get("source", "-")),
                     ths, chips, temp, fans, rec["status"]])
    widths = [max(len(headers[i]), *(len(r[i]) for r in rows)) if rows else len(headers[i])
              for i in range(len(headers))]
    fmt = " | ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers))
    print("-+-".join("-" * w for w in widths))
    for row in rows:
        print(fmt.format(*row))


def cmd_scan(args: argparse.Namespace) -> int:
    candidates = discover(
        args.target, timeout=args.timeout, workers=args.workers,
        http_port=args.http_port, cgminer_port=args.cgminer_port,
        username=args.user, password=args.password,
        api_key=args.api_key, token=args.token)
    records = [_fetch_record(c, args) for c in candidates]

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
    scan.add_argument("--user", default="root",
                      help="stock-firmware web username (default root)")
    scan.add_argument("--password", default="root",
                      help="stock-firmware web password (default root)")
    scan.add_argument("--api-key", metavar="KEY",
                      help="dashd (VNish) x-api-key header, if the miner requires it")
    scan.add_argument("--token", metavar="JWT",
                      help="dashd (VNish) bearer token, if the miner requires it")
    scan.add_argument("--http-port", type=int, default=80,
                      help="HTTP port for dashd/stock adapters (default 80)")
    scan.add_argument("--cgminer-port", type=int, default=4028,
                      help="cgminer RPC port (default 4028)")
    scan.set_defaults(func=cmd_scan)

    args = parser.parse_args(argv)
    return args.func(args)
