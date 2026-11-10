#!/usr/bin/env python3
"""v0.14 test — the standalone BeeSky Agent app.

No hardware. Covers everything the agent app adds over the v0.5
`beesky agent` command line:

  * config model (beesky/agent_config.py): save/load round-trip;
    default-path resolution — $BEESKY_AGENT_CONFIG wins, a fake
    APPDATA is honoured on a (simulated) Windows platform, POSIX
    falls back to ~/.beesky/; from_dict tolerates unknown keys and
    a non-dict notify_config.
  * packaging: the spec builds a third exe named beesky-agent with
    the official icon; packaging/agent.iss produces
    BeeSkyAgentSetup-<version>.exe, references the exe + icon +
    UninstallDisplayIcon, and its version define matches BOTH the
    package version and the main installer.iss; the CI workflow
    builds the agent installer and ships beesky-agent.exe +
    BeeSkyAgentSetup-*.exe in the artifact, the Release and the
    signed update-manifest file list.
  * updater name matching: a signed manifest entry named
    beesky-agent.exe is selected by basename and applied onto a
    dummy beesky-agent.exe (same machinery as
    tests/mock_update_test.py — throwaway key via the shipped owner
    tool, local release server).
  * end-to-end (subprocesses on 127.0.0.1): real `beesky cloud`
    (key minted by `beesky cloud-add-agent`), tests/mock_dashd.py
    as the miner, and the agent app driven FROM A CONFIG FILE —
    `python -m beesky.agent_app test --config ...` exits 0 with
    TEST OK and the snapshot is visible in the cloud's /api/sites
    and /api/miners; `run --once` exits 0; a config with a WRONG
    key makes `test` exit 1 with TEST FAIL.
  * config GUI (this file runs under xvfb-run, like the v0.7 GUI
    test): the window constructs with all five fields, the key
    entry masks/unmasks, "Lưu cấu hình" writes the JSON and a load
    reads the same values back; the auto-start button is disabled
    off Windows.

Prints PASS lines; exit 1 on failure. Run via
tests/run_mock_test_v14.sh (which appends evidence to
tests/RESULTS.md).
"""

import functools
import hashlib
import http.cookiejar
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import beesky  # noqa: E402
from beesky import agent_app, agent_config  # noqa: E402
from beesky.agent_config import AgentConfig  # noqa: E402
from beesky.core import updater  # noqa: E402

CLOUD_PORT = 18792
DASHD_PORT = 18083
BASE = f"http://127.0.0.1:{CLOUD_PORT}"
SITE = "Xưởng Agent App"
PASSWORD = "mat-khau-test"

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
# config model
# ---------------------------------------------------------------------------

def test_config_model(tmp: Path) -> None:
    cfg = AgentConfig(
        target="192.168.1.10-192.168.1.60",
        cloud_url="https://cloud.example.com",
        key="secret-key-123", site="Xưởng 1", interval=45,
        notify_config={"telegram": {"bot_token": "x", "chat_id": "1"}},
        auto_update=True, http_port=18082)
    path = tmp / "nested" / "agent-config.json"
    returned = cfg.save(path)
    check("config: save creates parent dirs and returns the path",
          returned == path and path.exists())
    loaded = AgentConfig.load(path)
    check("config: save/load round-trip is lossless",
          loaded.to_dict() == cfg.to_dict(),
          json.dumps(loaded.to_dict(), ensure_ascii=False))
    check("config: core fields survive (key/site/interval/notify)",
          loaded.key == "secret-key-123" and loaded.site == "Xưởng 1"
          and loaded.interval == 45.0
          and loaded.notify_config == cfg.notify_config
          and loaded.auto_update is True)

    tolerated = AgentConfig.from_dict(
        {"target": "t", "cloud_url": "u", "key": "k", "site": "s",
         "notify_config": "not-a-dict", "future_field": 1})
    check("config: from_dict drops unknown keys, "
          "non-dict notify_config -> None",
          tolerated.notify_config is None
          and not hasattr(tolerated, "future_field"))
    check("config: missing_fields lists the empty required fields",
          AgentConfig().missing_fields()
          == ["target", "cloud_url", "key", "site"])

    check("config path: $BEESKY_AGENT_CONFIG wins on any platform",
          agent_config.default_config_path(
              env={"BEESKY_AGENT_CONFIG": "/tmp/elsewhere.json"},
              platform="win32")
          == Path("/tmp/elsewhere.json"))
    fake_appdata = r"C:\Users\Farm\AppData\Roaming"
    check("config path: Windows uses %APPDATA%\\BeeSky",
          agent_config.default_config_path(
              env={"APPDATA": fake_appdata}, platform="win32")
          == Path(fake_appdata) / "BeeSky" / "agent-config.json")
    check("config path: POSIX falls back to ~/.beesky",
          agent_config.default_config_path(env={}, platform="linux")
          == Path.home() / ".beesky" / "agent-config.json")


