"""Token pairing is read only; bad or redirected tokens never start a scan."""
import json,subprocess,sys,tempfile,threading,unittest
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from beesky.agent_connection import connection_info,ConnectionError
from beesky.agent_lock import agent_run_lock
from beesky.agent_config import AgentConfig

KEY='bsky_fixture-only-000000000000000000'
class Handler(BaseHTTPRequestHandler):
    mode='ok'
    requests=[]
    def do_GET(self):
        self.requests.append((self.path,self.headers.get('Authorization')))
        if self.mode=='redirect':
            self.send_response(302);self.send_header('Location','http://127.0.0.1:1/stolen');self.end_headers();return
        status=200 if self.headers.get('Authorization')=='Bearer '+KEY else 401
        self.send_response(status);self.send_header('Content-Type','application/json');self.end_headers()
        self.wfile.write(json.dumps({'agentId':'a','agentName':'Agent test','siteId':'s','siteName':'Xưởng 1','organizationName':'Tổ chức 1'} if status==200 else {'message':KEY}).encode())
    def log_message(self,*args):pass

class ConnectionTests(unittest.TestCase):
    def setUp(self):
        Handler.mode='ok';Handler.requests=[]
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        threading.Thread(target=self.server.serve_forever,daemon=True).start()
        self.url='http://127.0.0.1:'+str(self.server.server_port)
        self.temp=tempfile.TemporaryDirectory()
    def tearDown(self):self.server.shutdown();self.server.server_close();self.temp.cleanup()
    def test_valid_token_resolves_server_destination(self):
        self.assertEqual(connection_info(self.url,KEY)['siteName'],'Xưởng 1')
        self.assertEqual(Handler.requests,[('/api/agent/connection','Bearer '+KEY)])
    def test_bad_token_never_echoes_secret_or_server_error(self):
        wrong='bsky_wrong-only-000000000000000000'
        with self.assertRaises(ConnectionError) as caught:connection_info(self.url,wrong)
        self.assertNotIn(wrong,str(caught.exception));self.assertNotIn(KEY,str(caught.exception))
    def test_no_credential_redirect_and_no_insecure_remote_url(self):
        Handler.mode='redirect'
        with self.assertRaises(ConnectionError):connection_info(self.url,KEY)
        self.assertEqual(len(Handler.requests),1)
        for url in ('http://example.com','https://user:pass@example.com','https://example.com/#/login'):
            with self.assertRaises(ConnectionError):connection_info(url,KEY)
        self.assertEqual(len(Handler.requests),1)
    def test_cli_reads_token_from_stdin_and_saved_protected_config(self):
        path=Path(self.temp.name)/'agent.json'
        AgentConfig(cloud_url=self.url,key=KEY).save(path)
        result=subprocess.run([sys.executable,'-m','beesky.agent_app','connection','--config',str(path)],input=json.dumps({'cloud_url':self.url}),capture_output=True,text=True,encoding='utf-8',timeout=20)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)['siteName'],'Xưởng 1')
        self.assertNotIn(KEY,result.stdout+result.stderr)
    def test_one_agent_per_configuration_and_lock_releases(self):
        path=Path(self.temp.name)/'agent.json'
        with agent_run_lock(path):
            with self.assertRaises(RuntimeError):
                with agent_run_lock(path):pass
        with agent_run_lock(path):pass
    def test_scanner_host_registers_the_agent_engine_for_autostart(self):
        from unittest.mock import patch
        from beesky.agent_app import _task_command_parts
        base=Path(self.temp.name);folder=base/'agent';folder.mkdir()
        engine=folder/'beesky-agentw.exe';engine.write_bytes(b'test engine')
        config=base/'agent.json'
        with patch.object(sys,'frozen',True,create=True):
            command,args=_task_command_parts(config,windowed=True,exe_path=base/'beesky-gui.exe')
        self.assertEqual(command,str(engine));self.assertIn('run',args)
        self.assertIn(str(config),args)

if __name__=='__main__':unittest.main()
