#!/usr/bin/env python3
"""v0.12 test — dashboard redesign backend: history sampling + settings UI.

Two layers, no hardware:

  * Store level (in-process): ``add_snapshot`` writes at most one
    ``history_samples`` row per site per 60 s (two snapshots 10 s
    apart -> one row; +70 s -> a second), row totals mirror the
    snapshot (summed TH/s, miner/problem counts, max temp), rows are
    filterable per site, and samples older than 30 days are pruned
    on the write path.

  * HTTP level (subprocess on 127.0.0.1): `beesky cloud` (:18794,
    password set). ``GET /api/history`` is 401 logged out; after
    login, three ingests with explicit timestamps produce exactly
    the two throttled points with the right totals; the ``?site=``
    filter works. The served dashboard is asserted to carry the
    v0.12 redesign — sidebar nav labels, view containers, history
    chart container, settings form ids (pool config + electricity
    price) — while keeping every pre-v0.12 marker the older suites
    rely on (heat map + thresholds, pool/energy panels, official
    logo SVG).

Prints PASS lines; exit 1 on failure. Run via
tests/run_mock_test_v12.sh (appends evidence to tests/RESULTS.md).
"""

import http.cookiejar
import json
import os
import re
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

CLOUD_PORT = 18794
BASE = f"http://127.0.0.1:{CLOUD_PORT}"
SITE = "Xưởng 1"
PASSWORD = "history-test-password"

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


def miner(ip: str, ths: float, status: str = "OK",
          temp: float | None = 70.0) -> dict:
    return {"ip": ip, "model": "Antminer S19 Pro", "source": "dashd",
            "status": status, "ths": ths, "max_temp_c": temp,
            "chips_alive": 342, "chips_total": 342, "fans_rpm": [4000],
            "problems": [] if status == "OK" else [
                {"code": "OVER_TEMP", "detail": "hot"}]}


# ----------------------------------------------------------------------
# store level
# ----------------------------------------------------------------------

def store_level_checks() -> None:
    from beesky.cloud.store import CloudStore

    tmp = Path(tempfile.mkdtemp(prefix="beesky-v12-store-"))
    store = CloudStore(str(tmp / "store.db"))
    agent_a = store.create_agent("Site A", "hist-key-a")
    agent_b = store.create_agent("Site B", "hist-key-b")
    t0 = 1_700_000_000.0
    pair = [miner("10.0.0.1", 100.0), miner("10.0.0.2", 5.5, "CHECK", 88.0)]

    store.add_snapshot(agent_a, t0, pair)
    rows = store.history_series("Site A", 0)
    check("store: first snapshot writes one history sample",
          len(rows) == 1, f"got {len(rows)}")
    if rows:
        row = rows[0]
        check("store: sample totals mirror the snapshot",
              row["total_ths"] == 105.5 and row["miners_total"] == 2
              and row["miners_problem"] == 1
              and row["max_temp_c"] == 88.0,
              json.dumps(row))

    store.add_snapshot(agent_a, t0 + 10, pair)
    check("store: snapshot 10 s later is throttled (still 1 row)",
          len(store.history_series("Site A", 0)) == 1)

    store.add_snapshot(agent_a, t0 + 70,
                       [miner("10.0.0.1", 90.0), miner("10.0.0.2", 5.5)])
    rows = store.history_series("Site A", 0)
    check("store: snapshot +70 s writes the 2nd row",
          len(rows) == 2 and rows[1]["total_ths"] == 95.5
          and rows[1]["miners_problem"] == 0,
          json.dumps(rows))

    store.add_snapshot(agent_b, t0 + 30, [miner("10.0.1.1", 42.0)])
    check("store: per-site filter + all-sites view",
          len(store.history_series("Site B", 0)) == 1
          and len(store.history_series(None, 0)) == 3
          and store.history_series("Nope", 0) == [])
    check("store: since_ts window is honoured",
          [r["ts"] for r in store.history_series("Site A", t0 + 60)]
          == [t0 + 70])

    agent_c = store.create_agent("Site Old", "hist-key-c")
    store.add_snapshot(agent_c, t0, [miner("10.0.2.1", 10.0)])
    store.add_snapshot(agent_c, t0 + 31 * 86400, [miner("10.0.2.1", 11.0)])
    rows = store.history_series("Site Old", 0)
    check("store: samples older than 30 days are pruned on write",
          len(rows) == 1 and rows[0]["ts"] == t0 + 31 * 86400,
          json.dumps(rows))
    store.close()


# ----------------------------------------------------------------------
# HTTP level
# ----------------------------------------------------------------------