# ---------------------------------------------------------------------------
# packaging / workflow assertions
# ---------------------------------------------------------------------------

def test_packaging() -> None:
    spec = (ROOT / "packaging" / "beesky.spec").read_text(encoding="utf-8")
    check("spec: third Analysis targets entry_agent.py",
          "entry_agent.py" in spec)
    check("spec: agent exe is named beesky-agent",
          'name="beesky-agent"' in spec)
    check("spec: all three EXEs carry the official icon",
          spec.count("icon=ICON if os.path.exists(ICON) else None") >= 3)
    check("spec: agent exe is a console build (run logs visible)",
          'name="beesky-agent"' in spec
          and spec.rsplit('name="beesky-agent"', 1)[1].split(")")[0]
          .find("console=True") >= 0)

    agent_iss = (ROOT / "packaging" / "agent.iss").read_text(
        encoding="utf-8")
    main_iss = (ROOT / "packaging" / "installer.iss").read_text(
        encoding="utf-8")
    check("agent.iss: output is BeeSkyAgentSetup-<version>.exe",
          "OutputBaseFilename=BeeSkyAgentSetup-{#MyAppVersion}"
          in agent_iss)
    check("agent.iss: installs beesky-agent.exe + icon + uninstall icon",
          "beesky-agent.exe" in agent_iss
          and "SetupIconFile=assets\\beesky-logo.ico" in agent_iss
          and "UninstallDisplayIcon={app}\\beesky.ico" in agent_iss)
    check("agent.iss: Start Menu shortcut launches the config window",
          '"{autoprograms}\\BeeSky Agent"' in agent_iss
          and 'Filename: "{app}\\beesky-agent.exe"' in agent_iss)
    check("versions in sync: agent.iss == package == installer.iss",
          f'#define MyAppVersion "{beesky.__version__}"' in agent_iss
          and f'#define MyAppVersion "{beesky.__version__}"' in main_iss,
          f"package reports {beesky.__version__}")

    workflow = (ROOT / ".github" / "workflows"
                / "build-windows.yml").read_text(encoding="utf-8")
    check("workflow: builds the agent installer",
          "packaging\\agent.iss" in workflow)
    check("workflow: agent exe + agent setup in artifact AND release",
          workflow.count("dist/BeeSkyAgentSetup-*.exe") >= 2
          and workflow.count("dist/beesky-agent.exe") >= 2)
    check("workflow: update manifest lists beesky-agent.exe + "
          "BeeSkyAgentSetup",
          '"beesky-agent.exe"' in workflow
          and "AGENT_INSTALLER" in workflow)
    check("workflow: frozen agent exe smoke check present",
          ".\\dist\\beesky-agent.exe --help" in workflow)


# ---------------------------------------------------------------------------
# updater name matching for beesky-agent.exe
# ---------------------------------------------------------------------------

