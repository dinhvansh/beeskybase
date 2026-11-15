#!/usr/bin/env python3
"""v0.27.0 test — one-device deep fetch (`beesky inspect --json`).

The detail tabs' data: pools / fans / per-board detail fetched
for ONE miner through the scan's own probe + credential
resolution (docs/device-detail-mapping.md). Sections are
explicit — {"supported": true, ...} with real data or
{"supported": false, "reason"} — never an empty success.

Fixtures (the repo's real mocks):
  * mock_dashd.py — open VNish: summary carries pools +
    cooling (fan mode "auto", duty 62) + chip_statuses counts;
    /boards carries per-chip grades (board 1: chips 10 + 55 red);
  * mock_miner.py — cgminer RPC on :4028: acs strings (board 2
    dead at 10/55/114), a `pools` command, fan speeds, NO mode;
  * mock_stock_fw.py — stock CGI (cgminer-shaped, root/root):
    boards + fans from the CGI, pools with NO source (the RPC
    port is pointed at a closed one on purpose);
  * mock_creds_miner.py dashd mode — reads locked behind
    /unlock for "dashd-pw"; its summary has chip counts + fans
    but NO pools list and NO /boards, so sections degrade
    honestly under the winning credential set.

Asserts: per-family sections; the vnish grade split
(grey/orange/red = STABLE/SLOW/CRITICAL); cgminer boards carry
acs counts with NO grade buckets (the DATA-GAP is structural);
unsupported markers with reasons; cred resolution reuse
(--creds-file winner + label, all-fail 401 degradation, --group
layer); the exit-2 contract for malformed targets/files; the
exit-0 error document for an unclaimed device.

Prints PASS lines; exit 1 on failure.
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

FAILURES: list[str] = []

DASHD_PORT = 18821
STOCK_PORT = 18822
LOCKED_PORT = 18823
CLOSED_HTTP = 18999
CLOSED_RPC = 18998


def check(label: str, condition: bool, extra: str = "") -> None:
    if condition:
        print(f"PASS: {label}")
    else:
        FAILURES.append(label)
        print(f"FAIL: {label} {extra}")


def _wait_port(port: int, timeout_s: float = 15.0) -> bool:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.2)
    return False


class Server:
    def __init__(self, argv: list[str], port: int,
                 env_extra: dict | None = None):
        env = dict(os.environ)
        if env_extra:
            env.update(env_extra)
        self.proc = subprocess.Popen(
            argv, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            env=env)
        self.port = port

    def stop(self) -> None:
        self.proc.terminate()
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def _inspect(*argv: str) -> tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "beesky", "inspect", *argv],
        cwd=ROOT, capture_output=True, text=True, timeout=90)
    return proc.returncode, proc.stdout, proc.stderr


def _inspect_doc(*argv: str) -> dict:
    rc, out, err = _inspect(*argv)
    try:
        doc = json.loads(out)
    except json.JSONDecodeError:
        raise AssertionError(
            f"inspect stdout not one JSON doc: rc={rc} "
            f"out={out[:160]!r} err={err[:160]!r}")
    assert rc == 0, f"inspect rc={rc} err={err[:160]!r}"
    return doc


# ---------------------------------------------------------------------------
# per-family sections
# ---------------------------------------------------------------------------

def test_vnish() -> None:
    doc = _inspect_doc("127.0.0.1", "--json",
                       "--http-port", str(DASHD_PORT),
                       "--cgminer-port", str(CLOSED_RPC))
    check("vnish: claimed as vnish, model carried",
          doc["source"] == "vnish" and doc["model"] == "Antminer S19 Pro",
          f"source={doc.get('source')} model={doc.get('model')}")
    boards = doc["boards"]
    check("vnish boards: supported", boards["supported"] is True)
    b1 = boards["boards"][0]
    check("vnish boards: grade split grey/orange/red = stable/slow/critical",
          (b1["stable"], b1["slow"], b1["critical"]) == (112, 0, 2),
          f"b1={ {k: b1.get(k) for k in ('stable', 'slow', 'critical')} }")
    check("vnish boards: totals + dead positions from /boards grades",
          b1["chips_total"] == 114 and b1["dead_positions"] == [10, 55],
          f"total={b1.get('chips_total')} dead={b1.get('dead_positions')}")
    check("vnish boards: per-chip list with grades + temps",
          isinstance(b1["chips"], list) and len(b1["chips"]) == 114
          and b1["chips"][9]["grade"] == "red"
          and b1["chips"][0]["grade"] == "grey",
          f"chips={type(b1.get('chips'))}")
    check("vnish boards: chip AND pcb temps both carried",
          b1["chip_temp_c"] == 74.0 and b1["pcb_temp_c"] == 62.0,
          f"chip={b1.get('chip_temp_c')} pcb={b1.get('pcb_temp_c')}")
    pools = doc["pools"]
    check("vnish pools: supported from the summary PoolStats",
          pools["supported"] is True and len(pools["pools"]) == 1
          and pools["pools"][0]["url"] == "stratum+tcp://pool.example.com:3333"
          and pools["pools"][0]["user"] == "mockworker.001"
          and pools["pools"][0]["accepted"] == 2048,
          f"pools={pools}")
    fans = doc["fans"]
    check("vnish fans: mode + duty + per-fan status carried",
          fans["supported"] is True and fans["mode"] == "auto"
          and fans["duty_pct"] == 62 and len(fans["fans"]) == 4
          and fans["fans"][0]["rpm"] == 4320
          and fans["fans"][0]["status"] == "ok"
          and fans["fans"][0]["max_rpm"] == 6000,
          f"fans={fans}")


def test_cgminer() -> None:
    doc = _inspect_doc("127.0.0.1", "--json",
                       "--http-port", str(CLOSED_HTTP))
    check("cgminer: claimed as cgminer", doc["source"] == "cgminer",
          f"source={doc.get('source')}")
    boards = doc["boards"]
    check("cgminer boards: supported", boards["supported"] is True)
    b2 = boards["boards"][1]
    check("cgminer boards: acs counts + dead positions + char breakdown",
          b2["chips_total"] == 114 and b2["chips_ok"] == 111
          and b2["dead_positions"] == [10, 55, 114]
          and b2["other_chars"] == {"x": 3},
          f"b2={ {k: b2.get(k) for k in ('chips_total', 'chips_ok', 'dead_positions', 'other_chars')} }")
    check("cgminer boards: NO grade buckets (the DATA-GAP is structural)",
          "stable" not in b2 and "slow" not in b2
          and "critical" not in b2,
          f"b2 keys={sorted(b2)}")
    pools = doc["pools"]
    check("cgminer pools: supported via the RPC pools command",
          pools["supported"] is True and len(pools["pools"]) == 1
          and pools["pools"][0]["status"] == "Alive"
          and pools["pools"][0]["user"] == "mockworker.001",
          f"pools={pools}")
    fans = doc["fans"]
    check("cgminer fans: speeds supported, mode honestly null",
          fans["supported"] is True and fans["mode"] is None
          and [f["rpm"] for f in fans["fans"]] == [4320, 4380, 4440, 4500],
          f"fans={fans}")


def test_stock() -> None:
    doc = _inspect_doc("127.0.0.1", "--json",
                       "--http-port", str(STOCK_PORT),
                       "--cgminer-port", str(CLOSED_RPC))
    check("stock: claimed as stock", doc["source"] == "stock",
          f"source={doc.get('source')}")
    boards = doc["boards"]
    check("stock boards: acs from the status CGI, all chips ok",
          boards["supported"] is True
          and boards["boards"][0]["chips_ok"] == 114
          and boards["boards"][0]["chips_total"] == 114,
          f"boards={boards}")
    fans = doc["fans"]
    check("stock fans: speeds from the CGI, mode null",
          fans["supported"] is True and fans["mode"] is None
          and fans["fans"][0]["rpm"] == 4200,
          f"fans={fans}")
    pools = doc["pools"]
    check("stock pools: unsupported marker with the no-source reason",
          pools["supported"] is False
          and "no pool list" in pools["reason"],
          f"pools={pools}")


# ---------------------------------------------------------------------------
# credential resolution reuse (the v0.23 / v0.24 layers, not a copy)
# ---------------------------------------------------------------------------

def _write_json(tmp: str, name: str, data) -> str:
    path = Path(tmp) / name
    path.write_text(json.dumps(data), encoding="utf-8")
    return str(path)


def test_locked_dashd(tmp: str) -> None:
    creds = _write_json(tmp, "creds.json", [
        {"label": "VNish khóa", "user": "root", "password": "dashd-pw",
         "type": "vnish"},
    ])
    doc = _inspect_doc("127.0.0.1", "--json",
                       "--http-port", str(LOCKED_PORT),
                       "--cgminer-port", str(CLOSED_RPC),
                       "--creds-file", creds)
    check("locked dashd: the winning creds-file set claims it (+ label)",
          doc["source"] == "vnish" and doc["cred_label"] == "VNish khóa",
          f"source={doc.get('source')} label={doc.get('cred_label')!r}")
    boards = doc["boards"]
    check("locked dashd: boards from summary counts, chips list absent",
          boards["supported"] is True
          and boards["boards"][0]["stable"] == 114
          and boards["boards"][0]["chips"] is None,
          f"boards={boards}")
    check("locked dashd: pools unsupported — summary carries none",
          doc["pools"]["supported"] is False
          and "no pools list" in doc["pools"]["reason"],
          f"pools={doc['pools']}")
    check("locked dashd: fans supported with mode absent (no settings)",
          doc["fans"]["supported"] is True
          and doc["fans"]["mode"] is None
          and len(doc["fans"]["fans"]) == 4,
          f"fans={doc['fans']}")

    wrong = _write_json(tmp, "wrong.json", [
        {"label": "Sai", "user": "root", "password": "sai-pw",
         "type": "vnish"},
    ])
    doc = _inspect_doc("127.0.0.1", "--json",
                       "--http-port", str(LOCKED_PORT),
                       "--cgminer-port", str(CLOSED_RPC),
                       "--creds-file", wrong)
    check("locked dashd, wrong creds: still surfaces as vnish…",
          doc["source"] == "vnish", f"source={doc.get('source')}")
    check("…with every section unsupported on the 401, none faked",
          doc["boards"]["supported"] is False
          and doc["pools"]["supported"] is False
          and doc["fans"]["supported"] is False
          and "401" in doc["boards"]["reason"],
          f"boards={doc['boards']}")

    # --group: the group's own sets lead (the v0.24 layering).
    groups_file = _write_json(tmp, "groups.json", {
        "version": 1,
        "groups": [{
            "name": "Trại khóa", "targets": "127.0.0.1",
            "creds": [{"label": "Theo nhóm", "user": "root",
                       "password": "dashd-pw", "type": "vnish"}],
        }],
    })
    doc = _inspect_doc("127.0.0.1", "--json",
                       "--http-port", str(LOCKED_PORT),
                       "--cgminer-port", str(CLOSED_RPC),
                       "--group", "Trại khóa",
                       "--groups-file", groups_file)
    check("inspect --group: the group's set wins (label proves it)",
          doc["source"] == "vnish" and doc["cred_label"] == "Theo nhóm",
          f"label={doc.get('cred_label')!r}")
    rc, out, err = _inspect("127.0.0.1", "--json",
                            "--group", "Không có nhóm này",
                            "--groups-file", groups_file)
    check("inspect --group: unknown group exits 2, stdout empty",
          rc == 2 and out == "" and "group not found" in err,
          f"rc={rc} err={err[:80]!r}")


# ---------------------------------------------------------------------------
# contracts: validation + the unclaimed-device document
# ---------------------------------------------------------------------------

def test_contracts(tmp: str) -> None:
    for target in ["not-an-ip", "127.0.0.0/24", "999.1.1.1", "::1",
                   "127.0.0.1-127.0.0.9"]:
        rc, out, err = _inspect(target, "--json")
        check(f"validation: {target!r} exits 2, stdout empty",
              rc == 2 and out == "" and "not a single IPv4" in err,
              f"rc={rc} out={out[:40]!r} err={err[:60]!r}")
    bad_creds = _write_json(tmp, "bad.json", [{"user": "root"}])
    rc, out, err = _inspect("127.0.0.1", "--json",
                            "--creds-file", bad_creds)
    check("validation: malformed creds file exits 2 before any I/O",
          rc == 2 and out == "" and "creds" in err,
          f"rc={rc} err={err[:80]!r}")
    doc = _inspect_doc("127.0.0.99", "--json",
                       "--http-port", str(CLOSED_HTTP),
                       "--cgminer-port", str(CLOSED_RPC))
    check("unclaimed device: exit-0 error document, source null",
          doc["source"] is None and "error" in doc
          and "boards" not in doc,
          f"doc={doc}")


def main() -> int:
    servers = [
        Server([sys.executable, str(ROOT / "tests" / "mock_dashd.py"),
                "127.0.0.1", str(DASHD_PORT)], DASHD_PORT),
        Server([sys.executable, str(ROOT / "tests" / "mock_stock_fw.py"),
                "127.0.0.1", str(STOCK_PORT)], STOCK_PORT),
        Server([sys.executable, str(ROOT / "tests" / "mock_miner.py")],
               4028),
        Server([sys.executable, str(ROOT / "tests" / "mock_creds_miner.py"),
                "127.0.0.1", str(LOCKED_PORT), "dashd"], LOCKED_PORT),
    ]
    try:
        for server in servers:
            if not _wait_port(server.port):
                print(f"FAIL: mock on port {server.port} never came up")
                return 1
        test_vnish()
        test_cgminer()
        test_stock()
        with tempfile.TemporaryDirectory() as tmp:
            test_locked_dashd(tmp)
            test_contracts(tmp)
    finally:
        for server in servers:
            server.stop()
    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
