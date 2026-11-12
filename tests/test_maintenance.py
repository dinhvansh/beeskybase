"""Maintenance persistence, monthly calendar, workflow and evidence tests."""
import base64
import datetime as dt
import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from beesky.cloud.store import CloudStore
from beesky.cloud.maintenance import MaintenanceService, MaintenanceError, MaintenanceScheduler

PNG='iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+j+1sAAAAASUVORK5CYII='
class MaintenanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=str(Path(self.tmp.name)/'db.sqlite')
        self.store=CloudStore(self.path);self.service=MaintenanceService(self.store)
        self.clock=patch('beesky.cloud.maintenance.today_vn',return_value=dt.date(2026,1,12));self.clock.start()
        plan={'layout':{'devices':[{'id':'d1','site':'s','ip':'10.0.0.1','model':'S19 Pro','serial':'SERIAL','worker':'pool.worker','customerOwner':'Khách A'},{'id':'d2','site':'other','ip':'10.0.1.1'}],'racks':[{'id':'r','site':'s','slots':['d1']}]},'groups':[{'id':'g','site':'s','memberIds':['d1']}]}
        self.store.set_setting('power_plan',json.dumps({'revision':1,'data':plan}))
    def tearDown(self):
        self.clock.stop();self.store.close();self.tmp.cleanup()
    def schedule(self,**updates):
        body={'site':'s','siteName':'Xưởng','name':'Bảo trì','owner':'Kỹ thuật','actor':'Quản trị','startMonth':'2026-01','day':31,'scopeType':'rack','scopeId':'r','scopeName':'Kệ 1','items':[{'title':'Kiểm tra quạt','photoRequired':True}]};body.update(updates)
        return self.service.save_schedule(body)
    def first(self,month='2026-01'):
        return self.service.listing(month)['tickets'][0]
    def payload(self,t,result='pass',**updates):
        data={'revision':t['revision'],'actor':'Kỹ thuật','action':'save','notes':'Kết luận','cost':100,'items':[{'id':i['id'],'result':result,'notes':'Ghi nhận'} for i in t['items']]};data.update(updates);return data
    def photo(self,t,**updates):
        data={'revision':t['revision'],'actor':'Kỹ thuật','itemId':t['items'][0]['id'],'stage':'before','name':'test.png','data':PNG};data.update(updates);return self.service.add_photo(t['id'],data)
    def test_month_end_idempotency_catchup_and_target_snapshot(self):
        self.schedule();self.service.tick(dt.date(2026,3,1));self.service.tick(dt.date(2026,3,1))
        with self.store._lock:
            rows=self.store._db.execute('SELECT data FROM maintenance_tickets ORDER BY period').fetchall()
        self.assertEqual([json.loads(r['data'])['due'] for r in rows],['2026-01-31','2026-02-28','2026-03-31'])
        self.assertEqual(self.first()['targets'][0]['worker'],'pool.worker');self.assertEqual(len(self.first()['targets']),1)
        self.store.set_setting('power_plan',json.dumps({'data':{'layout':{'devices':[],'racks':[]}}}))
        self.assertEqual(len(self.first()['targets']),1)
    def test_leap_year_deadline(self):
        self.schedule(startMonth='2028-01');self.service.tick(dt.date(2028,2,1))
        self.assertEqual(self.first('2028-02')['due'],'2028-02-29')
    def test_template_edits_only_change_future_tickets(self):
        s=self.schedule();old=self.first();self.schedule(id=s['id'],revision=s['revision'],items=[{'title':'Checklist mới'}]);self.service.tick(dt.date(2026,2,1))
        self.assertEqual(self.service.ticket(old['id'])['items'][0]['title'],'Kiểm tra quạt')
        self.assertEqual(self.first('2026-02')['items'][0]['title'],'Checklist mới')
    def test_submission_requires_checklist_notes_and_required_photos(self):
        self.schedule();t=self.first()
        for result in ['', 'fail','pass']:
            with self.assertRaises(MaintenanceError):self.service.update_ticket(t['id'],self.payload(t,result,action='submit'))
        self.assertEqual(self.service.ticket(t['id'])['status'],'open')
        t=self.photo(t);t=self.service.update_ticket(t['id'],self.payload(t,'pass',action='submit'));self.assertEqual(t['status'],'pending')
        with self.assertRaises(MaintenanceError):self.photo(t)
        t=self.service.update_ticket(t['id'],{'revision':t['revision'],'actor':'Giám sát','action':'return','reason':'Bổ sung số đo'})
        self.assertEqual(t['status'],'in_progress')
        t=self.service.update_ticket(t['id'],self.payload(t,'pass',action='submit'))
        t=self.service.update_ticket(t['id'],{'revision':t['revision'],'actor':'Giám sát','action':'approve'})
        self.assertEqual(t['status'],'completed');self.assertEqual(t['approved_by'],'Giám sát')
        with self.assertRaises(MaintenanceError):self.service.update_ticket(t['id'],self.payload(t))
        with self.assertRaises(MaintenanceError):self.service.delete_photo(t['id'],t['photos'][0]['id'],{'revision':t['revision'],'actor':'KT'})
    def test_photo_persistence_limits_mime_and_ownership(self):
        self.schedule();t=self.first()
        for change in [{'data':base64.b64encode(b'<svg onload=alert(1)>').decode()},{'itemId':'wrong'},{'stage':'bad'}]:
            with self.assertRaises(MaintenanceError):self.photo(t,**change)
        t=self.photo(t,stage='after');photo=t['photos'][0];self.assertEqual(photo['stage'],'after');mime,blob=self.service.photo(photo['id']);self.assertEqual(mime,'image/png');self.assertEqual(blob,base64.b64decode(PNG))
        reopened=CloudStore(self.path)
        try:self.assertEqual(MaintenanceService(reopened).photo(photo['id'])[1],blob)
        finally:reopened.close()
        for i in range(7):t=self.photo(t)
        with self.assertRaises(MaintenanceError):self.photo(t)
        t=self.service.delete_photo(t['id'],photo['id'],{'revision':t['revision'],'actor':'KT'})
        self.assertEqual(len(t['photos']),7)
    def test_concurrency_and_invalid_results_are_atomic(self):
        self.schedule();t=self.first();new=self.service.update_ticket(t['id'],self.payload(t))
        with self.assertRaises(MaintenanceError) as e:self.service.update_ticket(t['id'],self.payload(t))
        self.assertEqual(e.exception.status,409)
        with self.assertRaises(MaintenanceError):self.service.update_ticket(t['id'],self.payload(new,'bad'))
        self.assertEqual(self.service.ticket(t['id'])['revision'],new['revision'])
    def test_na_reason_and_repair_links_are_atomic_and_scoped(self):
        self.schedule();t=self.first()
        with self.assertRaises(MaintenanceError):self.service.update_ticket(t['id'],self.payload(t,'na',action='submit',items=[{'id':t['items'][0]['id'],'result':'na','notes':''}]))
        t=self.service.update_ticket(t['id'],self.payload(t,'fail'))
        body={'revision':t['revision'],'actor':'KT','itemId':t['items'][0]['id'],'deviceId':'other','cost':50}
        with self.assertRaises(MaintenanceError):self.service.create_repair(t['id'],body)
        body['deviceId']='d1';t=self.service.create_repair(t['id'],body);self.assertEqual(len(t['repairs']),1)
        body['revision']=t['revision']
        with self.assertRaises(MaintenanceError):self.service.create_repair(t['id'],body)
        rows=self.store.list_repairs();self.assertEqual(len(rows),1);self.assertIn(t['id'],rows[0]['detail'])
    def test_pause_future_start_validation_and_report_escaping(self):
        s=self.schedule(name='<script>alert(1)</script>');self.service.toggle_schedule(s['id'],{'revision':s['revision'],'actor':'KT'});self.service.tick(dt.date(2026,4,1))
        self.assertEqual(len(self.service.listing('2026-04')['tickets']),0)
        report=self.service.report('2026-01');self.assertNotIn('<script>',report);self.assertIn('&lt;script&gt;',report)
        self.assertEqual(self.service.listing('2026-01','other')['summary']['total'],0)
        for change in [{'day':0},{'day':32},{'day':float('nan')},{'startMonth':'2026-13'},{'items':[]}]:
            with self.assertRaises(MaintenanceError):self.schedule(**change)
    def test_scheduler_runs_without_browser(self):
        calls=[]
        class Fake:
            def tick(self):calls.append(1)
        scheduler=MaintenanceScheduler(Fake(),interval=.01);scheduler.start()
        try:
            deadline=time.time()+1
            while len(calls)<2 and time.time()<deadline:time.sleep(.01)
            self.assertGreaterEqual(len(calls),2)
        finally:scheduler.stop()
if __name__=='__main__':unittest.main()
