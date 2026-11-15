#!/usr/bin/env python3
"""v0.28.0 test — pool presets, clone payloads, scan-record pool
enrichment, and the worker-pattern expander.

No hardware. Loopback mocks (the established fixtures):

  * tests/mock_dashd.py on 127.0.0.1:18093 (state A) AND
    127.0.0.2:18093 (state B) — two VNish devices behind one
    http_port, so a two-target ops job proves the {n} counter
    keys off the TARGET LIST order, not completion order.
    API key "mock-api-key" (settings writes need it).
  * tests/mock_miner.py on 127.0.0.1:4028 — cgminer RPC with a
    `pools` reply (URL/User/Status verbatim, "Alive").
  * tests/mock_stock_fw.py on 127.0.0.1:18094 — stock CGI
    (carries NO pool list: its scan record must omit `pools`).

Asserts: the pattern token table (docs/presets-ipreport-
mapping.md §1.4) against the core expander; pools_normalised's
never-raise contract; per-family scan enrichment (dashd from
the already-fetched summary, cgminer via the extra RPC call,
stock omitted); the ops pools-payload validation (exit 2
before I/O) and its per-device execution — pattern expansion
in target order, honest failures for non-dashd devices and
for tokens whose data BeeSky does not carry ({mac}), and the
clone shape (literal slots, no password -> target keeps its
own). Prints PASS lines; exit 1 on failure.
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

from beesky.core import ops, patterns  # noqa: E402
from beesky.core.cgminer import CgminerClient, CgminerError  # noqa: E402
from beesky.core.patterns import PatternContext, PatternError  # noqa: E402

DASHD_PORT = 18093
STOCK_PORT = 18094
CGMINER_PORT = 4028
CLOSED_HTTP = 18997
CLOSED_RPC = 18998

FAILURES: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        print(f"PASS {name}")
    else:
        print(f"FAIL {name} :: {detail}")
        FAILURES.append(name)


def _wait_port(host: str, port: int, timeout: float = 15.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.3):
                return True
        except OSError:
            time.sleep(0.1)
    return False


def _spawn(args: list[str], env_extra: dict) -> subprocess.Popen:
    env = {**os.environ, "PYTHONPATH": str(ROOT), **env_extra}
    return subprocess.Popen(
        [sys.executable, *args], cwd=ROOT, env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _state(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _scan(ip: str, http_port: int, cgminer_port: int) -> dict:
    proc = subprocess.run(
        [sys.executable, "-m", "beesky", "scan", ip, "--json",
         "--http-port", str(http_port),
         "--cgminer-port", str(cgminer_port), "--timeout", "2"],
        cwd=ROOT, env={**os.environ, "PYTHONPATH": str(ROOT)},
        capture_output=True, text=True, timeout=90)
    assert proc.returncode == 0, \
        f"scan rc={proc.returncode} err={proc.stderr[:200]!r}"
    doc = json.loads(proc.stdout)
    assert doc["found"] == 1, f"scan found={doc['found']} doc={doc}"
    return doc["records"][0]


def _run_job(doc: dict):
    events: list[dict] = []
    job = ops.validate_job(doc)
    summary = ops.run_job(job, events.append)
    return events, summary


def _creds_key(tmp: Path) -> Path:
    path = tmp / "creds-key.json"
    path.write_text(json.dumps([
        {"label": "Key", "api_key": "mock-api-key", "type": "vnish"}]),
        encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# the pattern expander (pure units — the §1.4 token table)
# ---------------------------------------------------------------------------

def test_patterns() -> None:
    ctx = PatternContext(
        ip="192.168.2.101", index=2,
        current_user="acct.w1",
        current_url="stratum+tcp://pool.example.com:3333")
    e = patterns.expand_worker
    check("pattern: literal text passes through",
          e("farm.worker-7", ctx) == "farm.worker-7")
    check("pattern: {account} = before first dot",
          e("{account}", ctx) == "acct")
    check("pattern: {worker} = after first dot",
          e("{worker}", ctx) == "w1")
    check("pattern: account/worker recombine the current user",
          e("{account}.{worker}", ctx) == "acct.w1")
    nodot = PatternContext(ip="10.0.0.1", current_user="solo")
    check("pattern: no dot -> account is whole, worker empty",
          e("{account}|{worker}", nodot) == "solo|")
    check("pattern: {ip:.} dotted + octets",
          e("{ip:.}/{ip1}.{ip2}.{ip3}.{ip4}", ctx)
          == "192.168.2.101/192.168.2.101")
    check("pattern: {ip4} is the last octet",
          e("w-{ip4}", ctx) == "w-101")
    check("pattern: {n} default start/step at index 2 -> 3",
          e("{n}", ctx) == "3")
    check("pattern: {nn} pads to 2, {nnn} to 3",
          e("{nn}/{nnn}", ctx) == "03/003")
    check("pattern: {n:10:5} start/step honoured",
          e("{n:10:5}", ctx) == "20")
    check("pattern: index 0 is the first device ({n} -> 1)",
          e("{n}", PatternContext(ip="10.0.0.1")) == "1")
    check("pattern: {pool-host}/{port}/{proto-str} from current URL",
          e("{proto-str}://{pool-host}:{port}", ctx)
          == "stratum+tcp://pool.example.com:3333")
    check("pattern: unclosed brace is literal",
          e("w{", ctx) == "w{")

    def fails(template, context, needle):
        try:
            e(template, context)
        except PatternError as exc:
            return needle in str(exc)
        return False

    bare = PatternContext(ip="10.0.0.9")
    check("pattern: {account} without a current pool fails honestly",
          fails("{account}", bare, "current pool worker"))
    check("pattern: {pool-host} without a current URL fails honestly",
          fails("{pool-host}", bare, "current pool"))
    check("pattern: {mac} fails — BeeSky carries no MAC (D4)",
          fails("{mac}", ctx, "MAC address"))
    check("pattern: {host} fails — no hostname carried (D4)",
          fails("{host}", ctx, "hostname"))
    check("pattern: unknown token fails, never passes through",
          fails("{bogus}", ctx, "unknown pattern"))
    check("pattern: malformed {n:x} fails",
          fails("{n:x}", ctx, "integers"))
    check("pattern: needs_current_pool classification",
          patterns.needs_current_pool("w.{account}") is True
          and patterns.needs_current_pool("w.{n}-{ip4}") is False
          and patterns.needs_current_pool("plain") is False)


# ---------------------------------------------------------------------------
# pools_normalised: the never-raise enrichment contract
# ---------------------------------------------------------------------------

class _StubClient(CgminerClient):
    def __init__(self, reply=None, exc=None):
        self._reply, self._exc = reply, exc

    def pools(self) -> dict:
        if self._exc is not None:
            raise self._exc
        return self._reply


def test_pools_normalised() -> None:
    good = _StubClient(reply={
        "STATUS": [{"STATUS": "S"}],
        "POOLS": [{"POOL": 0, "URL": "stratum+tcp://p:3333",
                   "Status": "Alive", "User": "w.1"}]})
    check("pools_normalised: verbatim url/worker/status",
          good.pools_normalised() == [
              {"url": "stratum+tcp://p:3333", "worker": "w.1",
               "status": "Alive"}],
          str(good.pools_normalised()))
    check("pools_normalised: transport failure -> None",
          _StubClient(exc=CgminerError("down")).pools_normalised()
          is None)
    check("pools_normalised: STATUS E refusal -> None",
          _StubClient(reply={"STATUS": [{"STATUS": "E"}],
                             "POOLS": []}).pools_normalised()
          is None)
    check("pools_normalised: no POOLS list -> None",
          _StubClient(reply={"STATUS": []}).pools_normalised()
          is None)


# ---------------------------------------------------------------------------
# scan enrichment, per family
# ---------------------------------------------------------------------------

def test_scan_enrichment() -> None:
    rec = _scan("127.0.0.1", DASHD_PORT, CLOSED_RPC)
    check("scan dashd: record gains pools from the summary (free)",
          rec.get("source") == "vnish" and rec.get("pools") == [
              {"url": "stratum+tcp://pool.example.com:3333",
               "worker": "mockworker.001", "status": "alive"}],
          str(rec.get("pools")))

    rec = _scan("127.0.0.1", CLOSED_HTTP, CGMINER_PORT)
    check("scan cgminer: record gains pools via the RPC pools call",
          rec.get("source") == "cgminer" and rec.get("pools") == [
              {"url": "stratum+tcp://pool.example.com:3333",
               "worker": "mockworker.001", "status": "Alive"}],
          str(rec.get("pools")))

    rec = _scan("127.0.0.1", STOCK_PORT, CLOSED_RPC)
    check("scan stock: no pool source in a scan -> key omitted (G2)",
          rec.get("source") == "stock" and "pools" not in rec,
          f"source={rec.get('source')} keys={sorted(rec)}")


# ---------------------------------------------------------------------------
# ops: pools payload validation + execution
# ---------------------------------------------------------------------------

def test_ops_validation(tmp: Path) -> None:
    def rejected(doc) -> bool:
        try:
            ops.validate_job(doc)
        except ops.JobError:
            return True
        return False

    base = {"type": "switch_pool", "targets": ["127.0.0.1"]}
    check("ops pools: mixed pools + single-slot form rejected",
          rejected({**base, "payload": {
              "pool_id": 0,
              "pools": [{"url": "u", "user": "w"}]}}))
    check("ops pools: empty list rejected",
          rejected({**base, "payload": {"pools": []}}))
    check("ops pools: 4 slots rejected (miner has 3)",
          rejected({**base, "payload": {"pools": [
              {"url": "u", "user": "w"}] * 4}}))
    check("ops pools: slot without user rejected",
          rejected({**base, "payload": {
              "pools": [{"url": "stratum+tcp://x:3333"}]}}))
    check("ops pools: slot without url rejected",
          rejected({**base, "payload": {"pools": [{"user": "w"}]}}))
    job = ops.validate_job({**base, "payload": {
        "clone_from": "127.0.0.9",
        "pools": [{"url": "stratum+tcp://x:3333", "user": "w.1",
                   "password": "pw"},
                  {"url": "stratum+tcp://y:3333", "user": "w.2"}]}})
    check("ops pools: valid preset/clone payload normalised",
          job["payload"]["pools"] == [
              {"url": "stratum+tcp://x:3333", "user": "w.1",
               "password": "pw"},
              {"url": "stratum+tcp://y:3333", "user": "w.2"}],
          str(job["payload"]))

    job_path = tmp / "mixed.json"
    job_path.write_text(json.dumps({**base, "payload": {
        "url": "stratum+tcp://x:3333",
        "pools": [{"url": "u", "user": "w"}]}}), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, "-m", "beesky", "ops", "--job",
         str(job_path)],
        cwd=ROOT, env={**os.environ, "PYTHONPATH": str(ROOT)},
        capture_output=True, text=True, timeout=60)
    check("ops pools: CLI refuses a mixed payload with exit 2",
          proc.returncode == 2 and proc.stdout.strip() == "",
          f"rc={proc.returncode} out={proc.stdout[:80]!r}")


def test_ops_apply(tmp: Path, state_a: Path, state_b: Path) -> None:
    creds = _creds_key(tmp)
    common = {"type": "switch_pool", "http_port": DASHD_PORT,
              "cgminer_port": CLOSED_RPC, "creds_file": str(creds)}

    # {account} reads the CURRENT pool user (mockworker.001).
    events, _ = _run_job({**common, "targets": ["127.0.0.1"],
                          "payload": {"pools": [{
                              "url": "stratum+tcp://pool.example.com:3333",
                              "user": "{account}.x"}]}})
    pools = _state(state_a).get("pools") or []
    check("apply {account}: expands from the current worker",
          events[1]["ok"] is True and pools
          and pools[0].get("user") == "mockworker.x",
          f"{events[1]} / {pools}")

    # Two targets, one job: {nn} must follow TARGET LIST order
    # (device .1 -> 01, device .2 -> 02) and {ip4} the device.
    events, summary = _run_job({**common,
                                "targets": ["127.0.0.1", "127.0.0.2"],
                                "payload": {"pools": [
                                    {"url": "stratum+tcp://new.example.com:4444",
                                     "user": "farm.{nn}"},
                                    {"url": "stratum+tcp://bak.example.com:4444",
                                     "user": "farm.{ip4}"}]}})
    by_ip = {e["ip"]: e for e in events if e.get("event") == "result"}
    pools_a = _state(state_a).get("pools") or []
    pools_b = _state(state_b).get("pools") or []
    check("apply preset over 2 devices: both ok",
          summary["ok"] == 2 and by_ip["127.0.0.1"]["ok"]
          and by_ip["127.0.0.2"]["ok"],
          f"{summary} / {by_ip}")
    check("apply preset: {nn} follows the target list order",
          pools_a and pools_a[0].get("user") == "farm.01"
          and pools_b and pools_b[0].get("user") == "farm.02",
          f"A={pools_a} B={pools_b}")
    check("apply preset: slot 2 written too, {ip4} per device",
          len(pools_a) > 1 and pools_a[1].get("user") == "farm.1"
          and len(pools_b) > 1 and pools_b[1].get("user") == "farm.2",
          f"A={pools_a} B={pools_b}")
    check("apply preset: slot urls landed in order",
          pools_a[0].get("url") == "stratum+tcp://new.example.com:4444"
          and pools_a[1].get("url") == "stratum+tcp://bak.example.com:4444",
          f"A={pools_a}")

    # A token whose data BeeSky does not carry fails the device
    # BEFORE any write (the mock's pools stay untouched).
    before = _state(state_a).get("pools")
    events, _ = _run_job({**common, "targets": ["127.0.0.1"],
                          "payload": {"pools": [{
                              "url": "stratum+tcp://z:3333",
                              "user": "w.{mac}"}]}})
    check("apply {mac}: honest per-device pattern failure",
          events[1]["ok"] is False
          and "pool pattern" in events[1]["message"]
          and "MAC" in events[1]["message"],
          f"{events[1]}")
    check("apply {mac}: nothing was written",
          _state(state_a).get("pools") == before,
          str(_state(state_a).get("pools")))

    # Non-dashd target: the executor's canonical refusal.
    events, _ = _run_job({
        "type": "switch_pool", "targets": ["127.0.0.1"],
        "http_port": STOCK_PORT, "cgminer_port": CLOSED_RPC,
        "payload": {"pools": [{"url": "stratum+tcp://x:3333",
                               "user": "w.1"}]}})
    check("apply preset on stock: honest not-supported failure",
          events[1]["ok"] is False
          and "not supported" in events[1]["message"],
          f"{events[1]}")

    # Clone shape: literal slots, NO password in the payload ->
    # the target keeps its own per-slot pass ("x" in the mock).
    events, _ = _run_job({**common, "targets": ["127.0.0.2"],
                          "payload": {
                              "clone_from": "127.0.0.1",
                              "pools": [{
                                  "url": "stratum+tcp://pool.example.com:3333",
                                  "user": "clone.001"}]}})
    pools_b = _state(state_b).get("pools") or []
    check("clone payload: literal worker lands, target pass kept",
          events[1]["ok"] is True and pools_b
          and pools_b[0].get("user") == "clone.001"
          and pools_b[0].get("pass") == "x",
          f"{events[1]} / {pools_b}")


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="beesky-pools-"))
    state_a = tmp / "dashd-a.json"
    state_b = tmp / "dashd-b.json"
    procs = [
        _spawn(["tests/mock_dashd.py", "127.0.0.1", str(DASHD_PORT)],
               {"BEESKY_MOCK_DASHD_STATE": str(state_a)}),
        _spawn(["tests/mock_dashd.py", "127.0.0.2", str(DASHD_PORT)],
               {"BEESKY_MOCK_DASHD_STATE": str(state_b)}),
        _spawn(["tests/mock_miner.py"], {}),
        _spawn(["tests/mock_stock_fw.py", "127.0.0.1",
                str(STOCK_PORT)], {}),
    ]
    try:
        for host, port in (("127.0.0.1", DASHD_PORT),
                           ("127.0.0.2", DASHD_PORT),
                           ("127.0.0.1", CGMINER_PORT),
                           ("127.0.0.1", STOCK_PORT)):
            if not _wait_port(host, port):
                check(f"mock on {host}:{port} up", False, "timeout")
                return 1
        test_patterns()
        test_pools_normalised()
        test_scan_enrichment()
        test_ops_validation(tmp)
        test_ops_apply(tmp, state_a, state_b)
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
    print("ALL POOLS TESTS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
