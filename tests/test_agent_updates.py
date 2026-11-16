"""Whole-app updates against a local signed release, never a user's installation."""
import functools
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

from beesky import agent_updates as updates
from beesky.core import updater
from beesky.agent import AgentService


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


class UpdateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.keys = tempfile.TemporaryDirectory(prefix='beesky-fixture-signing-')
        cls.openssl = shutil.which('openssl') or 'C:/Program Files/Git/usr/bin/openssl.exe'
        cls.private = Path(cls.keys.name) / 'fixture-only.pem'
        subprocess.run([cls.openssl, 'genpkey', '-algorithm', 'RSA', '-pkeyopt',
                        'rsa_keygen_bits:2048', '-out', str(cls.private)], check=True, capture_output=True)
        raw = subprocess.check_output([cls.openssl, 'rsa', '-in', str(cls.private), '-modulus', '-noout'], text=True)
        cls.modulus = raw.strip().split('=', 1)[1]

    @classmethod
    def tearDownClass(cls):
        cls.keys.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='beesky-update-test-')
        self.root = Path(self.temp.name).resolve()
        self.release = self.root / 'release'
        self.release.mkdir()
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(QuietHandler, directory=str(self.release)))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f'http://127.0.0.1:{self.server.server_port}/'
        self.config = self.root / 'private-config.json'
        self.config.write_text('{"key":"fixture-token-must-not-enter-update-job"}', encoding='utf-8')
        self.install = self.root / 'installation with spaces'
        self.install.mkdir()
        self.engine = self.install / 'beesky-agent.exe'
        self.engine.write_bytes(b'original-engine')
        (self.install / 'beesky_agent_app.exe').write_bytes(b'original-ui')
        self.signer = patch.object(updater, 'UPDATE_RSA_N_HEX', self.modulus)
        self.signer.start()
        self.addCleanup(self.signer.stop)
        self.publish()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self.temp.cleanup()

    def publish(self, sha=None):
        self.payload = b'fixture installer, never executed by unit tests'
        self.name = 'BeeSkyAgentSetup-99.0.0.exe'
        self.entry = {'name': self.name, 'url': self.base + self.name,
                      'size': len(self.payload), 'sha256': sha or hashlib.sha256(self.payload).hexdigest()}
        (self.release / self.name).write_bytes(self.payload)
        (self.release / updater.MANIFEST_NAME).write_text(json.dumps({'version': '99.0.0', 'files': [self.entry]}), encoding='utf-8')
        subprocess.run([self.openssl, 'dgst', '-sha256', '-sign', str(self.private), '-out',
                        str(self.release / updater.SIG_NAME), str(self.release / updater.MANIFEST_NAME)], check=True, capture_output=True)

    def stage(self):
        directory = updates.update_root(self.config) / 'update-fixture'
        directory.mkdir(parents=True)
        for name in [self.name, updater.MANIFEST_NAME, updater.SIG_NAME]:
            shutil.copyfile(self.release / name, directory / name)
        job = directory / 'update-job.json'
        job.write_text(json.dumps({'directory': str(self.install), 'config': str(self.config), 'uiPid': 12345}), encoding='utf-8')
        return job

    def test_signed_release_and_previous_result_are_reported_without_paths_or_token(self):
        updates._result(self.config, 'failed', 'Thử cập nhật lại.', '98.0.0')
        result = updates.check_update(self.config, self.base)
        self.assertTrue(result['ok'])
        self.assertTrue(result['available'])
        self.assertEqual(result['latest'], '99.0.0')
        self.assertEqual(result['previous']['phase'], 'failed')
        self.assertNotIn('fixture-token', json.dumps(result))

    def test_unsigned_or_tampered_manifest_is_not_an_available_update(self):
        path = self.release / updater.MANIFEST_NAME
        path.write_bytes(path.read_bytes() + b' ')
        result = updates.check_update(self.config, self.base)
        self.assertFalse(result['ok'])
        self.assertFalse(result['available'])

    @unittest.skipUnless(os.name == 'nt', 'Windows installer preparation')
    def test_prepare_downloads_verifies_and_waits_for_helper_without_stopping_agent(self):
        progress = []
        def spawn(args):
            (Path(args[0]).parent / 'helper-ready').write_text('fixture helper')
            return Mock()
        with patch.object(sys, 'frozen', True, create=True), patch.object(sys, 'executable', str(self.engine)), patch.object(updates, '_spawn', side_effect=spawn), patch.object(updates, 'stop_agent') as stop:
            result = updates.prepare_update(self.config, 12345, progress.append, self.base)
        self.assertTrue(result['ready'])
        stop.assert_not_called()
        self.assertTrue(any(event.get('progress') == 100 for event in progress))
        job = next(updates.update_root(self.config).glob('update-*/update-job.json'))
        self.assertNotIn('fixture-token', job.read_text())
        self.assertEqual(self.engine.read_bytes(), b'original-engine')

    @unittest.skipUnless(os.name == 'nt', 'Windows installer preparation')
    def test_wrong_file_hash_never_spawns_helper_or_stops_worker(self):
        self.publish(sha='0' * 64)
        with patch.object(sys, 'frozen', True, create=True), patch.object(sys, 'executable', str(self.engine)), patch.object(updates, '_spawn') as spawn, patch.object(updates, 'stop_agent') as stop:
            with self.assertRaises(ValueError):
                updates.prepare_update(self.config, 12345, url_base=self.base)
        spawn.assert_not_called()
        stop.assert_not_called()
        self.assertEqual(updates.last_result(self.config)['phase'], 'failed')

    def test_installer_success_preserves_config_and_resumes_only_previously_running_worker(self):
        for was_running in (False, True):
            job = self.stage() if not was_running else job
            before = self.config.read_bytes()
            installer = subprocess.CompletedProcess([], 0)
            version = subprocess.CompletedProcess([], 0, b'{"version":"99.0.0"}')
            with patch.object(updates, '_wait_ui', return_value=True), patch.object(updates, 'runtime_status', return_value={'running': was_running}), patch.object(updates, 'stop_agent', return_value={'ok': True}), patch.object(updates.subprocess, 'run', side_effect=[installer, version]), patch.object(updates, '_spawn') as spawn:
                self.assertTrue(updates._install_locked(self.config, job))
            self.assertEqual(self.config.read_bytes(), before)
            self.assertEqual(updates.last_result(self.config)['phase'], 'complete')
            self.assertEqual(spawn.call_count, 2 if was_running else 1)
            self.assertEqual(spawn.call_args.args[0], [str(self.install / 'beesky_agent_app.exe')])

    def test_installer_failure_reopens_agent_and_restores_the_running_state(self):
        job = self.stage()
        with patch.object(updates, '_wait_ui', return_value=True), patch.object(updates, 'runtime_status', return_value={'running': True}), patch.object(updates, 'stop_agent', return_value={'ok': True}), patch.object(updates.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1)), patch.object(updates, '_spawn') as spawn:
            self.assertFalse(updates._install_locked(self.config, job))
        self.assertEqual(spawn.call_count, 2)
        self.assertEqual(updates.last_result(self.config)['phase'], 'failed')
        self.assertIn('fixture-token-must-not-enter-update-job', self.config.read_text())

    def test_tampering_after_download_does_not_stop_or_install(self):
        job = self.stage()
        (job.parent / self.name).write_bytes(b'tampered')
        with patch.object(updates, '_wait_ui', return_value=True), patch.object(updates, 'stop_agent') as stop, patch.object(updates.subprocess, 'run') as install, patch.object(updates, '_spawn') as spawn:
            self.assertFalse(updates._install_locked(self.config, job))
        stop.assert_not_called()
        install.assert_not_called()
        self.assertEqual(spawn.call_count, 1)  # reopen original UI with error

    def test_ui_still_open_aborts_without_stopping_or_opening_another_window(self):
        job = self.stage()
        with patch.object(updates, '_wait_ui', return_value=False), patch.object(updates, 'stop_agent') as stop, patch.object(updates.subprocess, 'run') as install, patch.object(updates, '_spawn') as spawn:
            self.assertFalse(updates._install_locked(self.config, job))
        stop.assert_not_called()
        install.assert_not_called()
        spawn.assert_not_called()

    def test_native_agent_reports_update_without_swapping_only_its_engine(self):
        service = AgentService(lambda: [], 'https://cloud.invalid', 'fixture', 'Fixture', auto_update=True)
        service._started_mono = 0
        with patch.object(sys, 'frozen', True, create=True), patch.object(sys, 'executable', str(self.engine)), patch.object(updater, 'check', return_value={'ok': True, 'update_available': True, 'latest': '99.0.0', 'current': '0.0.0'}), patch.object(updater, 'apply') as apply, patch.object(service, '_deliver_events'):
            service._maybe_update_check()
        apply.assert_not_called()
        self.assertFalse(service._exit_for_update)
        self.assertFalse(service._pending_events[0]['data']['auto_update'])


if __name__ == '__main__':
    unittest.main()
