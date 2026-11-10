#!/usr/bin/env python3
"""v0.9 end-to-end test — farm-vs-pool comparison + energy reports.

Three layers, no hardware:

  * Store level (in-process): pool config upserts redact secret header
    values from every view (names only) and keep stored secrets when a
    re-POST omits ``headers``; the POOL_GAP rule fires only on the
    second consecutive over-threshold sample and dedupes to 1/hour;
    energy integrates ``power_w`` across snapshots with the 3x-interval
    dt cap.

  * Adapter level: ``fetch_pool_ths`` against an in-process mock pool
    JSON server — dot-path extraction, GH/s -> TH/s conversion, and
    the worker_filter list semantics.

  * HTTP level (subprocesses on 127.0.0.1, the v0.5 cloud shape):
    `beesky cloud` (:18793, password set, BEESKY_POOL_POLL_S=1), the
    mock dashd S19 Pro on 127.0.0.1:18098 (serves power_consumption
    3210 W), the mock pool on :18123 and `beesky agent --interval 1`.
    Assertions: pool/energy/settings endpoints 401 logged out; the
    miner record carries power_w 3210; a pool config POST/GET
    round-trips with the secret header sent to the pool but never
    echoed by the cloud; a ~5% gap samples quietly, flipping the pool
    to 40% of farm raises POOL_GAP; energy accumulates > 0 kWh for
    the miner and the electricity price is settable.

Prints PASS lines; exit 1 on failure. Run via
tests/run_mock_test_v9.sh (appends evidence to tests/RESULTS.md).
"""

import http.cookiejar
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DASHD_PORT = 18098
POOL_PORT = 18123
CLOUD_PORT = 18793
BASE = f"http://127.0.0.1:{CLOUD_PORT}"
POOL_URL = f"http://127.0.0.1:{POOL_PORT}/api"
SITE = "Xưởng 1"
IP = "127.0.0.1"
PASSWORD = "mat-khau-test"
POOL_SECRET = "pool-secret-xyz"
DASHD_POWER_W = 3210

POOL_STATE = {"value_ths": None, "last_auth": None, "hits": 0}

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
        with opener.open(request, timeout=5) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")


def fetch_json(path: str, opener=_opener) -> tuple[int, dict]:
    status, body = fetch(path, opener=opener)
    return status, json.loads(body)


