#!/usr/bin/env python3
"""v0.5 end-to-end cloud test — agent -> cloud -> multi-site web.

No hardware. Builds the whole shape in subprocesses on 127.0.0.1:

  * `beesky cloud-add-agent --site "Xưởng 1"` mints an agent key
    (parsed from its stdout),
  * `beesky cloud --port 18790` with BEESKY_CLOUD_PASSWORD set,
  * tests/mock_watch_miner.py — control-file fake S19 Pro on :14031,
  * `beesky agent 127.0.0.1 --cloud ... --interval 1` pushing to it.

Asserts with plain urllib (+ a cookie jar for the viewer):

  * ingest with a wrong agent key            -> 401 (and with no key)
  * viewer: /api/sites without login          -> 401
  * viewer: POST /login wrong password        -> 401, no session
  * viewer: POST /login right password        -> session cookie,
    /api/sites works, GET / serves the cloud dashboard (#F5D800)
  * /api/sites shows site "Xưởng 1": 1 miner, ~110 TH/s, online
  * control file flipped to 66 TH/s -> a HASHRATE_DROP (major, ~40%)
    arrives at the cloud's /api/events, tagged with the site
  * /api/miners?site= shows the dropped ~66 TH/s, annotated with site

Prints PASS lines; exit 1 on failure. Run via tests/run_mock_test_v5.sh
(which appends evidence to tests/RESULTS.md).
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
MINER_PORT = 14031
CLOUD_PORT = 18790
BASE = f"http://127.0.0.1:{CLOUD_PORT}"
SITE = "Xưởng 1"
PASSWORD = "mat-khau-test"
HEALTHY = {"ghs": 110000.0, "temps": [65, 71, 74], "dead": {}}
DROPPED = {"ghs": 66000.0, "temps": [65, 71, 74], "dead": {}}

# LAN/cloud HTTP in tests must connect directly — ignore proxy env vars.
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


def wait_for(label: str, fn, timeout: float = 40.0):
    """Poll *fn* until it returns a truthy value; return it (or None)."""
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


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="beesky-cloud-"))
    db = tmp / "cloud.db"
    control = tmp / "miner.json"
    control.write_text(json.dumps(HEALTHY), encoding="utf-8")
    env = {**os.environ, "PYTHONPATH": str(ROOT)}

    # -- mint an agent key through the real CLI -------------------------
    minted = subprocess.run(
        [sys.executable, "-m", "beesky", "cloud-add-agent",
         "--db", str(db), "--site", SITE],
        cwd=ROOT, env=env, capture_output=True, text=True)
    match = re.search(r"BEESKY_AGENT_KEY=(\S+)", minted.stdout)
    check("cloud-add-agent prints a key once", match is not None,
          minted.stdout + minted.stderr)
    if not match:
        return 1
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

        # -- ingest auth ------------------------------------------------
        body = json.dumps({"site": SITE, "ts": time.time(),
                           "miners": []}).encode()
        code, _ = fetch("/api/ingest", opener=_plain, method="POST",
                        data=body, headers={
                            "Authorization": "Bearer wrong-key",
                            "Content-Type": "application/json"})
        check("ingest with a wrong agent key -> 401", code == 401,
              f"got {code}")
        code, _ = fetch("/api/ingest", opener=_plain, method="POST",
                        data=body,
                        headers={"Content-Type": "application/json"})
        check("ingest with no agent key -> 401", code == 401,
              f"got {code}")

        # -- viewer auth --------------------------------------------------
        code, _ = fetch_json("/api/sites", opener=_plain)
        check("viewer /api/sites without login -> 401", code == 401,
              f"got {code}")

        form = urllib.parse.urlencode({"password": "sai-mat-khau"}).encode()
        code, _ = fetch("/login", method="POST", data=form, headers={
            "Content-Type": "application/x-www-form-urlencoded"})
        check("login with wrong password -> 401", code == 401,
              f"got {code}")
        code, _ = fetch_json("/api/sites")
        check("still locked out after wrong password", code == 401,
              f"got {code}")

        form = urllib.parse.urlencode({"password": PASSWORD}).encode()
        code, _ = fetch("/login", method="POST", data=form, headers={
            "Content-Type": "application/x-www-form-urlencoded"})
        check("login with right password -> session (200 after redirect)",
              code == 200, f"got {code}")
        code, sites0 = fetch_json("/api/sites")
        ours0 = [s for s in sites0.get("sites", []) if s["site"] == SITE]
        check("/api/sites works with the session cookie; site registered",
              code == 200 and len(ours0) == 1
              and ours0[0]["miner_count"] == 0,
              json.dumps(sites0, ensure_ascii=False))

        code, html = fetch("/")
        check("GET / serves the cloud dashboard (brand #F5D800)",
              code == 200 and "BeeSky" in html and "#F5D800" in html)

        # -- agent pushes -------------------------------------------------
        agent = subprocess.Popen(
            [sys.executable, "-m", "beesky", "agent", "127.0.0.1",
             "--cloud", BASE, "--key", agent_key, "--site", SITE,
             "--interval", "1", "--timeout", "1.0",
             "--cgminer-port", str(MINER_PORT), "--http-port", "18099"],
            cwd=ROOT, env=env, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True)

        def site_ready():
            _c, data = fetch_json("/api/sites")
            found = [s for s in data.get("sites", [])
                     if s["site"] == SITE and s["miner_count"] == 1]
            return found[0] if found else None

        site = wait_for("site with 1 miner in /api/sites", site_ready)
        check("/api/sites shows the site after agent push", site is not None)
        if site:
            check("site summary: ~110 TH/s, 1 OK / 0 problems, online",
                  abs((site.get("total_ths") or 0) - 110.0) < 0.6
                  and site.get("ok_count") == 1
                  and site.get("problem_count") == 0
                  and site.get("online") is True,
                  json.dumps(site, ensure_ascii=False))

        # Let the agent's local engine build its >=3-sample baseline.
        time.sleep(5)

        # -- drop phase: event must travel agent -> cloud -----------------
        control.write_text(json.dumps(DROPPED), encoding="utf-8")
        events_path = ("/api/events?n=50&site="
                       + urllib.parse.quote(SITE))

        def the_drop():
            _c, data = fetch_json(events_path)
            found = [e for e in data.get("events", [])
                     if e.get("type") == "HASHRATE_DROP"]
            return found[0] if found else None

        drop = wait_for("HASHRATE_DROP at cloud /api/events", the_drop,
                        timeout=45.0)
        check("hashrate drop: HASHRATE_DROP arrives at the cloud",
              drop is not None)
        if drop:
            pct = (drop.get("data") or {}).get("drop_pct")
            check("drop event: severity major, drop_pct ~= 40, site tag",
                  drop.get("severity") == "major"
                  and pct is not None and abs(pct - 40.0) < 0.6
                  and drop.get("site") == SITE,
                  json.dumps(drop, ensure_ascii=False))
            print()
            print("Captured cloud event:")
            print(json.dumps(drop, ensure_ascii=False))

        def dropped_miner():
            _c, data = fetch_json(
                "/api/miners?site=" + urllib.parse.quote(SITE))
            found = [m for m in data.get("miners", [])
                     if m.get("ip") == "127.0.0.1"]
            if found and abs((found[0].get("ths") or 0) - 66.0) < 0.6:
                return found[0]
            return None

        rec = wait_for("dropped miner in /api/miners?site=", dropped_miner)
        check("/api/miners?site= shows ~66 TH/s, record annotated with site",
              rec is not None and rec.get("site") == SITE,
              json.dumps(rec, ensure_ascii=False) if rec else "")
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

    print()
    if FAILURES:
        print(f"CLOUD TEST FAILED: {len(FAILURES)} assertion(s): {FAILURES}")
        return 1
    print("CLOUD TEST PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
