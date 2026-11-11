#!/usr/bin/env python3
"""v0.23.0 test — multi-credential scan (--creds-file).

Fleets run several machine lines with different web logins, so a
scan takes a LIST of credential sets (JSON file: label / user /
password / type, type in any|stock|vnish) and tries them per miner
in FAMILY order: sets tagged for the detected family first, then
"any" sets, then the rest — a wrong tag never locks a machine out.
The winning set's label lands on the record as cred_label and rides
the bridge JSON like any other field.

Fixtures: tests/mock_creds_miner.py — dashd mode (reads locked
behind POST /api/v1/unlock for password "dashd-pw") and stock mode
(digest auth for exactly stockuser/stockpw), both logging every
auth attempt so the ORDER is assertable, not just the outcome.

Asserts:
  * unit: ordered_creds family order (both families, typeless and
    unknown tags count as "any"); _load_creds_file normalisation
    (label defaults to the user, unknown/missing type -> "any");
  * dashd gated: the vnish-tagged set is listed SECOND but wins,
    and the stock-tagged set's password is NEVER tried as a dashd
    login (unlock log holds exactly the winning attempt);
  * dashd API-key method: against a dashd that accepts ONLY an
    x-api-key, a password set unlocks yet cannot read, and the
    vnish set carrying "api_key" wins with its label recorded;
  * dashd wrong-tag rescue: vnish set fails, a stock-TAGGED set
    holding the right dashd password still wins (tier 3);
  * dashd all-fail: the miner still surfaces — as a vnish
    FETCH_ERROR record carrying the 401 — with no cred_label;
  * stock: the stock-tagged set is listed SECOND but wins on the
    first auth attempt (the vnish set's user never reaches the
    stock endpoint); an "any" set rescues when the stock set fails;
  * legacy unchanged: --user/--password alone still works (no
    cred_label), a wrong legacy password finds nothing, and a
    locked dashd stays invisible without a creds file;
  * validation: missing / malformed / misshapen creds files exit 2.

Prints PASS lines; exit 1 on failure.
"""

import contextlib
import io
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

from beesky import cli  # noqa: E402
from beesky.core.discover import ordered_creds  # noqa: E402

FAILURES: list[str] = []

DASHD_PORT = 18811
STOCK_PORT = 18812
APIKEY_PORT = 18813


def check(label: str, condition: bool, extra: str = "") -> None:
    if condition:
        print(f"PASS: {label}")
    else:
        FAILURES.append(label)
        print(f"FAIL: {label} {extra}")


# ---------------------------------------------------------------------------
# unit-level: ordering + file normalisation
# ---------------------------------------------------------------------------

def test_ordering() -> None:
    sets = [
        {"label": "v1", "user": "u", "password": "p", "type": "vnish"},
        {"label": "a1", "user": "u", "password": "p", "type": "any"},
        {"label": "s1", "user": "u", "password": "p", "type": "stock"},
        {"label": "s2", "user": "u", "password": "p", "type": "stock"},
        {"label": "x1", "user": "u", "password": "p"},  # typeless -> any
        {"label": "v2", "user": "u", "password": "p", "type": "vnish"},
    ]
    stock_order = [c["label"] for c in ordered_creds(sets, "stock")]
    check("order: stock family first, then any, then the rest",
          stock_order == ["s1", "s2", "a1", "x1", "v1", "v2"],
          f"got {stock_order}")
    vnish_order = [c["label"] for c in ordered_creds(sets, "vnish")]
    check("order: vnish family first, then any, then the rest",
          vnish_order == ["v1", "v2", "a1", "x1", "s1", "s2"],
          f"got {vnish_order}")


def test_load_normalisation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "creds.json"
        path.write_text(json.dumps([
            {"user": "root", "password": "root"},
            {"label": "Kho", "user": "a", "password": "b",
             "type": "bogus"},
            {"label": "V", "user": "c", "password": "d",
             "type": "vnish"},
        ]), encoding="utf-8")
        creds = cli._load_creds_file(str(path))
    check("load: label defaults to the user name",
          creds[0]["label"] == "root")
    check("load: missing/unknown type normalises to any",
          creds[0]["type"] == "any" and creds[1]["type"] == "any")
    check("load: a real family tag survives", creds[2]["type"] == "vnish")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "keyonly.json"
        path.write_text(json.dumps([
            {"api_key": "k-123", "type": "vnish"},
        ]), encoding="utf-8")
        key_creds = cli._load_creds_file(str(path))
    check("load: an api_key-only entry is valid (no login needed)",
          key_creds[0]["api_key"] == "k-123"
          and key_creds[0]["type"] == "vnish"
          and key_creds[0]["user"] == "")
    check("load: api_key-only entry's label falls back to 'api_key'",
          key_creds[0]["label"] == "api_key")


