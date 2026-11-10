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

    python -m beesky gui [--target 192.168.1.0/24]
    python -m beesky gui --smoke <target>   (headless self-check)

    python -m beesky update [--check] [--url-base URL]
                                   [--force-file PATH] [--relaunch]
                                   (signed self-update, docs/updating.md)

    python -m beesky fw identify <ip> [--ssh-user root]
                                   [--ssh-password-env VAR] [--ssh-key F]
    python -m beesky fw install <ip> <firmware-file> [--yes]
                                   [--wait-minutes 5] (VNish API or stock CGI)
    python -m beesky fw unlock <ip> --payload-dir DIR --experimental-unlock
                                   [--race-delay-ms 0]
                                   (THỬ NGHIỆM — also needs env
                                    BEESKY_ALLOW_UNLOCK=1 + typed IP
                                    confirmation; docs/firmware.md)
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
import time
from pathlib import Path

from . import __version__
from .agent import AgentService
from .cloud.server import run_cloud_server
from .cloud.store import CloudStore
from .core import firmware as firmware_mod
from .core import notify as notify_mod
from .core import report
from .core import updater
from .core.bitmain import BitmainClient, BitmainError
from .core.cgminer import CgminerClient, CgminerError
from .core.dashd import DashdClient, DashdError
from .core.discover import Candidate, discover, probe_host
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
    # Command executors (v0.6) talk to the miners with the very same
    # credentials/ports the scan adapters above already use.
    creds = {"user": args.user, "password": args.password,
             "api_key": args.api_key, "token": args.token,
             "http_port": args.http_port, "cgminer_port": args.cgminer_port,
             "timeout": max(args.timeout, 2.0)}
    service = AgentService(lambda: _scan_records(args), cloud_url=args.cloud,
                           key=args.key, site=args.site,
                           interval=args.interval, notify_config=config,
                           creds=creds, auto_update=args.auto_update,
                           update_url_base=args.update_url)
    service.run(once=args.once)
    return 0


# ---------------------------------------------------------------------------
# update — signed self-update channel (v0.10, docs/updating.md)
# ---------------------------------------------------------------------------

def cmd_update(args: argparse.Namespace) -> int:
    print(f"BeeSky {__version__} — signed self-update channel")
    if args.check:
        res = updater.check(args.url_base)
        if not res["enabled"]:
            print(res["error"])
            return 0
        if not res["ok"]:
            print(res["error"], file=sys.stderr)
            return 2
        print(f"signature: OK (release manifest verified)")
        print(f"current: {res['current']}   latest: {res['latest']}")
        if res["update_available"]:
            names = ", ".join(f["name"] for f in res["manifest"]["files"])
            print(f"UPDATE AVAILABLE: {res['latest']} — run "
                  f"`beesky update` to install (files: {names})")
        else:
            print("already up to date")
        return 0
    # --force-file PATH updates that file (entry = its basename);
    # without it the running frozen exe is the target (updater
    # refuses source runs itself).
    target = args.force_file
    verdict = updater.apply(args.url_base, target_path=target,
                            relaunch=args.relaunch)
    print(verdict["message"])
    if not verdict["ok"]:
        return 2
    if verdict["restart_scheduled"]:
        print("exiting now so the update can finish — BeeSky restarts "
              "into the new version" if args.relaunch else
              "exiting now so the swap helper can finish the update")
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


def cmd_gui(args: argparse.Namespace) -> int:
    from .gui import run_gui, smoke
    if args.smoke:
        return smoke(args.smoke)
    return run_gui(default_target=args.target)


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
# fw — firmware identify / install / unlock (v0.11, docs/firmware.md)
# ---------------------------------------------------------------------------

def _fw_ssh(args: argparse.Namespace) -> firmware_mod.SshRunner:
    """Build the SshRunner from the fw flags (creds only from flags/env)."""
    password = None
    if args.ssh_password_env:
        password = os.environ.get(args.ssh_password_env)
    return firmware_mod.SshRunner(
        args.ip, user=args.ssh_user, password=password,
        port=args.ssh_port, key_file=args.ssh_key)


def _confirm_ip(ip: str, action: str) -> bool:
    """Typed confirmation: the operator must retype the target IP."""
    try:
        typed = input(f"Gõ lại đúng IP đích ({ip}) để xác nhận {action}: ")
    except EOFError:
        typed = ""
    return typed.strip() == ip


def cmd_fw_identify(args: argparse.Namespace) -> int:
    info = firmware_mod.identify(
        args.ip, http_port=args.http_port, cgminer_port=args.cgminer_port,
        user=args.user, password=args.password, api_key=args.api_key,
        token=args.token, ssh=_fw_ssh(args), timeout=args.timeout)
    print(f"IP:           {info['ip']}")
    print(f"Nguồn (probe): {info['source'] or '—'}")
    print(f"Model:        {info['model'] or '—'}")
    if info["miner_type"]:
        print(f"miner_type.cgi: {info['miner_type']}")
    if info["compile_time"]:
        print(f"compile_time (SSH): {info['compile_time']}")
    print(f"SSH:          {info['ssh']}")
    for note in info["notes"]:
        print(f"  ghi chú: {note}")
    print(f"Kết luận:     {info['verdict']}")
    return 0 if info["source"] else 1


