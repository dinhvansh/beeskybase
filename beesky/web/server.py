"""Web dashboard server — stdlib-only monitoring UI for BeeSky.

    python -m beesky serve <target> --port 8787 --interval 30
                                      [--host 127.0.0.1] [--notify cfg.json]

A :class:`MonitorService` runs the normal scan pipeline (discovery +
per-vendor adapters, injected as a callable so this module never imports
the CLI) on an interval in a background thread. Each pass feeds the
v0.3 :class:`~beesky.core.events.EventEngine`, dispatches the events
through :class:`~beesky.core.notify.Notifier`, and keeps the latest
state in memory:

  * the newest status record per miner IP,
  * a ring buffer with the last 200 events.

A ``ThreadingHTTPServer`` then serves one self-contained dashboard page
plus a small JSON API:

  GET  /             dashboard HTML (beesky/web/dashboard.html)
  GET  /api/miners   {"generated_at", "generated_ts", "miners": [...]}
  GET  /api/events   {"generated_at", "events": [...]}   (?n= capped at 200)
  GET  /api/status   {"uptime_s", "target", "interval", "miner_count",
                      "event_count", "last_scan_at", "scanning"}
  POST /api/scan     trigger an immediate background scan -> 202 {"ok": true}

There is **no authentication** in v0.4, so the default bind is
127.0.0.1. Binding anything wider (``--host 0.0.0.0``, as the Docker
image does inside its container) is the deployer's explicit choice —
see docs/web.md.
"""

from __future__ import annotations

import json
import sys
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

EVENTS_BUFFER = 200

_FALLBACK_HTML = """<!DOCTYPE html>
<html lang="vi"><head><meta charset="utf-8"><title>BeeSky</title></head>
<body style="background:#000;color:#fff;font-family:sans-serif">
<h1 style="color:#F5D800">BeeSky</h1>
<p>Không tìm thấy file dashboard.html cạnh server.py — API vẫn hoạt động:
<a style="color:#F5D800" href="/api/miners">/api/miners</a>,
<a style="color:#F5D800" href="/api/status">/api/status</a>.</p>
</body></html>"""


def _load_dashboard_html() -> bytes:
    path = Path(__file__).with_name("dashboard.html")
    try:
        return path.read_bytes()
    except OSError:
        return _FALLBACK_HTML.encode("utf-8")


def _is_error_record(record: dict) -> bool:
    return any(p.get("code") == "FETCH_ERROR" for p in record["problems"])


def _stamp(ts: float) -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))


# ---------------------------------------------------------------------------
# monitoring service
# ---------------------------------------------------------------------------

class MonitorService:
    """Repeated scans + event engine + notify, with in-memory state.

    *scan_fn* is a zero-argument callable returning one pass of normalised
    status records (the CLI passes its own ``_scan_records``); keeping it
    injected means the web layer reuses the exact scan/watch pipeline —
    adapters, credentials and ports included — without importing the CLI.
    """

    def __init__(self, scan_fn, target: str, interval: float = 30.0,
                 notify_config: dict | None = None):
        from ..core.events import EventEngine
        from ..core.notify import Notifier

        notify_config = notify_config or {}
        self._scan_fn = scan_fn
        self.target = target
        self.interval = float(interval)
        self.engine = EventEngine(notify_config.get("thresholds"))
        self.notifier = Notifier(notify_config)

        self._lock = threading.Lock()
        self._miners: dict[str, dict] = {}
        self._seen_last: set[str] = set()
        self._events: deque = deque(maxlen=EVENTS_BUFFER)
        self._event_total = 0
        self._last_scan_at: float | None = None
        self._scan_count = 0

        self._started_at = time.time()
        self._stop = threading.Event()
        self._scan_lock = threading.Lock()  # at most one scan at a time
        self._thread: threading.Thread | None = None

    # -- lifecycle ------------------------------------------------------

    def start(self) -> None:
        self._thread = threading.Thread(
            target=self._loop, name="beesky-monitor", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5)

    def _loop(self) -> None:
        while not self._stop.is_set():
            self.run_scan()
            self._stop.wait(self.interval)

    # -- scanning ---------------------------------------------------------

    @property
    def scanning(self) -> bool:
        return self._scan_lock.locked()

    def trigger_scan(self) -> bool:
        """Start a scan in a side thread; False if one is already running."""
        if self.scanning:
            return False
        threading.Thread(target=self.run_scan, name="beesky-scan-once",
                         daemon=True).start()
        return True

    def run_scan(self) -> None:
        """One full pass: scan -> engine -> state -> notifications."""
        if not self._scan_lock.acquire(blocking=False):
            return
        try:
            try:
                records = self._scan_fn()
            except Exception as exc:  # noqa: BLE001 — keep the loop alive
                print(f"beesky serve: scan failed: {exc}", file=sys.stderr)
                return
            present = {r["ip"]: r for r in records
                       if not _is_error_record(r)}
            events = self.engine.observe_cycle(present)
            now = time.time()
            with self._lock:
                for ip, record in present.items():
                    self._miners[ip] = record
                self._seen_last = set(present)
                self._events.extend(events)
                self._event_total += len(events)
                self._last_scan_at = now
                self._scan_count += 1
            for event in events:
                print(f"EVENT {event['type']} [{event['severity']}] "
                      f"{event['ip']} {event['model']} — {event['detail']}",
                      flush=True)
                self.notifier.dispatch(event)
                for error in self.notifier.pop_errors():
                    print(f"notify error: {error}", file=sys.stderr)
        finally:
            self._scan_lock.release()

    # -- snapshots (copies, safe to serialise after the lock is dropped) ---

    def snapshot_miners(self) -> list[dict]:
        with self._lock:
            return [{**record, "online": ip in self._seen_last}
                    for ip, record in sorted(self._miners.items())]

    def snapshot_events(self, n: int = 50) -> list[dict]:
        n = max(1, min(int(n), EVENTS_BUFFER))
        with self._lock:
            return list(reversed(self._events))[:n]  # newest first

    def status(self) -> dict:
        with self._lock:
            return {
                "uptime_s": int(time.time() - self._started_at),
                "target": self.target,
                "interval": self.interval,
                "miner_count": len(self._miners),
                "event_count": self._event_total,
                "events_buffered": len(self._events),
                "scan_count": self._scan_count,
                "last_scan_at": (_stamp(self._last_scan_at)
                                 if self._last_scan_at else None),
                "last_scan_ts": self._last_scan_at,
                "scanning": self.scanning,
            }


