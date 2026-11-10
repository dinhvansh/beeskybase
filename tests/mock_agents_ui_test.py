#!/usr/bin/env python3
"""v0.13 test — dashboard icons + agent management from the web.

Two layers, no hardware:

  * Store level (in-process): ``agent_views`` never carries key
    material (no plaintext — never stored — and no SHA-256 hash);
    ``revoke_agent`` flips the flag and the revoked key immediately
    fails the single auth lookup (``agent_by_key``) behind every
    agent-facing endpoint; a pre-v0.13 database (agents table without
    the ``revoked`` column) is migrated on open and its agents keep
    authenticating until revoked.

  * HTTP level (subprocess on 127.0.0.1): `beesky cloud` (:18795,
    password set). The agent endpoints are 401 logged out; after
    login, POST /api/agents mints an agent whose raw key comes back
    exactly once — GET /api/agents lists the agent without the key
    or its hash anywhere in the payload; a real snapshot ingest with
    the minted key succeeds (200) and shows the agent online; after
    POST /api/agents/revoke the same ingest is rejected (401). The
    served dashboard is asserted to carry the v0.13 additions — the
    Agent & trại section ids, seven inline nav icons + stat-card
    icon chips (distinctive path fragments) — while keeping every
    pre-v0.13 marker the older suites rely on.

Prints PASS lines; exit 1 on failure. Run via
tests/run_mock_test_v13.sh (appends evidence to tests/RESULTS.md).
"""

import hashlib
import http.cookiejar
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

CLOUD_PORT = 18795
BASE = f"http://127.0.0.1:{CLOUD_PORT}"
SITE = "Xưởng 9"
PASSWORD = "agents-test-password"

_jar = http.cookiejar.CookieJar()
_opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({}),
    urllib.request.HTTPCookieProcessor(_jar))
_plain = urllib.request.build_opener(urllib.request.ProxyHandler({}))
FAILURES: list[str] = []


def check(label: str, condition: bool, extra: str = "") -> None:
    if condition:
        print(f"PASS: {label}")
    else:
        print(f"FAIL: {label} {extra}")
        FAILURES.append(label)


def fetch(path: str, opener=_opener, method: str = "GET",
          data: bytes | None = None,
          headers: dict | None = None) -> tuple[int, str]:
    request = urllib.request.Request(
        BASE + path, method=method, data=data, headers=headers or {})
    try:
        with opener.open(request, timeout=10) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")


def fetch_json(path: str, opener=_opener) -> tuple[int, dict]:
    status, body = fetch(path, opener=opener)
    try:
        return status, json.loads(body)
    except json.JSONDecodeError:
        return status, {}


def post_json(path: str, payload: dict, opener=_opener,
              headers: dict | None = None) -> tuple[int, dict]:
    merged = {"Content-Type": "application/json"}
    merged.update(headers or {})
    status, body = fetch(path, opener=opener, method="POST",
                         data=json.dumps(payload).encode(),
                         headers=merged)
    try:
        return status, json.loads(body)
    except json.JSONDecodeError:
        return status, {}


