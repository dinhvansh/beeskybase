#!/usr/bin/env python3
"""v0.26 Operations task runner test — beesky/core/ops.py + `ops` CLI.

No hardware. Four loopback mocks (the v0.6/v0.23 fixtures):

  * tests/mock_dashd.py on 127.0.0.1:18090 — VNish dashd with the
    api-doc action endpoints; every action hit lands in the
    BEESKY_MOCK_DASHD_STATE file (reboots / switch_pools /
    settings_posts / pools). Password "mock-pw", API key
    "mock-api-key".
  * tests/mock_bitmain.py on 127.0.0.1:18091 — stock firmware;
    /cgi-bin/reboot.cgi hits land in BEESKY_MOCK_BITMAIN_STATE.
  * tests/mock_watch_miner.py on :14028 (writable RPC) and :14029
    (control api_writable=false) — the cgminer `restart` primitive
    and its honest read-only refusal.
  * tests/mock_creds_miner.py (dashd mode) on :18092 — reads are
    401-gated; /unlock accepts "dashd-pw" and LOGS every attempt,
    which proves the v0.24 group → global credential resolution
    order the runner shares with scan.

Asserts the job contract (exit 2 before any I/O on malformed jobs),
the NDJSON event stream shape, per-family truthful outcomes for
reboot / switch_pool / rescan, group-vs-global cred resolution, and
cooperative cancellation. Prints PASS lines; exit 1 on failure.
"""

import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from beesky.core import ops  # noqa: E402

