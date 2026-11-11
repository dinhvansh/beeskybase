#!/usr/bin/env python3
"""v0.16 test — the agent as a true background service + install
security.

No hardware, no Windows: the Windows-only pieces are verified at
the seams they expose off Windows (the generated Task Scheduler
XML is a pure function; DPAPI is forced through the
``agent_config._dpapi_available`` probe with a reversible fake
standing in for the OS crypto).

Covers:

  * key protection (beesky/agent_config.py): with the DPAPI branch
    forced ON, save() writes key_protected and NO plain-text key
    anywhere in the file, and load() returns the key; a protect
    failure degrades to a plain-text save instead of losing the
    config; with the branch OFF (POSIX reality) the key stays plain
    and the file is chmod 0600; a legacy plain-text config is
    migrated to protected form on its next save; an undecryptable
    blob loads as an empty key.
  * log hygiene (beesky/agent.py redact + the run stream): the
    redacting stream scrubs the key from everything written
    through it.
  * task v2: task_xml() carries the SYSTEM principal (S-1-5-18),
    HighestAvailable, BootTrigger with PT30S delay, LogonTrigger,
    Hidden=true, ExecutionTimeLimit PT0S, RestartOnFailure
    PT1M x5, no battery stops, RunOnlyIfNetworkAvailable=false —
    and points at beesky-agentw.exe with the config path baked in;
    --console points at beesky-agent.exe instead.
  * packaging: the spec builds beesky-agentw (console=False) from
    the agent Analysis; agent.iss ships it; the CI workflow ships
    it in artifact + Release + the signed update-manifest list;
    versions in sync at 0.29.0.
  * end-to-end (subprocesses on 127.0.0.1; real cloud + mock
    dashd): `run --once` from a config file writes
    agent-status.json (ok, 1 miner) and an agent.log that contains
    pass output but NOT the agent key; a wrong key yields
    ok=false + error in the status and still no key in the log;
    `run --once --background` prints nothing to stdout (all output
    lands in the log); a non-local http:// cloud URL produces the
    unencrypted warning (localhost does not).
  * config GUI (under xvfb-run): the "Trạng thái chạy ngầm" card
    renders Chưa có dữ liệu / Đang chạy tốt (with miner count) /
    Lỗi gần nhất from fabricated status files, the "Xem log"
    button exists, and the Cloud URL hint appears for a non-local
    http:// URL and clears for https / localhost.

Prints PASS lines; exit 1 on failure. Run via
tests/run_mock_test_v16.sh (which appends evidence to
tests/RESULTS.md).
"""

import base64
import http.cookiejar
import json
import os
import re
import stat
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

import beesky  # noqa: E402
from beesky import agent, agent_app, agent_config  # noqa: E402
from beesky.agent_config import AgentConfig  # noqa: E402

CLOUD_PORT = 18796
DASHD_PORT = 18084
BASE = f"http://127.0.0.1:{CLOUD_PORT}"
SITE = "Xưởng Agent Ngầm"
PASSWORD = "mat-khau-test"

_opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({}),
    urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
_plain = urllib.request.build_opener(urllib.request.ProxyHandler({}))
FAILURES: list[str] = []


def check(label: str, condition: bool, extra: str = "") -> None:
    if condition:
        print(f"PASS: {label}")
    else:
        print(f"FAIL: {label} {extra}")
        FAILURES.append(label)


def fetch(path: str, opener=_plain, method: str = "GET",
          data: bytes | None = None,
          headers: dict | None = None) -> tuple[int, str]:
    request = urllib.request.Request(
        BASE + path, method=method, data=data, headers=headers or {})
    try:
        with opener.open(request, timeout=5) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")


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


# ---------------------------------------------------------------------------
# key protection — DPAPI branch forced through the probe
# ---------------------------------------------------------------------------

def _fake_protect(plain: str) -> str:
    """Deterministic reversible stand-in for DPAPI (tests only)."""
    return base64.b64encode(
        ("FAKE-DPAPI::" + plain).encode("utf-8")[::-1]).decode("ascii")


def _fake_unprotect(blob: str) -> str:
    raw = base64.b64decode(blob.encode("ascii"))[::-1].decode("utf-8")
    if not raw.startswith("FAKE-DPAPI::"):
        raise OSError("foreign blob")
    return raw[len("FAKE-DPAPI::"):]


