"""Cloud store — SQLite persistence for agents, snapshots and events.

The cloud side of BeeSky (v0.5) is deliberately small: farm *agents*
(:mod:`beesky.agent`) dial out and POST their latest scan snapshot plus
any events; this module keeps them in one stdlib ``sqlite3`` database.

Tables:

  agents     one row per farm agent: site name, SHA-256 hash of its
             agent key (the key itself is never stored), timestamps.
  snapshots  scan snapshots per agent — only the latest is served, but
             a short history (100 per agent) is kept for debugging.
  events     fleet events pushed by agents, newest first; pruned to
             the most recent 5000 rows.
  commands   remote actions (v0.6) issued by the viewer for the agent
             of one site to execute on its LAN: pending -> sent
             (claimed by the agent) -> done | failed, with the
             executor's result text.

All access is serialised through one lock, so the store is safe to
share between the threads of a ``ThreadingHTTPServer``.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import time

SNAPSHOT_HISTORY = 100
EVENT_HISTORY = 5000
COMMAND_HISTORY = 5000


def hash_key(key: str) -> str:
    """SHA-256 hex of an agent key — the only form ever persisted."""
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def _stamp(ts: float | None) -> str | None:
    if ts is None:
        return None
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))


class CloudStore:
    """Thread-safe SQLite store for the cloud server."""

    def __init__(self, path: str):
        self.path = path
        self._lock = threading.Lock()
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        with self._lock, self._db:
            self._db.executescript(
                """
                CREATE TABLE IF NOT EXISTS agents (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    site        TEXT NOT NULL,
                    key_hash    TEXT NOT NULL UNIQUE,
                    created_at  REAL NOT NULL,
                    last_seen_at REAL,
                    interval_s  REAL
                );
                CREATE TABLE IF NOT EXISTS snapshots (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id    INTEGER NOT NULL REFERENCES agents(id),
                    ts          REAL NOT NULL,
                    miners_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_snapshots_agent
                    ON snapshots(agent_id, id);
                CREATE TABLE IF NOT EXISTS events (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id  INTEGER NOT NULL REFERENCES agents(id),
                    site      TEXT NOT NULL,
                    ts        REAL NOT NULL,
                    type      TEXT NOT NULL,
                    severity  TEXT NOT NULL,
                    ip        TEXT,
                    model     TEXT,
                    detail    TEXT,
                    data_json TEXT NOT NULL DEFAULT '{}'
                );
                CREATE INDEX IF NOT EXISTS idx_events_id ON events(id);
                CREATE TABLE IF NOT EXISTS commands (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id    INTEGER NOT NULL REFERENCES agents(id),
                    site        TEXT NOT NULL,
                    ip          TEXT NOT NULL,
                    type        TEXT NOT NULL,
                    payload_json TEXT NOT NULL DEFAULT '{}',
                    status      TEXT NOT NULL DEFAULT 'pending',
                    result_text TEXT,
                    created_at  REAL NOT NULL,
                    claimed_at  REAL,
                    finished_at REAL
                );
                CREATE INDEX IF NOT EXISTS idx_commands_agent
                    ON commands(agent_id, status, id);
                """
            )

    def close(self) -> None:
        with self._lock:
            self._db.close()

    # ------------------------------------------------------------------
    # agents
    # ------------------------------------------------------------------

    def create_agent(self, site: str, key: str) -> int:
        """Register an agent for *site*; returns the new agent id."""
        with self._lock, self._db:
            cur = self._db.execute(
                "INSERT INTO agents (site, key_hash, created_at) "
                "VALUES (?, ?, ?)",
                (site, hash_key(key), time.time()))
            return int(cur.lastrowid)

    def agent_by_key(self, key: str) -> dict | None:
        """Look an agent up by its plaintext key (hashed for the query)."""
        with self._lock:
            row = self._db.execute(
                "SELECT * FROM agents WHERE key_hash = ?",
                (hash_key(key),)).fetchone()
        return dict(row) if row else None

    def list_agents(self) -> list[dict]:
        with self._lock:
            rows = self._db.execute(
                "SELECT * FROM agents ORDER BY id").fetchall()
        return [dict(r) for r in rows]

    def agent_by_site(self, site: str) -> dict | None:
        """The (first) agent registered for *site*, or None."""
        with self._lock:
            row = self._db.execute(
                "SELECT * FROM agents WHERE site = ? ORDER BY id LIMIT 1",
                (site,)).fetchone()
        return dict(row) if row else None

    def get_agent(self, agent_id: int) -> dict | None:
        with self._lock:
            row = self._db.execute(
                "SELECT * FROM agents WHERE id = ?",
                (agent_id,)).fetchone()
        return dict(row) if row else None

    def touch_agent(self, agent_id: int, ts: float,
                    interval_s: float | None = None) -> None:
        with self._lock, self._db:
            if interval_s:
                self._db.execute(
                    "UPDATE agents SET last_seen_at = ?, interval_s = ? "
                    "WHERE id = ?", (ts, float(interval_s), agent_id))
            else:
                self._db.execute(
                    "UPDATE agents SET last_seen_at = ? WHERE id = ?",
                    (ts, agent_id))

    # ------------------------------------------------------------------
    # snapshots
    # ------------------------------------------------------------------

    def add_snapshot(self, agent_id: int, ts: float,
                     miners: list[dict]) -> None:
        with self._lock, self._db:
            self._db.execute(
                "INSERT INTO snapshots (agent_id, ts, miners_json) "
                "VALUES (?, ?, ?)",
                (agent_id, float(ts),
                 json.dumps(miners, ensure_ascii=False)))
            self._db.execute(
                "DELETE FROM snapshots WHERE agent_id = ? AND id NOT IN "
                "(SELECT id FROM snapshots WHERE agent_id = ? "
                " ORDER BY id DESC LIMIT ?)",
                (agent_id, agent_id, SNAPSHOT_HISTORY))

    def latest_snapshot(self, agent_id: int) -> tuple[float, list[dict]] | None:
        """(ts, miners) of the newest snapshot for *agent_id*, or None."""
        with self._lock:
            row = self._db.execute(
                "SELECT ts, miners_json FROM snapshots WHERE agent_id = ? "
                "ORDER BY id DESC LIMIT 1", (agent_id,)).fetchone()
        if row is None:
            return None
        return float(row["ts"]), json.loads(row["miners_json"])

    # ------------------------------------------------------------------
    # events
    # ------------------------------------------------------------------

    def add_events(self, agent_id: int, site: str,
                   events: list[dict]) -> int:
        """Store event dicts (EventEngine shape); returns how many."""
        rows = []
        for ev in events:
            try:
                ts = float(ev.get("ts") or time.time())
            except (TypeError, ValueError):
                ts = time.time()
            rows.append((
                agent_id, site, ts,
                str(ev.get("type") or "UNKNOWN"),
                str(ev.get("severity") or "info"),
                ev.get("ip"), ev.get("model"), ev.get("detail"),
                json.dumps(ev.get("data") or {}, ensure_ascii=False)))
        if not rows:
            return 0
        with self._lock, self._db:
            self._db.executemany(
                "INSERT INTO events (agent_id, site, ts, type, severity, "
                "ip, model, detail, data_json) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)
            self._db.execute(
                "DELETE FROM events WHERE id NOT IN "
                "(SELECT id FROM events ORDER BY id DESC LIMIT ?)",
                (EVENT_HISTORY,))
        return len(rows)

    def list_events(self, n: int = 50, site: str | None = None) -> list[dict]:
        """Newest-first events, optionally filtered to one site."""
        n = max(1, min(int(n), EVENT_HISTORY))
        query = "SELECT * FROM events"
        params: list = []
        if site:
            query += " WHERE site = ?"
            params.append(site)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(n)
        with self._lock:
            rows = self._db.execute(query, params).fetchall()
        events = []
        for row in rows:
            ev = dict(row)
            try:
                data = json.loads(ev.pop("data_json") or "{}")
            except json.JSONDecodeError:
                data = {}
            events.append({
                "ts": ev["ts"],
                "time": _stamp(ev["ts"]),
                "site": ev["site"],
                "agent_id": ev["agent_id"],
                "ip": ev["ip"],
                "model": ev["model"],
                "type": ev["type"],
                "severity": ev["severity"],
                "detail": ev["detail"],
                "data": data,
            })
        return events

    # ------------------------------------------------------------------
    # commands — remote actions (v0.6)
    # ------------------------------------------------------------------

    @staticmethod
    def _command_view(row: sqlite3.Row) -> dict:
        try:
            payload = json.loads(row["payload_json"] or "{}")
        except json.JSONDecodeError:
            payload = {}
        return {
            "id": row["id"],
            "agent_id": row["agent_id"],
            "site": row["site"],
            "ip": row["ip"],
            "type": row["type"],
            "payload": payload if isinstance(payload, dict) else {},
            "status": row["status"],
            "result": row["result_text"],
            "created_at": _stamp(row["created_at"]),
            "created_ts": row["created_at"],
            "claimed_at": _stamp(row["claimed_at"]),
            "finished_at": _stamp(row["finished_at"]),
        }

    def create_command(self, agent_id: int, site: str, ip: str,
                       command_type: str, payload: dict | None) -> dict:
        """Queue a command for one agent; returns its public view."""
        with self._lock, self._db:
            cur = self._db.execute(
                "INSERT INTO commands (agent_id, site, ip, type, "
                "payload_json, status, created_at) "
                "VALUES (?, ?, ?, ?, ?, 'pending', ?)",
                (agent_id, site, ip, command_type,
                 json.dumps(payload or {}, ensure_ascii=False),
                 time.time()))
            cmd_id = int(cur.lastrowid)
            self._db.execute(
                "DELETE FROM commands WHERE id NOT IN "
                "(SELECT id FROM commands ORDER BY id DESC LIMIT ?)",
                (COMMAND_HISTORY,))
            row = self._db.execute(
                "SELECT * FROM commands WHERE id = ?", (cmd_id,)).fetchone()
        return self._command_view(row)

    def claim_pending(self, agent_id: int, limit: int = 20) -> list[dict]:
        """Atomically claim this agent's pending commands (oldest first).

        Claimed rows flip to status ``sent`` with a claimed_at stamp in
        the same transaction, so two concurrent polls never hand the
        same command out twice.
        """
        limit = max(1, min(int(limit), 100))
        with self._lock, self._db:
            rows = self._db.execute(
                "SELECT * FROM commands WHERE agent_id = ? "
                "AND status = 'pending' ORDER BY id LIMIT ?",
                (agent_id, limit)).fetchall()
            now = time.time()
            views = []
            for row in rows:
                self._db.execute(
                    "UPDATE commands SET status = 'sent', claimed_at = ? "
                    "WHERE id = ?", (now, row["id"]))
                fresh = self._db.execute(
                    "SELECT * FROM commands WHERE id = ?",
                    (row["id"],)).fetchone()
                views.append(self._command_view(fresh))
        return views

    def finish_command(self, command_id: int, agent_id: int, status: str,
                       result_text: str) -> dict | None:
        """Mark a claimed command done|failed — owner agent only.

        Returns the updated view, or None when the command does not
        exist, belongs to another agent, or is already finished.
        """
        if status not in ("done", "failed"):
            raise ValueError(f"bad finish status {status!r}")
        with self._lock, self._db:
            row = self._db.execute(
                "SELECT * FROM commands WHERE id = ?",
                (command_id,)).fetchone()
            if row is None or row["agent_id"] != agent_id \
                    or row["status"] in ("done", "failed"):
                return None
            self._db.execute(
                "UPDATE commands SET status = ?, result_text = ?, "
                "finished_at = ? WHERE id = ?",
                (status, result_text, time.time(), command_id))
            fresh = self._db.execute(
                "SELECT * FROM commands WHERE id = ?",
                (command_id,)).fetchone()
        return self._command_view(fresh)

    def get_command(self, command_id: int) -> dict | None:
        with self._lock:
            row = self._db.execute(
                "SELECT * FROM commands WHERE id = ?",
                (command_id,)).fetchone()
        return self._command_view(row) if row else None

    def list_commands(self, site: str | None = None,
                      limit: int = 50) -> list[dict]:
        """Newest-first command history, optionally filtered by site."""
        limit = max(1, min(int(limit), COMMAND_HISTORY))
        query = "SELECT * FROM commands"
        params: list = []
        if site:
            query += " WHERE site = ?"
            params.append(site)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        with self._lock:
            rows = self._db.execute(query, params).fetchall()
        return [self._command_view(r) for r in rows]

    # ------------------------------------------------------------------
    # viewer summaries
    # ------------------------------------------------------------------

    def sites_summary(self, now: float | None = None) -> list[dict]:
        """One summary dict per registered agent/site for /api/sites."""
        now = time.time() if now is None else float(now)
        sites = []
        for agent in self.list_agents():
            snap = self.latest_snapshot(agent["id"])
            miners = snap[1] if snap else []
            ths_values = [m["ths"] for m in miners
                          if m.get("ths") is not None]
            temp_values = [m["max_temp_c"] for m in miners
                           if m.get("max_temp_c") is not None]
            interval = agent.get("interval_s") or 30.0
            last_seen = agent.get("last_seen_at")
            online = (last_seen is not None
                      and now - last_seen <= 3.0 * float(interval))
            sites.append({
                "site": agent["site"],
                "agent_id": agent["id"],
                "created_at": _stamp(agent.get("created_at")),
                "last_seen_at": last_seen,
                "last_seen": _stamp(last_seen),
                "interval_s": interval,
                "online": online,
                "snapshot_ts": snap[0] if snap else None,
                "miner_count": len(miners),
                "ok_count": sum(1 for m in miners
                                if m.get("status") == "OK"),
                "problem_count": sum(1 for m in miners
                                     if m.get("status") != "OK"),
                "total_ths": round(sum(ths_values), 2),
                "max_temp": (max(temp_values) if temp_values else None),
            })
        return sites

    def miners_by_site(self, site: str | None = None) -> list[dict]:
        """Latest records across agents, each annotated with its site."""
        merged = []
        for agent in self.list_agents():
            if site and agent["site"] != site:
                continue
            snap = self.latest_snapshot(agent["id"])
            if not snap:
                continue
            for record in snap[1]:
                merged.append({**record, "site": agent["site"]})
        merged.sort(key=lambda r: (r["site"], r.get("ip") or ""))
        return merged
