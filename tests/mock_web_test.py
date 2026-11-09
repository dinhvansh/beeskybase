#!/usr/bin/env python3
"""v0.4 end-to-end web test — dashboard + JSON API, no hardware.

Starts tests/mock_watch_miner.py (control-file fake S19 Pro on
127.0.0.1:14029) and the real server (`python -m beesky serve 127.0.0.1
--port 18788 --interval 1`), then asserts with plain urllib:

  * GET /                -> 200, contains "BeeSky" and the brand #F5D800
  * GET /api/miners      -> the mock S19 Pro at ~110 TH/s, status OK
  * GET /api/status      -> miner_count 1, target/interval as configured
  * POST /api/scan       -> 202 {"ok": true}
  * control file flipped to 66 TH/s -> GET /api/events gains a
    HASHRATE_DROP (severity major, drop_pct ~= 40)

Prints PASS lines; exit 1 on failure. Run via tests/run_mock_test_v4.sh
(which appends evidence to tests/RESULTS.md).
"""

import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MINER_PORT = 14029
WEB_PORT = 18788
BASE = f"http://127.0.0.1:{WEB_PORT}"
HEALTHY = {"ghs": 110000.0, "temps": [65, 71, 74], "dead": {}}
DROPPED = {"ghs": 66000.0, "temps": [65, 71, 74], "dead": {}}

# Farm/LAN HTTP must connect directly — ignore any proxy env vars.
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
FAILURES: list[str] = []


def check(label: str, condition: bool, extra: str = "") -> None:
    if condition:
        print(f"PASS: {label}")
    else:
        print(f"FAIL: {label} {extra}")
        FAILURES.append(label)


def fetch(path: str, method: str = "GET") -> tuple[int, str]:
    request = urllib.request.Request(
        BASE + path, method=method, data=b"" if method == "POST" else None)
    with _opener.open(request, timeout=5) as response:
        return response.status, response.read().decode("utf-8")


def fetch_json(path: str, method: str = "GET") -> tuple[int, dict]:
    status, body = fetch(path, method)
    return status, json.loads(body)


def wait_for(label: str, fn, timeout: float = 40.0):
    """Poll *fn* until it returns a truthy value; return it (or None)."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            value = fn()
        except (OSError, urllib.error.URLError, ValueError):
            value = None
        if value:
            return value
        time.sleep(0.4)
    print(f"  (timed out waiting for: {label})")
    return None


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="beesky-web-"))
    control = tmp / "miner.json"
    control.write_text(json.dumps(HEALTHY), encoding="utf-8")

    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    miner = subprocess.Popen(
        [sys.executable, str(ROOT / "tests" / "mock_watch_miner.py"),
         "--port", str(MINER_PORT), "--control", str(control)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    server = subprocess.Popen(
        [sys.executable, "-m", "beesky", "serve", "127.0.0.1",
         "--port", str(WEB_PORT), "--interval", "1", "--timeout", "1.0",
         "--cgminer-port", str(MINER_PORT), "--http-port", "18099"],
        cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True)
    try:
        html = wait_for("dashboard /", lambda: fetch("/")[1])
        check("GET / returns the dashboard", html is not None)
        if html:
            check("dashboard carries the BeeSky brand (name + #F5D800)",
                  "BeeSky" in html and "#F5D800" in html)

        def the_miner():
            _s, data = fetch_json("/api/miners")
            found = [m for m in data.get("miners", [])
                     if m.get("ip") == "127.0.0.1"]
            return found[0] if found else None

        miner_rec = wait_for("miner in /api/miners", the_miner)
        check("GET /api/miners lists the mock miner", miner_rec is not None)
        if miner_rec:
            check("miner record: S19 Pro, ~110 TH/s, 342/342 chips, OK",
                  miner_rec.get("model") == "Antminer S19 Pro"
                  and abs((miner_rec.get("ths") or 0) - 110.0) < 0.6
                  and miner_rec.get("chips_alive") == 342
                  and miner_rec.get("chips_total") == 342
                  and miner_rec.get("status") == "OK"
                  and miner_rec.get("online") is True,
                  json.dumps(miner_rec))

        def status_ready():
            _s, data = fetch_json("/api/status")
            return data if data.get("scan_count", 0) >= 5 else None

        status = wait_for("status after >=5 scans", status_ready)
        check("GET /api/status counts sane (1 miner, target, interval)",
              status is not None
              and status.get("miner_count") == 1
              and status.get("target") == "127.0.0.1"
              and status.get("interval") == 1.0
              and status.get("last_scan_at"),
              json.dumps(status))

        code, payload = fetch_json("/api/scan", method="POST")
        check("POST /api/scan -> 202 {ok: true}",
              code == 202 and payload.get("ok") is True,
              f"{code} {payload}")

        control.write_text(json.dumps(DROPPED), encoding="utf-8")

        def the_drop():
            _s, data = fetch_json("/api/events?n=50")
            found = [e for e in data.get("events", [])
                     if e.get("type") == "HASHRATE_DROP"
                     and e.get("ip") == "127.0.0.1"]
            return found[0] if found else None

        drop = wait_for("HASHRATE_DROP in /api/events", the_drop,
                        timeout=45.0)
        check("hashrate drop phase: /api/events gains HASHRATE_DROP",
              drop is not None)
        if drop:
            pct = (drop.get("data") or {}).get("drop_pct")
            check("drop event: severity major, drop_pct ~= 40",
                  drop.get("severity") == "major"
                  and pct is not None and abs(pct - 40.0) < 0.6,
                  json.dumps(drop))
            print()
            print("Captured drop event:")
            print(json.dumps(drop, ensure_ascii=False))
    finally:
        server.terminate()
        miner.terminate()
        for proc in (server, miner):
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()

    print()
    if FAILURES:
        print(f"WEB TEST FAILED: {len(FAILURES)} assertion(s): {FAILURES}")
        return 1
    print("WEB TEST PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
