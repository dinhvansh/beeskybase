#!/usr/bin/env python3
"""v0.8 end-to-end test — heat map + repair history.

Two layers, no hardware:

  * Store level (in-process): problem events ingested through
    ``CloudStore.add_events`` become ``auto_event`` repair rows,
    deduplicated to one identical (site, ip, title) row per hour;
    non-problem event types (HASHRATE_DROP, BACK_ONLINE) do not.

  * HTTP level (subprocesses on 127.0.0.1, the v0.5 cloud shape):
    `beesky cloud` (:18792, password set), the control-file fake
    S19 Pro (:14033) and `beesky agent --interval 1`. Assertions:
      - GET/POST /api/repairs without login -> 401
      - cloud + local dashboards carry the heat-map section and the
        JS colour thresholds (heatColor, >= 90 red band)
      - flipping the miner to dead chips makes a CHIPS_LOST event
        arrive at the cloud AND an auto repair row appear in
        /api/repairs for that miner
      - a manual POST /api/repairs (logged in) is stored and listed
        with its cost_vnd + technician, kind "manual"

Prints PASS lines; exit 1 on failure. Run via
tests/run_mock_test_v8.sh (appends evidence to tests/RESULTS.md).
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

MINER_PORT = 14033
CLOUD_PORT = 18792
BASE = f"http://127.0.0.1:{CLOUD_PORT}"
SITE = "Xưởng 1"
IP = "127.0.0.1"
PASSWORD = "mat-khau-test"
HEALTHY = {"ghs": 110000.0, "temps": [65, 71, 74], "dead": {}}
DEAD_CHIPS = {"ghs": 107000.0, "temps": [65, 71, 74],
              "dead": {"2": [10, 55, 114]}}

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
# store level: auto-log rule + dedupe
# ----------------------------------------------------------------------

def store_level_checks() -> None:
    from beesky.cloud.store import CloudStore

    tmp = Path(tempfile.mkdtemp(prefix="beesky-repairs-store-"))
    store = CloudStore(str(tmp / "store.db"))
    agent_id = store.create_agent(SITE, "store-test-key")
    now = time.time()

    def ev(etype, ts, detail="chi tiết"):
        return {"ts": ts, "type": etype, "severity": "major", "ip": IP,
                "model": "Antminer S19 Pro", "detail": detail, "data": {}}

    store.add_events(agent_id, SITE, [ev("CHIPS_LOST", now)])
    rows = store.list_repairs(site=SITE, ip=IP)
    check("store: CHIPS_LOST event becomes an auto repair row",
          len(rows) == 1 and rows[0]["kind"] == "auto_event"
          and rows[0]["title"] == "CHIPS_LOST"
          and rows[0]["site"] == SITE and rows[0]["ip"] == IP,
          json.dumps(rows, ensure_ascii=False))

    store.add_events(agent_id, SITE, [ev("CHIPS_LOST", now + 60)])
    check("store: identical auto row within 1h is deduplicated",
          len(store.list_repairs(site=SITE, ip=IP)) == 1)

    store.add_events(agent_id, SITE, [ev("CHIPS_LOST", now + 3700)])
    check("store: same event after 1h logs a fresh auto row",
          len(store.list_repairs(site=SITE, ip=IP)) == 2)

    for etype in ("OVER_TEMP", "CHAIN_DOWN", "OFFLINE"):
        store.add_events(agent_id, SITE, [ev(etype, now + 3800)])
    store.add_events(agent_id, SITE, [ev("HASHRATE_DROP", now + 3800),
                                      ev("BACK_ONLINE", now + 3800)])
    titles = {r["title"] for r in store.list_repairs(site=SITE, ip=IP)}
    check("store: OVER_TEMP/CHAIN_DOWN/OFFLINE auto-log; "
          "HASHRATE_DROP/BACK_ONLINE do not",
          titles == {"CHIPS_LOST", "OVER_TEMP", "CHAIN_DOWN", "OFFLINE"},
          str(titles))
    store.close()


# ----------------------------------------------------------------------
# HTTP level: cloud + agent + mock miner
# ----------------------------------------------------------------------

def http_level_checks() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="beesky-repairs-"))
    db = tmp / "cloud.db"
    control = tmp / "miner.json"
    control.write_text(json.dumps(HEALTHY), encoding="utf-8")
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

    cloud_env = {**env, "BEESKY_CLOUD_PASSWORD": PASSWORD}
    cloud = subprocess.Popen(
        [sys.executable, "-m", "beesky", "cloud", "--port", str(CLOUD_PORT),
         "--db", str(db)],
        cwd=ROOT, env=cloud_env, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True)
    miner = subprocess.Popen(
        [sys.executable, str(ROOT / "tests" / "mock_watch_miner.py"),
         "--port", str(MINER_PORT), "--control", str(control)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    agent = None
    try:
        up = wait_for("cloud login page",
                      lambda: fetch("/login", opener=_plain)[0] == 200
                      or None)
        check("cloud starts and serves /login", up is not None)

        # -- repairs endpoints are login-gated --------------------------
        code, _ = fetch_json("/api/repairs", opener=_plain)
        check("GET /api/repairs without login -> 401", code == 401,
              f"got {code}")
        code, _ = post_json("/api/repairs",
                            {"site": SITE, "ip": IP, "title": "x"},
                            opener=_plain)
        check("POST /api/repairs without login -> 401", code == 401,
              f"got {code}")

        form = urllib.parse.urlencode({"password": PASSWORD}).encode()
        code, _ = fetch("/login", method="POST", data=form, headers={
            "Content-Type": "application/x-www-form-urlencoded"})
        check("login with right password -> session", code == 200,
              f"got {code}")
        code, empty = fetch_json("/api/repairs")
        check("GET /api/repairs with session -> 200, empty at first",
              code == 200 and empty.get("repairs") == [],
              json.dumps(empty, ensure_ascii=False))

        # -- heat map present in both dashboards -------------------------
        code, html = fetch("/")
        check("cloud dashboard: heat-map section + colour thresholds",
              code == 200 and "Bản đồ nhiệt" in html
              and 'id="heatmap"' in html and "heatColor" in html
              and "t < 60" in html and "t < 90" in html
              and "#8a1f1a" in html,
              f"code {code}")
        local_html = (ROOT / "beesky" / "web" / "dashboard.html") \
            .read_text(encoding="utf-8")
        check("local web dashboard: heat-map section + colour thresholds",
              "Bản đồ nhiệt" in local_html and 'id="heatmap"' in local_html
              and "heatColor" in local_html and "t < 60" in local_html
              and "t < 90" in local_html and "#8a1f1a" in local_html)

        # -- agent pushes; miner healthy --------------------------------
        agent = subprocess.Popen(
            [sys.executable, "-m", "beesky", "agent", "127.0.0.1",
             "--cloud", BASE, "--key", agent_key, "--site", SITE,
             "--interval", "1", "--timeout", "1.0",
             "--cgminer-port", str(MINER_PORT), "--http-port", "18097"],
            cwd=ROOT, env=env, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True)

        def site_ready():
            _c, data = fetch_json("/api/sites")
            found = [s for s in data.get("sites", [])
                     if s["site"] == SITE and s["miner_count"] == 1]
            return found[0] if found else None

        site = wait_for("site with 1 miner in /api/sites", site_ready)
        check("/api/sites shows the site after agent push", site is not None)
        time.sleep(4)  # let the agent engine build its chain baseline

        # -- dead chips: CHIPS_LOST event -> auto repair row --------------
        control.write_text(json.dumps(DEAD_CHIPS), encoding="utf-8")
        events_path = ("/api/events?n=50&site="
                       + urllib.parse.quote(SITE))

        def the_event():
            _c, data = fetch_json(events_path)
            found = [e for e in data.get("events", [])
                     if e.get("type") == "CHIPS_LOST"]
            return found[0] if found else None

        event = wait_for("CHIPS_LOST at cloud /api/events", the_event,
                         timeout=45.0)
        check("dead chips: CHIPS_LOST event arrives at the cloud",
              event is not None)

        repairs_path = ("/api/repairs?site=" + urllib.parse.quote(SITE)
                        + "&ip=" + IP)

        def the_auto_row():
            _c, data = fetch_json(repairs_path)
            found = [r for r in data.get("repairs", [])
                     if r.get("kind") == "auto_event"
                     and r.get("title") == "CHIPS_LOST"]
            return found[0] if found else None

        auto_row = wait_for("auto repair row in /api/repairs",
                            the_auto_row, timeout=20.0)
        check("CHIPS_LOST also lands in repair history as auto_event",
              auto_row is not None)
        if auto_row:
            check("auto row: site/ip keyed, no cost/technician",
                  auto_row.get("site") == SITE
                  and auto_row.get("ip") == IP
                  and auto_row.get("cost_vnd") is None
                  and auto_row.get("technician") is None,
                  json.dumps(auto_row, ensure_ascii=False))
            print()
            print("Captured auto repair row:")
            print(json.dumps(auto_row, ensure_ascii=False))

        # -- manual entry --------------------------------------------------
        code, created = post_json("/api/repairs", {
            "site": SITE, "ip": IP,
            "title": "Thay board 2",
            "detail": "Board 2 chết 3 chip — đã thay board, test lại đạt",
            "cost_vnd": 1500000, "technician": "Tuấn"})
        manual = created.get("repair") or {}
        check("POST /api/repairs (logged in) -> 201 manual row",
              code == 201 and manual.get("kind") == "manual"
              and manual.get("title") == "Thay board 2",
              f"code {code}: {json.dumps(created, ensure_ascii=False)}")

        code, listing = fetch_json(repairs_path)
        manuals = [r for r in listing.get("repairs", [])
                   if r.get("kind") == "manual"]
        check("manual row listed with cost_vnd + technician",
              code == 200 and len(manuals) == 1
              and manuals[0].get("cost_vnd") == 1500000
              and manuals[0].get("technician") == "Tuấn",
              json.dumps(listing, ensure_ascii=False))
        if manuals:
            print()
            print("Captured manual repair row:")
            print(json.dumps(manuals[0], ensure_ascii=False))

        code, bad = post_json("/api/repairs",
                              {"site": SITE, "ip": IP, "title": "  "})
        check("POST /api/repairs with blank title -> 400", code == 400,
              f"got {code}")
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
    store_level_checks()
    http_level_checks()
    print()
    if FAILURES:
        print(f"REPAIRS TEST FAILED: {len(FAILURES)} assertion(s): "
              f"{FAILURES}")
        return 1
    print("REPAIRS TEST PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
