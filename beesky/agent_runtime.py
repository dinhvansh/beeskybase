"""Detached agent control, scoped to one config and authenticated on loopback.

The UI and its pipes do not own the worker's lifetime. Reopening the UI can
observe/stop the same worker. Never kill a PID read from an untrusted stale file:
the control server must prove ownership immediately before termination.
"""
from __future__ import annotations

from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import hmac
import json
import os
import secrets
import signal
import subprocess
import sys
import threading
import time
import urllib.request


def runtime_path(config_path):
    return Path(config_path).with_suffix('.runtime.json')


def _control(config_path, action='status'):
    try:
        data = json.loads(runtime_path(config_path).read_text(encoding='utf-8'))
        port, token, pid = data['port'], data['token'], data['pid']
        if (type(port) is not int or not 1 <= port <= 65535
                or type(pid) is not int or pid <= 0
                or not isinstance(token, str) or len(token) != 64):
            return None
        request = urllib.request.Request(
            f'http://127.0.0.1:{port}/{action}',
            method='POST' if action == 'stop' else 'GET',
            data=b'' if action == 'stop' else None,
            headers={'Authorization': 'Bearer ' + token})
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(request, timeout=2) as response:
            result = json.loads(response.read(4096))
        if result.get('pid') != pid or result.get('instance') != token:
            return None
        return {'running': True, 'pid': pid}
    except (OSError, ValueError, KeyError, TypeError):
        return None


def runtime_status(config_path):
    return _control(config_path) or {'running': False}


@contextmanager
def control_server(config_path):
    stopped = threading.Event()
    token = secrets.token_hex(32)
    pid = os.getpid()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_GET(self):
            self._answer(False)

        def do_POST(self):
            self._answer(True)

        def _answer(self, stop):
            expected = 'Bearer ' + token
            authorized = hmac.compare_digest(
                self.headers.get('Authorization', ''), expected)
            if not authorized or self.path != ('/stop' if stop else '/status'):
                self.send_error(403)
                return
            if stop:
                stopped.set()
            body = json.dumps({'pid': pid, 'instance': token}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    path = runtime_path(config_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        # Open exclusively to owner before writing the control credential.
        descriptor = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(descriptor, 'w', encoding='utf-8') as file:
            json.dump({'pid': pid, 'port': server.server_port, 'token': token}, file)
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
        yield stopped
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
        try:
            if json.loads(path.read_text(encoding='utf-8')).get('token') == token:
                path.unlink()
        except (OSError, ValueError):
            pass


def launch_agent(config_path):
    from .agent_config import AgentConfig
    from .agent_connection import connection_info
    config_path = Path(config_path).resolve()
    existing = runtime_status(config_path)
    if existing['running']:
        return {'ok': True, **existing, 'message': 'Agent đã chạy ngầm.'}
    cfg = AgentConfig.load(config_path)
    if cfg.missing_fields():
        raise ValueError('Lưu đủ token, xưởng và dải IP trước khi chạy Agent.')
    destination = connection_info(cfg.cloud_url, cfg.key)
    cfg.site = destination['siteName']
    cfg.save(config_path)
    if getattr(sys, 'frozen', False):
        command = [sys.executable]
    else:
        command = [sys.executable, '-m', 'beesky.agent_app']
    command += ['run', '--background', '--config', str(config_path)]
    options = {'stdin': subprocess.DEVNULL, 'stdout': subprocess.DEVNULL,
               'stderr': subprocess.DEVNULL, 'close_fds': True}
    if os.name == 'nt':
        options['creationflags'] = (subprocess.CREATE_NO_WINDOW
                                    | subprocess.CREATE_NEW_PROCESS_GROUP)
    else:
        options['start_new_session'] = True
    process = subprocess.Popen(command, **options)
    for _ in range(100):
        status = runtime_status(config_path)
        if status['running']:
            return {'ok': True, **status,
                    'message': 'Agent đang chạy ngầm. Đóng cửa sổ vẫn tiếp tục quét và gửi dữ liệu.'}
        if process.poll() is not None:
            break
        time.sleep(.1)
    # A competing launch can own the same config; never terminate that worker.
    if process.poll() is None:
        process.terminate()
        process.wait(timeout=5)
    return {'ok': False, 'running': False,
            'message': 'Agent chưa khởi động được. Mở nhật ký để xem lỗi; kiểm tra token và quyền ghi cấu hình.'}


def stop_agent(config_path, wait_seconds=12):
    control = _control(config_path, 'stop')
    if not control:
        return {'ok': True, 'running': False, 'message': 'Agent đã dừng.'}
    until = time.monotonic() + wait_seconds
    while time.monotonic() < until:
        if not runtime_status(config_path)['running']:
            return {'ok': True, 'running': False, 'message': 'Đã dừng Agent chạy ngầm.'}
        time.sleep(.1)
    # Only terminate a process that still proves it owns this exact config.
    current = _control(config_path)
    if current and current['pid'] == control['pid']:
        os.kill(current['pid'], signal.SIGTERM)
        for _ in range(50):
            if not runtime_status(config_path)['running']:
                return {'ok': True, 'running': False, 'message': 'Đã dừng Agent.'}
            time.sleep(.1)
    return {'ok': False, 'running': True,
            'message': 'Chưa dừng được Agent. Kiểm tra nhật ký rồi thử lại.'}