# ---------------------------------------------------------------------------
# HTTP layer
# ---------------------------------------------------------------------------

def make_handler(service: MonitorService, dashboard_html: bytes):
    class Handler(BaseHTTPRequestHandler):
        server_version = "BeeSky/0.4"
        protocol_version = "HTTP/1.1"

        # Polling every 10 s per open tab would flood the console.
        def log_message(self, *_args):  # noqa: D102 — silence access log
            pass

        def _send(self, code: int, body: bytes, content_type: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_json(self, code: int, payload: dict) -> None:
            self._send(code, json.dumps(payload, ensure_ascii=False)
                       .encode("utf-8"), "application/json; charset=utf-8")

        def do_GET(self):  # noqa: N802 — stdlib handler API
            parsed = urlparse(self.path)
            if parsed.path == "/":
                self._send(200, dashboard_html,
                           "text/html; charset=utf-8")
            elif parsed.path == "/api/miners":
                now = time.time()
                self._send_json(200, {
                    "generated_at": _stamp(now), "generated_ts": now,
                    "miners": service.snapshot_miners()})
            elif parsed.path == "/api/events":
                raw_n = parse_qs(parsed.query).get("n", ["50"])[0]
                try:
                    n = int(raw_n)
                except ValueError:
                    n = 50
                now = time.time()
                self._send_json(200, {
                    "generated_at": _stamp(now), "generated_ts": now,
                    "events": service.snapshot_events(n)})
            elif parsed.path == "/api/status":
                self._send_json(200, service.status())
            else:
                self._send_json(404, {"error": "not found",
                                      "path": parsed.path})

        def do_POST(self):  # noqa: N802 — stdlib handler API
            parsed = urlparse(self.path)
            length = int(self.headers.get("Content-Length") or 0)
            if length:
                self.rfile.read(length)  # drain; the body is ignored
            if parsed.path == "/api/scan":
                started = service.trigger_scan()
                self._send_json(202, {"ok": True, "started": started})
            else:
                self._send_json(404, {"error": "not found",
                                      "path": parsed.path})

    return Handler


def run_server(service: MonitorService, host: str = "127.0.0.1",
               port: int = 8787) -> None:
    """Start the monitor thread and serve HTTP until Ctrl+C."""
    dashboard_html = _load_dashboard_html()
    httpd = ThreadingHTTPServer((host, port), make_handler(service,
                                                           dashboard_html))
    httpd.daemon_threads = True
    service.start()
    print(f"BeeSky web: http://{host}:{port} — quét {service.target} "
          f"mỗi {service.interval:g}s (Ctrl+C để dừng)", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nbeesky serve stopped")
    finally:
        service.stop()
        httpd.server_close()