def cmd_fw_install(args: argparse.Namespace) -> int:
    fw_path = Path(args.file)
    if not fw_path.is_file():
        print(f"fw install: không thấy file firmware: {fw_path}",
              file=sys.stderr)
        return 2
    size, sha256 = firmware_mod.file_info(fw_path)
    print(f"Firmware: {fw_path} — {size} bytes, sha256 {sha256}")

    cand = probe_host(args.ip, timeout=args.timeout,
                      http_port=args.http_port,
                      cgminer_port=args.cgminer_port,
                      username=args.user, password=args.password,
                      api_key=args.api_key, token=args.token)
    if cand is None or cand.source not in ("vnish", "stock"):
        found = cand.source if cand else "không có phản hồi"
        print(f"fw install: {args.ip} không phải đích cài firmware được "
              f"(probe: {found}) — chỉ cài được cho máy VNish/dashd "
              "(qua API) hoặc stock Bitmain (qua upgrade.cgi)",
              file=sys.stderr)
        return 1
    print(f"Đích: {args.ip} — nguồn {cand.source}"
          + (f", model {cand.model}" if cand.model else ""))
    if not args.yes:
        if not _confirm_ip(args.ip, "cài firmware"):
            print("Đã huỷ — IP gõ vào không khớp.", file=sys.stderr)
            return 2
    if cand.source == "vnish":
        ok, message = firmware_mod.install_dashd(
            args.ip, fw_path, http_port=args.http_port,
            api_key=args.api_key, token=args.token,
            dashd_password=args.dashd_password,
            keep_settings=args.keep_settings)
    else:
        ok, message = firmware_mod.install_stock(
            args.ip, fw_path, http_port=args.http_port,
            user=args.user, password=args.password)
    print(("OK: " if ok else "THẤT BẠI: ") + message)
    if not ok:
        return 1
    firmware_mod.wait_back(
        args.ip, minutes=args.wait_minutes, http_port=args.http_port,
        cgminer_port=args.cgminer_port, user=args.user,
        password=args.password, api_key=args.api_key, token=args.token)
    return 0


def cmd_fw_unlock(args: argparse.Namespace) -> int:
    # HARD GATES — all checked before ANY network I/O (docs/firmware.md).
    if not args.experimental_unlock:
        print("fw unlock: TỪ CHỐI — thiếu cờ --experimental-unlock. "
              "Đây là tính năng THỬ NGHIỆM theo recipe khôi phục từ "
              "HashCore Toolkit; đọc docs/firmware.md trước.",
              file=sys.stderr)
        return 2
    if os.environ.get("BEESKY_ALLOW_UNLOCK") != "1":
        print("fw unlock: TỪ CHỐI — chưa đặt biến môi trường "
              "BEESKY_ALLOW_UNLOCK=1.", file=sys.stderr)
        return 2
    first, second = firmware_mod.payload_paths(args.payload_dir)
    missing = [p.name for p in (first, second) if not p.is_file()]
    if missing:
        print(f"fw unlock: TỪ CHỐI — thiếu file payload trong "
              f"{args.payload_dir}: {', '.join(missing)}. BeeSky không "
              "kèm sẵn file .bmu (chúng nằm trong gói firmware) — xem "
              "docs/firmware.md.", file=sys.stderr)
        return 2
    print("fw unlock — THỬ NGHIỆM: nạp update_first.bmu + đua kill "
          "tiến trình kiểm chữ ký + update_second.bmu lên máy stock "
          "đang khoá. Hãy thử boot SD trước; hỏng thì khôi phục bằng "
          "firmware gốc / SD.")
    if not _confirm_ip(args.ip, "unlock THỬ NGHIỆM"):
        print("Đã huỷ — IP gõ vào không khớp.", file=sys.stderr)
        return 2
    ok, _stages = firmware_mod.unlock(
        args.ip, args.payload_dir, http_port=args.http_port,
        user=args.user, password=args.password, ssh=_fw_ssh(args),
        race_delay_ms=args.race_delay_ms)
    print("UNLOCK THÀNH CÔNG" if ok else
          "UNLOCK CHƯA THÀNH CÔNG — xem stage FAIL ở trên")
    return 0 if ok else 1


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