def _run_cli(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), \
            contextlib.redirect_stderr(err):
        rc = cli.main(argv)
    return rc, out.getvalue(), err.getvalue()


def test_validation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        bad_json = Path(tmp) / "bad.json"
        bad_json.write_text("{not json", encoding="utf-8")
        not_list = Path(tmp) / "obj.json"
        not_list.write_text('{"user": "root"}', encoding="utf-8")
        bad_entry = Path(tmp) / "entry.json"
        bad_entry.write_text('[{"user": "root"}]', encoding="utf-8")
        for label, path in [("malformed JSON", bad_json),
                            ("non-list top level", not_list),
                            ("entry without password", bad_entry),
                            ("missing file", Path(tmp) / "nope.json")]:
            rc, _out, err = _run_cli(
                ["scan", "127.0.0.1", "--creds-file", str(path), "--json"])
            check(f"validation: {label} exits 2 with a creds message",
                  rc == 2 and "creds" in err, f"rc={rc} err={err[:80]!r}")


# ---------------------------------------------------------------------------
# subprocess scans against the gated mocks
# ---------------------------------------------------------------------------

def _wait_port(port: int, timeout_s: float = 15.0) -> bool:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.2)
    return False


class MockServer:
    def __init__(self, mode: str, port: int, log_path: Path,
                 extra_env: dict | None = None):
        env = dict(os.environ)
        env["BEESKY_MOCK_CREDS_LOG"] = str(log_path)
        if extra_env:
            env.update(extra_env)
        self.log_path = log_path
        self.proc = subprocess.Popen(
            [sys.executable, str(ROOT / "tests" / "mock_creds_miner.py"),
             "127.0.0.1", str(port), mode],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
        self.port = port

    def attempts(self) -> list[dict]:
        if not self.log_path.exists():
            return []
        return [json.loads(line) for line in
                self.log_path.read_text(encoding="utf-8").splitlines()
                if line.strip()]

    def stop(self) -> None:
        self.proc.terminate()
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def _scan(port: int, *extra: str) -> dict:
    proc = subprocess.run(
        [sys.executable, "-m", "beesky", "scan", "127.0.0.1",
         "--http-port", str(port), "--json", *extra],
        cwd=ROOT, capture_output=True, text=True, timeout=90)
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        raise AssertionError(
            f"scan stdout not one JSON doc: rc={proc.returncode} "
            f"out={proc.stdout[:160]!r} err={proc.stderr[:160]!r}")


def _write_creds(tmp: str, name: str, sets: list[dict]) -> str:
    path = Path(tmp) / name
    path.write_text(json.dumps(sets), encoding="utf-8")
    return str(path)


def test_dashd_family_first(tmp: str, server: MockServer) -> None:
    # The winning (vnish) set is listed SECOND; the stock-tagged
    # set's password must never be tried as a dashd login at all.
    creds = _write_creds(tmp, "dashd_mixed.json", [
        {"label": "Kho gốc", "user": "root", "password": "stockpw",
         "type": "stock"},
        {"label": "VNish trại", "user": "root", "password": "dashd-pw",
         "type": "vnish"},
    ])
    before = len(server.attempts())
    doc = _scan(DASHD_PORT, "--creds-file", creds)
    new = server.attempts()[before:]
    check("dashd: locked miner found via the creds file",
          doc["found"] == 1, f"found={doc.get('found')}")
    rec = doc["records"][0] if doc["records"] else {}
    check("dashd: record is the vnish S19, healthy",
          rec.get("source") == "vnish" and rec.get("status") == "OK",
          f"rec={ {k: rec.get(k) for k in ('source', 'status')} }")
    check("dashd: cred_label names the winning vnish set (bridge JSON)",
          rec.get("cred_label") == "VNish trại",
          f"cred_label={rec.get('cred_label')!r}")
    unlocks = [a["pw"] for a in new if a["kind"] == "unlock"]
    check("dashd: only the vnish set was tried as a login",
          unlocks == ["dashd-pw"], f"unlock attempts={unlocks}")


def test_dashd_wrong_tag_rescue(tmp: str, server: MockServer) -> None:
    creds = _write_creds(tmp, "dashd_rescue.json", [
        {"label": "VNish sai", "user": "root", "password": "sai-pw",
         "type": "vnish"},
        {"label": "Gắn nhầm tag", "user": "root", "password": "dashd-pw",
         "type": "stock"},
    ])
    before = len(server.attempts())
    doc = _scan(DASHD_PORT, "--creds-file", creds)
    new = server.attempts()[before:]
    rec = doc["records"][0] if doc["records"] else {}
    check("dashd rescue: a wrong tag never locks the machine out",
          doc["found"] == 1 and rec.get("cred_label") == "Gắn nhầm tag",
          f"found={doc.get('found')} label={rec.get('cred_label')!r}")
    unlocks = [a["pw"] for a in new if a["kind"] == "unlock"]
    check("dashd rescue: family set tried first, rescue set second",
          unlocks == ["sai-pw", "dashd-pw"], f"unlocks={unlocks}")


def test_dashd_all_fail(tmp: str, server: MockServer) -> None:
    creds = _write_creds(tmp, "dashd_fail.json", [
        {"label": "VNish sai", "user": "root", "password": "sai-pw",
         "type": "vnish"},
    ])
    doc = _scan(DASHD_PORT, "--creds-file", creds)
    rec = doc["records"][0] if doc["records"] else {}
    problems = rec.get("problems") or [{}]
    check("dashd all-fail: the locked miner still surfaces",
          doc["found"] == 1 and rec.get("source") == "vnish",
          f"found={doc.get('found')} source={rec.get('source')!r}")
    check("dashd all-fail: it reports its auth error (401 FETCH_ERROR)",
          problems[0].get("code") == "FETCH_ERROR"
          and "401" in str(problems[0].get("detail")),
          f"problems={problems}")
    check("dashd all-fail: no cred_label on an error record",
          "cred_label" not in rec)


def test_dashd_api_key(tmp: str, server: MockServer) -> None:
    # The mock (BEESKY_MOCK_CREDS_API_KEY=farm-key-123) accepts ONLY
    # the x-api-key for reads: the password set's /unlock succeeds
    # but its token still cannot read, so the api_key set must win.
    creds = _write_creds(tmp, "dashd_apikey.json", [
        {"label": "Mật khẩu VNish", "user": "root",
         "password": "dashd-pw", "type": "vnish"},
        {"label": "API key trại", "api_key": "farm-key-123",
         "type": "vnish"},
    ])
    before = len(server.attempts())
    doc = _scan(APIKEY_PORT, "--creds-file", creds)
    new = server.attempts()[before:]
    rec = doc["records"][0] if doc["records"] else {}
    check("dashd api-key: key-only miner found, healthy",
          doc["found"] == 1 and rec.get("source") == "vnish"
          and rec.get("status") == "OK",
          f"found={doc.get('found')} source={rec.get('source')!r}")
    check("dashd api-key: cred_label names the api_key set",
          rec.get("cred_label") == "API key trại",
          f"cred_label={rec.get('cred_label')!r}")
    unlocks = [a["pw"] for a in new if a["kind"] == "unlock"]
    keys = [a["key"] for a in new if a["kind"] == "apikey"]
    check("dashd api-key: password set tried first (unlock ok, read no)",
          unlocks == ["dashd-pw"], f"unlocks={unlocks}")
    check("dashd api-key: the winning key reached /summary",
          "farm-key-123" in keys, f"apikey attempts={keys}")


def test_dashd_legacy_invisible(tmp: str, server: MockServer) -> None:
    # No creds file: exactly the pre-v0.23 behaviour — anonymous
    # reads fail and the locked dashd is not surfaced at all.
    doc = _scan(DASHD_PORT)
    check("dashd legacy: locked dashd stays invisible (unchanged)",
          doc["found"] == 0, f"found={doc.get('found')}")


def test_stock_family_first(tmp: str, server: MockServer) -> None:
    # The winning (stock) set is listed SECOND; detection must try
    # it FIRST against the stock endpoint — the vnish set's user
    # never reaches the digest endpoint at all.
    creds = _write_creds(tmp, "stock_mixed.json", [
        {"label": "VNish trại", "user": "vnishuser",
         "password": "dashd-pw", "type": "vnish"},
        {"label": "Kho S19", "user": "stockuser", "password": "stockpw",
         "type": "stock"},
    ])
    before = len(server.attempts())
    doc = _scan(STOCK_PORT, "--creds-file", creds)
    new = server.attempts()[before:]
    check("stock: digest miner found via the creds file",
          doc["found"] == 1, f"found={doc.get('found')}")
    rec = doc["records"][0] if doc["records"] else {}
    check("stock: record is stock + cred_label names the stock set",
          rec.get("source") == "stock"
          and rec.get("cred_label") == "Kho S19",
          f"source={rec.get('source')!r} label={rec.get('cred_label')!r}")
    users = [a["user"] for a in new if a["kind"] == "auth"]
    check("stock: the stock set authenticated; vnish user never tried",
          users and all(u == "stockuser" for u in users),
          f"auth attempts={users}")


def test_stock_any_rescue(tmp: str, server: MockServer) -> None:
    creds = _write_creds(tmp, "stock_rescue.json", [
        {"label": "Kho sai", "user": "wronguser", "password": "wrongpw",
         "type": "stock"},
        {"label": "Dự phòng", "user": "stockuser", "password": "stockpw",
         "type": "any"},
    ])
    before = len(server.attempts())
    doc = _scan(STOCK_PORT, "--creds-file", creds)
    new = server.attempts()[before:]
    rec = doc["records"][0] if doc["records"] else {}
    check("stock rescue: the 'any' set wins after the family set fails",
          doc["found"] == 1 and rec.get("cred_label") == "Dự phòng",
          f"found={doc.get('found')} label={rec.get('cred_label')!r}")
    users = [a["user"] for a in new if a["kind"] == "auth"]
    check("stock rescue: family set was attempted before the rescue",
          bool(users) and users[0] == "wronguser"
          and users[-1] == "stockuser",
          f"auth attempts={users}")


def test_stock_legacy(tmp: str, server: MockServer) -> None:
    doc = _scan(STOCK_PORT, "--user", "stockuser",
                "--password", "stockpw")
    rec = doc["records"][0] if doc["records"] else {}
    check("stock legacy: --user/--password still works, no label",
          doc["found"] == 1 and rec.get("source") == "stock"
          and "cred_label" not in rec,
          f"found={doc.get('found')} rec keys={sorted(rec)[:6]}")
    doc = _scan(STOCK_PORT, "--user", "stockuser",
                "--password", "wrongpw")
    check("stock legacy: a wrong password finds nothing (unchanged)",
          doc["found"] == 0, f"found={doc.get('found')}")


def main() -> int:
    test_ordering()
    test_load_normalisation()
    test_validation()
    with tempfile.TemporaryDirectory() as tmp:
        dashd = MockServer("dashd", DASHD_PORT, Path(tmp) / "dashd.log")
        stock = MockServer("stock", STOCK_PORT, Path(tmp) / "stock.log")
        apikey = MockServer("dashd", APIKEY_PORT, Path(tmp) / "apikey.log",
                            extra_env={
                                "BEESKY_MOCK_CREDS_API_KEY": "farm-key-123"})
        try:
            if not (_wait_port(DASHD_PORT) and _wait_port(STOCK_PORT)
                    and _wait_port(APIKEY_PORT)):
                check("mocks came up", False)
            else:
                test_dashd_family_first(tmp, dashd)
                test_dashd_wrong_tag_rescue(tmp, dashd)
                test_dashd_all_fail(tmp, dashd)
                test_dashd_legacy_invisible(tmp, dashd)
                test_dashd_api_key(tmp, apikey)
                test_stock_family_first(tmp, stock)
                test_stock_any_rescue(tmp, stock)
                test_stock_legacy(tmp, stock)
        finally:
            dashd.stop()
            stock.stop()
            apikey.stop()
    print()
    if FAILURES:
        print(f"CREDS TEST FAILED: {len(FAILURES)} assertion(s): "
              f"{FAILURES}")
        return 1
    print("CREDS TEST PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