class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def test_updater_name_match(tmp: Path) -> None:
    saved_n = updater.UPDATE_RSA_N_HEX
    server = None
    try:
        spec = importlib.util.spec_from_file_location(
            "make_update_key", ROOT / "tools" / "make_update_key.py")
        tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tool)
        key_file = tmp / "update-signing-key.pem"
        n_hex = tool.generate(key_file, tmp / "update_key.py")
        updater.UPDATE_RSA_N_HEX = n_hex
        updater.UPDATE_RSA_E = 65537

        _v = [int(p) for p in beesky.__version__.split(".")[:3]]
        newer = f"{_v[0]}.{_v[1] + 1}.0"
        new_bytes = f"BeeSky Agent fake {newer} binary\n".encode() * 32
        old_bytes = b"BeeSky Agent fake old binary (the dummy)\n"

        release = tmp / "release"
        release.mkdir()
        (release / "beesky-agent.exe").write_bytes(new_bytes)
        handler = functools.partial(_QuietHandler, directory=str(release))
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=server.serve_forever,
                         daemon=True).start()
        base = f"http://127.0.0.1:{server.server_address[1]}/"
        manifest = {
            "version": newer,
            "published_at": "2026-11-10T00:00:00Z",
            "files": [{
                "name": "beesky-agent.exe",
                "url": base + "beesky-agent.exe",
                "sha256": hashlib.sha256(new_bytes).hexdigest(),
                "size": len(new_bytes),
            }],
        }
        manifest_file = release / "update-manifest.json"
        manifest_file.write_text(json.dumps(manifest, indent=2) + "\n",
                                 encoding="utf-8")
        signed = subprocess.run(
            ["openssl", "dgst", "-sha256", "-sign", str(key_file),
             "-out", str(release / "update-manifest.sig"),
             str(manifest_file)], capture_output=True, text=True)
        assert signed.returncode == 0, signed.stderr

        farm = tmp / "farm"
        farm.mkdir()
        dummy = farm / "beesky-agent.exe"
        dummy.write_bytes(old_bytes)
        dummy.chmod(0o755)
        verdict = updater.apply(base, target_path=dummy)
        check("updater: manifest entry beesky-agent.exe matches by "
              "basename and applies",
              verdict["ok"], verdict["message"])
        check("updater: dummy beesky-agent.exe now holds the new bytes",
              dummy.read_bytes() == new_bytes)
        check("updater: previous agent exe kept as .old backup",
              (farm / "beesky-agent.exe.old").read_bytes() == old_bytes)
    finally:
        updater.UPDATE_RSA_N_HEX = saved_n
        if server is not None:
            server.shutdown()


# ---------------------------------------------------------------------------
# end-to-end: config file -> agent app -> mock cloud
# ---------------------------------------------------------------------------

