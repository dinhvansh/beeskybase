"""Real detached processes against a local Cloud and a synthetic miner.

No scheduled task, user configuration or real mining hardware is modified.
"""
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from beesky.agent_config import AgentConfig
from beesky.agent_runtime import control_server, runtime_path, runtime_status, stop_agent
from beesky import agent_app


def port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


class RuntimeTests(unittest.TestCase):
    def test_detached_worker_survives_launcher_and_reopens_then_stops(self):
        key = secrets.token_urlsafe(32)
        snapshots = []

        class Cloud(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def answer(self, value, code=200):
                data = json.dumps(value).encode()
                self.send_response(code)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def authorized(self):
                return self.headers.get('Authorization') == 'Bearer ' + key

            def do_GET(self):
                if not self.authorized():
                    return self.answer({'detail': 'invalid'}, 401)
                if self.path == '/api/agent/connection':
                    return self.answer({'agentId': 'fixture-agent', 'agentName': 'Test Agent',
                                        'siteId': 'fixture-site', 'siteName': 'Xưởng máy thử',
                                        'organizationName': 'Isolated test'})
                self.answer({'commands': []})

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                if not self.authorized():
                    return self.answer({'detail': 'invalid'}, 401)
                if self.path == '/api/ingest':
                    snapshots.append(body)
                self.answer({'ok': True})

        cloud = ThreadingHTTPServer(('127.0.0.1', 0), Cloud)
        thread = threading.Thread(target=cloud.serve_forever, daemon=True)
        thread.start()
        with tempfile.TemporaryDirectory(prefix='beesky-runtime-') as temp:
            cfg_path = Path(temp) / 'agent-config.json'
            miner_port = port()
            env = {**os.environ, 'PYTHONPATH': str(ROOT)}
            miner = subprocess.Popen([sys.executable, str(ROOT / 'tests/mock_dashd.py'),
                                      '127.0.0.1', str(miner_port)],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            def command(mode):
                executable=os.environ.get('BEESKY_TEST_AGENT_EXE')
                prefix=[executable] if executable else [sys.executable,'-m','beesky.agent_app']
                result = subprocess.run([*prefix,mode,
                                         '--config', str(cfg_path)], cwd=ROOT, env=env,
                                        capture_output=True, text=True, encoding='utf-8', timeout=60)
                return result.returncode, json.loads(result.stdout)

            try:
                cfg = AgentConfig(target='127.0.0.1', cloud_url=f'http://127.0.0.1:{cloud.server_port}',
                                  key=key, site='must be resolved by server', interval=1,
                                  timeout=.3, workers=2, http_port=miner_port, cgminer_port=port())
                cfg.save(cfg_path)
                code, started = command('start')
                self.assertEqual(code, 0)
                self.assertTrue(started['running'])
                pid = started['pid']
                # The launcher has exited. Query from a fresh process, like reopening UI.
                code, observed = command('status')
                self.assertTrue(observed['running'])
                self.assertEqual(observed['pid'], pid)
                _, again = command('start')
                self.assertEqual(again['pid'], pid)
                until = time.monotonic() + 25
                while time.monotonic() < until and not any(s['miners'] for s in snapshots):
                    time.sleep(.1)
                self.assertTrue(any(s['miners'] for s in snapshots), 'Worker must actually scan and POST a miner')
                self.assertEqual(snapshots[0]['site'], 'Xưởng máy thử')
                self.assertNotIn(key, (Path(temp) / 'agent.log').read_text(encoding='utf-8'))
                code, stopped = command('stop')
                self.assertEqual(code, 0)
                self.assertFalse(stopped['running'])
                self.assertFalse(command('status')[1]['running'])
                self.assertFalse(runtime_path(cfg_path).exists())
            finally:
                stop_agent(cfg_path, wait_seconds=2)
                miner.terminate()
                miner.wait(timeout=10)
        cloud.shutdown()
        cloud.server_close()
        thread.join(timeout=3)

    def test_stale_pid_is_never_terminated_without_control_authentication(self):
        with tempfile.TemporaryDirectory() as temp:
            config = Path(temp) / 'agent-config.json'
            runtime_path(config).write_text(json.dumps({'pid': os.getpid(), 'port': port(),
                                                       'token': secrets.token_hex(32)}))
            with patch('beesky.agent_runtime.os.kill') as kill:
                self.assertFalse(runtime_status(config)['running'])
                self.assertTrue(stop_agent(config)['ok'])
                kill.assert_not_called()

    def test_control_requires_exact_instance_credential(self):
        import urllib.request
        import urllib.error
        with tempfile.TemporaryDirectory() as temp:
            config = Path(temp) / 'agent-config.json'
            with control_server(config) as event:
                info = json.loads(runtime_path(config).read_text())
                req = urllib.request.Request(f"http://127.0.0.1:{info['port']}/stop", data=b'',
                                             headers={'Authorization': 'Bearer incorrect'})
                with self.assertRaises(urllib.error.HTTPError) as caught:
                    urllib.request.urlopen(req)
                self.assertEqual(caught.exception.code, 403)
                caught.exception.close()
                self.assertFalse(event.is_set())

    def test_logon_startup_uses_current_user_and_needs_no_system_principal(self):
        result = subprocess.CompletedProcess(['whoami'], 0, 'MACHINE\\operator\n', '')
        with patch('beesky.agent_app.subprocess.run', return_value=result):
            xml = agent_app.task_xml('test-config.json', system=False)
        self.assertIn('<LogonType>InteractiveToken</LogonType>', xml)
        self.assertIn('<RunLevel>LeastPrivilege</RunLevel>', xml)
        self.assertNotIn('<BootTrigger>', xml)
        self.assertNotIn('S-1-5-18', xml)
        self.assertIn('test-config.json', xml)


if __name__ == '__main__':
    unittest.main()
