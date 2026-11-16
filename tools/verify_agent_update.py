"""CI-only: verified installer handoff, real worker resume, and full UI bundle.

Uses loopback, an isolated install folder and an older-version comparison seam.
The installer is the actual current build; no customer's PC is installed on.
"""
import functools
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from beesky import __version__, agent_updates
from beesky.agent_config import AgentConfig
from beesky.agent_runtime import runtime_status, stop_agent
from beesky.core import updater


def wait_for(probe, message, timeout=90):
    until = time.monotonic() + timeout
    while time.monotonic() < until:
        result = probe()
        if result:
            return result
        time.sleep(.25)
    raise AssertionError(message)


def main():
    if os.name != 'nt' or os.environ.get('GITHUB_ACTIONS') != 'true' or not os.environ.get('RUNNER_TEMP'):
        raise SystemExit('This installer test runs only in an isolated Windows CI job.')
    key_path = Path(sys.argv[1]).resolve()  # supplied by the signing step, never logged
    python = sys.executable
    temporary = tempfile.TemporaryDirectory(prefix='beesky-inapp-update-', dir=os.environ['RUNNER_TEMP'])
    base = Path(temporary.name).resolve()
    assert base.is_relative_to(Path(os.environ['RUNNER_TEMP']).resolve())
    release = base / 'release'
    release.mkdir()
    install = base / 'Agent with spaces'
    install.mkdir()
    engine = install / 'beesky-agent.exe'
    shutil.copyfile(ROOT / 'dist/beesky-agent.exe', engine)
    (install / 'beesky_agent_app.exe').write_bytes(b'old UI fixture')
    name = f'BeeSkyAgentSetup-{__version__}.exe'
    shutil.copyfile(ROOT / 'dist' / name, release / name)
    token = secrets.token_urlsafe(32)
    received = []

    class Handler(SimpleHTTPRequestHandler):
        def log_message(self, *_):
            pass
        def do_GET(self):
            if self.path.startswith('/api/'):
                body = json.dumps({'commands': [], 'serverTime': time.time()}).encode()
                self.send_response(200)
                self.end_headers()
                self.wfile.write(body)
            else:
                super().do_GET()
        def do_POST(self):
            body = self.rfile.read(int(self.headers['Content-Length']))
            if self.headers.get('Authorization') != 'Bearer ' + token:
                self.send_error(401)
                return
            if self.path == '/api/ingest':
                received.append(json.loads(body))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{}')

    server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Handler, directory=str(release)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f'http://127.0.0.1:{server.server_port}/'
    manifest = {'version': __version__, 'files': [{'name': name, 'url': url + name,
        'size': (release / name).stat().st_size, 'sha256': hashlib.sha256((release / name).read_bytes()).hexdigest()}]}
    (release / updater.MANIFEST_NAME).write_text(json.dumps(manifest), encoding='utf-8')
    openssl = shutil.which('openssl') or 'C:/Program Files/Git/usr/bin/openssl.exe'
    subprocess.run([openssl, 'dgst', '-sha256', '-sign', str(key_path), '-out',
                    str(release / updater.SIG_NAME), str(release / updater.MANIFEST_NAME)], check=True, capture_output=True)
    config = base / 'state' / 'agent.json'
    AgentConfig(target='127.0.0.1', cloud_url=url.rstrip('/'), key=token,
                site='Isolated update fixture', interval=1, timeout=.1, http_port=1, cgminer_port=1).save(config)
    original_config = config.read_bytes()
    worker = subprocess.Popen([str(engine), 'run', '--background', '--config', str(config)])
    ui = subprocess.Popen([python, '-c', 'import time;time.sleep(180)'])
    try:
        original_pid = wait_for(lambda: runtime_status(config).get('pid'), 'Seed worker did not start')
        wait_for(lambda: received, 'Seed worker did not send a snapshot')
        # Exercise the public prepare path with a signed newer-version comparison.
        # Binary, installer, helper and verification key are all the actual build.
        with patch.object(sys, 'frozen', True, create=True), patch.object(sys, 'executable', str(engine)), patch.object(updater, 'CURRENT_VERSION', '0.0.0'):
            ready = agent_updates.prepare_update(config, ui.pid, url_base=url)
        assert ready['ready']
        assert runtime_status(config)['pid'] == original_pid, 'Download must not stop an active worker'
        before = len(received)
        ui.terminate()
        ui.wait(timeout=10)
        wait_for(lambda: (agent_updates.last_result(config) or {}).get('phase') in ('complete', 'failed'), 'Helper never completed', timeout=180)
        outcome = agent_updates.last_result(config)
        assert outcome['phase'] == 'complete', outcome['message']
        wait_for(lambda: runtime_status(config).get('pid') not in (None, original_pid), 'Worker was not resumed after installing')
        wait_for(lambda: len(received) > before, 'Resumed worker did not deliver')
        assert config.read_bytes() == original_config, 'Update changed the saved configuration'
        assert (install / 'beesky_agent_app.exe').stat().st_size > 10000
        assert (install / 'flutter_windows.dll').is_file()
        assert (install / 'beesky-agentw.exe').is_file()
        for weight in (400, 500, 600, 700):
            assert (install / f'data/flutter_assets/assets/fonts/NotoSans-{weight}.ttf').is_file()
        print('Verified in-app update: signed download, UI exit, full install, preserved config, resumed worker and delivery.')
    finally:
        if ui.poll() is None:
            ui.terminate()
            ui.wait(timeout=10)
        stop_agent(config, wait_seconds=2)
        worker.wait(timeout=20)
        # Only the UI whose executable is inside this CI-owned install folder.
        gui = str(install / 'beesky_agent_app.exe').replace("'", "''")
        cleanup = f"Get-CimInstance Win32_Process | Where-Object {{ $_.ExecutablePath -eq '{gui}' }} | ForEach-Object {{ Stop-Process -Id $_.ProcessId -Force }}"
        subprocess.run(['powershell', '-NoProfile', '-Command', cleanup], check=True, capture_output=True)
        uninstall = install / 'unins000.exe'
        if uninstall.exists():
            subprocess.run([str(uninstall), '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART'], check=True)
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
        # Helper bootloader may still be removing its own temporary extraction.
        for attempt in range(30):
            try:
                temporary.cleanup()
                break
            except PermissionError:
                if attempt == 29:
                    raise
                time.sleep(.5)


if __name__ == '__main__':
    main()