def test_end_to_end(tmp: Path) -> None:
    db = tmp / "cloud.db"
    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    minted = subprocess.run(
        [sys.executable, "-m", "beesky", "cloud-add-agent",
         "--db", str(db), "--site", SITE],
        cwd=ROOT, env=env, capture_output=True, text=True)
    match = re.search(r"BEESKY_AGENT_KEY=(\S+)", minted.stdout)
    check("e2e: cloud-add-agent mints the key the config will carry",
          match is not None, minted.stdout + minted.stderr)
    if not match:
        return
    agent_key = match.group(1)

    cloud_env = {**env, "BEESKY_CLOUD_PASSWORD": PASSWORD}
    cloud = subprocess.Popen(
        [sys.executable, "-m", "beesky", "cloud",
         "--port", str(CLOUD_PORT), "--db", str(db)],
        cwd=ROOT, env=cloud_env, stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)
    miner = subprocess.Popen(
        [sys.executable, str(ROOT / "tests" / "mock_dashd.py"),
         "127.0.0.1", str(DASHD_PORT)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        up = wait_for("cloud login page",
                      lambda: fetch("/login", opener=_plain)[0] == 200
                      or None)
        check("e2e: cloud starts", up is not None)

        form = urllib.parse.urlencode({"password": PASSWORD}).encode()
        code, _ = fetch("/login", method="POST", data=form, headers={
            "Content-Type": "application/x-www-form-urlencoded"})
        check("e2e: viewer login works", code == 200, f"got {code}")

        # -- the config file IS the agent's command line ---------------
        cfg = AgentConfig(
            target="127.0.0.1", cloud_url=BASE, key=agent_key,
            site=SITE, interval=5, http_port=DASHD_PORT,
            cgminer_port=14099)
        cfg_path = tmp / "agent-config.json"
        cfg.save(cfg_path)
        on_disk = json.loads(cfg_path.read_text(encoding="utf-8"))
        check("e2e: config file on disk carries the documented fields",
              all(k in on_disk for k in
                  ("target", "cloud_url", "key", "site", "interval",
                   "notify_config", "auto_update")))

        def app_run(*extra: str,
                    config: Path = cfg_path) -> subprocess.CompletedProcess:
            return subprocess.run(
                [sys.executable, "-m", "beesky.agent_app", *extra,
                 "--config", str(config)],
                cwd=ROOT, env=env, capture_output=True, text=True,
                timeout=120)

        tested = app_run("test")
        check("agent app: `test` from a config file exits 0, TEST OK",
              tested.returncode == 0 and "TEST OK" in tested.stdout,
              tested.stdout + tested.stderr[-300:])

        def site_ready():
            _c, data = fetch_json("/api/sites")
            found = [s for s in data.get("sites", [])
                     if s["site"] == SITE and s["miner_count"] == 1]
            return found[0] if found else None

        site = wait_for("config-driven snapshot in /api/sites",
                        site_ready)
        check("e2e: the test ingest landed — site shows 1 miner",
              site is not None)
        _c, miners_data = fetch_json(
            "/api/miners?site=" + urllib.parse.quote(SITE))
        recs = [m for m in miners_data.get("miners", [])
                if m.get("ip") == "127.0.0.1"]
        check("e2e: /api/miners shows the dashd S19 Pro from the "
              "config-driven agent",
              len(recs) == 1 and recs[0].get("source") == "vnish"
              and "S19 Pro" in str(recs[0].get("model")),
              json.dumps(recs, ensure_ascii=False)[:300])

        ran = app_run("run", "--once")
        check("agent app: `run --once` from the config exits 0",
              ran.returncode == 0
              and "BeeSky agent: site" in ran.stdout,
              ran.stdout + ran.stderr[-300:])

        bad = AgentConfig(target="127.0.0.1", cloud_url=BASE,
                          key="wrong-key", site=SITE,
                          http_port=DASHD_PORT, cgminer_port=14099)
        bad_path = tmp / "agent-config-wrong.json"
        bad.save(bad_path)
        failed = app_run("test", config=bad_path)
        check("agent app: `test` with a wrong key exits 1, TEST FAIL",
              failed.returncode == 1 and "TEST FAIL" in failed.stdout,
              failed.stdout + failed.stderr[-300:])

        # install-task off Windows: instructions, no schtasks call.
        code, message = agent_app.install_task(cfg_path)
        check("agent app: install-task off Windows prints the "
              "systemd/cron guidance instead of failing obscurely",
              code is False and "systemd" in message)
        check("agent app: task command embeds exe + run + --config",
              agent_app.agent_command(cfg_path).endswith(
                  f'run --config "{cfg_path}"')
              and "agent_app" in agent_app.agent_command(cfg_path))
    finally:
        for proc in (cloud, miner):
            proc.terminate()
        for proc in (cloud, miner):
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()


# ---------------------------------------------------------------------------
# config GUI — runs under xvfb-run (see run_mock_test_v14.sh)
# ---------------------------------------------------------------------------

def test_gui(tmp: Path) -> None:
    import tkinter as tk

    from beesky import agent_gui

    cfg_path = tmp / "gui-agent-config.json"
    root = tk.Tk()
    try:
        app = agent_gui.AgentConfigApp(root, config_path=cfg_path)
        check("gui: config window constructs with all five fields",
              all(hasattr(app, name) for name in
                  ("target_var", "cloud_var", "key_var", "site_var",
                   "interval_var")))
        check("gui: key entry starts masked",
              str(app.key_entry.cget("show")) == "*")
        app.show_key_var.set(True)
        app._toggle_key_visibility()
        check("gui: 'Hiện key' toggle unmasks the key entry",
              str(app.key_entry.cget("show")) == "")
        check("gui: auto-start button disabled off Windows",
              str(app.autostart_button.cget("state")) == "disabled")

        app.target_var.set("192.168.1.10-192.168.1.60")
        app.cloud_var.set("http://127.0.0.1:8788")
        app.key_var.set("gui-key-1")
        app.site_var.set("Xưởng GUI")
        app.interval_var.set("45")
        check("gui: 'Lưu cấu hình' accepts a complete form",
              app.save_config() is True)
        check("gui: save wrote the config JSON",
              cfg_path.exists())
        loaded = AgentConfig.load(cfg_path)
        check("gui: saved JSON round-trips the form values",
              loaded.target == "192.168.1.10-192.168.1.60"
              and loaded.cloud_url == "http://127.0.0.1:8788"
              and loaded.key == "gui-key-1"
              and loaded.site == "Xưởng GUI"
              and loaded.interval == 45.0)
        root.update()
    finally:
        root.destroy()


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="beesky-agent-app-"))
    test_config_model(tmp)
    test_packaging()
    test_updater_name_match(tmp)
    test_end_to_end(tmp)
    test_gui(tmp)
    print()
    if FAILURES:
        print(f"AGENT APP TEST FAILED: {len(FAILURES)} assertion(s): "
              f"{FAILURES}")
        return 1
    print("AGENT APP TEST PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
