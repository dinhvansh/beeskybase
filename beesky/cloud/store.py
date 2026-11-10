"""Cloud store — SQLite persistence for agents, snapshots and events.

The cloud side of BeeSky (v0.5) is deliberately small: farm *agents*
(:mod:`beesky.agent`) dial out and POST their latest scan snapshot plus
any events; this module keeps them in one stdlib ``sqlite3`` database.

Tables:

  agents     one row per farm agent: site name, SHA-256 hash of its
             agent key (the key itself is never stored), timestamps,
             and a ``revoked`` flag (v0.13): a revoked agent's key no
             longer authenticates, so its ingests are rejected. Agents
             are minted either by the ``cloud-add-agent`` CLI or from
             the dashboard (Cài đặt -> Agent & trại); both paths share
             :meth:`CloudStore.create_agent`.
  snapshots  scan snapshots per agent — only the latest is served, but
             a short history (100 per agent) is kept for debugging.
  events     fleet events pushed by agents, newest first; pruned to
             the most recent 5000 rows.
  commands   remote actions (v0.6) issued by the viewer for the agent
             of one site to execute on its LAN: pending -> sent
             (claimed by the agent) -> done | failed, with the
             executor's result text.
  repairs    repair history (v0.8) per miner: ``auto_event`` rows are
             derived from problem events as they are ingested (see
             :meth:`CloudStore.add_events`), ``manual`` rows are
             entered by a technician through the viewer API. Records
             carry no MAC/serial, so history is keyed by site + IP;
             ``mac_or_serial`` is kept for the day a source provides it.
  pool_configs / pool_samples
             farm-vs-pool comparison (v0.9): per-site pool API config
             (header values are secrets — the store hands them only to
             the poller, never to viewer views) and the poller's
             samples: pool-side TH/s next to the farm-side snapshot sum
             and the gap between them.
  energy_hours
             energy accounting (v0.9): per (site, miner, hour) kWh
             integrated from record ``power_w`` across consecutive
             snapshots inside :meth:`CloudStore.add_snapshot`.
  settings   tiny key/value table (electricity price for estimates).
  history_samples
             farm hashrate history (v0.12): one throttled sample per
             site per minute taken inside :meth:`CloudStore.add_snapshot`
             (site totals: TH/s, miner counts, max temp), kept 30 days;
             feeds the overview chart via ``GET /api/history``.

All access is serialised through one lock, so the store is safe to
share between the threads of a ``ThreadingHTTPServer``.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import time

from ..core import report as _core_report

SNAPSHOT_HISTORY = 100
EVENT_HISTORY = 5000
COMMAND_HISTORY = 5000
REPAIR_HISTORY = 10000
POOL_SAMPLE_HISTORY = 2000

# History sampling (v0.12): at most one history_samples row per site
# per HISTORY_SAMPLE_INTERVAL_S, rows kept for HISTORY_RETENTION_S.
HISTORY_SAMPLE_INTERVAL_S = 60.0
HISTORY_RETENTION_S = 30 * 86400.0

# Event types that also become auto repair-history rows (v0.8): the
# problem events a technician would want on a miner's timeline. The
# title of an auto row is the event type, and identical (site, ip,
# title) auto rows are written at most once per AUTO_REPAIR_DEDUPE_S —
# the event engine already latches, this is a second spam guard.
AUTO_REPAIR_TYPES = ("CHIPS_LOST", "CHAIN_DOWN", "OVER_TEMP", "OFFLINE")
AUTO_REPAIR_DEDUPE_S = 3600.0


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
                    interval_s  REAL,
                    revoked     INTEGER NOT NULL DEFAULT 0
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
                CREATE TABLE IF NOT EXISTS repairs (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id      INTEGER REFERENCES agents(id),
                    site          TEXT NOT NULL,
                    ip            TEXT NOT NULL,
                    mac_or_serial TEXT,
                    created_at    REAL NOT NULL,
                    kind          TEXT NOT NULL DEFAULT 'manual',
                    title         TEXT NOT NULL,
                    detail        TEXT,
                    cost_vnd      INTEGER,
                    technician    TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_repairs_miner
                    ON repairs(site, ip, id);
                CREATE TABLE IF NOT EXISTS pool_configs (
                    site           TEXT PRIMARY KEY,
                    adapter        TEXT NOT NULL DEFAULT 'generic',
                    url            TEXT NOT NULL DEFAULT '',
                    headers_json   TEXT NOT NULL DEFAULT '{}',
                    json_path      TEXT NOT NULL DEFAULT '',
                    unit           TEXT NOT NULL DEFAULT 'TH/s',
                    worker_filter  TEXT,
                    notify_gap_pct REAL NOT NULL DEFAULT 10.0
                );
                CREATE TABLE IF NOT EXISTS pool_samples (
                    id       INTEGER PRIMARY KEY AUTOINCREMENT,
                    site     TEXT NOT NULL,
                    ts       REAL NOT NULL,
                    pool_ths REAL NOT NULL,
                    farm_ths REAL NOT NULL,
                    gap_pct  REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_pool_samples_site
                    ON pool_samples(site, id);
                CREATE TABLE IF NOT EXISTS energy_hours (
                    site       TEXT NOT NULL,
                    ip         TEXT NOT NULL,
                    hour_bucket REAL NOT NULL,
                    day        TEXT NOT NULL,
                    kwh        REAL NOT NULL DEFAULT 0,
                    samples    INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (site, ip, hour_bucket)
                );
                CREATE INDEX IF NOT EXISTS idx_energy_day
                    ON energy_hours(day);
                CREATE TABLE IF NOT EXISTS settings (
                    key   TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS history_samples (
                    site           TEXT NOT NULL,
                    ts             REAL NOT NULL,
                    total_ths      REAL NOT NULL DEFAULT 0,
                    miners_total   INTEGER NOT NULL DEFAULT 0,
                    miners_problem INTEGER NOT NULL DEFAULT 0,
                    max_temp_c     REAL
                );
                CREATE INDEX IF NOT EXISTS idx_history_site
                    ON history_samples(site, ts);
                """
            )
            # Migration for databases created before v0.13: the
            # CREATE TABLE above is a no-op there, so add the
            # agents.revoked column explicitly when it is missing.
            agent_cols = [r[1] for r in
                          self._db.execute("PRAGMA table_info(agents)")]
            if agent_cols and "revoked" not in agent_cols:
                with self._db:
                    self._db.execute(
                        "ALTER TABLE agents ADD COLUMN revoked "
                        "INTEGER NOT NULL DEFAULT 0")

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
        """Look an agent up by its plaintext key (hashed for the query).

        Revoked agents (v0.13) do not authenticate: this is the single
        lookup behind every agent-facing endpoint (ingest, command
        claim/result), so filtering here invalidates the key for all
        of them at once.
        """
        with self._lock:
            row = self._db.execute(
                "SELECT * FROM agents WHERE key_hash = ? AND revoked = 0",
                (hash_key(key),)).fetchone()
        return dict(row) if row else None

    def revoke_agent(self, agent_id: int) -> bool:
        """Revoke an agent (v0.13): its key stops authenticating.

        The row (and its snapshots/events history) is kept so the
        dashboard can show the agent as revoked; only the credential
        dies. Returns False when no such agent exists.
        """
        with self._lock, self._db:
            if self._db.execute(
                    "SELECT 1 FROM agents WHERE id = ?",
                    (agent_id,)).fetchone() is None:
                return False
            self._db.execute(
                "UPDATE agents SET revoked = 1 WHERE id = ?",
                (agent_id,))
        return True

    def agent_views(self, now: float | None = None) -> list[dict]:
        """Public agent list for the viewer API — no key material.

        Neither the plaintext key (never stored) nor its SHA-256 hash
        leaves the store through this view. ``online`` mirrors the
        sites_summary rule (seen within 3x the agent's interval);
        revoked agents are always offline.
        """
        now = time.time() if now is None else float(now)
        views = []
        for agent in self.list_agents():
            interval = agent.get("interval_s") or 30.0
            last_seen = agent.get("last_seen_at")
            revoked = bool(agent.get("revoked"))
            online = (not revoked and last_seen is not None
                      and now - float(last_seen) <= 3.0 * float(interval))
            views.append({
                "id": agent["id"],
                "site": agent["site"],
                "created_at": _stamp(agent.get("created_at")),
                "created_ts": agent.get("created_at"),
                "last_seen_at": last_seen,
                "last_seen": _stamp(last_seen),
                "online": online,
                "revoked": revoked,
            })
        return views

    def list_agents(self) -> list[dict]:
        with self._lock:
            rows = self._db.execute(
                "SELECT * FROM agents ORDER BY id").fetchall()
        return [dict(r) for r in rows]

    def agent_by_site(self, site: str) -> dict | None:
        """The (first) live agent registered for *site*, or None.

        Revoked agents (v0.13) are skipped, so a re-created agent for
        the same site takes over command routing / pool accounting.
        """
        with self._lock:
            row = self._db.execute(
                "SELECT * FROM agents WHERE site = ? AND revoked = 0 "
                "ORDER BY id LIMIT 1",
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
        ts = float(ts)
        with self._lock, self._db:
            self._integrate_energy(agent_id, ts, miners)
            self._db.execute(
                "INSERT INTO snapshots (agent_id, ts, miners_json) "
                "VALUES (?, ?, ?)",
                (agent_id, ts,
                 json.dumps(miners, ensure_ascii=False)))
            self._db.execute(
                "DELETE FROM snapshots WHERE agent_id = ? AND id NOT IN "
                "(SELECT id FROM snapshots WHERE agent_id = ? "
                " ORDER BY id DESC LIMIT ?)",
                (agent_id, agent_id, SNAPSHOT_HISTORY))
            self._sample_history(agent_id, ts, miners)

    def _sample_history(self, agent_id: int, ts: float,
                        miners: list[dict]) -> None:
        """Append one throttled history sample — caller holds txn.

        At most one row per site per HISTORY_SAMPLE_INTERVAL_S: agents
        typically push every few seconds, and a minute of resolution
        is plenty for a 24 h farm chart. Totals mirror sites_summary:
        summed TH/s equivalents over records that carry one (v0.20 —
        sol-rate records excluded), problem = status not OK. Rows
        older than HISTORY_RETENTION_S are pruned here, on the write
        path, so no background job is needed.
        """
        agent = self._db.execute(
            "SELECT site FROM agents WHERE id = ?",
            (agent_id,)).fetchone()
        if agent is None:
            return
        site = agent["site"]
        last = self._db.execute(
            "SELECT MAX(ts) FROM history_samples WHERE site = ?",
            (site,)).fetchone()[0]
        if last is not None \
                and ts - float(last) < HISTORY_SAMPLE_INTERVAL_S:
            return
        # v0.20: the history total is the H/s-family TH/s sum only —
        # a sol-rate record (Equihash) has no TH/s equivalent and no
        # longer pollutes the series with its raw sol number.
        ths_values = [v for m in miners if isinstance(m, dict)
                      for v in [_core_report.ths_equivalent(m)]
                      if v is not None]
        temp_values = [m["max_temp_c"] for m in miners
                       if isinstance(m, dict)
                       and m.get("max_temp_c") is not None]
        self._db.execute(
            "INSERT INTO history_samples (site, ts, total_ths, "
            "miners_total, miners_problem, max_temp_c) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (site, ts, round(sum(ths_values), 4), len(miners),
             sum(1 for m in miners
                 if isinstance(m, dict) and m.get("status") != "OK"),
             max(temp_values) if temp_values else None))
        self._db.execute(
            "DELETE FROM history_samples WHERE ts < ?",
            (ts - HISTORY_RETENTION_S,))

    def history_series(self, site: str | None = None,
                       since_ts: float = 0.0) -> list[dict]:
        """History samples since *since_ts*, oldest first.

        With *site* empty/None every site's rows come back; the
        dashboard sums same-minute buckets client-side for the
        all-sites chart.
        """
        query = "SELECT * FROM history_samples WHERE ts >= ?"
        params: list = [float(since_ts)]
        if site:
            query += " AND site = ?"
            params.append(site)
        query += " ORDER BY ts, site"
        with self._lock:
            rows = self._db.execute(query, params).fetchall()
        return [{
            "site": r["site"],
            "ts": r["ts"],
            "time": _stamp(r["ts"]),
            "total_ths": r["total_ths"],
            "miners_total": r["miners_total"],
            "miners_problem": r["miners_problem"],
            "max_temp_c": r["max_temp_c"],
        } for r in rows]

    def _integrate_energy(self, agent_id: int, ts: float,
                          miners: list[dict]) -> None:
        """Accumulate kWh from ``power_w`` — caller holds lock + txn.

        For each miner present in BOTH the previous snapshot and this
        one, energy = power_w × dt, integrated into the hour bucket of
        *ts*. dt is capped at 3× the agent's scan interval so a long
        cloud/agent outage does not fabricate hours of phantom usage
        at full power, and a miner missing from the previous snapshot
        earns nothing yet (its baseline is being established).
        """
        prev = self._db.execute(
            "SELECT ts, miners_json FROM snapshots WHERE agent_id = ? "
            "ORDER BY id DESC LIMIT 1", (agent_id,)).fetchone()
        if prev is None:
            return
        dt = ts - float(prev["ts"])
        if dt <= 0:
            return
        agent = self._db.execute(
            "SELECT site, interval_s FROM agents WHERE id = ?",
            (agent_id,)).fetchone()
        if agent is None:
            return
        interval = float(agent["interval_s"] or 30.0)
        dt = min(dt, 3.0 * interval)
        try:
            prev_miners = json.loads(prev["miners_json"])
        except json.JSONDecodeError:
            return
        prev_ips = {m.get("ip") for m in prev_miners
                    if isinstance(m, dict)}
        bucket = float(int(ts // 3600) * 3600)
        day = time.strftime("%Y-%m-%d", time.localtime(ts))
        for miner in miners:
            if not isinstance(miner, dict):
                continue
            power = miner.get("power_w")
            ip = miner.get("ip")
            if power is None or not ip or ip not in prev_ips:
                continue
            try:
                kwh = float(power) * dt / 3.6e6
            except (TypeError, ValueError):
                continue
            if kwh <= 0:
                continue
            self._db.execute(
                "INSERT INTO energy_hours (site, ip, hour_bucket, day, "
                "kwh, samples) VALUES (?, ?, ?, ?, ?, 1) "
                "ON CONFLICT(site, ip, hour_bucket) DO UPDATE SET "
                "kwh = kwh + excluded.kwh, samples = samples + 1",
                (agent["site"], ip, bucket, day, kwh))

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
        """Store event dicts (EventEngine shape); returns how many.

        Problem events (see AUTO_REPAIR_TYPES) also append an
        ``auto_event`` row to the miner's repair history, deduplicated
        to at most one identical (site, ip, title) row per hour.
        """
        rows = []
        auto_rows = []
        for ev in events:
            try:
                ts = float(ev.get("ts") or time.time())
            except (TypeError, ValueError):
                ts = time.time()
            etype = str(ev.get("type") or "UNKNOWN")
            rows.append((
                agent_id, site, ts, etype,
                str(ev.get("severity") or "info"),
                ev.get("ip"), ev.get("model"), ev.get("detail"),
                json.dumps(ev.get("data") or {}, ensure_ascii=False)))
            if etype in AUTO_REPAIR_TYPES and ev.get("ip"):
                auto_rows.append((
                    agent_id, site, str(ev["ip"]),
                    ev.get("mac") or ev.get("serial"), ts,
                    etype, ev.get("detail")))
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
            for agent_id_, site_, ip_, mac_serial, ts_, title, detail \
                    in auto_rows:
                recent = self._db.execute(
                    "SELECT MAX(created_at) FROM repairs "
                    "WHERE site = ? AND ip = ? AND title = ? "
                    "AND kind = 'auto_event'",
                    (site_, ip_, title)).fetchone()[0]
                if recent is not None \
                        and ts_ - float(recent) < AUTO_REPAIR_DEDUPE_S:
                    continue
                self._insert_repair(agent_id_, site_, ip_, mac_serial,
                                    ts_, "auto_event", title, detail,
                                    None, None)
            self._prune_repairs()
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
    # repairs — per-miner repair history (v0.8)
    # ------------------------------------------------------------------

    @staticmethod
    def _repair_view(row: sqlite3.Row) -> dict:
        return {
            "id": row["id"],
            "agent_id": row["agent_id"],
            "site": row["site"],
            "ip": row["ip"],
            "mac_or_serial": row["mac_or_serial"],
            "created_at": _stamp(row["created_at"]),
            "created_ts": row["created_at"],
            "kind": row["kind"],
            "title": row["title"],
            "detail": row["detail"],
            "cost_vnd": row["cost_vnd"],
            "technician": row["technician"],
        }

    def _insert_repair(self, agent_id, site, ip, mac_or_serial, ts,
                       kind, title, detail, cost_vnd, technician) -> int:
        """Raw repairs INSERT — caller holds the lock + transaction."""
        cur = self._db.execute(
            "INSERT INTO repairs (agent_id, site, ip, mac_or_serial, "
            "created_at, kind, title, detail, cost_vnd, technician) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (agent_id, site, ip, mac_or_serial, float(ts), kind, title,
             detail, cost_vnd, technician))
        return int(cur.lastrowid)

    def _prune_repairs(self) -> None:
        """Keep the newest REPAIR_HISTORY rows — caller holds the lock."""
        self._db.execute(
            "DELETE FROM repairs WHERE id NOT IN "
            "(SELECT id FROM repairs ORDER BY id DESC LIMIT ?)",
            (REPAIR_HISTORY,))

    def add_repair(self, site: str, ip: str, title: str,
                   detail: str | None = None,
                   cost_vnd: int | None = None,
                   technician: str | None = None,
                   kind: str = "manual",
                   mac_or_serial: str | None = None,
                   agent_id: int | None = None,
                   ts: float | None = None) -> dict:
        """Append one repair-history row; returns its public view."""
        if agent_id is None:
            agent = self.agent_by_site(site)
            agent_id = agent["id"] if agent else None
        with self._lock, self._db:
            repair_id = self._insert_repair(
                agent_id, site, ip, mac_or_serial,
                time.time() if ts is None else ts, kind, title, detail,
                cost_vnd, technician)
            self._prune_repairs()
            row = self._db.execute(
                "SELECT * FROM repairs WHERE id = ?",
                (repair_id,)).fetchone()
        return self._repair_view(row)

    def list_repairs(self, site: str | None = None, ip: str | None = None,
                     n: int = 50) -> list[dict]:
        """Newest-first repair history, filterable by site and/or miner."""
        n = max(1, min(int(n), REPAIR_HISTORY))
        query = "SELECT * FROM repairs"
        clauses, params = [], []
        if site:
            clauses.append("site = ?")
            params.append(site)
        if ip:
            clauses.append("ip = ?")
            params.append(ip)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(n)
        with self._lock:
            rows = self._db.execute(query, params).fetchall()
        return [self._repair_view(r) for r in rows]

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
    # settings (v0.9)
    # ------------------------------------------------------------------

    def get_setting(self, key: str, default: str | None = None) -> str | None:
        with self._lock:
            row = self._db.execute(
                "SELECT value FROM settings WHERE key = ?",
                (key,)).fetchone()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        with self._lock, self._db:
            self._db.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, str(value)))

    def electricity_price_vnd(self) -> float:
        """Configured electricity price (VNĐ/kWh), default 2000."""
        raw = self.get_setting("electricity_price_vnd_kwh")
        try:
            price = float(raw) if raw is not None else 2000.0
        except ValueError:
            price = 2000.0
        return price if price >= 0 else 2000.0

    # ------------------------------------------------------------------
    # pool comparison (v0.9) — config, samples, POOL_GAP events
    # ------------------------------------------------------------------

    @staticmethod
    def pool_config_view(raw: dict) -> dict:
        """Public view of a pool config — secret values NEVER included.

        Header *names* are listed and ``headers_set`` says whether any
        are stored; the values themselves only leave the store through
        :meth:`pool_config_raw` (the poller's internal path).
        """
        try:
            headers = json.loads(raw.get("headers_json") or "{}")
        except json.JSONDecodeError:
            headers = {}
        if not isinstance(headers, dict):
            headers = {}
        return {
            "site": raw["site"],
            "adapter": raw["adapter"],
            "url": raw["url"],
            "json_path": raw["json_path"],
            "unit": raw["unit"],
            "worker_filter": raw["worker_filter"],
            "notify_gap_pct": raw["notify_gap_pct"],
            "header_names": sorted(headers.keys()),
            "headers_set": bool(headers),
        }

    def upsert_pool_config(self, site: str, *, adapter: str = "generic",
                           url: str = "", headers: dict | None = None,
                           json_path: str = "", unit: str = "TH/s",
                           worker_filter: str | None = None,
                           notify_gap_pct: float = 10.0) -> dict:
        """Create or replace a site's pool config; returns the view.

        ``headers=None`` keeps the previously stored headers (so the
        viewer can edit other fields without re-sending secrets); pass
        a dict — possibly empty — to replace them.
        """
        with self._lock, self._db:
            existing = self._db.execute(
                "SELECT headers_json FROM pool_configs WHERE site = ?",
                (site,)).fetchone()
            headers_json = (existing["headers_json"] if existing
                            else "{}") if headers is None else json.dumps(
                                headers, ensure_ascii=False)
            self._db.execute(
                "INSERT INTO pool_configs (site, adapter, url, "
                "headers_json, json_path, unit, worker_filter, "
                "notify_gap_pct) VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(site) DO UPDATE SET adapter = excluded.adapter, "
                "url = excluded.url, headers_json = excluded.headers_json, "
                "json_path = excluded.json_path, unit = excluded.unit, "
                "worker_filter = excluded.worker_filter, "
                "notify_gap_pct = excluded.notify_gap_pct",
                (site, adapter, url, headers_json, json_path, unit,
                 worker_filter, float(notify_gap_pct)))
            row = self._db.execute(
                "SELECT * FROM pool_configs WHERE site = ?",
                (site,)).fetchone()
        return self.pool_config_view(dict(row))

    def pool_config_raw(self, site: str) -> dict | None:
        """Full config incl. parsed headers — poller use ONLY."""
        with self._lock:
            row = self._db.execute(
                "SELECT * FROM pool_configs WHERE site = ?",
                (site,)).fetchone()
        if row is None:
            return None
        raw = dict(row)
        try:
            headers = json.loads(raw.pop("headers_json") or "{}")
        except json.JSONDecodeError:
            headers = {}
        raw["headers"] = headers if isinstance(headers, dict) else {}
        return raw

    def list_pool_configs(self) -> list[dict]:
        """All pool configs, public (redacted) view."""
        with self._lock:
            rows = self._db.execute(
                "SELECT * FROM pool_configs ORDER BY site").fetchall()
        return [self.pool_config_view(dict(r)) for r in rows]

    def list_pool_config_sites(self) -> list[str]:
        with self._lock:
            rows = self._db.execute(
                "SELECT site FROM pool_configs ORDER BY site").fetchall()
        return [r["site"] for r in rows]

    def farm_ths(self, site: str) -> float | None:
        """Farm-side TH/s for *site*: sum over its latest snapshot.

        v0.20: only H/s-family rates count, at their true TH/s
        equivalent (report.ths_equivalent). A sol-rate record has no
        TH/s equivalent — a site whose snapshot holds only Equihash
        miners returns None and the pool poller skips it, instead of
        comparing the pool against a meaningless raw sol sum.
        """
        agent = self.agent_by_site(site)
        if agent is None:
            return None
        snap = self.latest_snapshot(agent["id"])
        if not snap:
            return None
        values = [v for m in snap[1] if isinstance(m, dict)
                  for v in [_core_report.ths_equivalent(m)]
                  if v is not None]
        return round(sum(values), 4) if values else None

    def record_pool_sample(self, site: str, ts: float, pool_ths: float,
                           farm_ths: float) -> dict:
        """Store one pool sample; maybe emit a POOL_GAP event.

        gap_pct is the pool shortfall relative to the farm side:
        ``(farm - pool) / farm * 100``. The event (severity ``major``)
        fires when this sample AND the previous one both exceed the
        site's ``notify_gap_pct`` — a single bad poll never alarms —
        and at most once per hour per site (repairs-style dedupe).
        Returns the sample dict plus ``event_fired``.
        """
        ts = float(ts)
        if farm_ths > 0:
            gap_pct = (farm_ths - pool_ths) / farm_ths * 100.0
        elif pool_ths > 0:
            gap_pct = -100.0  # pool reports hash the farm cannot see
        else:
            gap_pct = 0.0
        event_fired = False
        with self._lock, self._db:
            prev = self._db.execute(
                "SELECT gap_pct FROM pool_samples WHERE site = ? "
                "ORDER BY id DESC LIMIT 1", (site,)).fetchone()
            self._db.execute(
                "INSERT INTO pool_samples (site, ts, pool_ths, farm_ths, "
                "gap_pct) VALUES (?, ?, ?, ?, ?)",
                (site, ts, float(pool_ths), float(farm_ths),
                 round(gap_pct, 2)))
            self._db.execute(
                "DELETE FROM pool_samples WHERE site = ? AND id NOT IN "
                "(SELECT id FROM pool_samples WHERE site = ? "
                " ORDER BY id DESC LIMIT ?)",
                (site, site, POOL_SAMPLE_HISTORY))
            config = self._db.execute(
                "SELECT notify_gap_pct FROM pool_configs WHERE site = ?",
                (site,)).fetchone()
            threshold = float(config["notify_gap_pct"]) \
                if config else 10.0
            if prev is not None and gap_pct > threshold \
                    and float(prev["gap_pct"]) > threshold:
                last = self._db.execute(
                    "SELECT MAX(ts) FROM events WHERE site = ? "
                    "AND type = 'POOL_GAP'", (site,)).fetchone()[0]
                agent = self._db.execute(
                    "SELECT id FROM agents WHERE site = ? "
                    "ORDER BY id LIMIT 1", (site,)).fetchone()
                if agent is not None and (last is None
                                          or ts - float(last) >= 3600.0):
                    detail = (
                        f"pool reports {pool_ths:.2f} TH/s vs farm "
                        f"{farm_ths:.2f} TH/s — gap {gap_pct:.1f}% exceeds "
                        f"{threshold:.0f}% for 2 consecutive checks")
                    self._db.execute(
                        "INSERT INTO events (agent_id, site, ts, type, "
                        "severity, ip, model, detail, data_json) "
                        "VALUES (?, ?, ?, 'POOL_GAP', 'major', NULL, "
                        "NULL, ?, ?)",
                        (agent["id"], site, ts, detail,
                         json.dumps({"pool_ths": round(pool_ths, 2),
                                     "farm_ths": round(farm_ths, 2),
                                     "gap_pct": round(gap_pct, 2),
                                     "threshold_pct": threshold},
                                    ensure_ascii=False)))
                    self._db.execute(
                        "DELETE FROM events WHERE id NOT IN "
                        "(SELECT id FROM events ORDER BY id DESC LIMIT ?)",
                        (EVENT_HISTORY,))
                    event_fired = True
        return {"site": site, "ts": ts, "time": _stamp(ts),
                "pool_ths": round(float(pool_ths), 2),
                "farm_ths": round(float(farm_ths), 2),
                "gap_pct": round(gap_pct, 2),
                "event_fired": event_fired}

    def latest_pool_sample(self, site: str) -> dict | None:
        with self._lock:
            row = self._db.execute(
                "SELECT * FROM pool_samples WHERE site = ? "
                "ORDER BY id DESC LIMIT 1", (site,)).fetchone()
        if row is None:
            return None
        return {"site": site, "ts": row["ts"], "time": _stamp(row["ts"]),
                "pool_ths": row["pool_ths"], "farm_ths": row["farm_ths"],
                "gap_pct": row["gap_pct"]}

    def pool_series(self, site: str, since_ts: float) -> list[dict]:
        """Samples for *site* since *since_ts*, oldest first."""
        with self._lock:
            rows = self._db.execute(
                "SELECT * FROM pool_samples WHERE site = ? AND ts >= ? "
                "ORDER BY id", (site, float(since_ts))).fetchall()
        return [{"ts": r["ts"], "time": _stamp(r["ts"]),
                 "pool_ths": r["pool_ths"], "farm_ths": r["farm_ths"],
                 "gap_pct": r["gap_pct"]} for r in rows]

    # ------------------------------------------------------------------
    # energy reports (v0.9)
    # ------------------------------------------------------------------

    def energy_report(self, site: str | None = None,
                      days: int = 7) -> dict:
        """Per-day + per-miner kWh over the last *days* local days.

        Days are local calendar days ending today; days without data
        simply do not appear in ``per_day`` (the panel's honest empty
        state keys off an all-zero total).
        """
        days = max(1, min(int(days), 366))
        now = time.time()
        cutoff_day = time.strftime(
            "%Y-%m-%d", time.localtime(now - (days - 1) * 86400))
        today = time.strftime("%Y-%m-%d", time.localtime(now))
        clauses = ["day >= ?"]
        params: list = [cutoff_day]
        if site:
            clauses.append("site = ?")
            params.append(site)
        where = " AND ".join(clauses)
        with self._lock:
            day_rows = self._db.execute(
                f"SELECT day, SUM(kwh) AS kwh FROM energy_hours "
                f"WHERE {where} GROUP BY day ORDER BY day",
                params).fetchall()
            miner_rows = self._db.execute(
                f"SELECT site, ip, SUM(kwh) AS kwh FROM energy_hours "
                f"WHERE {where} GROUP BY site, ip "
                f"ORDER BY kwh DESC", params).fetchall()
        per_day = [{"day": r["day"], "kwh": round(float(r["kwh"]), 4)}
                   for r in day_rows]
        per_miner = [{"site": r["site"], "ip": r["ip"],
                      "kwh": round(float(r["kwh"]), 4)}
                     for r in miner_rows]
        today_kwh = next((d["kwh"] for d in per_day if d["day"] == today),
                         0.0)
        return {
            "days": days,
            "today": {"day": today, "kwh": today_kwh},
            "per_day": per_day,
            "per_miner": per_miner,
            "total_kwh": round(sum(d["kwh"] for d in per_day), 4),
        }

    # ------------------------------------------------------------------
    # viewer summaries
    # ------------------------------------------------------------------

    def sites_summary(self, now: float | None = None) -> list[dict]:
        """One summary dict per registered agent/site for /api/sites."""
        now = time.time() if now is None else float(now)
        sites = []
        for agent in self.list_agents():
            if agent.get("revoked"):
                continue  # revoked agents leave the fleet views (v0.13)
            snap = self.latest_snapshot(agent["id"])
            miners = snap[1] if snap else []
            # v0.20: total_ths is the H/s-family TH/s sum (identical
            # for TH/s and pre-v0.20 records); rate_totals carries the
            # per-unit grouped totals the dashboard renders.
            ths_values = [v for m in miners
                          for v in [_core_report.ths_equivalent(m)]
                          if v is not None]
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
                "rate_totals": [
                    {"unit": unit, "value": round(value, 2)}
                    for value, unit in
                    _core_report.fleet_rate_totals(miners)],
                "max_temp": (max(temp_values) if temp_values else None),
            })
        return sites

    def miners_by_site(self, site: str | None = None) -> list[dict]:
        """Latest records across agents, each annotated with its site."""
        merged = []
        for agent in self.list_agents():
            if agent.get("revoked"):
                continue  # revoked agents leave the fleet views (v0.13)
            if site and agent["site"] != site:
                continue
            snap = self.latest_snapshot(agent["id"])
            if not snap:
                continue
            for record in snap[1]:
                merged.append({**record, "site": agent["site"]})
        merged.sort(key=lambda r: (r["site"], r.get("ip") or ""))
        return merged
