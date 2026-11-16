"""Agent status must count responding hardware and recover after a failed upload."""
import contextlib
import io
import json
import unittest
from unittest.mock import patch, Mock
from beesky.agent import AgentService
from beesky import agent_app
from beesky.agent_config import AgentConfig


class MonitoringTests(unittest.TestCase):
    def service(self, records):
        hook = Mock()
        service = AgentService(lambda: records, 'https://cloud.invalid', 'fixture-key',
                               'Xưởng thử', status_hook=hook)
        service.engine.observe_cycle = Mock(return_value=[])
        service._deliver_events = Mock()
        service._deliver_results = Mock()
        service._run_commands = Mock()
        service._maybe_update_check = Mock()
        return service, hook

    def test_fetch_errors_are_not_counted_as_responding_miners(self):
        service, hook = self.service([
            {'ip': '192.0.2.1', 'problems': []},
            {'ip': '192.0.2.2', 'problems': [{'code': 'FETCH_ERROR'}]}])
        with patch.object(service, '_deliver_snapshot', return_value=True):
            service.run_pass()
        hook.assert_called_once_with(True, 1, None)

    def test_empty_scan_and_later_delivery_recovery_are_reported(self):
        service, hook = self.service([])
        with patch.object(service, '_deliver_snapshot', side_effect=[False, True]):
            service.run_pass()
            service.run_pass()
        self.assertFalse(hook.call_args_list[0].args[0])
        self.assertEqual(hook.call_args_list[1].args, (True, 0, None))

    def test_network_prefill_requires_no_scanner_or_configuration(self):
        output = io.StringIO()
        with patch('beesky.core.discover.default_scan_target', return_value='10.25.6.0/24'), contextlib.redirect_stdout(output):
            self.assertEqual(agent_app.main(['network']), 0)
        self.assertEqual(json.loads(output.getvalue()), {'target': '10.25.6.0/24'})

    def test_test_cycle_reports_responding_count_and_writes_status(self):
        service, hook = self.service([
            {'ip': '192.0.2.1', 'problems': []},
            {'ip': '192.0.2.2', 'problems': [{'code': 'FETCH_ERROR'}]}])
        cfg = AgentConfig(target='192.0.2.0/24', cloud_url='https://cloud.invalid',
                          key='fixture-key', site='Xưởng thử')
        with patch('beesky.agent_app.build_service', return_value=service), patch.object(service, '_deliver_snapshot', return_value=True):
            ok, message = agent_app.test_ingest(cfg, status_hook=hook)
        self.assertTrue(ok)
        self.assertIn('snapshot 1 máy', message)
        hook.assert_called_once_with(True, 1, None)


if __name__ == '__main__':
    unittest.main()
