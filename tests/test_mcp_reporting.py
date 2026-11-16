"""MCP transport and isolation checks against an ephemeral real cloud store."""
import hashlib
import asyncio
import json
import os
import secrets
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from beesky.cloud.server import make_handler
from beesky.cloud.store import CloudStore
from beesky.cloud.mcp import call_tool, authenticate


class ReportingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = CloudStore(str(Path(self.temp.name) / 'cloud.db'))
        self.token = secrets.token_urlsafe(32)
        self.config = Path(self.temp.name) / 'grants.json'
        self.grant = {'id': secrets.token_hex(8), 'token_sha256': hashlib.sha256(self.token.encode()).hexdigest(),
                      'sites': ['farm-a'], 'expires_at': time.time() + 3600}
        self.save_grant()
        self.env = patch.dict(os.environ, {'BEESKY_MCP_GRANTS_FILE': str(self.config)})
        self.env.start()
        for site in ['farm-a', 'farm-b']:
            agent = self.store.create_agent(site, secrets.token_urlsafe(32))
            self.store.add_snapshot(agent, time.time(), [{'ip': '10.0.0.1', 'model': site,
                'status': 'OK', 'ths': 110, 'rate_value': 110, 'rate_unit': 'TH/s',
                'max_temp_c': 70, 'raw': {'password': 'must-not-leak'}, 'password': 'must-not-leak'}])
        # Open legacy viewer deliberately: MCP must still demand its own grant.
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), make_handler(self.store, b'preview', None))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f'http://127.0.0.1:{self.server.server_port}'
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def save_grant(self):
        self.config.write_text(json.dumps([self.grant]), encoding='utf-8')

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.store.close()
        self.env.stop()
        self.temp.cleanup()

    def request(self, message=None, token=True, **headers):
        headers = {'Content-Type': 'application/json',
                   'Accept': 'application/json, text/event-stream', **headers}
        if token:
            headers['Authorization'] = 'Bearer ' + self.token
        req = urllib.request.Request(self.base + '/mcp', data=json.dumps(message).encode(), headers=headers)
        try:
            response = self.opener.open(req, timeout=5)
        except urllib.error.HTTPError as exc:
            response = exc
        with response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else None

    def tool(self, name, arguments):
        return self.request({'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call',
                             'params': {'name': name, 'arguments': arguments}})

    def test_handshake_list_and_read_scoped_data(self):
        status, msg = self.request({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
                    'params': {'protocolVersion': '2025-06-18', 'capabilities': {},
                               'clientInfo': {'name': 'test', 'version': '1'}}})
        self.assertEqual(status, 200)
        self.assertEqual(msg['result']['protocolVersion'], '2025-06-18')
        status, body = self.request({'jsonrpc': '2.0', 'method': 'notifications/initialized'})
        self.assertEqual((status, body), (202, None))
        _, msg = self.request({'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'})
        self.assertEqual(len(msg['result']['tools']), 5)
        self.assertTrue(all(t['annotations']['readOnlyHint'] for t in msg['result']['tools']))
        _, msg = self.tool('list_farms', {})
        self.assertEqual([f['site'] for f in msg['result']['structuredContent']['farms']], ['farm-a'])
        _, msg = self.tool('list_miners', {'site': 'farm-a'})
        payload = msg['result']['structuredContent']
        self.assertEqual(payload['rows'][0]['rate_unit'], 'TH/s')
        self.assertNotIn('password', json.dumps(payload))
        self.assertNotIn('farm-b', json.dumps(payload))
        for name in ['list_events', 'get_hashrate_history', 'get_energy_report']:
            _, msg = self.tool(name, {'site': 'farm-a'})
            self.assertFalse(msg['result']['isError'], name)

    def test_deny_cross_farm_missing_site_extra_args_and_write_tools(self):
        for name, args in [('list_miners', {'site': 'farm-b'}), ('get_energy_report', {'site': ''}),
                           ('get_hashrate_history', {}), ('list_events', {'site': 'farm-a', 'limit': 999}),
                           ('list_farms', {'tenant_id': 'other'}), ('reboot', {'site': 'farm-a'})]:
            status, msg = self.tool(name, args)
            self.assertEqual(status, 200)
            self.assertTrue(msg['result']['isError'], (name, args))

    def test_auth_fails_closed_and_revokes_without_restart(self):
        self.assertEqual(self.request({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list'}, token=False)[0], 401)
        self.grant['revoked'] = True
        self.save_grant()
        self.assertEqual(self.tool('list_farms', {})[0], 401)
        self.grant['revoked'] = False
        self.grant['expires_at'] = time.time() - 1
        self.save_grant()
        self.assertEqual(self.tool('list_farms', {})[0], 401)
        self.config.write_text('broken', encoding='utf-8')
        self.assertIsNone(authenticate('Bearer ' + self.token))
        with patch.dict(os.environ, {'BEESKY_MCP_GRANTS_FILE': ''}):
            self.assertIsNone(authenticate('Bearer ' + self.token))

    def test_transport_origin_bounds_and_legacy_api(self):
        message = {'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list'}
        self.assertEqual(self.request(message, Origin='https://evil.example')[0], 403)
        self.assertEqual(self.request(message, **{'MCP-Protocol-Version': 'invalid'})[0], 400)
        self.assertEqual(self.request(message, Accept='text/html')[0], 406)
        self.assertEqual(self.request({'oversized': 'x' * 33000})[0], 413)
        _, body = self.request([message])
        self.assertEqual(body['error']['code'], -32600)
        # Existing viewer behavior remains unchanged.
        with self.opener.open(self.base + '/api/sites') as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(len(json.load(response)['sites']), 2)

    def test_official_mcp_sdk_client(self):
        try:
            import httpx
            from mcp import ClientSession
            from mcp.client.streamable_http import streamablehttp_client
        except ImportError:
            self.skipTest('Optional MCP SDK not installed')
        async def check():
            def factory(**kwargs):
                return httpx.AsyncClient(**kwargs, trust_env=False)
            async with streamablehttp_client(self.base + '/mcp',
                    headers={'Authorization': 'Bearer ' + self.token},
                    httpx_client_factory=factory) as (read, write, _):
                async with ClientSession(read, write) as client:
                    initialized = await client.initialize()
                    self.assertEqual(initialized.serverInfo.name, 'beesky-reporting')
                    tools = await client.list_tools()
                    self.assertEqual(len(tools.tools), 5)
                    report = await client.call_tool('list_miners', {'site': 'farm-a'})
                    self.assertFalse(report.isError)
                    self.assertEqual(report.structuredContent['rows'][0]['site'], 'farm-a')
                    denied = await client.call_tool('list_miners', {'site': 'farm-b'})
                    self.assertTrue(denied.isError)
        asyncio.run(check())


if __name__ == '__main__':
    unittest.main()
