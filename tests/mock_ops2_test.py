#!/usr/bin/env python3
"""v0.29 VNish ops tail test — docs/vnish-ops-mapping.md.

No hardware. Two loopback mocks:

  * tests/mock_dashd.py on 127.0.0.1:18093 — VNish dashd serving
    the api-doc tail endpoints (mining pause/resume/restart,
    locate-miner, throttle, autotune resets, apikeys,
    perf-summary). Every hit lands in the BEESKY_MOCK_DASHD_STATE
    file WITH the winning auth kind, so the tests assert the
    request shape (path / body / auth header), not just success.
    Password "mock-pw", API key "mock-api-key".
  * tests/mock_bitmain.py on 127.0.0.1:18094 — stock firmware, for
    the honest not-supported failures + a stock diagnostic bundle.

Asserts the new payload contracts (JobError before any I/O),
per-action success against the contract mock, verbatim refusal
propagation, the locate state passthrough, the SaveConfigResult
flags, the settings round-trips (preset + password), and the
diagnostic-report files. Prints PASS lines; exit 1 on failure.
"""

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from beesky.core import actions, ops  # noqa: E402

DASHD_PORT = 18093
STOCK_PORT = 18094
DEAD_HTTP = 18099
DEAD_RPC = 14099

API_KEY_SET = [{"label": "Key", "api_key": "mock-api-key",
                "type": "vnish"}]
PASSWORD_SET = [{"label": "VNish", "user": "root",
                 "password": "mock-pw", "type": "vnish"}]
WRONG_SET = [{"label": "Sai", "user": "root", "password": "sai-pw",
              "type": "vnish"}]
NEW_KEY = "k" * 32

FAILURES: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        print(f"PASS {name}")
    else:
        print(f"FAIL {name} :: {detail}")
        FAILURES.append(name)


def _wait_port(port: int, timeout: float = 10.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.3):
                return True
        except OSError:
            time.sleep(0.1)
    return False


