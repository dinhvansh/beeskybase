"""Real HTTP/SQLite tests, isolated from the user's preview database."""
import json, tempfile, threading, time, unittest
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.request import Request, build_opener, ProxyHandler
from urllib.error import HTTPError
from beesky.cloud.store import CloudStore
from tools.serve_preview import handler

class PowerAPI(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=str(Path(self.tmp.name)/'test.db')
        self.store=CloudStore(self.path)
        root=Path(__file__).resolve().parents[1]/'cloud-preview'
        self.server=ThreadingHTTPServer(('127.0.0.1',0),handler(self.store,root))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.base='http://127.0.0.1:'+str(self.server.server_port)
        self.opener=build_opener(ProxyHandler({}))
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.store.close();self.tmp.cleanup()
    def request(self,path,data=None,key=None):
        req=Request(self.base+path,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json',**({'Authorization':'Bearer '+key} if key else {})})
        try:
            with self.opener.open(req) as res:return res.status,json.load(res)
        except HTTPError as e:return e.code,json.load(e)
    def test_persistence_conflict_and_validation(self):
        plan={'version':1,'stations':[],'farms':[],'layout':{'racks':[],'devices':[]}}
        self.assertEqual(self.request('/api/power-plan')[1]['revision'],0)
        self.assertEqual(self.request('/api/power-plan',{'revision':0,'data':plan})[0],200)
        self.assertEqual(self.request('/api/power-plan',{'revision':0,'data':plan})[0],409)
        self.assertEqual(self.request('/api/power-plan',{'revision':1,'data':{}})[0],400)
        bad={**plan,'bad':float('nan')}
        self.assertEqual(self.request('/api/power-plan',{'revision':1,'data':bad})[0],400)
        other=CloudStore(self.path)
        try:self.assertEqual(json.loads(other.get_setting('power_plan'))['data'],plan)
        finally:other.close()
    def test_ingest_updates_model_power_timestamp_and_site(self):
        self.store.create_agent('Real test site','test-key')
        self.assertEqual(self.request('/api/ingest',{'miners':[]},'bad')[0],401)
        ts=time.time();records=[{'ip':'10.0.0.1','model':'Antminer S21 Hydro','power_w':5400}]
        self.assertEqual(self.request('/api/ingest',{'ts':ts,'miners':records},'test-key')[0],200)
        result=self.request('/api/miners?site=Real%20test%20site')[1]['miners'][0]
        self.assertEqual(result['power_w'],5400);self.assertEqual(result['snapshot_ts'],ts)
        self.assertEqual(result['site'],'Real test site')
        self.assertEqual(self.request('/api/miners?site=other')[1]['miners'],[])
    def test_authentication_gates_plan_and_assets(self):
        secured=ThreadingHTTPServer(('127.0.0.1',0),handler(self.store,Path(__file__).resolve().parents[1]/'cloud-preview','test-password'))
        t=threading.Thread(target=secured.serve_forever,daemon=True);t.start()
        old=self.base;self.base='http://127.0.0.1:'+str(secured.server_port)
        try:
            self.assertEqual(self.request('/api/power-plan')[0],401)
            self.assertEqual(self.request('/api/power-plan',{'revision':0,'data':{}})[0],401)
        finally:self.base=old;secured.shutdown();secured.server_close();t.join()
if __name__=='__main__':unittest.main()
