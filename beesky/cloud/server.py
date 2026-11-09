"""Cloud server — receives agent pushes, serves the multi-site web.

    python -m beesky cloud --port 8788 --db beesky-cloud.db [--host H]

The deployment shape mirrors HashCore Pulse / EMCD Monitoring: an
*agent* inside each farm LAN scans the miners and dials OUT to this
server; the cloud itself never scans anything. One cloud instance
manages many sites.

Ingest (agent → cloud), authenticated per agent key
(``Authorization: Bearer <key>`` or ``X-Agent-Key: <key>``; only the
key's SHA-256 is stored — see :mod:`beesky.cloud.store`):

  POST /api/ingest         {"site", "ts", "interval", "miners": [...]}
  POST /api/ingest/events  {"site", "ts", "events": [...]}

Viewer (browser), behind a single admin password taken from the
``BEESKY_CLOUD_PASSWORD`` environment variable:

  GET  /              multi-site dashboard (beesky/cloud/dashboard.html)
  GET  /api/sites     per-site summaries computed from latest snapshots
  GET  /api/miners    latest records, ``?site=`` filters, each record
                      annotated with its ``site``
  GET  /api/events    newest-first stored events (``?n=``, ``?site=``)
  GET|POST /login     password form -> session cookie (in-memory)
  GET  /logout

If ``BEESKY_CLOUD_PASSWORD`` is unset the viewer is OPEN and startup
prints a loud warning — acceptable for a local test, never for a real
deployment. TLS is the deployer's job (reverse proxy); agent keys and
the viewer password otherwise travel as plain HTTP.
"""

from __future__ import annotations

import hmac
import json
import secrets
import sys
import time
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .store import CloudStore

MAX_BODY_BYTES = 16 * 1024 * 1024
SESSION_COOKIE = "beesky_session"
SESSION_TTL_S = 24 * 3600

_FALLBACK_HTML = """<!DOCTYPE html>
<html lang="vi"><head><meta charset="utf-8"><title>BeeSky Cloud</title></head>
<body style="background:#000;color:#fff;font-family:sans-serif">
<h1 style="color:#F5D800">BeeSky Cloud</h1>
<p>Không tìm thấy file dashboard.html — API vẫn hoạt động:
<a style="color:#F5D800" href="/api/sites">/api/sites</a>,
<a style="color:#F5D800" href="/api/miners">/api/miners</a>.</p>
</body></html>"""

_LOGIN_HTML = """<!DOCTYPE html>
<html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BeeSky Cloud — Đăng nhập</title></head>
<body style="background:#000;color:#fff;font-family:'Segoe UI',system-ui,Arial,sans-serif;
display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0">
<form method="post" action="/login" style="background:#141414;border:1px solid #2c2c2c;
border-top:3px solid #F5D800;border-radius:8px;padding:28px;width:320px">
<div style="font-size:24px;font-weight:800">Bee<span style="color:#F5D800">Sky</span> Cloud</div>
<p style="color:#a8a8a8;font-size:13px">Nhập mật khẩu quản trị để xem các trại.</p>
{error}
<input type="password" name="password" autofocus placeholder="Mật khẩu"
style="width:100%;box-sizing:border-box;padding:10px;border-radius:6px;border:1px solid #2c2c2c;
background:#1d1d1d;color:#fff;margin-bottom:12px">
<button type="submit" style="width:100%;background:#F5D800;color:#000;border:0;border-radius:6px;
padding:10px;font-weight:700;cursor:pointer">Đăng nhập</button>
</form></body></html>"""

_LOGIN_ERROR = ('<p style="color:#d9534f;font-size:13px">'
                'Mật khẩu không đúng — thử lại.</p>')


def _dashboard_candidates() -> list[Path]:
    """Where dashboard.html may live: frozen bundle first, then source.

    In the PyInstaller one-file exe the HTML ships as data under
    ``sys._MEIPASS/beesky/cloud/`` (see packaging/beesky.spec); in a
    source checkout it sits beside this module.
    """
    candidates = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass) / "beesky" / "cloud"
                          / "dashboard.html")
    candidates.append(Path(__file__).with_name("dashboard.html"))
    return candidates