def _spawn(args: list[str], env_extra: dict) -> subprocess.Popen:
    env = {**os.environ, "PYTHONPATH": str(ROOT), **env_extra}
    return subprocess.Popen(
        [sys.executable, *args], cwd=ROOT, env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _run_cli(job_path: Path) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    return subprocess.run(
        [sys.executable, "-m", "beesky", "ops", "--job", str(job_path)],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)


def _run_job(doc: dict):
    events: list[dict] = []
    job = ops.validate_job(doc)
    summary = ops.run_job(job, events.append)
    return events, summary


def _creds(tmp: Path, name: str, sets: list) -> str:
    path = tmp / name
    path.write_text(json.dumps(sets), encoding="utf-8")
    return str(path)


def _state(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _dashd_job(tmp: Path, task_type: str, creds_name=None, sets=None,
               payload=None) -> dict:
    doc = {"type": task_type, "targets": ["127.0.0.1"],
           "http_port": DASHD_PORT, "cgminer_port": DEAD_RPC}
    if payload is not None:
        doc["payload"] = payload
    if sets is not None:
        doc["creds_file"] = _creds(tmp, creds_name, sets)
    return doc


# ---------------------------------------------------------------------------
# validation: the tail's payload contracts fail loud before any I/O
# ---------------------------------------------------------------------------

def test_validation(tmp: Path) -> None:
    bad = {
        "throttle missing percent": {
            "type": "throttle", "targets": ["127.0.0.1"], "payload": {}},
        "throttle percent 10 (below the doc range)": {
            "type": "throttle", "targets": ["127.0.0.1"],
            "payload": {"percent": 10}},
        "throttle percent 101": {
            "type": "throttle", "targets": ["127.0.0.1"],
            "payload": {"percent": 101}},
        "throttle percent bool": {
            "type": "throttle", "targets": ["127.0.0.1"],
            "payload": {"percent": True}},
        "apikey short key": {
            "type": "configure_api_key", "targets": ["127.0.0.1"],
            "payload": {"key": "short"}},
        "apikey bad operation": {
            "type": "configure_api_key", "targets": ["127.0.0.1"],
            "payload": {"operation": "rotate", "key": NEW_KEY}},
        "set_preset empty": {
            "type": "set_preset", "targets": ["127.0.0.1"],
            "payload": {"preset": "  "}},
        "change_password empty": {
            "type": "change_password", "targets": ["127.0.0.1"],
            "payload": {"new_password": ""}},
        "diagnostic missing report_dir": {
            "type": "diagnostic_report", "targets": ["127.0.0.1"],
            "payload": {}},
        "reset restart not bool": {
            "type": "reset_autotune_all", "targets": ["127.0.0.1"],
            "payload": {"restart": "yes"}},
    }
    for name, doc in bad.items():
        try:
            ops.validate_job(doc)
        except ops.JobError:
            check(f"validation: {name} -> JobError", True)
        else:
            check(f"validation: {name} -> JobError", False,
                  "validate_job accepted it")

    job_path = tmp / "bad-throttle.json"
    job_path.write_text(json.dumps(bad["throttle percent 10 "
                                     "(below the doc range)"]),
                        encoding="utf-8")
    proc = _run_cli(job_path)
    check("validation: throttle job via CLI -> exit 2, empty stdout",
          proc.returncode == 2 and proc.stdout.strip() == "",
          f"rc={proc.returncode} out={proc.stdout[:60]!r}")


# ---------------------------------------------------------------------------
# the bodyless mining actions + find-miner
# ---------------------------------------------------------------------------

def test_mining_actions(tmp: Path, dashd_state: Path) -> None:
    events, _ = _run_job(_dashd_job(tmp, "pause_mining", "k.json",
                                    API_KEY_SET))
    state = _state(dashd_state)
    hits = [h for h in state.get("mining_posts", [])
            if h["path"] == "/api/v1/mining/pause"]
    check("pause_mining (api-key set): ok + POST /mining/pause "
          "carried the x-api-key header",
          events[1]["ok"] is True and hits
          and hits[-1]["auth"] == "apikey",
          f"{events[1]} / {hits}")

    events, _ = _run_job(_dashd_job(tmp, "resume_mining", "p.json",
                                    PASSWORD_SET))
    state = _state(dashd_state)
    hits = [h for h in state.get("mining_posts", [])
            if h["path"] == "/api/v1/mining/resume"]
    check("resume_mining (password set): ok + bearer JWT auth",
          events[1]["ok"] is True and hits
          and hits[-1]["auth"] == "bearer",
          f"{events[1]} / {hits}")

    events, _ = _run_job(_dashd_job(tmp, "restart_mining", "k.json",
                                    API_KEY_SET))
    state = _state(dashd_state)
    check("restart_mining: ok + POST /mining/restart recorded",
          events[1]["ok"] is True
          and any(h["path"] == "/api/v1/mining/restart"
                  for h in state.get("mining_posts", [])),
          f"{events[1]} / {state.get('mining_posts')}")

    before = len(_state(dashd_state).get("mining_posts", []))
    events, _ = _run_job(_dashd_job(tmp, "pause_mining", "w.json",
                                    WRONG_SET))
    check("pause_mining (wrong password): honest 401 failure, "
          "nothing executed",
          events[1]["ok"] is False and "401" in events[1]["message"]
          and len(_state(dashd_state).get("mining_posts", [])) == before,
          f"{events[1]}")

    # Verbatim refusal propagation at the actions layer: a bad API
    # key draws the device's own err text into the failure message.
    ok, message = actions.execute(
        "127.0.0.1", "vnish", "pause_mining", None,
        {"api_key": "wrong-key", "http_port": DASHD_PORT,
         "timeout": 2.0})
    check("actions layer: device refusal surfaces verbatim "
          "(HTTP 401 + its err text)",
          ok is False and "401" in message and "unauthorized" in message,
          message)

    # find-miner: NO creds at all — the doc declares no auth for
    # /locate-miner. The mock toggles; the messages must report the
    # device-returned state both ways.
    events, _ = _run_job(_dashd_job(tmp, "find_miner"))
    check("find_miner (no creds): ok, device reports locate ON",
          events[1]["ok"] is True and "ON" in events[1]["message"]
          and _state(dashd_state).get("locate_on") is True,
          f"{events[1]} / {_state(dashd_state)}")
    events, _ = _run_job(_dashd_job(tmp, "find_miner"))
    check("find_miner again: the OFF state passes through verbatim",
          events[1]["ok"] is True and "OFF" in events[1]["message"]
          and _state(dashd_state).get("locate_on") is False,
          f"{events[1]}")


# ---------------------------------------------------------------------------
# throttle + autotune resets
# ---------------------------------------------------------------------------

def test_throttle_and_autotune(tmp: Path, dashd_state: Path) -> None:
    events, _ = _run_job(_dashd_job(
        tmp, "throttle", "k.json", API_KEY_SET, {"percent": 80}))
    state = _state(dashd_state)
    check("throttle 80: ok + body {percent: 80} recorded with "
          "api-key auth",
          events[1]["ok"] is True and state.get("throttles")
          and state["throttles"][-1] == {"percent": 80,
                                         "auth": "apikey"},
          f"{events[1]} / {state.get('throttles')}")

    events, _ = _run_job(_dashd_job(
        tmp, "throttle", "k.json", API_KEY_SET, {"percent": 55}))
    check("throttle 55: SaveConfigResult restart flag surfaces "
          "in the message",
          events[1]["ok"] is True
          and "restart is required" in events[1]["message"],
          f"{events[1]}")

    events, _ = _run_job(_dashd_job(tmp, "reset_autotune_all",
                                    "k.json", API_KEY_SET))
    state = _state(dashd_state)
    hits = [h for h in state.get("autotune_resets", [])
            if h["path"] == "/api/v1/autotune/reset-all"]
    check("reset_autotune_all: ok + body {restart: true} recorded",
          events[1]["ok"] is True and hits
          and hits[-1]["body"] == {"restart": True},
          f"{events[1]} / {hits}")

    events, _ = _run_job(_dashd_job(tmp, "reset_autotune_current",
                                    "k.json", API_KEY_SET))
    state = _state(dashd_state)
    hits = [h for h in state.get("autotune_resets", [])
            if h["path"] == "/api/v1/autotune/reset"]
    check("reset_autotune_current: ok + reset names the "
          "perf-summary current preset (perf-110)",
          events[1]["ok"] is True and hits
          and hits[-1]["body"] == {"presets": ["perf-110"],
                                   "restart": True},
          f"{events[1]} / {hits}")


# ---------------------------------------------------------------------------
# API-key configuration + the settings round-trips
# ---------------------------------------------------------------------------

def test_apikey_and_settings(tmp: Path, dashd_state: Path) -> None:
    events, _ = _run_job(_dashd_job(
        tmp, "configure_api_key", "k.json", API_KEY_SET,
        {"operation": "add", "key": NEW_KEY,
         "description": "beesky tail test"}))
    state = _state(dashd_state)
    adds = state.get("apikey_adds", [])
    check("configure_api_key add: ok + device status 'inserted' "
          "in the message + request body recorded",
          events[1]["ok"] is True and "inserted" in events[1]["message"]
          and adds and adds[-1]["key"] == NEW_KEY
          and adds[-1]["description"] == "beesky tail test",
          f"{events[1]} / {adds}")

    events, _ = _run_job(_dashd_job(
        tmp, "configure_api_key", "k.json", API_KEY_SET,
        {"operation": "remove", "key": NEW_KEY}))
    state = _state(dashd_state)
    check("configure_api_key remove: ok + delete recorded",
          events[1]["ok"] is True
          and state.get("apikey_deletes")
          and state["apikey_deletes"][-1]["key"] == NEW_KEY,
          f"{events[1]} / {state.get('apikey_deletes')}")

    events, _ = _run_job(_dashd_job(
        tmp, "set_preset", "k.json", API_KEY_SET,
        {"preset": "eco-95"}))
    posts = _state(dashd_state).get("settings_posts", [])
    last = posts[-1] if posts else {}
    preset = ((last.get("miner") or {}).get("overclock") or {}
              ).get("preset")
    check("set_preset (api key): ok + the settings POST carries "
          "miner.overclock.preset",
          events[1]["ok"] is True and preset == "eco-95",
          f"{events[1]} / preset={preset!r}")

    events, _ = _run_job(_dashd_job(
        tmp, "set_preset", "p.json", PASSWORD_SET,
        {"preset": "eco-95"}))
    check("set_preset (password only): honest x-api-key failure",
          events[1]["ok"] is False
          and "x-api-key" in events[1]["message"],
          f"{events[1]}")

    before = len(_state(dashd_state).get("settings_posts", []))
    events, _ = _run_job(_dashd_job(
        tmp, "change_password", "p.json", PASSWORD_SET,
        {"new_password": "new-pw-123"}))
    posts = _state(dashd_state).get("settings_posts", [])
    section = posts[-1].get("password") if posts else None
    check("change_password (password win): ok + POST body is the "
          "doc's PasswordChange {current, pw}",
          events[1]["ok"] is True
          and section == {"current": "mock-pw", "pw": "new-pw-123"}
          and len(posts) == before + 1,
          f"{events[1]} / {section}")

    events, _ = _run_job(_dashd_job(
        tmp, "change_password", "k.json", API_KEY_SET,
        {"new_password": "new-pw-123"}))
    check("change_password (api-key win): honest failure — the "
          "current password is unknown, nothing posted",
          events[1]["ok"] is False
          and "CURRENT" in events[1]["message"]
          and len(_state(dashd_state).get("settings_posts", []))
          == before + 1,
          f"{events[1]}")


# ---------------------------------------------------------------------------
# diagnostic reports + honest cross-family failures
# ---------------------------------------------------------------------------

def test_diagnostic(tmp: Path) -> None:
    report_dir = tmp / "reports"
    events, _ = _run_job({
        "type": "diagnostic_report", "targets": ["127.0.0.1"],
        "payload": {"report_dir": str(report_dir),
                    "reason": "tail test"},
        "http_port": DASHD_PORT, "cgminer_port": DEAD_RPC,
        "creds_file": _creds(tmp, "k.json", API_KEY_SET)})
    bundle_path = report_dir / "127.0.0.1-diagnostic.json"
    bundle = {}
    if bundle_path.exists():
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    check("diagnostic_report (dashd): ok + bundle file written, "
          "message names it",
          events[1]["ok"] is True and bundle_path.exists()
          and "127.0.0.1-diagnostic.json" in events[1]["message"],
          f"{events[1]}")
    check("diagnostic bundle: BeeSky-variant kind, the record and "
          "the inspect doc ride along, reason recorded",
          bundle.get("kind") == "beesky-diagnostic-report"
          and (bundle.get("record") or {}).get("model")
          == "Antminer S19 Pro"
          and (bundle.get("inspect") or {}).get("source") == "vnish"
          and bundle.get("reason") == "tail test",
          str(bundle)[:300])

    events, _ = _run_job({
        "type": "diagnostic_report", "targets": ["127.0.0.1"],
        "payload": {"report_dir": str(report_dir)},
        "http_port": STOCK_PORT, "cgminer_port": DEAD_RPC})
    bundle = {}
    if bundle_path.exists():
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    check("diagnostic_report (stock): ok + bundle names the "
          "stock source",
          events[1]["ok"] is True and bundle_path.exists()
          and bundle.get("source") == "stock",
          f"{events[1]} / {bundle.get('source')}")

    dead_dir = tmp / "reports-dead"
    events, _ = _run_job({
        "type": "diagnostic_report", "targets": ["127.0.0.1"],
        "payload": {"report_dir": str(dead_dir)},
        "http_port": DEAD_HTTP, "cgminer_port": DEAD_RPC,
        "timeout": 0.5})
    check("diagnostic_report (unreachable): honest failure, "
          "no file produced",
          events[1]["ok"] is False and not dead_dir.exists(),
          f"{events[1]}")

    for task_type, payload in (("pause_mining", None),
                               ("throttle", {"percent": 80})):
        doc = {"type": task_type, "targets": ["127.0.0.1"],
               "http_port": STOCK_PORT, "cgminer_port": DEAD_RPC}
        if payload:
            doc["payload"] = payload
        events, _ = _run_job(doc)
        check(f"{task_type} on stock: honest not-supported failure",
              events[1]["ok"] is False
              and "not supported" in events[1]["message"],
              f"{events[1]}")


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="beesky-ops2-"))
    dashd_state = tmp / "dashd-state.json"
    stock_state = tmp / "stock-state.json"
    procs = [
        _spawn(["tests/mock_dashd.py", "127.0.0.1", str(DASHD_PORT)],
               {"BEESKY_MOCK_DASHD_STATE": str(dashd_state)}),
        _spawn(["tests/mock_bitmain.py", "127.0.0.1", str(STOCK_PORT)],
               {"BEESKY_MOCK_BITMAIN_STATE": str(stock_state)}),
    ]
    try:
        for port in (DASHD_PORT, STOCK_PORT):
            if not _wait_port(port):
                check(f"mock on :{port} up", False, "timeout")
                return 1
        test_validation(tmp)
        test_mining_actions(tmp, dashd_state)
        test_throttle_and_autotune(tmp, dashd_state)
        test_apikey_and_settings(tmp, dashd_state)
        test_diagnostic(tmp)
    finally:
        for proc in procs:
            proc.terminate()
        for proc in procs:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        return 1
    print("ALL OPS2 TESTS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
