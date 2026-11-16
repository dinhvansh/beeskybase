"""Maintenance HTTP routes use the same viewer authentication as the cloud."""
import http.cookiejar
import json
import tempfile
import threading
import unittest
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, build_opener, ProxyHandler, HTTPCookieProcessor
from beesky.cloud.store import CloudStore
from beesky.cloud.maintenance import MaintenanceService, today_vn
from tools.serve_preview import handler
from test_maintenance import PNG

class MaintenanceHTTPTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.store=CloudStore(str(Path(self.tmp.name)/'test.db'));self.service=MaintenanceService(self.store)
        schedule={'site':'s','siteName':'Xưởng','name':'Bảo trì HTTP','owner':'KT','actor':'QT','startMonth':today_vn().strftime('%Y-%m'),'day':15,'scopeType':'site','scopeId':'s','scopeName':'Xưởng','items':[{'title':'Kiểm tra'}]}
        self.service.save_schedule(schedule);self.ticket=self.service.listing(schedule['startMonth'])['tickets'][0]
        self.ticket=self.service.add_photo(self.ticket['id'],{'revision':self.ticket['revision'],'actor':'KT','itemId':self.ticket['items'][0]['id'],'stage':'before','name':'photo.png','data':PNG})
        self.server=ThreadingHTTPServer(('127.0.0.1',0),handler(self.store,Path(__file__).resolve().parents[1]/'cloud-preview','test-password'))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start();self.base='http://127.0.0.1:'+str(self.server.server_port)
        self.plain=build_opener(ProxyHandler({}));self.auth=build_opener(ProxyHandler({}),HTTPCookieProcessor(http.cookiejar.CookieJar()))
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.store.close();self.tmp.cleanup()
    def request(self,path,body=None,authenticated=True):
        req=Request(self.base+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json'})
        try:
            with (self.auth if authenticated else self.plain).open(req) as res:return res.status,res.headers,res.read()
        except HTTPError as e:return e.code,e.headers,e.read()
    def login(self):
        self.auth.open(Request(self.base+'/login',data=urlencode({'password':'test-password'}).encode(),headers={'Content-Type':'application/x-www-form-urlencoded'})).close()
    def test_viewer_gate_protects_photos_reports_and_mutations(self):
        photo=self.ticket['photos'][0]['url']
        for path in ['/api/maintenance',photo,'/api/maintenance/report']:
            self.assertEqual(self.request(path,authenticated=False)[0],401)
        self.assertEqual(self.request('/api/maintenance/schedules',{},False)[0],401)
        self.login();status,headers,body=self.request(photo);self.assertEqual(status,200);self.assertEqual(headers['Content-Type'],'image/png');self.assertTrue(body.startswith(b'\x89PNG'))
        self.assertEqual(headers['X-Content-Type-Options'],'nosniff')
    def test_report_and_listing_have_evidence_and_no_photo_blob_in_json(self):
        self.login();status,headers,body=self.request('/api/maintenance');data=json.loads(body)
        self.assertEqual(status,200);self.assertEqual(data['summary']['total'],1);self.assertNotIn('body',data['tickets'][0]['photos'][0])
        status,headers,body=self.request('/api/maintenance/report');self.assertEqual(status,200);self.assertIn('text/html',headers['Content-Type']);self.assertIn(self.ticket['photos'][0]['url'],body.decode())
    def test_invalid_month_json_photo_and_revision_return_errors(self):
        self.login();self.assertEqual(self.request('/api/maintenance?month=invalid')[0],400)
        self.assertEqual(self.request('/api/maintenance/schedules',{})[0],400)
        bad={'revision':0,'actor':'KT','action':'save','items':[]}
        self.assertEqual(self.request('/api/maintenance/tickets/'+self.ticket['id'],bad)[0],409)
        self.assertEqual(self.request('/api/maintenance/tickets/'+self.ticket['id']+'/photos',{'actor':'KT','data':'bad','stage':'before','name':'test'})[0],400)
if __name__=='__main__':unittest.main()