def http_level_checks() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="beesky-v12-"))
    db = tmp / "cloud.db"
    env = dict(os.environ)
    env["BEESKY_CLOUD_PASSWORD"] = PASSWORD

    made = subprocess.run(
        [sys.executable, "-m", "beesky", "cloud-add-agent",
         "--db", str(db), "--site", SITE],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)
    match = re.search(r"BEESKY_AGENT_KEY=(\S+)", made.stdout)
    check("cloud-add-agent prints a key once", match is not None,
          made.stdout + made.stderr)
    if not match:
        return
    agent_key = match.group(1)

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

        code, _ = fetch_json("/api/history", opener=_plain)
        check("GET /api/history without login -> 401", code == 401,
              f"got {code}")

        form = urllib.parse.urlencode({"password": PASSWORD}).encode()
        code, _ = fetch("/login", method="POST", data=form, headers={
            "Content-Type": "application/x-www-form-urlencoded"})
        check("login with right password -> session", code == 200,
              f"got {code}")

        code, data = fetch_json("/api/history?hours=24")
        check("GET /api/history with session -> 200, empty at first",
              code == 200 and data.get("points") == [],
              json.dumps(data, ensure_ascii=False))

        # -- dashboard: v0.12 redesign + every legacy marker ------------
        code, html = fetch("/")
        nav = ["Tổng quan", "Máy đào", "Bản đồ nhiệt", "Điện năng",
               "Lịch sử sửa", "Sự kiện", "Cài đặt"]
        check("dashboard: sidebar nav with all seven views",
              code == 200 and all(
                  f'data-view="{v}"' in html and label in html
                  for v, label in zip(
                      ["overview", "miners", "heatmap", "energy",
                       "repairs", "events", "settings"], nav)))
        form_ids = ["pool-form", "pc-site", "pc-adapter", "pc-url",
                    "pc-path", "pc-unit", "pc-worker", "pc-gap",
                    "pc-headers", "price-form", "st-price",
                    "pool-config-list"]
        check("dashboard: settings forms (pool config + price) present",
              all(f'id="{i}"' in html for i in form_ids))
        check("dashboard: history chart container + topbar",
              'id="chart-wrap"' in html and 'id="chart-meta"' in html
              and 'id="last-update"' in html and 'id="view-title"' in html)
        check("dashboard: legacy markers survive (heat/pool/energy/logo)",
              "Bản đồ nhiệt" in html and 'id="heatmap"' in html
              and "heatColor" in html and "t < 60" in html
              and "t < 90" in html and "#8a1f1a" in html
              and 'id="pool-panel"' in html and 'id="energy-panel"' in html
              and "POOL_GAP" in html and "Lệnh gần đây" in html
              and 'viewBox="-373.37 -15.87 198.58 198.58"' in html
              and "M-207.439,26.24" in html)

        # -- ingests drive throttled history points ----------------------
        auth = {"Authorization": f"Bearer {agent_key}"}
        base_ts = time.time()
        pair = [miner("10.0.0.1", 100.0),
                miner("10.0.0.2", 5.5, "CHECK", 88.0)]

        def ingest(ts, miners):
            return post_json("/api/ingest",
                             {"site": SITE, "ts": ts, "interval": 5,
                              "miners": miners},
                             opener=_plain, headers=auth)

        code, resp = ingest(base_ts, pair)
        check("ingest snapshot 1 accepted",
              code == 200 and resp.get("ok") is True,
              f"got {code}: {resp}")
        code, _ = ingest(base_ts + 10, pair)
        check("ingest snapshot 2 (+10 s) accepted", code == 200,
              f"got {code}")
        code, data = fetch_json("/api/history?hours=1")
        points = data.get("points") or []
        check("history after +10 s: throttle keeps a single point",
              code == 200 and len(points) == 1
              and points[0]["site"] == SITE
              and points[0]["total_ths"] == 105.5
              and points[0]["miners_total"] == 2
              and points[0]["miners_problem"] == 1
              and points[0]["max_temp_c"] == 88.0,
              json.dumps(data, ensure_ascii=False))

        code, _ = ingest(base_ts + 70,
                         [miner("10.0.0.1", 90.0),
                          miner("10.0.0.2", 5.5)])
        check("ingest snapshot 3 (+70 s) accepted", code == 200,
              f"got {code}")
        code, data = fetch_json(f"/api/history?hours=1&site="
                                + urllib.parse.quote(SITE))
        points = data.get("points") or []
        check("history after +70 s: second point appears, site filter ok",
              code == 200 and len(points) == 2
              and points[1]["total_ths"] == 95.5
              and points[1]["miners_problem"] == 0,
              json.dumps(data, ensure_ascii=False))
        code, data = fetch_json("/api/history?hours=1&site=Nope")
        check("history for an unknown site is empty",
              code == 200 and data.get("points") == [],
              json.dumps(data, ensure_ascii=False))
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
        print(f"HISTORY TEST FAILED — {len(FAILURES)} check(s): "
              + ", ".join(FAILURES))
        return 1
    print("HISTORY TEST PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