def _add_fw_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("ip", help="miner IP address (single host)")
    parser.add_argument("--timeout", type=float, default=3.0,
                        help="per-probe timeout in seconds (default 3)")
    parser.add_argument("--user", default="root",
                        help="stock-firmware web username (default root)")
    parser.add_argument("--password", default="root",
                        help="stock-firmware web password (default root)")
    parser.add_argument("--api-key", metavar="KEY",
                        help="dashd (VNish) x-api-key header, if required")
    parser.add_argument("--token", metavar="JWT",
                        help="dashd (VNish) bearer token, if required")
    parser.add_argument("--dashd-password", metavar="PW",
                        help="dashd web password — exchanged for a JWT "
                             "via /unlock when no --api-key/--token given")
    parser.add_argument("--http-port", type=int, default=80,
                        help="HTTP port of the miner web API (default 80)")
    parser.add_argument("--cgminer-port", type=int, default=4028,
                        help="cgminer RPC port (default 4028)")
    parser.add_argument("--ssh-user", default="root",
                        help="SSH username (default root)")
    parser.add_argument("--ssh-password-env", metavar="VAR",
                        help="environment variable holding the SSH "
                             "password (needs sshpass on this machine); "
                             "the password itself is never a CLI value")
    parser.add_argument("--ssh-port", type=int, default=22,
                        help="SSH port (default 22)")
    parser.add_argument("--ssh-key", metavar="FILE",
                        help="SSH private key file for key auth")


def main(argv: list[str] | None = None) -> int:
    # Windows consoles default to a legacy code page (cp1252/cp437) that
    # cannot encode Vietnamese text — help screens and repair tickets would
    # crash with UnicodeEncodeError. Force UTF-8 output where supported.
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
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
    agent.add_argument("--auto-update", action="store_true",
                       help="apply signed updates automatically when "
                            "the daily check finds one (default OFF — "
                            "without it the agent only reports "
                            "UPDATE_AVAILABLE to the cloud)")
    agent.add_argument("--update-url", metavar="URL",
                       help="update channel base URL (default env "
                            "BEESKY_UPDATE_URL or the GitHub releases "
                            "URL; see docs/updating.md)")
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

    gui = sub.add_parser(
        "gui", help="open the desktop GUI (windowed scanner)")
    gui.add_argument("--target", default="192.168.1.0/24",
                     help="target pre-filled in the window "
                          "(default 192.168.1.0/24)")
    gui.add_argument("--smoke", metavar="TARGET",
                     help="headless self-check: scan TARGET once, print "
                          "the GUI rows, exit (used by tests)")
    gui.set_defaults(func=cmd_gui)

    update = sub.add_parser(
        "update", help="signed self-update: check the release channel "
                       "and install a newer BeeSky (docs/updating.md)")
    update.add_argument("--check", action="store_true",
                        help="only report: current vs latest version "
                             "and signature status; change nothing")
    update.add_argument("--url-base", metavar="URL",
                        help="update channel base URL (default env "
                             "BEESKY_UPDATE_URL or the GitHub "
                             "releases/latest/download URL)")
    update.add_argument("--force-file", metavar="PATH",
                        help="update this specific file (the manifest "
                             "entry matching its name) instead of the "
                             "running executable — for testing")
    update.add_argument("--relaunch", action="store_true",
                        help="after a successful swap, relaunch the "
                             "same command line (the agent's "
                             "--auto-update path)")
    update.set_defaults(func=cmd_update)

    fw = sub.add_parser(
        "fw", help="firmware: identify / install / unlock THỬ NGHIỆM "
                   "(v0.11, docs/firmware.md)")
    fw_sub = fw.add_subparsers(dest="fw_command", required=True)

    fw_identify = fw_sub.add_parser(
        "identify", help="what firmware is this miner running?")
    _add_fw_args(fw_identify)
    fw_identify.set_defaults(func=cmd_fw_identify)

    fw_install = fw_sub.add_parser(
        "install", help="install a firmware file (VNish API / stock CGI)")
    _add_fw_args(fw_install)
    fw_install.add_argument("file", help="local firmware file to upload")
    fw_install.add_argument("--yes", action="store_true",
                            help="skip the typed-IP confirmation")
    fw_install.add_argument("--wait-minutes", type=float, default=5,
                            help="poll up to this long for the miner to "
                                 "come back after install (default 5; "
                                 "0 = don't wait)")
    fw_install.add_argument("--keep-settings", choices=("true", "false"),
                            help="dashd only: keep_settings form field "
                                 "of /firmware/update")
    fw_install.set_defaults(func=cmd_fw_install)

    fw_unlock = fw_sub.add_parser(
        "unlock", help="THỬ NGHIỆM / EXPERIMENTAL: unlock a locked stock "
                       "miner with the recovered .bmu race recipe — "
                       "hard-gated, see docs/firmware.md")
    _add_fw_args(fw_unlock)
    fw_unlock.add_argument("--payload-dir", required=True, metavar="DIR",
                           help="directory holding update_first.bmu and "
                                "update_second.bmu (owner-supplied; "
                                "BeeSky ships none)")
    fw_unlock.add_argument("--experimental-unlock", action="store_true",
                           help="gate 1 of 3: acknowledge this is the "
                                "experimental unlock (also needs env "
                                "BEESKY_ALLOW_UNLOCK=1 and typing the "
                                "target IP)")
    fw_unlock.add_argument("--race-delay-ms", type=int, default=0,
                           help="delay before the first signature-check "
                                "kill shot (default 0; no timing value "
                                "was recovered — first real run is a "
                                "calibration)")
    fw_unlock.set_defaults(func=cmd_fw_unlock)

    args = parser.parse_args(argv)
    return args.func(args)