def _patched_config(probe, protect=None, unprotect=None):
    """Context manager monkeypatching agent_config's DPAPI seams."""
    class _Patch:
        def __enter__(self):
            self._saved = (agent_config._dpapi_available,
                           agent_config.protect_key,
                           agent_config.unprotect_key)
            agent_config._dpapi_available = probe
            if protect is not None:
                agent_config.protect_key = protect
            if unprotect is not None:
                agent_config.unprotect_key = unprotect
            return self

        def __exit__(self, *exc):
            (agent_config._dpapi_available, agent_config.protect_key,
             agent_config.unprotect_key) = self._saved
            return False
    return _Patch()


def test_key_protection(tmp: Path) -> None:
    path = tmp / "protected" / "agent-config.json"
    cfg = AgentConfig(target="192.168.1.0/24",
                      cloud_url="https://cloud.example.com",
                      key="top-secret-key-xyz", site="Xưởng 1")
    with _patched_config(lambda: True, _fake_protect, _fake_unprotect):
        cfg.save(path)
        raw = path.read_text(encoding="utf-8")
        check("dpapi: saved file contains NO plain-text key",
              "top-secret-key-xyz" not in raw)
        on_disk = json.loads(raw)
        check("dpapi: key field emptied, key_protected present",
              on_disk.get("key") == ""
              and bool(on_disk.get("key_protected")))
        loaded = AgentConfig.load(path)
        check("dpapi: load() transparently returns the plain key",
              loaded.key == "top-secret-key-xyz"
              and loaded.site == "Xưởng 1")

    def _boom(_plain: str) -> str:
        raise OSError("simulated DPAPI failure")

    with _patched_config(lambda: True, _boom, _fake_unprotect):
        cfg.save(path)
        check("dpapi: a protect failure degrades to plain text "
              "(config never lost)",
              "top-secret-key-xyz" in path.read_text(encoding="utf-8")
              and AgentConfig.load(path).key == "top-secret-key-xyz")

    with _patched_config(lambda: False):
        cfg.save(path)
        check("posix: without DPAPI the key stays plain text",
              "top-secret-key-xyz" in path.read_text(encoding="utf-8"))
        if not sys.platform.startswith("win"):
            mode = stat.S_IMODE(os.stat(path).st_mode)
            check("posix: config file is chmod 0600 after save",
                  mode == 0o600, oct(mode))

    # migration: a legacy plain-text file is upgraded on next save
    legacy = tmp / "legacy" / "agent-config.json"
    legacy.parent.mkdir(parents=True, exist_ok=True)
    legacy.write_text(json.dumps(
        {"target": "t", "cloud_url": "https://c", "key": "legacy-key",
         "site": "s"}), encoding="utf-8")
    with _patched_config(lambda: True, _fake_protect, _fake_unprotect):
        migrated = AgentConfig.load(legacy)
        check("migration: legacy plain-text key still loads",
              migrated.key == "legacy-key")
        migrated.save(legacy)
        check("migration: next save rewrites the key protected",
              "legacy-key" not in legacy.read_text(encoding="utf-8")
              and AgentConfig.load(legacy).key == "legacy-key")

    # a blob from another machine loads as an empty key, no crash
    foreign = tmp / "foreign" / "agent-config.json"
    foreign.parent.mkdir(parents=True, exist_ok=True)
    foreign.write_text(json.dumps(
        {"target": "t", "cloud_url": "https://c", "key": "",
         "key_protected": _fake_protect("someone-elses-key"),
         "site": "s"}), encoding="utf-8")
    with _patched_config(lambda: True, _fake_protect,
                         lambda _b: (_ for _ in ()).throw(
                             OSError("different machine"))):
        check("dpapi: an undecryptable blob loads as an empty key",
              AgentConfig.load(foreign).key == "")


# ---------------------------------------------------------------------------
# log hygiene
# ---------------------------------------------------------------------------