def post_json(path: str, payload: dict, opener=_opener) -> tuple[int, dict]:
    status, body = fetch(
        path, opener=opener, method="POST",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    try:
        return status, json.loads(body)
    except json.JSONDecodeError:
        return status, {}


def wait_for(label: str, fn, timeout: float = 40.0):
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


# ----------------------------------------------------------------------
# mock pool server (in-process thread)
# ----------------------------------------------------------------------

class _PoolHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def do_GET(self):
        POOL_STATE["hits"] += 1
        POOL_STATE["last_auth"] = self.headers.get("Authorization")
        value = POOL_STATE["value_ths"]
        payload = {"data": {
            "hashrate_ths": value,
            "hashrate_ghs": None if value is None else value * 1000.0,
            "workers": [
                {"worker": "xuong1.may01",
                 "hashrate": None if value is None else value * 0.6},
                {"worker": "xuong2.may01",
                 "hashrate": None if value is None else value * 0.4},
            ]}}
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def start_pool_server() -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("127.0.0.1", POOL_PORT), _PoolHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


# ----------------------------------------------------------------------
# store + adapter levels
# ----------------------------------------------------------------------

def store_level_checks() -> None:
    from beesky.cloud.pools import fetch_pool_ths
    from beesky.cloud.store import CloudStore

    tmp = Path(tempfile.mkdtemp(prefix="beesky-v09-store-"))
    store = CloudStore(str(tmp / "store.db"))
    agent_id = store.create_agent(SITE, "store-test-key")
    now = time.time()

    # -- pool config redaction --------------------------------------
    view = store.upsert_pool_config(
        SITE, url="http://pool.example/api",
        headers={"Authorization": f"Bearer {POOL_SECRET}",
                 "X-Api-Key": "another-secret"},
        json_path="data.hashrate", unit="TH/s", notify_gap_pct=10.0)
    check("store: config view lists header NAMES, never values",
          view["header_names"] == ["Authorization", "X-Api-Key"]
          and view["headers_set"] is True
          and POOL_SECRET not in json.dumps(view)
          and "another-secret" not in json.dumps(view),
          json.dumps(view))
    view2 = store.upsert_pool_config(
        SITE, url="http://pool.example/api2", headers=None,
        json_path="data.hashrate", unit="TH/s")
    raw = store.pool_config_raw(SITE)
    check("store: re-POST without headers keeps the stored secrets",
          view2["url"].endswith("api2")
          and raw["headers"].get("Authorization")
          == f"Bearer {POOL_SECRET}",
          json.dumps(raw["headers"]))

    # -- POOL_GAP rule ------------------------------------------------
    r1 = store.record_pool_sample(SITE, now, 80.0, 100.0)
    r2 = store.record_pool_sample(SITE, now + 300, 80.0, 100.0)
    r3 = store.record_pool_sample(SITE, now + 600, 80.0, 100.0)
    gaps = [e for e in store.list_events(20, SITE)
            if e["type"] == "POOL_GAP"]
    check("store: gap fires on 2nd consecutive breach, deduped 1/hour",
          r1["gap_pct"] == 20.0
          and (r1["event_fired"], r2["event_fired"], r3["event_fired"])
          == (False, True, False)
          and len(gaps) == 1 and gaps[0]["severity"] == "major",
          f"{r1} {r2} {r3} gaps={gaps}")
    store.record_pool_sample(SITE, now + 900, 99.0, 100.0)
    r5 = store.record_pool_sample(SITE, now + 1200, 99.0, 100.0)
    check("store: samples back under threshold never fire",
          r5["event_fired"] is False
          and len([e for e in store.list_events(20, SITE)
                   if e["type"] == "POOL_GAP"]) == 1)

    # -- energy integration -------------------------------------------
    miner = [{"ip": IP, "ths": 100.0, "power_w": 3600.0,
              "status": "OK", "max_temp_c": 70.0}]
    store.add_snapshot(agent_id, now, miner)          # baseline
    store.touch_agent(agent_id, now, 30.0)
    store.add_snapshot(agent_id, now + 60, miner)     # 3600 W x 60 s
    report = store.energy_report(site=SITE, days=7)
    check("store: energy integrates power_w across snapshots (0.06 kWh)",
          abs(report["total_kwh"] - 0.06) < 1e-6
          and report["per_miner"][0]["ip"] == IP,
          json.dumps(report))
    store.add_snapshot(agent_id, now + 60 + 86400, miner)  # dt >> cap
    report = store.energy_report(site=SITE, days=7)
    check("store: dt capped at 3x interval (adds 3600 W x 90 s = 0.09)",
          abs(report["total_kwh"] - 0.15) < 1e-6,
          json.dumps(report))
    store.close()

    # -- adapter level --------------------------------------------------
    POOL_STATE["value_ths"] = 100.0
    ths = fetch_pool_ths({"url": POOL_URL, "json_path": "data.hashrate_ghs",
                          "unit": "GH/s", "headers": {}})
    check("adapter: dot path + GH/s -> TH/s conversion",
          abs(ths - 100.0) < 1e-6, f"got {ths}")
    ths = fetch_pool_ths({"url": POOL_URL,
                          "json_path": "data.workers.hashrate",
                          "unit": "TH/s", "headers": {},
                          "worker_filter": "xuong1"})
    check("adapter: worker_filter sums only matching workers (60)",
          abs(ths - 60.0) < 1e-6, f"got {ths}")


# ----------------------------------------------------------------------
# HTTP level: cloud + agent + mock dashd + mock pool
# ----------------------------------------------------------------------

def http_level_checks() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="beesky-v09-"))
    db = tmp / "cloud.db"
    env = {**os.environ, "PYTHONPATH": str(ROOT)}

    minted = subprocess.run(
        [sys.executable, "-m", "beesky", "cloud-add-agent",
         "--db", str(db), "--site", SITE],
        cwd=ROOT, env=env, capture_output=True, text=True)
    match = re.search(r"BEESKY_AGENT_KEY=(\S+)", minted.stdout)
    check("cloud-add-agent prints a key once", match is not None,
          minted.stdout + minted.stderr)
    if not match:
        return
    agent_key = match.group(1)

    cloud_env = {**env, "BEESKY_CLOUD_PASSWORD": PASSWORD,
                 "BEESKY_POOL_POLL_S": "1"}
    cloud = subprocess.Popen(
        [sys.executable, "-m", "beesky", "cloud", "--port", str(CLOUD_PORT),
         "--db", str(db)],
        cwd=ROOT, env=cloud_env, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True)
    miner = subprocess.Popen(
        [sys.executable, str(ROOT / "tests" / "mock_dashd.py"),
         "127.0.0.1", str(DASHD_PORT)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    agent = None
    try:
        up = wait_for("cloud login page",
                      lambda: fetch("/login", opener=_plain)[0] == 200
                      or None)
        check("cloud starts and serves /login", up is not None)

        # -- new endpoints are login-gated ----------------------------
        for path in ("/api/pool-config", "/api/pool", "/api/energy",
                     "/api/settings"):
            code, _ = fetch_json(path, opener=_plain)
            check(f"GET {path} without login -> 401", code == 401,
                  f"got {code}")
        code, _ = post_json("/api/pool-config", {"site": SITE},
                            opener=_plain)
        check("POST /api/pool-config without login -> 401", code == 401,
              f"got {code}")
        code, _ = post_json("/api/settings",
                            {"electricity_price_vnd_kwh": 1},
                            opener=_plain)
        check("POST /api/settings without login -> 401", code == 401,
              f"got {code}")

        form = urllib.parse.urlencode({"password": PASSWORD}).encode()
        code, _ = fetch("/login", method="POST", data=form, headers={
            "Content-Type": "application/x-www-form-urlencoded"})
        check("login with right password -> session", code == 200,
              f"got {code}")

        code, settings = fetch_json("/api/settings")
        check("GET /api/settings: default price 2000 VND/kWh",
              code == 200
              and settings.get("electricity_price_vnd_kwh") == 2000.0,
              json.dumps(settings))

        code, html = fetch("/")
        check("cloud dashboard: pool + energy panels present",
              code == 200 and "So sánh với pool" in html
              and 'id="pool-panel"' in html and "Điện năng" in html
              and 'id="energy-panel"' in html and "POOL_GAP" in html,
              f"code {code}")

        # -- agent pushes the dashd miner (has power) -------------------
        agent = subprocess.Popen(
            [sys.executable, "-m", "beesky", "agent", "127.0.0.1",
             "--cloud", BASE, "--key", agent_key, "--site", SITE,
             "--interval", "1", "--timeout", "1.0",
             "--cgminer-port", "14099", "--http-port", str(DASHD_PORT)],
            cwd=ROOT, env=env, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True)

        def site_ready():
            _c, data = fetch_json("/api/sites")
            found = [s for s in data.get("sites", [])
                     if s["site"] == SITE and s["miner_count"] == 1]
            return found[0] if found else None

        site = wait_for("site with 1 miner in /api/sites", site_ready)
        check("/api/sites shows the site after agent push", site is not None)
        if site is None:
            return
        farm_ths = site["total_ths"]
        check("farm hashrate from dashd snapshot (~109.13 TH/s)",
              108.0 < farm_ths < 110.5, f"got {farm_ths}")

        def miner_record():
            _c, data = fetch_json("/api/miners")
            found = [m for m in data.get("miners", [])
                     if m.get("ip") == IP]
            return found[0] if found else None

        record = wait_for("miner record in /api/miners", miner_record)
        check("miner record carries power_w from dashd power_consumption",
              record is not None
              and record.get("power_w") == float(DASHD_POWER_W)
              and record.get("source") == "vnish",
              json.dumps(record)[:300] if record else "no record")

        # -- pool config round-trip, secret never echoed ----------------
        POOL_STATE["value_ths"] = farm_ths * 0.95
        code, created = post_json("/api/pool-config", {
            "site": SITE, "adapter": "generic", "url": POOL_URL,
            "headers": {"Authorization": f"Bearer {POOL_SECRET}"},
            "json_path": "data.hashrate_ths", "unit": "TH/s",
            "notify_gap_pct": 10})
        config = created.get("config") or {}
        check("POST /api/pool-config -> 201, view has names not values",
              code == 201 and config.get("header_names") == ["Authorization"]
              and config.get("headers_set") is True
              and POOL_SECRET not in json.dumps(created),
              f"code {code}: {json.dumps(created)}")
        code, raw_body = fetch("/api/pool-config")
        check("GET /api/pool-config never echoes the secret header",
              code == 200 and POOL_SECRET not in raw_body,
              raw_body[:200])

        def pool_sample():
            _c, data = fetch_json("/api/pool?site="
                                  + urllib.parse.quote(SITE))
            return data.get("latest")

        sample = wait_for("first pool sample", pool_sample, timeout=30.0)
        check("poller samples pool vs farm (gap ~5%, under threshold)",
              sample is not None
              and abs(sample["pool_ths"] - farm_ths * 0.95) < 1.0
              and abs(sample["gap_pct"] - 5.0) < 1.5,
              json.dumps(sample))
        check("poller sent the configured secret header to the pool",
              POOL_STATE["last_auth"] == f"Bearer {POOL_SECRET}",
              str(POOL_STATE["last_auth"]))

        def gap_event():
            _c, data = fetch_json("/api/events?n=50&site="
                                  + urllib.parse.quote(SITE))
            found = [e for e in data.get("events", [])
                     if e.get("type") == "POOL_GAP"]
            return found[0] if found else None

        check("no POOL_GAP while the gap stays ~5%",
              gap_event() is None)

        # -- flip the pool low: POOL_GAP after 2 polls -------------------
        POOL_STATE["value_ths"] = farm_ths * 0.40
        event = wait_for("POOL_GAP event", gap_event, timeout=35.0)
        check("pool at 40% of farm -> POOL_GAP (major) in the event feed",
              event is not None and event.get("severity") == "major",
              json.dumps(event))
        if event:
            print()
            print("Captured POOL_GAP event:")
            print(json.dumps(event, ensure_ascii=False))
        sample = wait_for("low pool sample",
                          lambda: (pool_sample()
                                   if pool_sample()
                                   and pool_sample()["gap_pct"] > 50
                                   else None),
                          timeout=20.0)
        check("latest sample shows the ~60% gap", sample is not None)

        # -- energy accumulates + price is settable ----------------------
        def energy_with_kwh():
            _c, data = fetch_json("/api/energy?days=7")
            return data if data.get("total_kwh", 0) > 0 else None

        energy = wait_for("energy total > 0", energy_with_kwh,
                          timeout=30.0)
        check("energy accumulates > 0 kWh for the dashd miner",
              energy is not None
              and any(m["ip"] == IP and m["kwh"] > 0
                      for m in energy.get("per_miner", [])),
              json.dumps(energy)[:300] if energy else "no energy")
        if energy:
            print()
            print("Captured energy report (excerpt):")
            print(json.dumps({"today": energy["today"],
                              "per_day": energy["per_day"],
                              "per_miner": energy["per_miner"]},
                             ensure_ascii=False))

        code, updated = post_json(
            "/api/settings", {"electricity_price_vnd_kwh": 3000})
        check("POST /api/settings sets the electricity price",
              code == 200
              and updated.get("electricity_price_vnd_kwh") == 3000.0,
              f"code {code}: {json.dumps(updated)}")
        code, energy = fetch_json("/api/energy?days=7")
        check("energy estimates now use 3000 VND/kWh",
              code == 200
              and energy.get("electricity_price_vnd_kwh") == 3000.0
              and energy["today"]["est_cost_vnd"]
              == round(energy["today"]["kwh"] * 3000),
              json.dumps(energy)[:300])
    finally:
        for proc in (agent, cloud, miner):
            if proc is not None:
                proc.terminate()
        for proc in (agent, cloud, miner):
            if proc is not None:
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()


def main() -> int:
    pool_server = start_pool_server()
    try:
        store_level_checks()
        http_level_checks()
    finally:
        pool_server.shutdown()
    print()
    if FAILURES:
        print(f"ENERGY/POOL TEST FAILED: {len(FAILURES)} assertion(s): "
              f"{FAILURES}")
        return 1
    print("ENERGY/POOL TEST PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
