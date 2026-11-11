"""BeeSky command-line interface.

    python -m beesky scan <target> [--json [out.json]] [--tickets dir/]
                                   [--timeout 1.5] [--workers 64]
                                   [--user root] [--password root]
                                   [--creds-file sets.json]
                                   [--api-key KEY] [--token JWT]
                                   [--http-port 80] [--cgminer-port 4028]
                                   (--json with no FILE prints one JSON
                                    document to stdout — the Flutter
                                    shell's sidecar bridge, v0.21)
    python -m beesky scan --group NAME [--creds-file sets.json]
                                   [--groups-file beesky-groups.json]
                                   (the group's targets + credential
                                    sets lead; last_scan is persisted)
    python -m beesky groups [--groups-file FILE]
                                   list | add --name N --targets T |
                                   remove NAME | show NAME |
                                   export FILE | import FILE
                                   (network groups, v0.24 —
                                    docs/network-groups-mapping.md)

    python -m beesky sysinfo [--json]  (version + auto-detected default
                                        scan target; --json for machines)

    python -m beesky ops --job FILE   (one Operations task — rescan /
                                        reboot / switch_pool — over a
                                        job file's targets, streaming
                                        NDJSON progress; v0.26,
                                        docs/operations-mapping.md)

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
import signal
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

from . import __version__
from .agent import AgentService
from .cloud.server import run_cloud_server
from .cloud.store import CloudStore
from .core import firmware as firmware_mod
from .core import groups as groups_mod
from .core import ops as ops_mod
from .core import notify as notify_mod
from .core import report
from .core import updater
from .core.bitmain import BitmainClient, BitmainError
from .core.cgminer import CgminerClient, CgminerError
from .core.dashd import DashdClient, DashdError
from .core.discover import (Candidate, default_scan_target, discover,
                            parse_targets, probe_host)
from .core.events import EventEngine
from .web.server import MonitorService, run_server


def _normalise_creds(data: list, source: str) -> list[dict]:
    """Normalise raw credential-set entries (v0.23 schema).

    Shared by --creds-file loading and by network-group creds
    (v0.24 — a group's embedded sets are the same schema, checked
    with the same rules and the same messages). An entry needs a
    login+password pair OR an "api_key" (the VNish API-key unlock
    method — HashCore keys methods per vendor the same way).
    "label" defaults to the user name (or "api_key"); a
    missing/unknown "type" normalises to "any".
    """
    creds: list[dict] = []
    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"{source}: entry {idx} must be an object")
        user = item.get("user")
        secret = item.get("password")
        api_key = item.get("api_key")
        has_login = isinstance(user, str) and isinstance(secret, str)
        has_key = isinstance(api_key, str) and bool(api_key)
        if not has_login and not has_key:
            raise ValueError(
                f"{source}: entry {idx} needs string "
                "\"user\" + \"password\", or an \"api_key\"")
        label = item.get("label")
        raw_type = item.get("type")
        creds.append({
            "label": str(label) if label else (
                user if has_login else "api_key"),
            "user": user if isinstance(user, str) else "",
            "password": secret if isinstance(secret, str) else "",
            "api_key": api_key if has_key else None,
            "type": raw_type if raw_type in ("stock", "vnish") else "any",
        })
    return creds


def _load_creds_file(path: str) -> list[dict]:
    """Read a --creds-file: a JSON list of credential sets (v0.23).

    Schema: [{"label": "...", "user": "...", "password": "...",
    "type": "any"|"stock"|"vnish", "api_key": "..."}, ...]. Raises
    ValueError with an operator-readable message — a typo'd file
    must fail loud, never silently scan with wrong logins.
    """
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read creds file {path}: {exc}") from exc
    if not isinstance(data, list):
        raise ValueError(
            f"creds file {path}: top level must be a JSON list of "
            "{\"label\", \"user\", \"password\", \"type\"} objects")
    return _normalise_creds(data, f"creds file {path}")


def _scan_creds(args: argparse.Namespace) -> list[dict] | None:
    """Credential sets for one scan-family command (v0.23).

    --creds-file wins when given (its sets, in file order); otherwise
    None — discover() then applies the legacy single --user/--password
    pair exactly as before. The file is read once per process and
    cached on the args namespace, so watch/serve/agent loops don't
    re-read it every pass (and can't crash mid-loop on a deleted
    file). Raises ValueError for a malformed file; command handlers
    validate up front and turn that into exit 2 before scanning.
    """
    if getattr(args, "_creds_loaded", False):
        return getattr(args, "_creds_cache", None)
    path = getattr(args, "creds_file", None)
    creds = _load_creds_file(path) if path else None
    args._creds_cache = creds
    args._creds_loaded = True
    return creds


def _validate_creds(args: argparse.Namespace, command: str) -> int | None:
    """Resolve --creds-file early; an exit code when it is malformed."""
    try:
        _scan_creds(args)
    except ValueError as exc:
        print(f"{command}: {exc}", file=sys.stderr)
        return 2
    return None


def _fetch_record(cand: Candidate, args: argparse.Namespace) -> dict:
    """Pull full health data for one candidate via its claiming adapter."""
    ip, timeout = cand.ip, max(args.timeout, 2.0)
    if cand.source == "vnish":
        client = DashdClient(ip, port=cand.http_port, timeout=timeout,
                             api_key=args.api_key or cand.dashd_api_key,
                             token=args.token or cand.dashd_token)
        try:
            record = client.fetch_record(ip)
        except DashdError as exc:
            record = report.error_record(ip, str(exc), source="vnish")
    elif cand.source == "stock":
        # The fetch reuses the exact set that won the probe (v0.23) —
        # cand.username/password carry it; they default to the scan's
        # legacy pair for candidates claimed any other way.
        client = BitmainClient(ip, port=cand.http_port, timeout=timeout,
                               username=cand.username,
                               password=cand.password)
        try:
            record = client.fetch_record(ip,
                                         status_data=cand.status_data or None)
        except BitmainError as exc:
            record = report.error_record(ip, str(exc), source="stock")
    else:
        # cgminer RPC (also the fallback for port-open-but-silent
        # candidates) — no auth, so never a cred_label.
        client = CgminerClient(ip, port=cand.cgminer_port, timeout=timeout)
        try:
            summary = client.summary()
            stats = client.stats()
        except CgminerError as exc:
            record = report.error_record(ip, str(exc), source="cgminer")
        else:
            record = report.build_record(ip, summary, stats, source="cgminer")
    # The winning set's label rides the record (v0.23) so the apps can
    # show which login a machine line uses; error records and RPC /
    # default-cred records stay label-free.
    if cand.cred_label and not _is_error_record(record):
        record["cred_label"] = cand.cred_label
    return record


def _scan_records(args: argparse.Namespace) -> list[dict]:
    """One full scan pass: discover + fetch, as normalised records."""
    candidates = discover(
        args.target, timeout=args.timeout, workers=args.workers,
        http_port=args.http_port, cgminer_port=args.cgminer_port,
        username=args.user, password=args.password,
        api_key=args.api_key, token=args.token,
        creds=_scan_creds(args))
    return [_fetch_record(c, args) for c in candidates]


def _print_table(records: list[dict]) -> None:
    headers = ["IP", "Model", "Source", "Hashrate", "Chips", "MaxTemp", "Fans", "Status"]
    rows: list[list[str]] = []
    for rec in records:
        chips = f"{rec['chips_alive']}/{rec['chips_total']}" if rec["chips_total"] else "-"
        temp = f"{rec['max_temp_c']:.0f}" if rec["max_temp_c"] is not None else "-"
        fans = "/".join(str(f) for f in rec["fans_rpm"]) or "-"
        rows.append([rec["ip"], str(rec["model"]), str(rec.get("source", "-")),
                     report.format_rate(rec), chips, temp, fans, rec["status"]])
    widths = [max(len(headers[i]), *(len(r[i]) for r in rows)) if rows else len(headers[i])
              for i in range(len(headers))]
    fmt = " | ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers))
    print("-+-".join("-" * w for w in widths))
    for row in rows:
        print(fmt.format(*row))


def _jsonable(value):
    """Coerce a value into plain JSON-safe data for the bridge.

    Records are plain dicts already (the cloud/agent path ships them
    as JSON), but the bridge must never crash on an exotic leaf an
    adapter might grow tomorrow: tuples/sets become lists, dict keys
    strings, anything else falls back to its repr-free str().
    """
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, (set, frozenset)):
        return [_jsonable(v) for v in sorted(value, key=repr)]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _apply_group(args: argparse.Namespace):
    """Resolve `scan --group NAME` (v0.24) onto the args namespace.

    The group's targets replace the scan target, and the credential
    layers merge core-side: the group's own sets first, then the
    --creds-file (global) sets, pre-seeded into the _scan_creds
    cache so _scan_records consumes the merged list.
    discover.ordered_creds partitions that list stably, so its
    tiers try group-family → global-family → group-any →
    global-any → the rest. Returns (store, group) so cmd_scan can
    persist last_scan afterwards; None without --group. Raises
    ValueError (unknown group, unreadable store, malformed creds
    anywhere) — cmd_scan turns it into exit 2 before scanning.
    """
    name = getattr(args, "group", None)
    if not name:
        return None
    store = groups_mod.GroupStore(getattr(args, "groups_file", None))
    group = store.find(name)
    if group is None:
        raise ValueError(
            f"group not found: {name!r} (store: {store.path})")
    group_sets = _normalise_creds(
        group["creds"], f"group {name!r} creds") if group["creds"] else None
    merged = groups_mod.effective_creds(group_sets, _scan_creds(args))
    if merged is not None:
        args._creds_cache = merged
        args._creds_loaded = True
    args.target = group["targets"]
    return store, group


def _persist_group_scan(store: groups_mod.GroupStore, group: dict,
                        records: list[dict]) -> None:
    """Write the group's last_scan summary after a successful scan.

    Best-effort: a store that refuses the write must not fail a
    scan that already succeeded — the warning goes to stderr,
    which bridge mode keeps off stdout by design.
    """
    try:
        scanned = len(parse_targets(group["targets"]))
    except ValueError:
        scanned = len(records)
    summary = groups_mod.scan_summary(
        records, scanned,
        datetime.now().astimezone().isoformat(timespec="seconds"))
    try:
        store.record_scan(group["name"], summary)
    except (ValueError, OSError) as exc:
        print(f"scan: warning: could not save last_scan for group "
              f"{group['name']!r}: {exc}", file=sys.stderr)


def cmd_scan(args: argparse.Namespace) -> int:
    # --json with no FILE ("-" sentinel from argparse) selects the
    # sidecar bridge mode (v0.21): stdout carries ONE JSON document
    # and nothing else — the Flutter shell parses it. All human
    # output is suppressed or moved to stderr in that mode.
    bridge = getattr(args, "json", None) == "-"
    started = time.monotonic()
    try:
        group_ctx = _apply_group(args)
        records = _scan_records(args)
    except ValueError as exc:
        print(f"scan: {exc}", file=sys.stderr)
        return 2
    elapsed = time.monotonic() - started

    if bridge:
        try:
            scanned = len(parse_targets(args.target))
        except ValueError:
            scanned = len(records)
        payload = {
            "records": [_jsonable(r) for r in records],
            "scanned": scanned,
            "found": len(records),
            "elapsed_s": round(elapsed, 3),
        }
        print(json.dumps(payload, ensure_ascii=False))
    else:
        if not records:
            print("No miners found.")
        else:
            _print_table(records)
            bad = sum(1 for r in records if r["status"] != "OK")
            print(f"\nFound {len(records)} miner(s), {bad} need(s) checking.")
        if args.json:
            Path(args.json).write_text(
                json.dumps(records, indent=2, ensure_ascii=False),
                encoding="utf-8")
            print(f"JSON written to {args.json}")
    if group_ctx is not None:
        _persist_group_scan(group_ctx[0], group_ctx[1], records)
    if args.tickets:
        written = report.write_tickets(records, args.tickets)
        for path in written:
            print(f"Ticket written to {path}",
                  file=sys.stderr if bridge else sys.stdout)
    return 0


def cmd_sysinfo(args: argparse.Namespace) -> int:
    """Version + auto-detected default target (Flutter handshake).

    The Flutter app cannot reimplement the subnet detection, so the
    sidecar answers it here: `beesky sysinfo --json` ->
    {"version": ..., "default_target": ...}.
    """
    info = {"version": __version__,
            "default_target": default_scan_target()}
    if args.json:
        print(json.dumps(info, ensure_ascii=False))
    else:
        print(f"BeeSky {info['version']}")
        print(f"Default scan target: {info['default_target']}")
    return 0


# ---------------------------------------------------------------------------
# groups — network groups (v0.24): named scan targets with their own
# credential sets, autoscan settings and last-scan summaries, stored
# in beesky-groups.json (docs/network-groups-mapping.md)
# ---------------------------------------------------------------------------

def _group_store(args: argparse.Namespace) -> groups_mod.GroupStore:
    return groups_mod.GroupStore(getattr(args, "groups_file", None))


def _groups_fail(message: str) -> int:
    print(f"groups: {message}", file=sys.stderr)
    return 2


def cmd_groups(args: argparse.Namespace) -> int:
    store = _group_store(args)
    action = args.groups_command
    try:
        groups = store.load()
    except ValueError as exc:
        return _groups_fail(str(exc))

    if action == "list":
        if not groups:
            print(f"No groups defined (store: {store.path}).")
            return 0
        for g in groups:
            last = g["last_scan"]
            last_text = ("never scanned" if last is None else
                         f"last scan {last['at']}: {last['found']} found, "
                         f"{last['ok']} ok, {last['check']} check, "
                         f"{last['error']} error")
            auto = (f"autoscan {g['autoscan']['interval_min']}m"
                    if g["autoscan"]["enabled"] else "autoscan off")
            print(f"{g['name']}  [{g['targets']}]  "
                  f"{len(g['creds'])} cred set(s), {auto}, {last_text}")
        return 0

    if action == "add":
        if groups_mod.find_group(groups, args.name.strip()) is not None:
            return _groups_fail(f"group already exists: {args.name!r}")
        try:
            group = groups_mod.normalise_group(
                {"name": args.name, "targets": args.targets},
                "groups add")
        except ValueError as exc:
            return _groups_fail(str(exc))
        groups.append(group)
        store.save(groups)
        print(f"Added group {group['name']!r} [{group['targets']}] "
              f"(store: {store.path}).")
        return 0

    if action == "remove":
        group = groups_mod.find_group(groups, args.name)
        if group is None:
            return _groups_fail(f"group not found: {args.name!r}")
        store.save([g for g in groups if g["name"] != group["name"]])
        print(f"Removed group {group['name']!r}.")
        return 0

    if action == "show":
        group = groups_mod.find_group(groups, args.name)
        if group is None:
            return _groups_fail(f"group not found: {args.name!r}")
        print(json.dumps(group, indent=2, ensure_ascii=False))
        return 0

    if action == "export":
        payload = {"version": groups_mod.STORE_VERSION, "groups": groups}
        try:
            Path(args.file).write_text(
                json.dumps(payload, indent=2, ensure_ascii=False),
                encoding="utf-8")
        except OSError as exc:
            return _groups_fail(f"cannot write {args.file}: {exc}")
        print(f"Exported {len(groups)} group(s) to {args.file}.")
        return 0

    if action == "import":
        try:
            data = json.loads(Path(args.file).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return _groups_fail(f"cannot read import file {args.file}: {exc}")
        if isinstance(data, list):
            raw_groups = data
        elif isinstance(data, dict) and isinstance(data.get("groups"), list):
            raw_groups = data["groups"]
        else:
            return _groups_fail(
                f"import file {args.file}: expected the groups document "
                "({\"version\": 1, \"groups\": [...]}) or a bare list")
        try:
            imported = [groups_mod.normalise_group(
                item, f"{args.file} entry {idx}")
                for idx, item in enumerate(raw_groups)]
        except ValueError as exc:
            return _groups_fail(str(exc))
        before = {g["name"] for g in groups}
        merged = groups_mod.merge_import(groups, imported)
        store.save(merged)
        replaced = sum(1 for g in imported if g["name"] in before)
        print(f"Imported {len(imported)} group(s) from {args.file}: "
              f"{replaced} replaced, {len(imported) - replaced} added, "
              f"{len(merged)} total.")
        return 0

    return _groups_fail(f"unknown groups command: {action}")


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


def cmd_ops(args: argparse.Namespace) -> int:
    """Run one Operations task from a job file, NDJSON to stdout.

    Exit 2 when the job (or its group / creds references) is
    malformed — validated before any device is touched, like
    scan's contract. A job that RAN exits 0 whatever the
    per-device outcomes were; the summary line carries the
    counts and the derived task status.
    """
    try:
        job = ops_mod.load_job(args.job)
        # Resolve creds up front too: an unknown group / unreadable
        # creds file must fail before the stream's first line.
        ops_mod.resolve_creds(job)
    except ops_mod.JobError as exc:
        print(f"ops: {exc}", file=sys.stderr)
        return 2

    cancel = threading.Event()

    def _request_cancel(signum, frame):  # noqa: ARG001 — signal API
        cancel.set()

    # POSIX stop path (mapping §4.7): SIGTERM/SIGINT ask the runner
    # to stop starting devices and still emit its summary. On
    # Windows the app kills this process outright; no handler runs.
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            signal.signal(sig, _request_cancel)
        except (ValueError, OSError):
            pass  # not the main thread / unsupported — kill still works

    def emit(event: dict) -> None:
        print(json.dumps(_jsonable(event), ensure_ascii=False),
              flush=True)

    ops_mod.run_job(job, emit, cancel)
    return 0


def cmd_watch(args: argparse.Namespace) -> int:
    bad = _validate_creds(args, "watch")
    if bad is not None:
        return bad
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
    bad = _validate_creds(args, "serve")
    if bad is not None:
        return bad
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
    bad = _validate_creds(args, "agent")
    if bad is not None:
        return bad
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
                        help="IP, CIDR (192.168.1.0/24) or range (192.168.1.10-192.168.1.60); "
                             "comma-separated mixes scan several ranges at once")
    parser.add_argument("--timeout", type=float, default=1.5,
                        help="per-probe timeout in seconds (default 1.5)")
    parser.add_argument("--workers", type=int, default=64,
                        help="max concurrent probes (default 64)")
    parser.add_argument("--user", default="root",
                        help="stock-firmware web username (default root)")
    parser.add_argument("--password", default="root",
                        help="stock-firmware web password (default root)")
    parser.add_argument("--creds-file", metavar="FILE",
                        help="JSON file with several credential sets to "
                             "try per miner, in family order: "
                             "[{\"label\": ..., \"user\": ..., \"password\": "
                             "..., \"type\": \"any|stock|vnish\", "
                             "\"api_key\": ...}, ...] — a vnish set with "
                             "api_key authenticates by x-api-key instead "
                             "of login (v0.23; takes precedence over "
                             "--user/--password; the winning set's label "
                             "lands on the record as cred_label)")
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
    # A --group scan takes its target from the group (v0.24), so the
    # positional becomes optional for scan alone; main() re-checks
    # that a target or a group was given.
    for _action in scan._actions:
        if _action.dest == "target":
            _action.nargs = "?"
    scan.add_argument("--group", metavar="NAME",
                      help="scan a saved network group: its targets "
                           "replace the positional target and its own "
                           "credential sets merge ahead of "
                           "--creds-file's (v0.24; see `beesky groups`)")
    scan.add_argument("--groups-file", metavar="FILE",
                      help="groups store file for --group (default: "
                           "beesky-groups.json beside the executable, "
                           "fallback %%APPDATA%%\\BeeSky; or env "
                           "BEESKY_GROUPS_FILE)")
    scan.add_argument("--json", nargs="?", const="-", metavar="FILE",
                      help="write status records as JSON to FILE; with no "
                           "FILE, print ONE JSON document to stdout "
                           "(sidecar bridge mode for the Flutter shell)")
    scan.add_argument("--tickets", metavar="DIR",
                      help="write one repair ticket per problem miner into DIR")
    scan.set_defaults(func=cmd_scan)

    groups = sub.add_parser(
        "groups", help="network groups: named scan targets with "
                       "their own credential sets, autoscan settings "
                       "and last-scan summaries (v0.24)")
    groups.add_argument("--groups-file", metavar="FILE",
                        help="groups store file (default: "
                             "beesky-groups.json beside the executable, "
                             "fallback %%APPDATA%%\\BeeSky; or env "
                             "BEESKY_GROUPS_FILE)")
    groups_sub = groups.add_subparsers(dest="groups_command", required=True)
    groups_sub.add_parser("list", help="list all groups")
    g_add = groups_sub.add_parser("add", help="add a group")
    g_add.add_argument("--name", required=True, help="group name")
    g_add.add_argument("--targets", required=True,
                       help="scan targets: CIDR / range / comma mix "
                            "(same syntax as the scan target)")
    g_remove = groups_sub.add_parser("remove", help="remove a group")
    g_remove.add_argument("name", help="group name")
    g_show = groups_sub.add_parser("show", help="print one group as JSON")
    g_show.add_argument("name", help="group name")
    g_export = groups_sub.add_parser(
        "export", help="export all groups as JSON")
    g_export.add_argument("file", help="destination file")
    g_import = groups_sub.add_parser(
        "import", help="import groups from a JSON file, merging BY "
                       "NAME (a same-name group replaces the stored "
                       "one, others are kept)")
    g_import.add_argument("file", help="file written by `groups export`")
    groups.set_defaults(func=cmd_groups)

    sysinfo = sub.add_parser(
        "sysinfo", help="print version + auto-detected default scan "
                        "target (Flutter shell handshake)")
    sysinfo.add_argument("--json", action="store_true",
                         help="print as one JSON document")
    sysinfo.set_defaults(func=cmd_sysinfo)

    ops = sub.add_parser(
        "ops", help="run ONE Operations task (rescan / reboot / "
                    "switch_pool) over a set of miners, streaming "
                    "NDJSON progress (v0.26; docs/operations-"
                    "mapping.md). The job is a JSON FILE — secrets "
                    "never ride the command line")
    ops.add_argument("--job", required=True, metavar="FILE",
                     help="job JSON file (see beesky/core/ops.py "
                          "for the schema)")
    ops.set_defaults(func=cmd_ops)

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
    gui.add_argument("--target", default=None,
                     help="target pre-filled in the window (default: "
                          "this machine's own subnet, auto-detected; "
                          "fallback 192.168.1.0/24)")
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
    if getattr(args, "command", None) == "scan" and not args.target \
            and not getattr(args, "group", None):
        parser.error("scan: a target is required (or use --group NAME)")
    return args.func(args)
