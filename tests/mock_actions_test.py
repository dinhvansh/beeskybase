#!/usr/bin/env python3
"""v0.6 end-to-end remote-actions test — viewer -> cloud -> agent -> miner.

No hardware. Builds the full command path in subprocesses on 127.0.0.1:

  * one `beesky cloud` (:18791, password set) with three minted agents,
  * site "Xưởng 1": tests/mock_watch_miner.py (cgminer) on :14032 —
    its privileged `restart` RPC is observable via a state file,
  * site "Xưởng 2": tests/mock_dashd.py (VNish dashd) on :18082 —
    implements the api-doc action endpoints, records every hit,
  * site "Xưởng 3": tests/mock_bitmain.py (stock) on :18083 —
    /cgi-bin/reboot.cgi records hits,
  * one `beesky agent --interval 1` per site.

Asserts:

  * agent command poll with no/wrong key            -> 401
  * viewer POST /api/commands without login         -> 401
  * ownership: agent A cannot claim agent B's pending command, and
    POSTing a result for it with A's key            -> 403
  * reboot, cgminer source: command finishes `done`; the mock's state
    file proves the restart RPC arrived
  * reboot with the cgminer API read-only (control flag): `failed`,
    result carries the miner's own "Access denied"
  * switch_pool to a cgminer miner: `failed`, "not supported"
  * reboot, dashd source: `done`; mock recorded POST /system/reboot
  * switch_pool {pool_id} on dashd: `done`; mock activated slot 1
  * switch_pool {url,user} on dashd: `done` via GET/POST /settings;
    mock's pool slot 0 now carries the new url
  * reboot, stock source: `done`; mock recorded reboot.cgi hit
  * cloud dashboard HTML carries the action UI ("Khởi động lại",
    "Lệnh gần đây"); GET /api/commands shows the history

Prints PASS lines; exit 1 on failure. Run via tests/run_mock_test_v6.sh
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
CLOUD_PORT = 18791
BASE = f"http://127.0.0.1:{CLOUD_PORT}"
CGMINER_PORT = 14032
DASHD_PORT = 18082
BITMAIN_PORT = 18083
SITE1, SITE2, SITE3 = "Xưởng 1", "Xưởng 2", "Xưởng 3"
PASSWORD = "mat-khau-test"
HEALTHY = {"ghs": 110000.0, "temps": [65, 71, 74], "dead": {}}

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


def fetch_json(path: str, opener=_opener,
               headers: dict | None = None) -> tuple[int, dict]:
    status, body = fetch(path, opener=opener, headers=headers)
    try:
        return status, json.loads(body)
    except json.JSONDecodeError:
        return status, {}


def post_json(path: str, payload: dict, opener=_opener,
              headers: dict | None = None) -> tuple[int, dict]:
    merged = {"Content-Type": "application/json"}
    merged.update(headers or {})
    status, body = fetch(path, opener=opener, method="POST",
                         data=json.dumps(payload).encode(), headers=merged)
    try:
        return status, json.loads(body)
    except json.JSONDecodeError:
        return status, {}


def wait_for(label: str, fn, timeout: float = 60.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            value = fn()
        except Exception:  # noqa: BLE001 — servers may not be up yet
            value = None
        if value:
            return value
        time.sleep(0.4)
    print(f"  (timed out waiting for: {label})")
    return None


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def command_by_id(cmd_id: int) -> dict | None:
    _code, data = fetch_json("/api/commands?n=100")
    for cmd in data.get("commands", []):
        if cmd.get("id") == cmd_id:
            return cmd
    return None


def wait_command(cmd_id: int, *statuses: str, timeout: float = 60.0):
    def probe():
        cmd = command_by_id(cmd_id)
        return cmd if cmd and cmd.get("status") in statuses else None
    return wait_for(f"command #{cmd_id} -> {statuses}", probe, timeout)


def create_command(site: str, ctype: str, payload: dict | None = None,
                   ip: str = "127.0.0.1") -> tuple[int, dict]:
    return post_json("/api/commands",
                     {"site": site, "ip": ip, "type": ctype,
                      "payload": payload or {}})


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="beesky-actions-"))
    db = tmp / "cloud.db"
    control = tmp / "miner.json"
    control.write_text(json.dumps(HEALTHY), encoding="utf-8")
    cgminer_state = Path(str(control) + ".state.json")
    dashd_state = tmp / "dashd-state.json"
    bitmain_state = tmp / "bitmain-state.json"
    env = {**os.environ, "PYTHONPATH": str(ROOT)}

    # -- mint three agent keys through the real CLI ----------------------
    keys: dict[str, str] = {}
    for site in (SITE1, SITE2, SITE3):
        minted = subprocess.run(
            [sys.executable, "-m", "beesky", "cloud-add-agent",
             "--db", str(db), "--site", site],
            cwd=ROOT, env=env, capture_output=True, text=True)
        match = re.search(r"BEESKY_AGENT_KEY=(\S+)", minted.stdout)
        if not match:
            check(f"cloud-add-agent mints a key for {site}", False,
                  minted.stdout + minted.stderr)
            return 1
        keys[site] = match.group(1)
    check("cloud-add-agent mints keys for all three sites", True)

    cloud_env = {**env, "BEESKY_CLOUD_PASSWORD": PASSWORD}
    cloud = subprocess.Popen(
        [sys.executable, "-m", "beesky", "cloud", "--port", str(CLOUD_PORT),
         "--db", str(db)],
        cwd=ROOT, env=cloud_env, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True)
    procs: list[subprocess.Popen] = [cloud]

    def spawn_agent(site: str, extra: list[str]) -> subprocess.Popen:
        proc = subprocess.Popen(
            [sys.executable, "-m", "beesky", "agent", "127.0.0.1",
             "--cloud", BASE, "--key", keys[site], "--site", site,
             "--interval", "1", "--timeout", "1.0"] + extra,
            cwd=ROOT, env=env, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True)
        procs.append(proc)
        return proc

    try:
        up = wait_for("cloud login page",
                      lambda: fetch("/login", opener=_plain)[0] == 200
                      or None)
        check("cloud starts and serves /login", up is not None)

        # -- agent-side auth ---------------------------------------------
        code, _ = fetch("/api/agent/commands", opener=_plain)
        check("agent command poll with no key -> 401", code == 401,
              f"got {code}")
        code, _ = fetch("/api/agent/commands", opener=_plain, headers={
            "Authorization": "Bearer wrong-key"})
        check("agent command poll with wrong key -> 401", code == 401,
              f"got {code}")

        # -- viewer auth ---------------------------------------------------
        code, _resp = post_json("/api/commands",
                                {"site": SITE1, "ip": "127.0.0.1",
                                 "type": "reboot", "payload": {}},
                                opener=_plain)
        check("viewer POST /api/commands without login -> 401",
              code == 401, f"got {code}")

        form = urllib.parse.urlencode({"password": PASSWORD}).encode()
        code, _ = fetch("/login", method="POST", data=form, headers={
            "Content-Type": "application/x-www-form-urlencoded"})
        check("viewer login with the right password", code == 200,
              f"got {code}")

        # -- ownership, before site 2's agent exists -----------------------
        code, resp = create_command(SITE2, "reboot")
        check("viewer creates a reboot command for site 2 -> 201",
              code == 201, f"got {code}: {resp}")
        cmd_b = (resp.get("command") or {}).get("id")
        if not cmd_b:
            return 1
        check("new command starts out pending",
              resp["command"].get("status") == "pending",
              json.dumps(resp, ensure_ascii=False))

        code, resp = fetch_json("/api/agent/commands?limit=5",
                                opener=_plain,
                                headers={"Authorization":
                                         f"Bearer {keys[SITE1]}"})
        claimed_by_a = [c for c in resp.get("commands", [])
                        if c.get("id") == cmd_b]
        check("agent A cannot claim agent B's command",
              code == 200 and not claimed_by_a,
              json.dumps(resp, ensure_ascii=False))

        code, resp = post_json(
            f"/api/agent/commands/{cmd_b}/result",
            {"status": "done", "result": "forged by agent A"},
            opener=_plain,
            headers={"Authorization": f"Bearer {keys[SITE1]}"})
        check("agent A finishing agent B's command -> 403", code == 403,
              f"got {code}: {resp}")
        still = command_by_id(cmd_b)
        check("B's command is still pending after A's attempts",
              bool(still) and still.get("status") == "pending",
              json.dumps(still, ensure_ascii=False))

        # -- dashboard carries the action UI --------------------------------
        code, html = fetch("/")
        check("dashboard HTML has the reboot button + commands panel",
              code == 200 and "Khởi động lại" in html
              and "Lệnh gần đây" in html)

        # -- site 2: dashd agent claims B's command and reboots -------------
        dashd = subprocess.Popen(
            [sys.executable, str(ROOT / "tests" / "mock_dashd.py"),
             "127.0.0.1", str(DASHD_PORT)],
            env={**env, "BEESKY_MOCK_DASHD_STATE": str(dashd_state)},
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        procs.append(dashd)
        spawn_agent(SITE2, ["--http-port", str(DASHD_PORT),
                            "--cgminer-port", "14099",
                            "--api-key", "mock-api-key"])

        done_b = wait_command(cmd_b, "done", "failed")
        check("site 2 command finishes", done_b is not None)
        if done_b:
            check("dashd reboot: status done, result from /system/reboot",
                  done_b.get("status") == "done"
                  and "dashd accepted reboot" in (done_b.get("result") or ""),
                  json.dumps(done_b, ensure_ascii=False))
            print()
            print("Captured dashd reboot command:")
            print(json.dumps(done_b, ensure_ascii=False))
        state = read_json(dashd_state)
        check("dashd mock recorded exactly one POST /system/reboot",
              len(state.get("reboots") or []) == 1,
              json.dumps(state, ensure_ascii=False))

        # -- site 2: switch_pool by slot, then by url/user -------------------
        code, resp = create_command(SITE2, "switch_pool", {"pool_id": 1})
        cmd_sp = (resp.get("command") or {}).get("id")
        done_sp = wait_command(cmd_sp, "done", "failed") if cmd_sp else None
        check("dashd switch_pool {pool_id: 1} finishes done",
              bool(done_sp) and done_sp.get("status") == "done",
              json.dumps(done_sp, ensure_ascii=False))
        state = read_json(dashd_state)
        check("dashd mock activated pool slot 1",
              state.get("active_pool") == 1
              and (state.get("switch_pools") or [{}])[-1].get("pool_id") == 1,
              json.dumps(state, ensure_ascii=False))

        new_url = "stratum+tcp://newpool.example.com:4444"
        code, resp = create_command(
            SITE2, "switch_pool",
            {"url": new_url, "user": "anh.worker9", "password": "pw9"})
        cmd_su = (resp.get("command") or {}).get("id")
        done_su = wait_command(cmd_su, "done", "failed") if cmd_su else None
        check("dashd switch_pool {url,user} finishes done via /settings",
              bool(done_su) and done_su.get("status") == "done",
              json.dumps(done_su, ensure_ascii=False))
        state = read_json(dashd_state)
        pools = state.get("pools") or []
        check("dashd mock pool slot 0 now carries the new url/user",
              bool(state.get("settings_posts"))
              and pools and pools[0].get("url") == new_url
              and pools[0].get("user") == "anh.worker9"
              and state.get("active_pool") == 0,
              json.dumps(state, ensure_ascii=False))

        # -- site 1: cgminer agent -------------------------------------------
        miner = subprocess.Popen(
            [sys.executable, str(ROOT / "tests" / "mock_watch_miner.py"),
             "--port", str(CGMINER_PORT), "--control", str(control)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        procs.append(miner)
        spawn_agent(SITE1, ["--cgminer-port", str(CGMINER_PORT),
                            "--http-port", "18099"])

        def site1_ready():
            _c, data = fetch_json("/api/sites")
            found = [s for s in data.get("sites", [])
                     if s["site"] == SITE1 and s["miner_count"] == 1]
            return found[0] if found else None

        check("site 1 agent reports its cgminer miner",
              wait_for("site 1 in /api/sites", site1_ready) is not None)

        code, resp = create_command(SITE1, "reboot")
        cmd_r = (resp.get("command") or {}).get("id")
        done_r = wait_command(cmd_r, "done", "failed") if cmd_r else None
        check("cgminer reboot finishes done",
              bool(done_r) and done_r.get("status") == "done",
              json.dumps(done_r, ensure_ascii=False))
        if done_r:
            print()
            print("Captured cgminer reboot command:")
            print(json.dumps(done_r, ensure_ascii=False))
        mstate = read_json(cgminer_state)
        check("cgminer mock recorded the restart RPC",
              mstate.get("restarts") == 1,
              json.dumps(mstate, ensure_ascii=False))

        # read-only API: the same command must fail honestly
        control.write_text(json.dumps(
            {**HEALTHY, "api_writable": False}), encoding="utf-8")
        code, resp = create_command(SITE1, "reboot")
        cmd_ro = (resp.get("command") or {}).get("id")
        done_ro = wait_command(cmd_ro, "done", "failed") if cmd_ro else None
        check("cgminer reboot on a read-only API -> failed",
              bool(done_ro) and done_ro.get("status") == "failed",
              json.dumps(done_ro, ensure_ascii=False))
        check("failure result carries the miner's 'Access denied'",
              bool(done_ro)
              and "Access denied" in (done_ro.get("result") or ""),
              json.dumps(done_ro, ensure_ascii=False))
        control.write_text(json.dumps(HEALTHY), encoding="utf-8")

        # switch_pool is honestly unsupported for cgminer
        code, resp = create_command(SITE1, "switch_pool", {"pool_id": 1})
        cmd_ns = (resp.get("command") or {}).get("id")
        done_ns = wait_command(cmd_ns, "done", "failed") if cmd_ns else None
        check("switch_pool to a cgminer miner -> failed 'not supported'",
              bool(done_ns) and done_ns.get("status") == "failed"
              and "not supported" in (done_ns.get("result") or ""),
              json.dumps(done_ns, ensure_ascii=False))

        # -- site 3: stock agent ----------------------------------------------
        bitmain = subprocess.Popen(
            [sys.executable, str(ROOT / "tests" / "mock_bitmain.py"),
             "127.0.0.1", str(BITMAIN_PORT)],
            env={**env, "BEESKY_MOCK_BITMAIN_STATE": str(bitmain_state)},
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        procs.append(bitmain)
        spawn_agent(SITE3, ["--http-port", str(BITMAIN_PORT),
                            "--cgminer-port", "14098"])

        def site3_ready():
            _c, data = fetch_json("/api/sites")
            found = [s for s in data.get("sites", [])
                     if s["site"] == SITE3 and s["miner_count"] == 1]
            return found[0] if found else None

        check("site 3 agent reports its stock miner",
              wait_for("site 3 in /api/sites", site3_ready) is not None)

        code, resp = create_command(SITE3, "reboot")
        cmd_s = (resp.get("command") or {}).get("id")
        done_s = wait_command(cmd_s, "done", "failed") if cmd_s else None
        check("stock reboot finishes done",
              bool(done_s) and done_s.get("status") == "done",
              json.dumps(done_s, ensure_ascii=False))
        bstate = read_json(bitmain_state)
        check("stock mock recorded the reboot.cgi hit",
              len(bstate.get("reboots") or []) == 1,
              json.dumps(bstate, ensure_ascii=False))

        # -- history ------------------------------------------------------------
        code, data = fetch_json(
            "/api/commands?n=50&site=" + urllib.parse.quote(SITE1))
        types1 = [c.get("type") for c in data.get("commands", [])]
        check("GET /api/commands?site= returns site 1 history newest-first",
              code == 200 and types1 == ["switch_pool", "reboot", "reboot"],
              json.dumps(data, ensure_ascii=False))
    finally:
        for proc in procs:
            proc.terminate()
        for proc in procs:
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()

    print()
    if FAILURES:
        print(f"ACTIONS TEST FAILED: {len(FAILURES)} assertion(s): {FAILURES}")
        return 1
    print("ACTIONS TEST PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