def test_redaction(tmp: Path) -> None:
    check("redact: every occurrence of the secret is masked",
          agent.redact("Bearer abc123; key abc123", "abc123")
          == "Bearer ***; key ***")
    check("redact: empty secrets are a no-op",
          agent.redact("unchanged", "") == "unchanged")

    sink = agent_app._LogSink(tmp / "agent.log")
    stream = agent_app._RedactingStream(sink, ["sekret-key", "Bearer sekret-key"])
    stream.write("ingest with Authorization: Bearer sekret-key done\n")
    stream.flush()
    content = (tmp / "agent.log").read_text(encoding="utf-8")
    check("log stream: the key never reaches agent.log",
          "sekret-key" not in content and "***" in content, content)


# ---------------------------------------------------------------------------
# task v2 XML
# ---------------------------------------------------------------------------

def test_task_xml(tmp: Path) -> None:
    cfg_path = tmp / "agent-config.json"
    had_frozen = hasattr(sys, "frozen")
    saved_frozen = getattr(sys, "frozen", False)
    sys.frozen = True  # exercise the frozen exe-name swap off Windows
    try:
        xml = agent_app.task_xml(
            cfg_path, exe_path=tmp / "beesky-agent.exe")
        xml_console = agent_app.task_xml(
            cfg_path, console=True, exe_path=tmp / "beesky-agent.exe")
    finally:
        if had_frozen:
            sys.frozen = saved_frozen
        else:
            del sys.frozen
    for label, needle in [
            ("SYSTEM principal (S-1-5-18)", "<UserId>S-1-5-18</UserId>"),
            ("highest run level",
             "<RunLevel>HighestAvailable</RunLevel>"),
            ("BootTrigger present", "<BootTrigger>"),
            ("boot delay PT30S", "<Delay>PT30S</Delay>"),
            ("LogonTrigger present", "<LogonTrigger>"),
            ("task hidden", "<Hidden>true</Hidden>"),
            ("no execution time limit",
             "<ExecutionTimeLimit>PT0S</ExecutionTimeLimit>"),
            ("restart on failure every minute",
             "<Interval>PT1M</Interval>"),
            ("restart count 5", "<Count>5</Count>"),
            ("network not required",
             "<RunOnlyIfNetworkAvailable>false"
             "</RunOnlyIfNetworkAvailable>"),
            ("never stops on batteries",
             "<StopIfGoingOnBatteries>false"
             "</StopIfGoingOnBatteries>"),
            ("windowless exe is the action",
             "beesky-agentw.exe"),
            ("config path baked into the action",
             f'--config "{cfg_path}"')]:
        check(f"task xml: {label}", needle in xml)
    check("task xml: --console escape hatch uses the console exe",
          "beesky-agent.exe" in xml_console
          and "beesky-agentw.exe" not in xml_console)


# ---------------------------------------------------------------------------
# packaging
# ---------------------------------------------------------------------------

