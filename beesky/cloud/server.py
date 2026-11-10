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

Remote actions (v0.6) ride the same two channels — the cloud never
reaches into a farm LAN, so commands travel down the agent's own
poll (see :mod:`beesky.core.actions` and docs/actions.md):

  GET  /api/agent/commands              claim this agent's pending
                                        commands (marks them ``sent``)
  POST /api/agent/commands/{id}/result  {"status": "done"|"failed",
                                        "result": "..."} — own
                                        commands only

Viewer (browser), behind a single admin password taken from the
``BEESKY_CLOUD_PASSWORD`` environment variable:

  GET  /              multi-site dashboard (beesky/cloud/dashboard.html)
  GET  /api/sites     per-site summaries computed from latest snapshots
  GET  /api/miners    latest records, ``?site=`` filters, each record
                      annotated with its ``site``
  GET  /api/events    newest-first stored events (``?n=``, ``?site=``)
  POST /api/commands  {"site", "ip", "type", "payload"} -> queue a
                      remote action for that site's agent
  GET  /api/commands  command history, newest first (``?n=``, ``?site=``)
  GET  /api/repairs   repair history (v0.8), newest first
                      (``?n=``, ``?site=``, ``?ip=``) — auto rows from
                      problem events + manual technician entries
  POST /api/repairs   {"site", "ip", "title", "detail", "cost_vnd",
                      "technician"} -> add a manual repair entry
  GET  /api/pool-config  pool API configs (v0.9), public view only —
                      header NAMES, never their values (``?site=``)
  POST /api/pool-config  {"site", "adapter", "url", "headers",
                      "json_path", "unit", "worker_filter",
                      "notify_gap_pct"} -> upsert one site's config;
                      omitting "headers" keeps the stored secrets
  GET  /api/pool      farm-vs-pool latest sample + 24 h series
                      (``?site=``; a background poller samples every
                      BEESKY_POOL_POLL_S seconds, default 300)
  GET  /api/energy    energy report (v0.9): per-day + per-miner kWh
                      with cost estimates (``?site=``, ``?days=``)
  GET|POST /api/settings  cloud settings — currently just
                      ``electricity_price_vnd_kwh`` (default 2000)
  GET  /api/history   farm hashrate history (v0.12): throttled
                      per-site samples, 1/min, kept 30 days
                      (``?site=``, ``?hours=`` default 24)
  GET  /api/agents    agent management (v0.13): registered agents
                      (id, site, created, last seen, online, revoked)
                      — never any key or hash material
  POST /api/agents    {"site"} -> mint an agent from the web (the
                      same store path as `cloud-add-agent`); the
                      response carries the raw key ONCE — the store
                      keeps only its SHA-256, as with the CLI
  POST /api/agents/revoke  {"id"} -> revoke an agent: its key stops
                      authenticating, so further ingests return 401
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
import os
import re
import secrets
import sys
import time
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from ..core.actions import COMMAND_TYPES
from .pools import DEFAULT_POLL_S, UNIT_TO_THS, PoolPoller
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
        server_version = "BeeSkyCloud/0.13"
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
            if path == "/api/agent/commands":
                self._handle_agent_claim(parse_qs(parsed.query))
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
            elif path == "/api/commands":
                raw_n = (query.get("n") or ["50"])[0]
                try:
                    n = int(raw_n)
                except ValueError:
                    n = 50
                site = (query.get("site") or [None])[0]
                now = time.time()
                self._send_json(200, {
                    "generated_at": _stamp(now), "generated_ts": now,
                    "commands": store.list_commands(site, n)})
            elif path == "/api/repairs":
                raw_n = (query.get("n") or ["50"])[0]
                try:
                    n = int(raw_n)
                except ValueError:
                    n = 50
                site = (query.get("site") or [None])[0]
                ip = (query.get("ip") or [None])[0]
                now = time.time()
                self._send_json(200, {
                    "generated_at": _stamp(now), "generated_ts": now,
                    "repairs": store.list_repairs(site, ip, n)})
            elif path == "/api/pool-config":
                site = (query.get("site") or [None])[0]
                configs = store.list_pool_configs()
                if site:
                    configs = [c for c in configs if c["site"] == site]
                now = time.time()
                self._send_json(200, {
                    "generated_at": _stamp(now), "generated_ts": now,
                    "configs": configs})
            elif path == "/api/pool":
                site = (query.get("site") or [None])[0]
                now = time.time()
                if site:
                    self._send_json(200, {
                        "generated_at": _stamp(now), "generated_ts": now,
                        "site": site,
                        "latest": store.latest_pool_sample(site),
                        "series_24h": store.pool_series(
                            site, now - 24 * 3600)})
                else:
                    pools = [{
                        "site": s,
                        "latest": store.latest_pool_sample(s),
                        "series_24h": store.pool_series(
                            s, now - 24 * 3600),
                    } for s in store.list_pool_config_sites()]
                    self._send_json(200, {
                        "generated_at": _stamp(now), "generated_ts": now,
                        "pools": pools})
            elif path == "/api/history":
                site = (query.get("site") or [None])[0]
                raw_hours = (query.get("hours") or ["24"])[0]
                try:
                    hours = float(raw_hours)
                except ValueError:
                    hours = 24.0
                hours = max(1.0, min(hours, 24 * 30.0))
                now = time.time()
                self._send_json(200, {
                    "generated_at": _stamp(now), "generated_ts": now,
                    "site": site,
                    "points": store.history_series(
                        site, now - hours * 3600)})
            elif path == "/api/energy":
                site = (query.get("site") or [None])[0]
                raw_days = (query.get("days") or ["7"])[0]
                try:
                    days = int(raw_days)
                except ValueError:
                    days = 7
                price = store.electricity_price_vnd()
                report = store.energy_report(site, days)
                report["electricity_price_vnd_kwh"] = price
                for entry in report["per_day"]:
                    entry["est_cost_vnd"] = round(entry["kwh"] * price)
                for entry in report["per_miner"]:
                    entry["est_cost_vnd"] = round(entry["kwh"] * price)
                report["today"]["est_cost_vnd"] = round(
                    report["today"]["kwh"] * price)
                report["total_est_cost_vnd"] = round(
                    report["total_kwh"] * price)
                now = time.time()
                self._send_json(200, {
                    "generated_at": _stamp(now), "generated_ts": now,
                    **report})
            elif path == "/api/settings":
                self._send_json(200, {
                    "electricity_price_vnd_kwh":
                        store.electricity_price_vnd()})
            elif path == "/api/agents":
                now = time.time()
                self._send_json(200, {
                    "generated_at": _stamp(now), "generated_ts": now,
                    "agents": store.agent_views(now)})
            else:
                self._send_json(404, {"error": "not found", "path": path})

        # -- POST -----------------------------------------------------------

        def do_POST(self):  # noqa: N802 — stdlib handler API
            parsed = urlparse(self.path)
            path = parsed.path
            result_match = re.fullmatch(r"/api/agent/commands/(\d+)/result",
                                        path)
            if path == "/login":
                self._handle_login()
            elif path in ("/api/ingest", "/api/ingest/events"):
                self._handle_ingest(events_only=(path == "/api/ingest/events"))
            elif result_match:
                self._handle_command_result(int(result_match.group(1)))
            elif path == "/api/commands":
                if self._viewer_gate(path):
                    self._handle_create_command()
            elif path == "/api/repairs":
                if self._viewer_gate(path):
                    self._handle_create_repair()
            elif path == "/api/pool-config":
                if self._viewer_gate(path):
                    self._handle_upsert_pool_config()
            elif path == "/api/settings":
                if self._viewer_gate(path):
                    self._handle_update_settings()
            elif path == "/api/agents":
                if self._viewer_gate(path):
                    self._handle_create_agent()
            elif path == "/api/agents/revoke":
                if self._viewer_gate(path):
                    self._handle_revoke_agent()
            else:
                length = int(self.headers.get("Content-Length") or 0)
                if length:
                    self.rfile.read(length)  # drain unknown bodies
                self._send_json(404, {"error": "not found", "path": path})

        # -- agent management (v0.13) -------------------------------------

        def _handle_create_agent(self) -> None:
            """Mint an agent from the web — the `cloud-add-agent` path.

            The raw key is generated here, handed to the store (which
            persists only its SHA-256) and returned in THIS response;
            it is never retrievable again, exactly like the CLI.
            """
            body = self._read_json_body()
            if body is None:
                self._send_json(400, {"error": "invalid JSON body"})
                return
            site = body.get("site")
            if not isinstance(site, str) or not site.strip():
                self._send_json(400, {"error": "site is required"})
                return
            site = site.strip()
            key = secrets.token_urlsafe(32)
            agent_id = store.create_agent(site, key)
            self._send_json(201, {"ok": True, "id": agent_id,
                                  "site": site, "key": key})

        def _handle_revoke_agent(self) -> None:
            body = self._read_json_body()
            if body is None:
                self._send_json(400, {"error": "invalid JSON body"})
                return
            agent_id = body.get("id")
            if isinstance(agent_id, bool) \
                    or not isinstance(agent_id, int):
                self._send_json(400, {"error": "id must be an integer"})
                return
            if not store.revoke_agent(agent_id):
                self._send_json(404, {
                    "error": f"no agent with id {agent_id}"})
                return
            self._send_json(200, {"ok": True, "id": agent_id,
                                  "revoked": True})

        # -- commands (v0.6 remote actions) ------------------------------

        def _handle_create_command(self) -> None:
            body = self._read_json_body()
            if body is None:
                self._send_json(400, {"error": "invalid JSON body"})
                return
            site = body.get("site")
            ip = body.get("ip")
            command_type = body.get("type")
            payload = body.get("payload") or {}
            if not isinstance(site, str) or not site \
                    or not isinstance(ip, str) or not ip:
                self._send_json(400, {"error": "site and ip are required"})
                return
            if command_type not in COMMAND_TYPES:
                self._send_json(400, {
                    "error": f"unknown command type {command_type!r}",
                    "types": list(COMMAND_TYPES)})
                return
            if not isinstance(payload, dict):
                self._send_json(400, {"error": "payload must be an object"})
                return
            agent = store.agent_by_site(site)
            if agent is None:
                self._send_json(404, {"error": f"no agent for site {site!r}"})
                return
            command = store.create_command(agent["id"], site, ip,
                                           command_type, payload)
            self._send_json(201, {"ok": True, "command": command})

        # -- pool comparison + settings (v0.9) ---------------------------

        def _handle_upsert_pool_config(self) -> None:
            body = self._read_json_body()
            if body is None:
                self._send_json(400, {"error": "invalid JSON body"})
                return
            site = body.get("site")
            if not isinstance(site, str) or not site:
                self._send_json(400, {"error": "site is required"})
                return
            adapter = body.get("adapter") or "generic"
            if adapter not in ("generic", "emcd"):
                self._send_json(400, {
                    "error": "adapter must be 'generic' or 'emcd'"})
                return
            unit = body.get("unit") or "TH/s"
            if unit not in UNIT_TO_THS:
                self._send_json(400, {
                    "error": f"unit must be one of {sorted(UNIT_TO_THS)}"})
                return
            headers = body.get("headers", None)
            if headers is not None and not isinstance(headers, dict):
                self._send_json(400, {
                    "error": "headers must be an object or omitted "
                             "(omitted keeps the stored secrets)"})
                return
            gap = body.get("notify_gap_pct", 10.0)
            if isinstance(gap, bool) \
                    or not isinstance(gap, (int, float)) or gap < 0:
                self._send_json(400, {
                    "error": "notify_gap_pct must be a non-negative "
                             "number"})
                return
            worker_filter = body.get("worker_filter")
            view = store.upsert_pool_config(
                site,
                adapter=str(adapter),
                url=str(body.get("url") or ""),
                headers=headers,
                json_path=str(body.get("json_path") or ""),
                unit=str(unit),
                worker_filter=(None if worker_filter is None
                               else str(worker_filter)),
                notify_gap_pct=float(gap))
            self._send_json(201, {"ok": True, "config": view})

        def _handle_update_settings(self) -> None:
            body = self._read_json_body()
            if body is None:
                self._send_json(400, {"error": "invalid JSON body"})
                return
            price = body.get("electricity_price_vnd_kwh")
            if price is not None:
                if isinstance(price, bool) \
                        or not isinstance(price, (int, float)) \
                        or price < 0:
                    self._send_json(400, {
                        "error": "electricity_price_vnd_kwh must be a "
                                 "non-negative number"})
                    return
                store.set_setting("electricity_price_vnd_kwh",
                                  repr(float(price)))
            self._send_json(200, {
                "ok": True,
                "electricity_price_vnd_kwh":
                    store.electricity_price_vnd()})

        # -- repairs (v0.8 repair history) -------------------------------

        def _handle_create_repair(self) -> None:
            body = self._read_json_body()
            if body is None:
                self._send_json(400, {"error": "invalid JSON body"})
                return
            site = body.get("site")
            ip = body.get("ip")
            title = body.get("title")
            if not isinstance(site, str) or not site \
                    or not isinstance(ip, str) or not ip \
                    or not isinstance(title, str) or not title.strip():
                self._send_json(400, {
                    "error": "site, ip and title are required"})
                return
            cost = body.get("cost_vnd")
            if cost is not None:
                if isinstance(cost, bool) \
                        or not isinstance(cost, (int, float)):
                    self._send_json(400, {
                        "error": "cost_vnd must be a number or null"})
                    return
                cost = int(cost)
            detail = body.get("detail")
            technician = body.get("technician")
            mac_serial = body.get("mac_or_serial")
            repair = store.add_repair(
                site, ip, title.strip(),
                None if detail is None else str(detail),
                cost,
                None if technician is None else str(technician),
                mac_or_serial=(None if mac_serial is None
                               else str(mac_serial)))
            self._send_json(201, {"ok": True, "repair": repair})

        def _handle_agent_claim(self, query: dict) -> None:
            agent = self._agent()
            if agent is None:
                self._send_json(401, {"error": "invalid agent key"})
                return
            raw_limit = (query.get("limit") or ["20"])[0]
            try:
                limit = int(raw_limit)
            except ValueError:
                limit = 20
            commands = store.claim_pending(agent["id"], limit)
            store.touch_agent(agent["id"], time.time())
            self._send_json(200, {"ok": True, "commands": commands})

        def _handle_command_result(self, command_id: int) -> None:
            agent = self._agent()
            if agent is None:
                self._send_json(401, {"error": "invalid agent key"})
                return
            existing = store.get_command(command_id)
            if existing is None:
                self._send_json(404, {"error": "no such command"})
                return
            if existing["agent_id"] != agent["id"]:
                self._send_json(403, {
                    "error": "command belongs to another agent"})
                return
            body = self._read_json_body()
            if body is None:
                self._send_json(400, {"error": "invalid JSON body"})
                return
            status = body.get("status")
            if status not in ("done", "failed"):
                self._send_json(400, {
                    "error": "status must be 'done' or 'failed'"})
                return
            result = body.get("result")
            updated = store.finish_command(
                command_id, agent["id"], status,
                "" if result is None else str(result))
            if updated is None:
                self._send_json(409, {
                    "error": "command already finished"})
                return
            self._send_json(200, {"ok": True, "command": updated})

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


def _pool_poll_interval() -> float:
    """Pool poll interval: BEESKY_POOL_POLL_S env, default 300 s."""
    raw = os.environ.get("BEESKY_POOL_POLL_S")
    if raw:
        try:
            value = float(raw)
            if value > 0:
                return value
        except ValueError:
            pass
    return DEFAULT_POLL_S


def run_cloud_server(store: CloudStore, host: str = "127.0.0.1",
                     port: int = 8788, password: str | None = None) -> None:
    """Serve the cloud app until Ctrl+C."""
    dashboard_html = _load_dashboard_html()
    httpd = ThreadingHTTPServer((host, port),
                                make_handler(store, dashboard_html, password))
    httpd.daemon_threads = True
    poller = PoolPoller(store, _pool_poll_interval())
    poller.start()
    print(f"Pool poller: mỗi {poller.interval_s:g} giây cho các trại "
          "đã cấu hình pool (BEESKY_POOL_POLL_S).", flush=True)
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
        poller.stop()
        httpd.server_close()
        store.close()