def wait_for(label: str, fn, timeout: float = 60.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            value = fn()
        except Exception:  # noqa: BLE001 — server may not be up yet
            value = None
        if value:
            return value
        time.sleep(0.4)
    print(f"  (timed out waiting for: {label})")
    return None


def miner(ip: str, ths: float) -> dict:
    return {"ip": ip, "model": "Antminer S19 Pro", "source": "dashd",
            "status": "OK", "ths": ths, "max_temp_c": 70.0,
            "chips_alive": 342, "chips_total": 342, "fans_rpm": [4000],
            "problems": []}


# ----------------------------------------------------------------------
# store level
# ----------------------------------------------------------------------

def store_level_checks() -> None:
    from beesky.cloud.store import CloudStore

    tmp = Path(tempfile.mkdtemp(prefix="beesky-v13-store-"))
    store = CloudStore(str(tmp / "store.db"))
    agent_id = store.create_agent("Store Site", "store-secret-key")
    views = store.agent_views()
    blob = json.dumps(views)
    check("store: agent_views carries no key material",
          len(views) == 1 and views[0]["id"] == agent_id
          and "key_hash" not in blob and "store-secret-key" not in blob
          and hashlib.sha256(b"store-secret-key").hexdigest() not in blob,
          blob)
    check("store: fresh agent is not revoked and offline",
          views[0]["revoked"] is False and views[0]["online"] is False
          and views[0]["site"] == "Store Site")
    check("store: agent_by_key authenticates before revoke",
          (store.agent_by_key("store-secret-key") or {}).get("id")
          == agent_id)
    check("store: revoke of unknown id -> False",
          store.revoke_agent(999999) is False)
    check("store: revoke existing agent -> True",
          store.revoke_agent(agent_id) is True)
    check("store: revoked key no longer authenticates",
          store.agent_by_key("store-secret-key") is None)
    views = store.agent_views()
    check("store: revoked agent shows revoked + offline in views",
          views[0]["revoked"] is True and views[0]["online"] is False)
    check("store: revoked site has no live agent_by_site",
          store.agent_by_site("Store Site") is None)
    store.close()

    # -- pre-v0.13 database: agents table without the revoked column --
    legacy = tmp / "legacy.db"
    conn = sqlite3.connect(legacy)
    conn.executescript("""
        CREATE TABLE agents (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            site        TEXT NOT NULL,
            key_hash    TEXT NOT NULL UNIQUE,
            created_at  REAL NOT NULL,
            last_seen_at REAL,
            interval_s  REAL
        );
    """)
    conn.execute(
        "INSERT INTO agents (site, key_hash, created_at) VALUES (?, ?, ?)",
        ("Legacy Site",
         hashlib.sha256(b"legacy-key").hexdigest(), 1700000000.0))
    conn.commit()
    conn.close()
    store = CloudStore(str(legacy))
    legacy_agent = store.agent_by_key("legacy-key")
    check("store: pre-v0.13 db migrated — legacy agent authenticates",
          legacy_agent is not None
          and legacy_agent["site"] == "Legacy Site",
          repr(legacy_agent))
    if legacy_agent is not None:
        check("store: migrated agent can be revoked like any other",
              store.revoke_agent(legacy_agent["id"]) is True
              and store.agent_by_key("legacy-key") is None)
    store.close()


# ----------------------------------------------------------------------
# HTTP level
# ----------------------------------------------------------------------

def http_level_checks() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="beesky-v13-"))
    db = tmp / "cloud.db"
    env = dict(os.environ)
    env["BEESKY_CLOUD_PASSWORD"] = PASSWORD

    cloud = subprocess.Popen(
        [sys.executable, "-m", "beesky", "cloud", "--port",
         str(CLOUD_PORT), "--db", str(db)],
        cwd=ROOT, env=env, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True)
    try:
        up = wait_for("cloud login page", lambda:
                      fetch("/login", opener=_plain)[0] == 200)
        check("cloud server starts", up is not None)
        if not up:
            return

        # -- logged out: every agent endpoint is gated -------------------
        code, _ = fetch_json("/api/agents", opener=_plain)
        check("GET /api/agents without login -> 401", code == 401,
              f"got {code}")
        code, _ = post_json("/api/agents", {"site": SITE}, opener=_plain)
        check("POST /api/agents without login -> 401", code == 401,
              f"got {code}")
        code, _ = post_json("/api/agents/revoke", {"id": 1},
                            opener=_plain)
        check("POST /api/agents/revoke without login -> 401",
              code == 401, f"got {code}")

        form = urllib.parse.urlencode({"password": PASSWORD}).encode()
        code, _ = fetch("/login", method="POST", data=form, headers={
            "Content-Type": "application/x-www-form-urlencoded"})
        check("login with right password -> session", code == 200,
              f"got {code}")

        code, data = fetch_json("/api/agents")
        check("GET /api/agents with session -> 200, empty at first",
              code == 200 and data.get("agents") == [],
              json.dumps(data, ensure_ascii=False))

        # -- minting ------------------------------------------------------
        code, data = post_json("/api/agents", {"site": "  "})
        check("POST /api/agents with blank site -> 400", code == 400,
              f"got {code}")
        code, data = post_json("/api/agents", {"site": SITE})
        agent_id = data.get("id")
        raw_key = data.get("key") or ""
        check("POST /api/agents mints + returns the raw key once",
              code == 201 and isinstance(agent_id, int)
              and data.get("site") == SITE and len(raw_key) >= 32,
              f"got {code}: {json.dumps(data, ensure_ascii=False)}")
        if not raw_key:
            return

        code, body = fetch("/api/agents")
        try:
            listing = json.loads(body)
        except json.JSONDecodeError:
            listing = {}
        agents = listing.get("agents") or []
        mine = [a for a in agents if a.get("id") == agent_id]
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        check("GET /api/agents lists the minted agent, key + hash absent",
              code == 200 and len(mine) == 1
              and mine[0]["site"] == SITE
              and mine[0]["revoked"] is False
              and raw_key not in body and key_hash not in body
              and "key_hash" not in body,
              body[:400])

        # -- the minted key really ingests --------------------------------
        auth = {"Authorization": f"Bearer {raw_key}"}

        def ingest(ts):
            return post_json(
                "/api/ingest",
                {"site": SITE, "ts": ts, "interval": 5,
                 "miners": [miner("10.0.0.1", 109.13)]},
                opener=_plain, headers=auth)

        code, resp = ingest(time.time())
        check("ingest with the web-minted key -> 200",
              code == 200 and resp.get("ok") is True,
              f"got {code}: {resp}")
        code, data = fetch_json("/api/agents")
        mine = [a for a in (data.get("agents") or [])
                if a.get("id") == agent_id]
        check("agent shows online after its first ingest",
              len(mine) == 1 and mine[0]["online"] is True
              and mine[0]["last_seen"] is not None,
              json.dumps(data, ensure_ascii=False))

        # -- revoke --------------------------------------------------------
        code, _ = post_json("/api/agents/revoke", {"id": "abc"})
        check("POST /api/agents/revoke with non-integer id -> 400",
              code == 400, f"got {code}")
        code, _ = post_json("/api/agents/revoke", {"id": 999999})
        check("POST /api/agents/revoke with unknown id -> 404",
              code == 404, f"got {code}")
        code, data = post_json("/api/agents/revoke", {"id": agent_id})
        check("POST /api/agents/revoke revokes the minted agent",
              code == 200 and data.get("revoked") is True,
              f"got {code}: {data}")
        code, data = fetch_json("/api/agents")
        mine = [a for a in (data.get("agents") or [])
                if a.get("id") == agent_id]
        check("revoked agent listed as revoked + offline",
              len(mine) == 1 and mine[0]["revoked"] is True
              and mine[0]["online"] is False,
              json.dumps(data, ensure_ascii=False))
        code, _ = ingest(time.time())
        check("ingest with the revoked key -> 401", code == 401,
              f"got {code}")

        # -- dashboard: v0.13 additions + every legacy marker -------------
        code, html = fetch("/")
        check("dashboard: agent management section ids present",
              code == 200 and all(
                  f'id="{i}"' in html for i in (
                      "agents-panel", "agent-form", "ag-site", "ag-msg",
                      "agents-list", "agent-key-panel", "ak-site",
                      "ak-key", "ak-cmd", "ak-copy", "ak-copy-cmd",
                      "ak-done"))
              and "chỉ hiện MỘT lần" in html)
        nav_fragments = [
            'x="14" y="14" width="7" height="7"',       # layout-grid
            'x="2" y="14" width="20" height="8"',       # server
            "M14 4v10.54a4 4 0 1 1-4 0V4",              # thermometer
            'points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"',  # zap
            "M14.7 6.3a1 1 0 0 0 0 1.4",                # wrench
            "M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9",          # bell
            '<circle cx="12" cy="12" r="3"/>',          # gear
        ]
        check("dashboard: seven sidebar nav icons (inline SVG)",
              html.count('class="nav-ic"') == 7
              and all(f in html for f in nav_fragments))
        check("dashboard: stat-card icon chips + logout icon",
              html.count('class="ic-chip"') == 4
              and 'points="22 12 18 12 15 21 9 3 6 12 2 12"' in html
              and "m21.73 18-8-14" in html
              and "M9 21H5a2 2 0 0 1-2-2V5" in html)
        nav = ["Tổng quan", "Máy đào", "Bản đồ nhiệt", "Điện năng",
               "Lịch sử sửa", "Sự kiện", "Cài đặt"]
        check("dashboard: legacy markers survive (nav/heat/pool/logo)",
              all(label in html for label in nav)
              and 'id="heatmap"' in html and "heatColor" in html
              and "t < 60" in html and "t < 90" in html
              and "#8a1f1a" in html and 'id="pool-panel"' in html
              and 'id="pool-form"' in html and 'id="pc-site"' in html
              and 'id="price-form"' in html and 'id="st-price"' in html
              and 'id="chart-wrap"' in html
              and 'viewBox="-373.37 -15.87 198.58 198.58"' in html
              and "M-207.439,26.24" in html)
    finally:
        cloud.terminate()
        try:
            cloud.wait(timeout=10)
        except subprocess.TimeoutExpired:
            cloud.kill()


def main() -> int:
    store_level_checks()
    http_level_checks()
    print()
    if FAILURES:
        print(f"AGENTS UI TEST FAILED — {len(FAILURES)} check(s): "
              + ", ".join(FAILURES))
        return 1
    print("AGENTS UI TEST PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