DASHD_PORT = 18090
STOCK_PORT = 18091
CREDS_PORT = 18092
CGMINER_PORT = 14028
CGMINER_RO_PORT = 14029
DEAD_HTTP = 18099
DEAD_RPC = 14099

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
    proc = subprocess.Popen(
        [sys.executable, *args], cwd=ROOT, env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return proc


def _run_cli(job_path: Path) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    return subprocess.run(
        [sys.executable, "-m", "beesky", "ops", "--job", str(job_path)],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)


def _job(tmp: Path, name: str, doc) -> Path:
    path = tmp / name
    path.write_text(json.dumps(doc), encoding="utf-8")
    return path


def _run_job(doc: dict):
    """In-process run: returns (events, summary)."""
    events: list[dict] = []
    job = ops.validate_job(doc)
    summary = ops.run_job(job, events.append)
    return events, summary


def _state(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


# ---------------------------------------------------------------------------
# validation: the CLI must refuse malformed jobs with exit 2 and an
# empty stdout (no device is touched — the mocks' state files are
# asserted untouched by the run-order in main)
# ---------------------------------------------------------------------------

def test_validation(tmp: Path) -> None:
    cases = {
        "non-object": [1, 2, 3],
        "unknown type": {"type": "nuke", "targets": ["127.0.0.1"]},
        "empty targets": {"type": "reboot", "targets": []},
        "bad ip": {"type": "reboot", "targets": ["999.1.1.1"]},
        "unknown group": {"type": "reboot", "targets": ["127.0.0.1"],
                            "group": "Không có"},
        "pool url without user": {
            "type": "switch_pool", "targets": ["127.0.0.1"],
            "payload": {"url": "stratum+tcp://x:3333"}},
        "negative pool_id": {
            "type": "switch_pool", "targets": ["127.0.0.1"],
            "payload": {"pool_id": -1}},
    }
    for name, doc in cases.items():
        proc = _run_cli(_job(tmp, "bad.json", doc))
        check(f"validation: {name} -> exit 2",
              proc.returncode == 2 and proc.stdout.strip() == ""
              and proc.stderr.strip() != "",
              f"rc={proc.returncode} out={proc.stdout[:80]!r} "
              f"err={proc.stderr[:80]!r}")

    bad_creds = tmp / "bad-creds.json"
    bad_creds.write_text('[{"label": "x"}]', encoding="utf-8")
    proc = _run_cli(_job(tmp, "badcreds.json", {
        "type": "reboot", "targets": ["127.0.0.1"],
        "creds_file": str(bad_creds)}))
    check("validation: malformed creds file -> exit 2",
          proc.returncode == 2 and proc.stdout.strip() == "",
          f"rc={proc.returncode}")

    proc = _run_cli(tmp / "does-not-exist.json")
    check("validation: missing job file -> exit 2",
          proc.returncode == 2 and proc.stdout.strip() == "",
          f"rc={proc.returncode}")


# ---------------------------------------------------------------------------
# reboot: one truthful outcome per family
# ---------------------------------------------------------------------------

def test_reboot(tmp: Path, dashd_state: Path, stock_state: Path,
                cg_state: Path) -> None:
    creds_vnish = tmp / "creds-vnish.json"
    creds_vnish.write_text(json.dumps([
        {"label": "VNish", "user": "root", "password": "mock-pw",
         "type": "vnish"}]), encoding="utf-8")
    events, summary = _run_job({
        "type": "reboot", "targets": ["127.0.0.1"],
        "http_port": DASHD_PORT, "cgminer_port": DEAD_RPC,
        "creds_file": str(creds_vnish)})
    result = events[1]
    check("reboot dashd (password set): ok",
          result["ok"] is True and summary["ok"] == 1
          and summary["status"] == "success",
          f"{result} / {summary}")
    check("reboot dashd: the mock recorded the reboot",
          len(_state(dashd_state).get("reboots", [])) == 1,
          str(_state(dashd_state)))

    creds_wrong = tmp / "creds-wrong.json"
    creds_wrong.write_text(json.dumps([
        {"label": "Sai", "user": "root", "password": "sai-pw",
         "type": "vnish"}]), encoding="utf-8")
    events, summary = _run_job({
        "type": "reboot", "targets": ["127.0.0.1"],
        "http_port": DASHD_PORT, "cgminer_port": DEAD_RPC,
        "creds_file": str(creds_wrong)})
    result = events[1]
    check("reboot dashd (wrong password): honest 401 failure",
          result["ok"] is False and "401" in result["message"]
          and summary["status"] == "error",
          f"{result} / {summary}")
    check("reboot dashd (wrong password): no second reboot recorded",
          len(_state(dashd_state).get("reboots", [])) == 1,
          str(_state(dashd_state)))

    creds_key = tmp / "creds-key.json"
    creds_key.write_text(json.dumps([
        {"label": "Key", "api_key": "mock-api-key", "type": "vnish"}]),
        encoding="utf-8")
    events, _ = _run_job({
        "type": "reboot", "targets": ["127.0.0.1"],
        "http_port": DASHD_PORT, "cgminer_port": DEAD_RPC,
        "creds_file": str(creds_key)})
    check("reboot dashd (api-key set): ok",
          events[1]["ok"] is True
          and len(_state(dashd_state).get("reboots", [])) == 2,
          f"{events[1]} / {_state(dashd_state)}")

    events, _ = _run_job({
        "type": "reboot", "targets": ["127.0.0.1"],
        "http_port": STOCK_PORT, "cgminer_port": DEAD_RPC})
    check("reboot stock (legacy root/root): ok + recorded",
          events[1]["ok"] is True
          and len(_state(stock_state).get("reboots", [])) == 1,
          f"{events[1]} / {_state(stock_state)}")

    events, _ = _run_job({
        "type": "reboot", "targets": ["127.0.0.1"],
        "http_port": DEAD_HTTP, "cgminer_port": CGMINER_PORT})
    check("reboot cgminer (writable RPC): ok + restart recorded",
          events[1]["ok"] is True
          and _state(cg_state).get("restarts") == 1,
          f"{events[1]} / {_state(cg_state)}")

    events, _ = _run_job({
        "type": "reboot", "targets": ["127.0.0.1"],
        "http_port": DEAD_HTTP, "cgminer_port": CGMINER_RO_PORT})
    check("reboot cgminer (read-only RPC): refused verbatim",
          events[1]["ok"] is False
          and "Access denied" in events[1]["message"],
          f"{events[1]}")

    events, summary = _run_job({
        "type": "reboot", "targets": ["127.0.0.1"],
        "http_port": DEAD_HTTP, "cgminer_port": DEAD_RPC, "timeout": 0.5})
    check("reboot unreachable: honest not-answering failure",
          events[1]["ok"] is False
          and "not answering" in events[1]["message"]
          and summary["failed"] == 1,
          f"{events[1]} / {summary}")


# ---------------------------------------------------------------------------
# switch_pool: dashd-only primitive, honest elsewhere
# ---------------------------------------------------------------------------

def test_switch_pool(tmp: Path, dashd_state: Path) -> None:
    creds_key = tmp / "creds-key.json"
    creds_key.write_text(json.dumps([
        {"label": "Key", "api_key": "mock-api-key", "type": "vnish"}]),
        encoding="utf-8")
    events, _ = _run_job({
        "type": "switch_pool", "targets": ["127.0.0.1"],
        "payload": {"pool_id": 1},
        "http_port": DASHD_PORT, "cgminer_port": DEAD_RPC,
        "creds_file": str(creds_key)})
    state = _state(dashd_state)
    check("switch_pool {pool_id:1} dashd: ok + slot activated",
          events[1]["ok"] is True and state.get("active_pool") == 1,
          f"{events[1]} / {state}")

    events, _ = _run_job({
        "type": "switch_pool", "targets": ["127.0.0.1"],
        "payload": {"url": "stratum+tcp://new.example.com:4444",
                    "user": "worker.new", "password": "pw"},
        "http_port": DASHD_PORT, "cgminer_port": DEAD_RPC,
        "creds_file": str(creds_key)})
    state = _state(dashd_state)
    pools = state.get("pools") or []
    check("switch_pool {url,user} dashd (api key): ok + slot rewritten",
          events[1]["ok"] is True and pools
          and pools[0].get("url") == "stratum+tcp://new.example.com:4444"
          and pools[0].get("user") == "worker.new",
          f"{events[1]} / {pools}")

    creds_pw = tmp / "creds-pwonly.json"
    creds_pw.write_text(json.dumps([
        {"label": "PW", "user": "root", "password": "mock-pw",
         "type": "vnish"}]), encoding="utf-8")
    events, _ = _run_job({
        "type": "switch_pool", "targets": ["127.0.0.1"],
        "payload": {"url": "stratum+tcp://new.example.com:4444",
                    "user": "worker.new"},
        "http_port": DASHD_PORT, "cgminer_port": DEAD_RPC,
        "creds_file": str(creds_pw)})
    check("switch_pool {url,user} dashd (password only): honest "
          "x-api-key failure",
          events[1]["ok"] is False and "x-api-key" in events[1]["message"],
          f"{events[1]}")

    events, _ = _run_job({
        "type": "switch_pool", "targets": ["127.0.0.1"],
        "payload": {"pool_id": 0},
        "http_port": STOCK_PORT, "cgminer_port": DEAD_RPC})
    check("switch_pool on stock: honest not-supported failure",
          events[1]["ok"] is False
          and "not supported" in events[1]["message"],
          f"{events[1]}")


# ---------------------------------------------------------------------------
# rescan + the group/global credential resolution (v0.24 layering)
# ---------------------------------------------------------------------------

def test_rescan_and_groups(tmp: Path, creds_log: Path) -> None:
    events, _ = _run_job({
        "type": "rescan", "targets": ["127.0.0.1"],
        "http_port": DASHD_PORT, "cgminer_port": DEAD_RPC})
    record = events[1].get("record") or {}
    check("rescan dashd: ok + fresh record rides the event",
          events[1]["ok"] is True and record.get("source") == "vnish"
          and bool(record.get("model")),
          f"{events[1]}")

    events, _ = _run_job({
        "type": "rescan", "targets": ["127.0.0.1"],
        "http_port": DEAD_HTTP, "cgminer_port": DEAD_RPC, "timeout": 0.5})
    check("rescan unreachable: ok=False, no record",
          events[1]["ok"] is False and "record" not in events[1],
          f"{events[1]}")

    groups_doc = {"version": 1, "groups": [
        {"name": "Trại Ops", "targets": "127.0.0.1",
         "creds": [{"label": "Nhóm", "user": "root",
                    "password": "dashd-pw", "type": "vnish"}]}]}
    groups_file = tmp / "groups.json"
    groups_file.write_text(json.dumps(groups_doc), encoding="utf-8")

    def unlock_attempts() -> list[str]:
        try:
            lines = creds_log.read_text(encoding="utf-8").splitlines()
        except OSError:
            return []
        return [json.loads(l).get("pw") for l in lines
                if l.strip() and json.loads(l).get("kind") == "unlock"]

    creds_log.write_text("", encoding="utf-8")
    events, _ = _run_job({
        "type": "rescan", "targets": ["127.0.0.1"],
        "http_port": CREDS_PORT, "cgminer_port": DEAD_RPC,
        "group": "Trại Ops", "groups_file": str(groups_file)})
    record = events[1].get("record") or {}
    check("group creds win: rescan ok, winner label is the group's",
          events[1]["ok"] is True
          and record.get("cred_label") == "Nhóm",
          f"{events[1]}")
    check("group creds win: exactly one unlock attempt (the group's)",
          unlock_attempts() == ["dashd-pw"],
          str(unlock_attempts()))

    groups_doc["groups"][0]["creds"] = [
        {"label": "Nhóm sai", "user": "root", "password": "sai-pw",
         "type": "vnish"}]
    groups_file.write_text(json.dumps(groups_doc), encoding="utf-8")
    global_creds = tmp / "creds-global.json"
    global_creds.write_text(json.dumps([
        {"label": "Toàn cục", "user": "root", "password": "dashd-pw",
         "type": "vnish"}]), encoding="utf-8")
    creds_log.write_text("", encoding="utf-8")
    events, _ = _run_job({
        "type": "rescan", "targets": ["127.0.0.1"],
        "http_port": CREDS_PORT, "cgminer_port": DEAD_RPC,
        "group": "Trại Ops", "groups_file": str(groups_file),
        "creds_file": str(global_creds)})
    record = events[1].get("record") or {}
    check("global rescue: group set fails, global set wins the miner",
          events[1]["ok"] is True
          and record.get("cred_label") == "Toàn cục",
          f"{events[1]}")
    check("global rescue: attempts ran group-first, then global",
          unlock_attempts() == ["sai-pw", "dashd-pw"],
          str(unlock_attempts()))


# ---------------------------------------------------------------------------
# stream shape + cancellation + the subprocess NDJSON contract
# ---------------------------------------------------------------------------

def test_stream_and_cancel(tmp: Path) -> None:
    # Shape check on a 2-target mixed run (one live mock, one
    # loopback address where nothing listens — refused instantly).
    events, summary = _run_job({
        "type": "rescan", "targets": ["127.0.0.1", "127.0.0.3"],
        "http_port": DASHD_PORT, "cgminer_port": DEAD_RPC,
        "timeout": 0.5, "workers": 2})
    kinds = [e["event"] for e in events]
    dones = sorted(e["done"] for e in events if e["event"] == "result")
    check("stream shape: start, one result per device, summary last",
          kinds[0] == "start" and kinds[-1] == "summary"
          and dones == [1, 2],
          str(kinds))
    check("stream shape: mixed outcomes -> hasErrors summary",
          summary["total"] == 2 and summary["completed"] == 2
          and summary["ok"] == 1 and summary["failed"] == 1
          and summary["cancelled"] == 0
          and summary["status"] == "hasErrors",
          str(summary))

    cancel = threading.Event()
    events = []

    def emit(event: dict) -> None:
        events.append(event)
        if event.get("event") == "result":
            cancel.set()

    job = ops.validate_job({
        "type": "rescan",
        "targets": ["127.0.0.1", "127.0.0.3", "127.0.0.4"],
        "http_port": DASHD_PORT, "cgminer_port": DEAD_RPC,
        "timeout": 0.5, "workers": 1})
    summary = ops.run_job(job, emit, cancel)
    check("cancellation: unstarted devices counted, status cancelled",
          summary["completed"] == 1 and summary["cancelled"] == 2
          and summary["status"] == "cancelled",
          str(summary))

    creds_vnish = tmp / "creds-vnish.json"
    creds_vnish.write_text(json.dumps([
        {"label": "VNish", "user": "root", "password": "mock-pw",
         "type": "vnish"}]), encoding="utf-8")
    proc = _run_cli(_job(tmp, "ok.json", {
        "type": "reboot", "targets": ["127.0.0.1"],
        "http_port": DASHD_PORT, "cgminer_port": DEAD_RPC,
        "creds_file": str(creds_vnish)}))
    lines = [json.loads(l) for l in proc.stdout.splitlines() if l.strip()]
    check("CLI NDJSON: exit 0, every line parses, summary last + ok",
          proc.returncode == 0 and lines
          and lines[-1]["event"] == "summary"
          and lines[-1]["ok"] == 1
          and any(l.get("event") == "result" and l.get("ok")
                  for l in lines),
          f"rc={proc.returncode} lines={len(lines)} "
          f"err={proc.stderr[:120]!r}")


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="beesky-ops-"))
    dashd_state = tmp / "dashd-state.json"
    stock_state = tmp / "stock-state.json"
    creds_log = tmp / "creds-log.jsonl"
    cg_control = tmp / "cgminer.json"
    cg_control.write_text("{}", encoding="utf-8")
    cg_ro_control = tmp / "cgminer-ro.json"
    cg_ro_control.write_text(json.dumps({"api_writable": False}),
                             encoding="utf-8")
    procs = [
        _spawn(["tests/mock_dashd.py", "127.0.0.1", str(DASHD_PORT)],
               {"BEESKY_MOCK_DASHD_STATE": str(dashd_state)}),
        _spawn(["tests/mock_bitmain.py", "127.0.0.1", str(STOCK_PORT)],
               {"BEESKY_MOCK_BITMAIN_STATE": str(stock_state)}),
        _spawn(["tests/mock_watch_miner.py", "--host", "127.0.0.1",
                "--port", str(CGMINER_PORT), "--control", str(cg_control)],
               {}),
        _spawn(["tests/mock_watch_miner.py", "--host", "127.0.0.1",
                "--port", str(CGMINER_RO_PORT),
                "--control", str(cg_ro_control)], {}),
        _spawn(["tests/mock_creds_miner.py", "127.0.0.1", str(CREDS_PORT),
                "dashd"],
               {"BEESKY_MOCK_CREDS_LOG": str(creds_log),
                "BEESKY_MOCK_CREDS_PW": "dashd-pw"}),
    ]
    try:
        for port in (DASHD_PORT, STOCK_PORT, CGMINER_PORT,
                     CGMINER_RO_PORT, CREDS_PORT):
            if not _wait_port(port):
                check(f"mock on :{port} up", False, "timeout")
                return 1
        test_validation(tmp)
        test_reboot(tmp, dashd_state, stock_state,
                    tmp / "cgminer.json.state.json")
        test_switch_pool(tmp, dashd_state)
        test_rescan_and_groups(tmp, creds_log)
        test_stream_and_cancel(tmp)
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
    print("ALL OPS TESTS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
