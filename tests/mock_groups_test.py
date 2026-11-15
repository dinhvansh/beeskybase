#!/usr/bin/env python3
"""v0.24.0 test — network groups (the HashCore Toolkit port).

A group is a named scan target with its own credential sets,
autoscan settings and a persisted last-scan summary, stored in
beesky-groups.json (docs/network-groups-mapping.md). The port of
HashCore's global → per-group override layering onto the v0.23
list model: a group scan merges group sets BEFORE global sets and
lets ordered_creds partition the merged list, so the try order is
group-family → global-family → group-any → global-any → the rest.

Asserts:
  * store: save/load round-trip keeps every field; a missing file
    loads empty; a bare-list document loads too; malformed JSON,
    a nameless entry, a bad creds shape and invalid targets all
    fail loud (GroupError);
  * merge units: the merged list's ordered_creds sequence is
    exactly the layered order above; merge_import replaces by
    name in place and appends new names;
  * CLI: groups add/list/show/remove (+ duplicate name, invalid
    targets, unknown name all exit 2); scan --group with an
    unknown name exits 2; export/import round-trip, same-name
    replacement, malformed/invalid imports exit 2 and change
    nothing;
  * live scans (mock dashd, subprocess bridge): a GROUP set beats
    a global same-family set (the global wrong password is never
    tried); the GLOBAL set rescues when the group's set fails
    (both attempts, in order); a group with no creds of its own
    falls back to the global file; last_scan is persisted after a
    group scan with the right counts; a groupless scan never
    touches the store.

Fixture: tests/mock_creds_miner.py dashd mode (reads locked
behind POST /api/v1/unlock for password "dashd-pw"), logging every
auth attempt so the ORDER is assertable.

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
from beesky.core import groups as groups_mod  # noqa: E402
from beesky.core.discover import ordered_creds  # noqa: E402

FAILURES: list[str] = []

DASHD_PORT = 18821


def check(label: str, condition: bool, extra: str = "") -> None:
    if condition:
        print(f"PASS: {label}")
    else:
        FAILURES.append(label)
        print(f"FAIL: {label} {extra}")


def _run_cli(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), \
            contextlib.redirect_stderr(err):
        rc = cli.main(argv)
    return rc, out.getvalue(), err.getvalue()


def _group(name, targets="127.0.0.1", creds=None, **kw):
    g = {"name": name, "targets": targets, "creds": creds or []}
    g.update(kw)
    return groups_mod.normalise_group(g, "test")


# ---------------------------------------------------------------------------
# store units
# ---------------------------------------------------------------------------

def test_store_units(tmp: str) -> None:
    path = Path(tmp) / "beesky-groups.json"
    store = groups_mod.GroupStore(path)
    check("store: a missing file loads as no groups", store.load() == [])

    g1 = _group("Trại chính", "192.168.2.0/24",
                description="Sảnh chính — S19 Pro + L9",
                creds=[{"label": "VNish trại", "user": "root",
                        "password": "dashd-pw", "type": "vnish"}],
                autoscan={"enabled": True, "interval_min": 45},
                last_scan={"at": "2026-11-11T08:00:00+07:00",
                           "scanned": 254, "found": 63, "ok": 12,
                           "check": 51, "error": 0})
    g2 = _group("Kho phụ", "192.168.3.0/24")
    store.save([g1, g2])
    loaded = groups_mod.GroupStore(path).load()
    check("store: round-trip keeps both groups",
          [g["name"] for g in loaded] == ["Trại chính", "Kho phụ"])
    check("store: round-trip keeps description + creds + autoscan + last_scan",
          loaded[0]["description"] == "Sảnh chính — S19 Pro + L9"
          and loaded[0]["creds"][0]["label"] == "VNish trại"
          and loaded[0]["autoscan"] == {"enabled": True, "interval_min": 45}
          and loaded[0]["last_scan"]["found"] == 63)
    check("store: description defaults to empty string",
          loaded[1]["description"] == "")
    check("store: defaults fill in (id minted, autoscan off, no scan)",
          bool(loaded[1]["id"])
          and loaded[1]["autoscan"] == {"enabled": False, "interval_min": 30}
          and loaded[1]["last_scan"] is None)
    doc = json.loads(path.read_text(encoding="utf-8"))
    check("store: the document is versioned",
          doc.get("version") == 1 and isinstance(doc.get("groups"), list))

    bare = Path(tmp) / "bare.json"
    bare.write_text(json.dumps([{"name": "Lẻ", "targets": "10.0.0.1"}]),
                    encoding="utf-8")
    check("store: a bare-list document loads too",
          [g["name"] for g in groups_mod.GroupStore(bare).load()] == ["Lẻ"])

    bad = Path(tmp) / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    try:
        groups_mod.GroupStore(bad).load()
        raised = False
    except groups_mod.GroupError:
        raised = True
    check("store: malformed JSON fails loud (GroupError)", raised)

    for label, raw in [
            ("a nameless entry", [{"targets": "10.0.0.1"}]),
            ("invalid targets", [{"name": "X", "targets": "999.0.0.0/24"}]),
            ("a bad creds shape", [{"name": "X", "targets": "10.0.0.1",
                                    "creds": [{"user": "root"}]}]),
            ("a non-string description",
             [{"name": "X", "targets": "10.0.0.1", "description": 42}]),
            ("a zero autoscan interval",
             [{"name": "X", "targets": "10.0.0.1",
               "autoscan": {"enabled": True, "interval_min": 0}}])]:
        badf = Path(tmp) / "bad_entry.json"
        badf.write_text(json.dumps(raw), encoding="utf-8")
        try:
            groups_mod.GroupStore(badf).load()
            raised = False
        except groups_mod.GroupError:
            raised = True
        check(f"store: {label} fails loud", raised)


# ---------------------------------------------------------------------------
# merge-order units
# ---------------------------------------------------------------------------

def test_merge_units() -> None:
    def s(label, typ):
        return {"label": label, "user": "u", "password": "p", "type": typ}

    group_sets = [s("G-stock", "stock"), s("G-any", "any"),
                  s("G-vnish", "vnish")]
    global_sets = [s("L-stock", "stock"), s("L-any", "any"),
                   s("L-vnish", "vnish")]
    merged = groups_mod.effective_creds(group_sets, global_sets)
    order = [c["label"] for c in ordered_creds(merged, "stock")]
    check("merge: order = group family, global family, group any, "
          "global any, group rest, global rest",
          order == ["G-stock", "L-stock", "G-any", "L-any",
                    "G-vnish", "L-vnish"],
          f"got {order}")
    check("merge: no sets anywhere -> None (legacy behaviour)",
          groups_mod.effective_creds([], None) is None
          and groups_mod.effective_creds(None, None) is None)
    check("merge: one layer only -> that layer, in order",
          [c["label"] for c in
           groups_mod.effective_creds(None, global_sets)]
          == ["L-stock", "L-any", "L-vnish"])

    existing = [_group("A", "10.0.0.0/24"), _group("B", "10.0.1.0/24")]
    imported = [_group("B", "10.0.9.0/24"), _group("C", "10.0.2.0/24")]
    merged_groups = groups_mod.merge_import(existing, imported)
    check("import merge: same name replaced in place, new appended",
          [g["name"] for g in merged_groups] == ["A", "B", "C"]
          and merged_groups[1]["targets"] == "10.0.9.0/24"
          and merged_groups[0]["targets"] == "10.0.0.0/24")


# ---------------------------------------------------------------------------
# CLI: groups CRUD + export/import
# ---------------------------------------------------------------------------

def test_cli_groups(tmp: str) -> None:
    store = str(Path(tmp) / "cli-groups.json")

    def groups_cli(*argv):
        return _run_cli(["groups", "--groups-file", store, *argv])

    rc, out, _ = groups_cli("list")
    check("cli: empty store lists cleanly", rc == 0 and "No groups" in out)
    rc, _, _ = groups_cli("add", "--name", "Trại A",
                          "--targets", "192.168.2.0/24")
    check("cli: add creates a group", rc == 0)
    rc, _, err = groups_cli("add", "--name", "Trại A",
                            "--targets", "192.168.9.0/24")
    check("cli: a duplicate name exits 2",
          rc == 2 and "already exists" in err)
    rc, _, err = groups_cli("add", "--name", "Trại B",
                            "--targets", "999.1.1.0/24")
    check("cli: invalid targets exit 2", rc == 2 and "invalid targets" in err)
    rc, _, _ = groups_cli("add", "--name", "Trại B",
                          "--targets", "192.168.3.0/24")
    rc, out, _ = groups_cli("list")
    check("cli: list shows both groups with their targets",
          rc == 0 and "Trại A" in out and "192.168.3.0/24" in out
          and "never scanned" in out)
    rc, out, _ = groups_cli("show", "Trại A")
    shown = json.loads(out) if rc == 0 else {}
    check("cli: show prints the group as JSON",
          shown.get("name") == "Trại A"
          and shown.get("targets") == "192.168.2.0/24"
          and shown.get("autoscan", {}).get("enabled") is False)
    rc, _, err = groups_cli("show", "Không có")
    check("cli: show of an unknown group exits 2",
          rc == 2 and "not found" in err)
    rc, _, _ = groups_cli("remove", "Trại B")
    check("cli: remove deletes the group", rc == 0)
    rc, _, err = groups_cli("remove", "Trại B")
    check("cli: removing an unknown group exits 2", rc == 2)

    rc, _, err = _run_cli(["scan", "--group", "Không có",
                           "--groups-file", store, "--json"])
    check("cli: scan --group with an unknown name exits 2",
          rc == 2 and "group not found" in err, f"rc={rc} err={err[:80]!r}")

    # export / import
    export_file = str(Path(tmp) / "export.json")
    rc, _, _ = groups_cli("export", export_file)
    exported = json.loads(Path(export_file).read_text(encoding="utf-8"))
    check("cli: export writes the versioned document",
          rc == 0 and exported["version"] == 1
          and [g["name"] for g in exported["groups"]] == ["Trại A"])

    other = str(Path(tmp) / "other-groups.json")
    _run_cli(["groups", "--groups-file", other, "add",
              "--name", "Kho X", "--targets", "10.0.0.0/24"])
    rc, out, _ = _run_cli(["groups", "--groups-file", other,
                           "import", export_file])
    names = [g["name"] for g in groups_mod.GroupStore(other).load()]
    check("cli: import adds new groups and keeps existing ones",
          rc == 0 and names == ["Kho X", "Trại A"], f"names={names}")

    changed = Path(tmp) / "changed.json"
    changed.write_text(json.dumps({"version": 1, "groups": [
        {"name": "Trại A", "targets": "172.16.0.0/24"}]}),
        encoding="utf-8")
    rc, out, _ = _run_cli(["groups", "--groups-file", other,
                           "import", str(changed)])
    groups_now = groups_mod.GroupStore(other).load()
    check("cli: import replaces a same-name group, keeps the rest",
          rc == 0 and "1 replaced" in out
          and [g["name"] for g in groups_now] == ["Kho X", "Trại A"]
          and groups_now[1]["targets"] == "172.16.0.0/24")

    broken = Path(tmp) / "broken.json"
    broken.write_text("{nope", encoding="utf-8")
    rc, _, _ = _run_cli(["groups", "--groups-file", other,
                         "import", str(broken)])
    check("cli: a malformed import file exits 2", rc == 2)
    invalid = Path(tmp) / "invalid.json"
    invalid.write_text(json.dumps(
        [{"name": "Hỏng", "targets": "999.0.0.0/24"}]), encoding="utf-8")
    rc, _, _ = _run_cli(["groups", "--groups-file", other,
                         "import", str(invalid)])
    names_after = [g["name"] for g in groups_mod.GroupStore(other).load()]
    check("cli: an invalid import exits 2 and changes nothing",
          rc == 2 and names_after == ["Kho X", "Trại A"])


# ---------------------------------------------------------------------------
# live scans against the gated mock dashd (subprocess bridge)
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
    def __init__(self, port: int, log_path: Path):
        env = dict(os.environ)
        env["BEESKY_MOCK_CREDS_LOG"] = str(log_path)
        self.log_path = log_path
        self.proc = subprocess.Popen(
            [sys.executable, str(ROOT / "tests" / "mock_creds_miner.py"),
             "127.0.0.1", str(port), "dashd"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)

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


def _write_json(path: Path, data) -> str:
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return str(path)


def _scan_group(store: str, name: str, *extra: str):
    proc = subprocess.run(
        [sys.executable, "-m", "beesky", "scan", "--group", name,
         "--groups-file", store, "--http-port", str(DASHD_PORT),
         "--json", *extra],
        cwd=ROOT, capture_output=True, text=True, timeout=90)
    return proc


def test_live_scans(tmp: str, server: MockServer) -> None:
    store_path = Path(tmp) / "live-groups.json"
    global_creds = _write_json(Path(tmp) / "global.json", [
        {"label": "Toàn cục sai", "user": "root", "password": "wrong-pw",
         "type": "vnish"},
    ])

    # 1) the GROUP set wins over the global same-family set.
    store = _write_json(store_path, {"version": 1, "groups": [
        {"name": "Trại dashd", "targets": "127.0.0.1",
         "creds": [{"label": "Nhóm thắng", "user": "root",
                    "password": "dashd-pw", "type": "vnish"}]},
        {"name": "Chưa quét", "targets": "127.0.0.1"},
    ]})
    before = len(server.attempts())
    proc = _scan_group(store, "Trại dashd", "--creds-file", global_creds)
    doc = json.loads(proc.stdout)
    new = server.attempts()[before:]
    rec = doc["records"][0] if doc["records"] else {}
    check("live: group scan finds the locked miner via the group",
          proc.returncode == 0 and doc["found"] == 1,
          f"rc={proc.returncode} found={doc.get('found')}")
    check("live: the GROUP set wins (cred_label)",
          rec.get("cred_label") == "Nhóm thắng",
          f"cred_label={rec.get('cred_label')!r}")
    unlocks = [a["pw"] for a in new if a["kind"] == "unlock"]
    check("live: the global set was never tried after the group win",
          unlocks == ["dashd-pw"], f"unlocks={unlocks}")

    saved = groups_mod.GroupStore(store).load()
    scanned_group = groups_mod.find_group(saved, "Trại dashd")
    last = scanned_group["last_scan"] or {}
    check("live: last_scan persisted with the scan's counts",
          last.get("found") == 1 and last.get("ok") == 1
          and last.get("check") == 0 and last.get("error") == 0
          and last.get("scanned") == 1 and bool(last.get("at")),
          f"last_scan={last}")
    untouched = groups_mod.find_group(saved, "Chưa quét")
    check("live: the other group's last_scan stays null",
          untouched is not None and untouched["last_scan"] is None)

    # 2) the GLOBAL set rescues when the group's set fails.
    store = _write_json(store_path, {"version": 1, "groups": [
        {"name": "Trại dashd", "targets": "127.0.0.1",
         "creds": [{"label": "Nhóm sai", "user": "root",
                    "password": "group-wrong", "type": "vnish"}]},
    ]})
    rescue_creds = _write_json(Path(tmp) / "rescue.json", [
        {"label": "Toàn cục cứu", "user": "root", "password": "dashd-pw",
         "type": "vnish"},
    ])
    before = len(server.attempts())
    proc = _scan_group(store, "Trại dashd", "--creds-file", rescue_creds)
    doc = json.loads(proc.stdout)
    new = server.attempts()[before:]
    rec = doc["records"][0] if doc["records"] else {}
    check("live: the GLOBAL set rescues a failed group set",
          doc["found"] == 1 and rec.get("cred_label") == "Toàn cục cứu",
          f"found={doc.get('found')} label={rec.get('cred_label')!r}")
    unlocks = [a["pw"] for a in new if a["kind"] == "unlock"]
    check("live: group set tried first, global rescue second",
          unlocks == ["group-wrong", "dashd-pw"], f"unlocks={unlocks}")

    # 3) a group with no creds of its own uses the global file.
    store = _write_json(store_path, {"version": 1, "groups": [
        {"name": "Trại dashd", "targets": "127.0.0.1"},
    ]})
    proc = _scan_group(store, "Trại dashd", "--creds-file", rescue_creds)
    doc = json.loads(proc.stdout)
    rec = doc["records"][0] if doc["records"] else {}
    check("live: a cred-less group falls back to the global sets",
          doc["found"] == 1 and rec.get("cred_label") == "Toàn cục cứu",
          f"found={doc.get('found')} label={rec.get('cred_label')!r}")

    # 4) unknown group via subprocess: clean exit 2, no scan output.
    proc = _scan_group(store, "Không có")
    check("live: an unknown group exits 2 with the store named",
          proc.returncode == 2 and "group not found" in proc.stderr
          and proc.stdout == "",
          f"rc={proc.returncode} err={proc.stderr[:80]!r}")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        test_store_units(tmp)
        test_merge_units()
        test_cli_groups(tmp)
        server = MockServer(DASHD_PORT, Path(tmp) / "dashd.log")
        try:
            if not _wait_port(DASHD_PORT):
                check("mock dashd came up", False)
            else:
                test_live_scans(tmp, server)
        finally:
            server.stop()
    print()
    if FAILURES:
        print(f"GROUPS TEST FAILED: {len(FAILURES)} assertion(s): "
              f"{FAILURES}")
        return 1
    print("GROUPS TEST PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
