from datetime import timedelta
from django.test import TestCase,TransactionTestCase
from django.db import connection,close_old_connections
from django.utils import timezone
from rest_framework.test import APIClient
from core.models import Agent,Miner,Snapshot,Observation,Placement,Rack,RackSlot,Site,AuditLog
from core.services import digest
from .test_accounts_isolation import user,organization

KEY='bsky_test-key-only-0000000000000000000'
class IngestTests(TestCase):
    def setUp(self):
        self.owner=user('scanner@example.com');self.org=organization(self.owner,'Scan Org');self.site=Site.objects.create(organization=self.org,name='Site')
        self.agent=Agent.objects.create(site=self.site,name='Scanner',key_hash=digest(KEY),key_prefix=KEY[:12]);self.client=APIClient();self.client.credentials(HTTP_AUTHORIZATION='Bearer '+KEY)
        self.viewer=APIClient();self.viewer.force_login(self.owner);self.ts=timezone.now().timestamp()
    def push(self,miners=None,**updates):
        data={'site':'forged-other-site','ts':self.ts,'miners':miners if miners is not None else [{'ip':'10.0.0.1','model':'S21 Hydro','mac_or_serial':'SERIAL-1','power_w':5360,'max_temp_c':65}]};data.update(updates)
        return self.client.post('/api/ingest',data,format='json')
    def test_agent_bound_site_retry_dedup_and_real_power_contract(self):
        self.assertEqual(self.push().status_code,200);self.assertTrue(self.push().json()['duplicate'])
        self.assertEqual(Snapshot.objects.count(),1);self.assertEqual(Observation.objects.count(),1);miner=Miner.objects.get();self.assertEqual(miner.site_id,self.site.id)
        result=self.viewer.get(f'/api/v2/sites/{self.site.id}/miners').json()['results'][0]
        self.assertEqual(result['telemetry']['power_w'],5360);self.assertEqual(result['identityStatus'],'reported');self.assertIsNone(result['placement'])
    def test_serial_preserves_identity_and_placement_on_ip_change(self):
        self.push();miner=Miner.objects.get();rack=Rack.objects.create(site=self.site,name='R');slot=RackSlot.objects.create(rack=rack,row=1,col=1);Placement.objects.create(miner=miner,slot=slot)
        response=self.push([{'ip':'10.0.0.2','model':'S21 Hydro','mac_or_serial':'SERIAL-1','power_w':5400}],ts=self.ts+1)
        self.assertEqual(response.status_code,200);self.assertEqual(Miner.objects.count(),1);miner.refresh_from_db();self.assertEqual(miner.ip,'10.0.0.2');self.assertEqual(miner.placement.slot_id,slot.id)
    def test_same_ip_new_serial_does_not_inherit_placement_or_identity(self):
        self.push();miner=Miner.objects.get();rack=Rack.objects.create(site=self.site,name='R');slot=RackSlot.objects.create(rack=rack,row=1,col=1);Placement.objects.create(miner=miner,slot=slot)
        self.push([{'ip':'10.0.0.1','model':'S19 Pro','mac_or_serial':'REPLACEMENT'}],ts=self.ts+1)
        self.assertEqual(Miner.objects.count(),2);self.assertEqual(Placement.objects.get().miner_id,miner.id)
        replacement=Miner.objects.get(serial='REPLACEMENT');self.assertFalse(Placement.objects.filter(miner=replacement).exists())
    def test_bad_batch_is_atomic_and_numeric_validation_is_strict(self):
        for records in [[{'ip':'bad'}],[{'ip':'10.0.0.1','power_w':-1}],[{'ip':'10.0.0.1','power_w':'5360'}],[{'ip':'10.0.0.1','mac_or_serial':'x'},{'ip':'10.0.0.2','mac_or_serial':'x'}],[{'ip':'10.0.0.1'},{'ip':'10.0.0.1'}]]:
            self.assertEqual(self.push(records).status_code,400)
        self.assertEqual(self.push(ts=self.ts+1000).status_code,400);self.assertEqual(self.push(ts=self.ts-90000).status_code,400)
        self.assertEqual(Miner.objects.count(),0);self.assertEqual(Snapshot.objects.count(),0)
        self.assertEqual(self.client.post('/api/ingest','{"miners":[{"ip":"10.0.0.1","power_w":NaN}]}',content_type='application/json').status_code,400)
    def test_old_snapshots_do_not_roll_back_telemetry(self):
        self.push();self.assertEqual(self.push([{'ip':'10.0.0.1','mac_or_serial':'SERIAL-1','power_w':100}],ts=self.ts-100).status_code,200)
        self.assertEqual(Miner.objects.get().telemetry['power_w'],5360)
    def test_multiple_agents_same_identity_dedup_and_conflicting_ip_is_rejected(self):
        self.push();key2='bsky_other-test-key-000000000000000000';other=Agent.objects.create(site=self.site,name='Other',key_hash=digest(key2),key_prefix=key2[:12]);self.client.credentials(HTTP_AUTHORIZATION='Bearer '+key2)
        self.assertEqual(self.push(ts=self.ts+1).status_code,200);self.assertEqual(Miner.objects.count(),1)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer '+KEY)
        self.assertEqual(self.push([{'ip':'10.0.0.3','mac_or_serial':'SERIAL-1'}],ts=self.ts+2).status_code,400)
        self.assertEqual(Miner.objects.get().ip,'10.0.0.1')
    def test_agent_rotation_revocation_and_list_never_exposes_secrets(self):
        base=f'/api/v2/sites/{self.site.id}/agents'
        response=self.viewer.get(base);self.assertNotIn(KEY,response.content.decode());self.assertNotIn(self.agent.key_hash,response.content.decode())
        response=self.viewer.post(base+'/'+str(self.agent.id),{},format='json');self.assertEqual(response.status_code,200);new_key=response.json()['key']
        self.assertEqual(self.push().status_code,401);self.client.credentials(HTTP_AUTHORIZATION='Bearer '+new_key);self.assertEqual(self.push().status_code,200)
        self.assertEqual(self.client.get('/api/agent/commands').json()['commands'],[])
        self.viewer.delete(base+'/'+str(self.agent.id),{},format='json');self.assertEqual(self.push(ts=self.ts+1).status_code,401)
    def test_stale_timestamp_and_heartbeat_are_separate(self):
        self.push(ts=self.ts-700)
        machine=self.viewer.get(f'/api/v2/sites/{self.site.id}/miners').json()['results'][0];self.assertTrue(machine['stale'])
        self.agent.refresh_from_db();self.assertGreater(self.agent.last_heartbeat_at,self.agent.last_snapshot_at+timedelta(minutes=10))
    def test_pagination_events_retry_and_bounded_history(self):
        for i in range(105):self.assertEqual(self.push([],ts=self.ts+i*.01).status_code,200)
        self.assertEqual(Snapshot.objects.count(),100)
        event={'ts':self.ts,'ip':'10.0.0.1','code':'OVER_TEMP','detail':'Hot'}
        payload={'events':[event]}
        self.assertEqual(self.client.post('/api/ingest/events',payload,format='json').json()['stored'],1)
        self.assertEqual(self.client.post('/api/ingest/events',payload,format='json').json()['stored'],0)
        self.assertEqual(self.viewer.get(f'/api/v2/sites/{self.site.id}/miners?limit=201').status_code,400)

class PlacementRaceTests(TransactionTestCase):
    def test_two_requests_cannot_occupy_one_slot(self):
        if connection.vendor!='postgresql':self.skipTest('Real row-lock concurrency is tested on PostgreSQL.')
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        owner=user('race@example.com');org=organization(owner,'Race');site=Site.objects.create(organization=org,name='Race site');rack=Rack.objects.create(site=site,name='R');slot=RackSlot.objects.create(rack=rack,row=1,col=1)
        machines=[Miner.objects.create(site=site,identity='serial:'+str(i),identity_status='reported',ip='10.0.0.'+str(i+1),last_seen_at=timezone.now()) for i in range(2)]
        barrier=Barrier(2)
        def move(miner):
            close_old_connections();client=APIClient();client.force_authenticate(user=owner);barrier.wait()
            try:return client.post(f'/api/v2/sites/{site.id}/miners/{miner.id}/placement',{'slotId':str(slot.id),'reason':'race'},format='json').status_code
            finally:close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:statuses=list(pool.map(move,machines))
        self.assertEqual(sorted(statuses),[200,400]);self.assertEqual(Placement.objects.count(),1);self.assertEqual(AuditLog.objects.filter(action='placement.changed').count(),1)
