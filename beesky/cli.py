"""BeeSky command-line interface.

    python -m beesky scan <target> [--json out.json] [--tickets dir/]
                                   [--timeout 1.5] [--workers 64]
                                   [--user root] [--password root]
                                   [--api-key KEY] [--token JWT]
                                   [--http-port 80] [--cgminer-port 4028]

    python -m beesky watch <target> [--interval 30] [--notify config.json]
                                    [--state state.json] [--once]
                                    (plus the scan options above)

    python -m beesky serve <target> [--port 8787] [--interval 30]
                                    [--host 127.0.0.1] [--notify config.json]
                                    (plus the scan options above)

    python -m beesky agent <target> --cloud URL --key KEY --site NAME
                                    [--interval 30] [--notify config.json]
                                    [--once] (plus the scan options above)

    python -m beesky cloud [--port 8788] [--db beesky-cloud.db]
                                    [--host 127.0.0.1]
    python -m beesky cloud-add-agent --site NAME [--db beesky-cloud.db]
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
import time
from pathlib import Path

from .agent import AgentService
from .cloud.server import run_cloud_server
from .cloud.store import CloudStore
from .core import notify as notify_mod
from .core import report
from .core.bitmain import BitmainClient, BitmainError
from .core.cgminer import CgminerClient, CgminerError
from .core.dashd import DashdClient, DashdError
from .core.discover import Candidate, discover
from .core.events import EventEngine
from .web.server import MonitorService, run_server


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


def _scan_records(args: argparse.Namespace) -> list[dict]:
    """One full scan pass: discover + fetch, as normalised records."""
    candidates = discover(
        args.target, timeout=args.timeout, workers=args.workers,
        http_port=args.http_port, cgminer_port=args.cgminer_port,
        username=args.user, password=args.password,
        api_key=args.api_key, token=args.token)
    return [_fetch_record(c, args) for c in candidates]


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
    records = _scan_records(args)

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


# ---------------------------------------------------------------------------
# watch — repeated scans -> event engine -> notifications
# ---------------------------------------------------------------------------

def _load_state(engine: EventEngine, path: str) -> None:
    try:
        saved = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    if isinstance(saved, dict):
        engine.load_state(saved.get("engine") or saved)


def _save_state(engine: EventEngine, path: str) -> None:
    payload = {"version": 1, "engine": engine.state()}
    tmp = Path(str(path) + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def _is_error_record(record: dict) -> bool:
    return any(p.get("code") == "FETCH_ERROR" for p in record["problems"])


def cmd_watch(args: argparse.Namespace) -> int:
    config: dict = {}
    if args.notify:
        try:
            config = json.loads(Path(args.notify).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"cannot read notify config {args.notify}: {exc}",
                  file=sys.stderr)
            return 2
    engine = EventEngine(config.get("thresholds"))
    notifier = notify_mod.Notifier(config)
    if args.state:
        _load_state(engine, args.state)

    mode = "single pass" if args.once else f"every {args.interval:g}s"
    print(f"BeeSky watch: {args.target} ({mode})"
          + (f", state {args.state}" if args.state else "")
          + (f", notify {args.notify}" if args.notify else ", no notify config"))
    try:
        while True:
            started = time.monotonic()
            records = _scan_records(args)
            present = {r["ip"]: r for r in records if not _is_error_record(r)}
            events = engine.observe_cycle(present)
            stamp = time.strftime("%H:%M:%S")
            print(f"[{stamp}] pass: {len(present)} miner(s) answering, "
                  f"{len(events)} event(s)", flush=True)
            for event in events:
                print(f"  EVENT {event['type']} [{event['severity']}] "
                      f"{event['ip']} {event['model']} — {event['detail']}",
                      flush=True)
                results = notifier.dispatch(event)
                if results:
                    sent = ", ".join(f"{name}={'ok' if ok else 'FAILED'}"
                                     for name, ok in results.items())
                    print(f"    notified: {sent}", flush=True)
                for error in notifier.pop_errors():
                    print(f"    notify error: {error}", file=sys.stderr)
            if args.state:
                _save_state(engine, args.state)
            if args.once:
                break
            delay = args.interval - (time.monotonic() - started)
            if delay > 0:
                time.sleep(delay)
    except KeyboardInterrupt:
        print("\nwatch stopped")
    return 0


# ---------------------------------------------------------------------------
# serve — watch engine behind the web dashboard
# ---------------------------------------------------------------------------

def _load_notify_config(path: str | None) -> dict | None:
    """Read a notify config JSON; None (with a message) when unreadable."""
    if not path:
        return {}
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"cannot read notify config {path}: {exc}", file=sys.stderr)
        return None


def cmd_serve(args: argparse.Namespace) -> int:
    config = _load_notify_config(args.notify)
    if config is None:
        return 2
    service = MonitorService(lambda: _scan_records(args), target=args.target,
                             interval=args.interval, notify_config=config)
    try:
        run_server(service, host=args.host, port=args.port)
    except OSError as exc:
        print(f"cannot bind {args.host}:{args.port}: {exc}", file=sys.stderr)
        return 2
    return 0


# ---------------------------------------------------------------------------
# agent / cloud — farm agent dialling out + multi-site cloud (v0.5)
# ---------------------------------------------------------------------------

def cmd_agent(args: argparse.Namespace) -> int:
    if not args.key:
        print("agent: missing --key (or BEESKY_AGENT_KEY) — mint one on "
              "the cloud with `beesky cloud-add-agent`", file=sys.stderr)
        return 2
    config = _load_notify_config(args.notify)
    if config is None:
        return 2
    service = AgentService(lambda: _scan_records(args), cloud_url=args.cloud,
                           key=args.key, site=args.site,
                           interval=args.interval, notify_config=config)
    service.run(once=args.once)
    return 0


def cmd_cloud(args: argparse.Namespace) -> int:
    password = os.environ.get("BEESKY_CLOUD_PASSWORD") or None
    store = CloudStore(args.db)
    try:
        run_cloud_server(store, host=args.host, port=args.port,
                         password=password)
    except OSError as exc:
        print(f"cannot bind {args.host}:{args.port}: {exc}", file=sys.stderr)
        store.close()
        return 2
    return 0


def cmd_cloud_add_agent(args: argparse.Namespace) -> int:
    store = CloudStore(args.db)
    try:
        key = secrets.token_urlsafe(32)
        agent_id = store.create_agent(args.site, key)
    finally:
        store.close()
    print(f"Đã tạo agent #{agent_id} cho site \"{args.site}\" (db: {args.db}).")
    print("Agent key — LƯU LẠI NGAY, key chỉ hiện MỘT LẦN này (cloud chỉ "
          "lưu bản băm SHA-256, không xem lại được):")
    print(f"BEESKY_AGENT_KEY={key}")
    print("Chạy agent tại trại:  beesky agent <target> --cloud <URL-cloud> "
          f"--key {key} --site \"{args.site}\"")
    return 0


# ---------------------------------------------------------------------------
# argument parsing
# ---------------------------------------------------------------------------

def _add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("target",
                        help="IP, CIDR (192.168.1.0/24) or range (192.168.1.10-192.168.1.60)")
    parser.add_argument("--timeout", type=float, default=1.5,
                        help="per-probe timeout in seconds (default 1.5)")
    parser.add_argument("--workers", type=int, default=64,
                        help="max concurrent probes (default 64)")
    parser.add_argument("--user", default="root",
                        help="stock-firmware web username (default root)")
    parser.add_argument("--password", default="root",
                        help="stock-firmware web password (default root)")
    parser.add_argument("--api-key", metavar="KEY",
                        help="dashd (VNish) x-api-key header, if the miner requires it")
    parser.add_argument("--token", metavar="JWT",
                        help="dashd (VNish) bearer token, if the miner requires it")
    parser.add_argument("--http-port", type=int, default=80,
                        help="HTTP port for dashd/stock adapters (default 80)")
    parser.add_argument("--cgminer-port", type=int, default=4028,
                        help="cgminer RPC port (default 4028)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="beesky", description="BeeSky — ASIC miner LAN scanner & repair diagnostics")
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="scan a target for miners and report health")
    _add_common_args(scan)
    scan.add_argument("--json", metavar="FILE", help="write status records as JSON")
    scan.add_argument("--tickets", metavar="DIR",
                      help="write one repair ticket per problem miner into DIR")
    scan.set_defaults(func=cmd_scan)

    watch = sub.add_parser(
        "watch", help="watch a target, emit events and send notifications")
    _add_common_args(watch)
    watch.add_argument("--interval", type=float, default=30,
                       help="seconds between scan passes (default 30)")
    watch.add_argument("--notify", metavar="CONFIG",
                       help="notify config JSON (see docs/notify.example.json)")
    watch.add_argument("--state", metavar="FILE",
                       help="persist engine state as JSON (needed for --once "
                            "change detection across runs)")
    watch.add_argument("--once", action="store_true",
                       help="run a single pass and exit")
    watch.set_defaults(func=cmd_watch)

    serve = sub.add_parser(
        "serve", help="serve the web dashboard, scanning on an interval")
    _add_common_args(serve)
    serve.add_argument("--port", type=int, default=8787,
                       help="HTTP port for the dashboard (default 8787)")
    serve.add_argument("--host", default="127.0.0.1",
                       help="bind address (default 127.0.0.1; no auth in "
                            "v0.4 — widen only on a trusted LAN)")
    serve.add_argument("--interval", type=float, default=30,
                       help="seconds between scan passes (default 30)")
    serve.add_argument("--notify", metavar="CONFIG",
                       help="notify config JSON (see docs/notify.example.json)")
    serve.set_defaults(func=cmd_serve)

    agent = sub.add_parser(
        "agent", help="run at the farm: scan locally, push to the cloud")
    _add_common_args(agent)
    agent.add_argument("--cloud", required=True, metavar="URL",
                       help="cloud base URL, e.g. https://cloud.example.com")
    agent.add_argument("--key", default=os.environ.get("BEESKY_AGENT_KEY"),
                       metavar="KEY",
                       help="agent key from `beesky cloud-add-agent` "
                            "(or env BEESKY_AGENT_KEY)")
    agent.add_argument("--site", required=True, metavar="NAME",
                       help="site name this agent reports as, e.g. 'Xưởng 1'")
    agent.add_argument("--interval", type=float, default=30,
                       help="seconds between scan passes (default 30)")
    agent.add_argument("--notify", metavar="CONFIG",
                       help="notify config JSON — local channels still "
                            "fire when the cloud is unreachable")
    agent.add_argument("--once", action="store_true",
                       help="run a single pass and exit")
    agent.set_defaults(func=cmd_agent)

    cloud = sub.add_parser(
        "cloud", help="run the cloud server (agents push, browsers view)")
    cloud.add_argument("--port", type=int, default=8788,
                       help="HTTP port (default 8788)")
    cloud.add_argument("--host", default="127.0.0.1",
                       help="bind address (default 127.0.0.1; use 0.0.0.0 "
                            "behind a reverse proxy / on a trusted host)")
    cloud.add_argument("--db", default="beesky-cloud.db", metavar="FILE",
                       help="SQLite database file (default beesky-cloud.db)")
    cloud.set_defaults(func=cmd_cloud)

    add_agent = sub.add_parser(
        "cloud-add-agent", help="register a farm agent and print its key once")
    add_agent.add_argument("--site", required=True, metavar="NAME",
                           help="site name, e.g. 'Xưởng 1'")
    add_agent.add_argument("--db", default="beesky-cloud.db", metavar="FILE",
                           help="SQLite database file (default "
                                "beesky-cloud.db)")
    add_agent.set_defaults(func=cmd_cloud_add_agent)

    args = parser.parse_args(argv)
    return args.func(args)