def test_packaging() -> None:
    spec = (ROOT / "packaging" / "beesky.spec").read_text(encoding="utf-8")
    check("spec: windowless twin named beesky-agentw",
          'name="beesky-agentw"' in spec)
    check("spec: agentw is a console=False build",
          spec.rsplit('name="beesky-agentw"', 1)[1].split(")")[0]
          .find("console=False") >= 0)
    agent_iss = (ROOT / "packaging" / "agent.iss").read_text(
        encoding="utf-8")
    check("agent.iss: ships beesky-agentw.exe alongside the console exe",
          "beesky-agentw.exe" in agent_iss
          and "beesky-agent.exe" in agent_iss)
    workflow = (ROOT / ".github" / "workflows"
                / "build-windows.yml").read_text(encoding="utf-8")
    check("workflow: agentw in artifact AND release file lists",
          workflow.count("dist/beesky-agentw.exe") >= 2)
    check("workflow: signed update manifest lists beesky-agentw.exe",
          '"beesky-agentw.exe"' in workflow)
    check("versions in sync at 0.29.0",
          beesky.__version__ == "0.29.0"
          and '#define MyAppVersion "0.29.0"' in agent_iss
          and '#define MyAppVersion "0.29.0"' in (ROOT / "packaging"
              / "installer.iss").read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# end-to-end: run --once writes status + a key-free log
# ---------------------------------------------------------------------------

def test_end_to_end(tmp: Path) -> None:
    db = tmp / "cloud.db"
    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    minted = subprocess.run(
        [sys.executable, "-m", "beesky", "cloud-add-agent",
         "--db", str(db), "--site", SITE],
        cwd=ROOT, env=env, capture_output=True, text=True)
    match = re.search(r"BEESKY_AGENT_KEY=(\S+)", minted.stdout)
    check("e2e: cloud mints the agent key", match is not None,
          minted.stdout + minted.stderr)
    if not match:
        return
    agent_key = match.group(1)

    cloud = subprocess.Popen(
        [sys.executable, "-m", "beesky", "cloud",
         "--port", str(CLOUD_PORT), "--db", str(db)],
        cwd=ROOT, env={**env, "BEESKY_CLOUD_PASSWORD": PASSWORD},
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    miner = subprocess.Popen(
        [sys.executable, str(ROOT / "tests" / "mock_dashd.py"),
         "127.0.0.1", str(DASHD_PORT)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        up = wait_for("cloud login page",
                      lambda: fetch("/login")[0] == 200 or None)
        check("e2e: cloud starts", up is not None)

        def app_run(*extra: str, config: Path) -> subprocess.CompletedProcess:
            return subprocess.run(
                [sys.executable, "-m", "beesky.agent_app", *extra,
                 "--config", str(config)],
                cwd=ROOT, env=env, capture_output=True, text=True,
                timeout=180)

        # -- healthy run, console entry --------------------------------
        good_dir = tmp / "good"
        good_dir.mkdir()
        cfg = AgentConfig(
            target="127.0.0.1", cloud_url=BASE, key=agent_key,
            site=SITE, interval=5, http_port=DASHD_PORT,
            cgminer_port=14097)
        cfg_path = good_dir / "agent-config.json"
        cfg.save(cfg_path)

        ran = app_run("run", "--once", config=cfg_path)
        check("bg e2e: `run --once` exits 0 and reports the pass",
              ran.returncode == 0 and "pass done" in ran.stdout,
              ran.stdout + ran.stderr[-300:])
        status = agent_app.read_status(cfg_path)
        check("bg e2e: agent-status.json written, ok with 1 miner",
              status is not None and status.get("ok") is True
              and status.get("miners") == 1
              and status.get("error") is None
              and status.get("site") == SITE
              and status.get("cloud_url") == BASE,
              json.dumps(status, ensure_ascii=False))
        log = agent_app.log_file_path(cfg_path)
        content = log.read_text(encoding="utf-8") if log.exists() else ""
        check("bg e2e: agent.log mirrors the run output",
              "pass done" in content)
        check("bg e2e: agent.log does NOT contain the agent key",
              agent_key not in content)
        check("bg e2e: localhost http cloud raises no warning",
              "CẢNH BÁO" not in ran.stderr, ran.stderr[-200:])

        # -- background flag: nothing on stdout, all in the log --------
        bg_dir = tmp / "background"
        bg_dir.mkdir()
        bg_cfg_path = bg_dir / "agent-config.json"
        cfg.save(bg_cfg_path)
        quiet = app_run("run", "--once", "--background",
                        config=bg_cfg_path)
        check("bg e2e: --background prints nothing to stdout",
              quiet.returncode == 0 and quiet.stdout == "",
              repr(quiet.stdout[:200]))
        bg_status = agent_app.read_status(bg_cfg_path)
        bg_log = agent_app.log_file_path(bg_cfg_path)
        check("bg e2e: --background still writes status + log",
              bg_status is not None and bg_status.get("ok") is True
              and bg_log.exists()
              and "pass done" in bg_log.read_text(encoding="utf-8"))

        # -- wrong key: failed cycle recorded, log still key-free -----
        bad_dir = tmp / "bad"
        bad_dir.mkdir()
        bad = AgentConfig(target="127.0.0.1", cloud_url=BASE,
                          key="SAI-KEY-12345", site=SITE, interval=5,
                          http_port=DASHD_PORT, cgminer_port=14097)
        bad_path = bad_dir / "agent-config.json"
        bad.save(bad_path)
        failed = app_run("run", "--once", config=bad_path)
        bad_status = agent_app.read_status(bad_path)
        check("bg e2e: a wrong-key cycle survives and is recorded "
              "as ok=false with an error",
              failed.returncode == 0 and bad_status is not None
              and bad_status.get("ok") is False
              and bool(bad_status.get("error")),
              json.dumps(bad_status, ensure_ascii=False))
        bad_log = agent_app.log_file_path(bad_path)
        bad_content = bad_log.read_text(encoding="utf-8") \
            if bad_log.exists() else ""
        check("bg e2e: the failing log never contains the (wrong) key",
              "SAI-KEY-12345" not in bad_content)

        # -- non-local http cloud: warning, still runs -----------------
        http_dir = tmp / "httpwarn"
        http_dir.mkdir()
        http_cfg = AgentConfig(
            target="127.0.0.1", cloud_url="http://203.0.113.10:9",
            key="whatever-key", site="Xưởng HTTP", interval=5,
            http_port=DASHD_PORT, cgminer_port=14097)
        http_path = http_dir / "agent-config.json"
        http_cfg.save(http_path)
        warned = app_run("run", "--once", config=http_path)
        check("bg e2e: non-local http:// cloud warns about the "
              "unencrypted key (but is not blocked)",
              "http://" in warned.stderr
              and "https" in warned.stderr,
              warned.stderr[-300:])
        http_status = agent_app.read_status(http_path)
        check("bg e2e: the unreachable-cloud cycle is recorded "
              "ok=false, not a crash",
              warned.returncode == 0 and http_status is not None
              and http_status.get("ok") is False)
    finally:
        for proc in (cloud, miner):
            proc.terminate()
        for proc in (cloud, miner):
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()


# ---------------------------------------------------------------------------
# config GUI — status card + http hint (xvfb-run)
# ---------------------------------------------------------------------------

def test_gui(tmp: Path) -> None:
    import tkinter as tk

    from beesky import agent_gui

    def build(directory: Path):
        directory.mkdir(parents=True, exist_ok=True)
        root = tk.Tk()
        app = agent_gui.AgentConfigApp(
            root, config_path=directory / "agent-config.json")
        return root, app

    # no status file yet
    root, app = build(tmp / "fresh")
    try:
        check("gui: status card starts at 'Chưa có dữ liệu'",
              str(app.bg_pill.cget("text")) == "Chưa có dữ liệu")
        check("gui: 'Xem log' button exists",
              str(app.view_log_button.cget("text")) == "Xem log")
        app.cloud_var.set("http://cloud.example.com")
        check("gui: non-local http:// cloud shows the https hint",
              "https" in app.cloud_hint_var.get(),
              app.cloud_hint_var.get())
        app.cloud_var.set("http://127.0.0.1:8788")
        check("gui: localhost http clears the hint",
              app.cloud_hint_var.get() == "")
        app.cloud_var.set("https://cloud.example.com")
        check("gui: https clears the hint",
              app.cloud_hint_var.get() == "")
        root.update()
    finally:
        root.destroy()

    # fabricated OK status
    ok_dir = tmp / "okrun"
    ok_dir.mkdir(parents=True, exist_ok=True)
    agent_app.write_status(
        ok_dir / "agent-config.json",
        AgentConfig(cloud_url=BASE, site=SITE), True, 3, None)
    root, app = build(ok_dir)
    try:
        check("gui: an OK status renders 'Đang chạy tốt' + miner count",
              str(app.bg_pill.cget("text")) == "Đang chạy tốt"
              and "3 máy" in app.bg_status_var.get(),
              app.bg_status_var.get())
        root.update()
    finally:
        root.destroy()

    # fabricated error status
    err_dir = tmp / "errun"
    err_dir.mkdir(parents=True, exist_ok=True)
    agent_app.write_status(
        err_dir / "agent-config.json",
        AgentConfig(cloud_url=BASE, site=SITE), False, 0,
        "cloud snapshot POST failed (see agent.log)")
    root, app = build(err_dir)
    try:
        check("gui: an error status renders 'Lỗi gần nhất' + the error",
              str(app.bg_pill.cget("text")) == "Lỗi gần nhất"
              and "snapshot POST failed" in app.bg_status_var.get(),
              app.bg_status_var.get())
        root.update()
    finally:
        root.destroy()


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="beesky-agent-bg-"))
    test_key_protection(tmp)
    test_redaction(tmp)
    test_task_xml(tmp)
    test_packaging()
    test_end_to_end(tmp)
    test_gui(tmp)
    print()
    if FAILURES:
        print(f"AGENT BG TEST FAILED: {len(FAILURES)} assertion(s): "
              f"{FAILURES}")
        return 1
    print("AGENT BG TEST PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