def _load_dashboard_html() -> bytes:
    for path in _dashboard_candidates():
        try:
            return path.read_bytes()
        except OSError:
            continue
    return _FALLBACK_HTML.encode("utf-8")


def _stamp(ts: float) -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))


class SessionStore:
    """In-memory viewer sessions: token -> expiry timestamp."""

    def __init__(self):
        self._sessions: dict[str, float] = {}

    def create(self) -> str:
        token = secrets.token_urlsafe(32)
        self._sessions[token] = time.time() + SESSION_TTL_S
        return token

    def valid(self, token: str | None) -> bool:
        if not token:
            return False
        expiry = self._sessions.get(token)
        if expiry is None:
            return False
        if expiry < time.time():
            del self._sessions[token]
            return False
        return True

    def drop(self, token: str | None) -> None:
        if token:
            self._sessions.pop(token, None)


# ---------------------------------------------------------------------------
# HTTP layer
# ---------------------------------------------------------------------------

def make_handler(store: CloudStore, dashboard_html: bytes,
                 password: str | None):
    sessions = SessionStore()

    class Handler(BaseHTTPRequestHandler):
        server_version = "BeeSkyCloud/0.5"
        protocol_version = "HTTP/1.1"

        def log_message(self, *_args):  # noqa: D102 — silence access log
            pass

        # -- plumbing ---------------------------------------------------

        def _send(self, code: int, body: bytes, content_type: str,
                  extra: dict | None = None) -> None:
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            for name, value in (extra or {}).items():
                self.send_header(name, value)
            self.end_headers()
            self.wfile.write(body)

        def _send_json(self, code: int, payload: dict) -> None:
            self._send(code, json.dumps(payload, ensure_ascii=False)
                       .encode("utf-8"), "application/json; charset=utf-8")

        def _read_json_body(self) -> dict | None:
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                return None
            if length <= 0 or length > MAX_BODY_BYTES:
                return None
            raw = self.rfile.read(length)
            try:
                data = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                return None
            return data if isinstance(data, dict) else None

        # -- auth ---------------------------------------------------------

        def _agent(self) -> dict | None:
            auth = self.headers.get("Authorization") or ""
            key = None
            if auth.lower().startswith("bearer "):
                key = auth[7:].strip()
            if not key:
                key = self.headers.get("X-Agent-Key")
            if not key:
                return None
            return store.agent_by_key(key)

        def _session_token(self) -> str | None:
            raw = self.headers.get("Cookie")
            if not raw:
                return None
            jar = cookies.SimpleCookie()
            try:
                jar.load(raw)
            except cookies.CookieError:
                return None
            morsel = jar.get(SESSION_COOKIE)
            return morsel.value if morsel else None

        def _viewer_ok(self) -> bool:
            if not password:
                return True  # open mode (loud warning printed at startup)
            return sessions.valid(self._session_token())

        def _viewer_gate(self, path: str) -> bool:
            """True if the request may proceed; otherwise a reply was sent."""
            if self._viewer_ok():
                return True
            if path.startswith("/api/"):
                self._send_json(401, {"error": "login required"})
            else:
                self._send(302, b"", "text/html",
                           {"Location": "/login"})
            return False

        # -- GET ----------------------------------------------------------

        def do_GET(self):  # noqa: N802 — stdlib handler API
            parsed = urlparse(self.path)
            path = parsed.path
            if path == "/login":
                if self._viewer_ok():
                    self._send(302, b"", "text/html", {"Location": "/"})
                else:
                    self._send(200, _LOGIN_HTML.format(error="")
                               .encode("utf-8"), "text/html; charset=utf-8")
                return
            if path == "/logout":
                sessions.drop(self._session_token())
                self._send(302, b"", "text/html", {
                    "Location": "/login",
                    "Set-Cookie": f"{SESSION_COOKIE}=; HttpOnly; Path=/; "
                                  "Max-Age=0"})
                return
            if not self._viewer_gate(path):
                return
            query = parse_qs(parsed.query)
            if path == "/":
                self._send(200, dashboard_html, "text/html; charset=utf-8")
            elif path == "/api/sites":
                now = time.time()
                self._send_json(200, {
                    "generated_at": _stamp(now), "generated_ts": now,
                    "sites": store.sites_summary(now)})
            elif path == "/api/miners":
                site = (query.get("site") or [None])[0]
                now = time.time()
                self._send_json(200, {
                    "generated_at": _stamp(now), "generated_ts": now,
                    "miners": store.miners_by_site(site)})
            elif path == "/api/events":
                raw_n = (query.get("n") or ["50"])[0]
                try:
                    n = int(raw_n)
                except ValueError:
                    n = 50
                site = (query.get("site") or [None])[0]
                now = time.time()
                self._send_json(200, {
                    "generated_at": _stamp(now), "generated_ts": now,
                    "events": store.list_events(n, site)})
            else:
                self._send_json(404, {"error": "not found", "path": path})

        # -- POST -----------------------------------------------------------

        def do_POST(self):  # noqa: N802 — stdlib handler API
            parsed = urlparse(self.path)
            path = parsed.path
            if path == "/login":
                self._handle_login()
            elif path in ("/api/ingest", "/api/ingest/events"):
                self._handle_ingest(events_only=(path == "/api/ingest/events"))
            else:
                length = int(self.headers.get("Content-Length") or 0)
                if length:
                    self.rfile.read(length)  # drain unknown bodies
                self._send_json(404, {"error": "not found", "path": path})

        def _handle_login(self) -> None:
            if not password:
                self._send(302, b"", "text/html", {"Location": "/"})
                return
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                length = 0
            raw = self.rfile.read(length).decode("utf-8", "replace") \
                if length else ""
            form = parse_qs(raw)
            given = (form.get("password") or [""])[0]
            if hmac.compare_digest(given, password):
                token = sessions.create()
                self._send(302, b"", "text/html", {
                    "Location": "/",
                    "Set-Cookie": f"{SESSION_COOKIE}={token}; HttpOnly; "
                                  "Path=/; SameSite=Lax"})
            else:
                self._send(401, _LOGIN_HTML.format(error=_LOGIN_ERROR)
                           .encode("utf-8"), "text/html; charset=utf-8")

        def _handle_ingest(self, events_only: bool) -> None:
            agent = self._agent()
            if agent is None:
                self._send_json(401, {"error": "invalid agent key"})
                return
            body = self._read_json_body()
            if body is None:
                self._send_json(400, {"error": "invalid JSON body"})
                return
            now = time.time()
            if events_only:
                events = body.get("events")
                if not isinstance(events, list):
                    self._send_json(400, {"error": "events must be a list"})
                    return
                stored = store.add_events(agent["id"], agent["site"], events)
                store.touch_agent(agent["id"], now)
                self._send_json(200, {"ok": True, "stored": stored})
                return
            miners = body.get("miners")
            if not isinstance(miners, list):
                self._send_json(400, {"error": "miners must be a list"})
                return
            try:
                ts = float(body.get("ts") or now)
            except (TypeError, ValueError):
                ts = now
            interval = body.get("interval")
            store.add_snapshot(agent["id"], ts, miners)
            store.touch_agent(
                agent["id"], now,
                float(interval) if isinstance(interval, (int, float))
                else None)
            self._send_json(200, {"ok": True, "agent_id": agent["id"],
                                  "site": agent["site"],
                                  "miners": len(miners)})

    return Handler


def run_cloud_server(store: CloudStore, host: str = "127.0.0.1",
                     port: int = 8788, password: str | None = None) -> None:
    """Serve the cloud app until Ctrl+C."""
    dashboard_html = _load_dashboard_html()
    httpd = ThreadingHTTPServer((host, port),
                                make_handler(store, dashboard_html, password))
    httpd.daemon_threads = True
    print(f"BeeSky cloud: http://{host}:{port} — db {store.path}", flush=True)
    if password:
        print("Trang xem: ĐÃ đặt mật khẩu (BEESKY_CLOUD_PASSWORD).",
              flush=True)
    else:
        print("=" * 68, flush=True)
        print("!!! CẢNH BÁO: BEESKY_CLOUD_PASSWORD chưa được đặt — trang xem",
              flush=True)
        print("!!! ĐANG MỞ cho bất kỳ ai kết nối được tới cổng này. Chỉ dùng",
              flush=True)
        print("!!! để test local; khi deploy thật hãy đặt mật khẩu + HTTPS.",
              flush=True)
        print("=" * 68, flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nbeesky cloud stopped")
    finally:
        httpd.server_close()
        store.close()
