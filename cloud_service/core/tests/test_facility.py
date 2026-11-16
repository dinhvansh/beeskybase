import base64
import io
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from PIL import Image
from rest_framework.test import APIClient
from core.models import Site,Miner,Membership,Customer,MachineGroup,Placement,RackSlot,MaintenanceSchedule,MaintenanceTicket,Alert,Repair,Agent
from core.facility import default_plan,refresh_alerts,power_report
from core.upkeep import ensure_tickets
from core.services import digest
from .test_accounts_isolation import user,organization

class FacilityFixture(TestCase):
    def setUp(self):
        self.owner=user('facility@example.test');self.org=organization(self.owner,'Org');self.site=Site.objects.create(organization=self.org,name='Workshop');self.client=APIClient();self.client.force_login(self.owner);self.base=f'/api/v2/sites/{self.site.id}'
        other=user('otherfacility@example.test');self.otherorg=organization(other,'Other');self.other=Site.objects.create(organization=self.otherorg,name='Other Workshop')
        self.m=Miner.objects.create(site=self.site,ip='10.0.0.1',model='S21 Hydro 335T',serial='SER1',identity='serial:ser1',identity_status='reported',last_seen_at=timezone.now(),telemetry={'power_w':5000,'max_temp_c':65,'worker':'real.worker'})
    def post(self,path,data):return self.client.post(self.base+path,data,format='json')
    def put(self,path,data):return self.client.put(self.base+path,data,format='json')
    def rack(self,name='Rack'):
        r=self.post('/racks',{'name':name,'rows':1,'cols':2});self.assertEqual(r.status_code,201,r.data);return r.json()
    def configured(self):
        rack=self.rack();self.assertEqual(self.post('/miners/'+str(self.m.id)+'/placement',{'slotId':rack['slots'][0]['id'],'reason':'Install'}).status_code,200)
        p=default_plan();p.update(station={'name':'Station','capacity':10,'unit':'kva','pf':.9,'target':80,'margin':10,'auxKw':1},cabinets=[{'id':'cab','name':'Cabinet','limitKw':4}],branches=[{'id':'br','name':'Branch','cabinet':'cab','phaseKw':{'A':2,'B':2,'C':2}}],feeds={rack['id']:{'branch':'br','phase':'A'}})
        response=self.put('/plan',{'revision':0,'data':p});self.assertEqual(response.status_code,200,response.data);return rack,p
class FacilityTests(FacilityFixture):
    def test_plan_persistence_revision_and_tenant_references(self):
        rack,p=self.configured();self.assertEqual(self.client.get(self.base+'/plan').json()['data'],p)
        self.assertEqual(self.put('/plan',{'revision':0,'data':p}).status_code,409)
        p['phases']={'00000000-0000-0000-0000-000000000001':'A'};self.assertEqual(self.put('/plan',{'revision':1,'data':p}).status_code,400)
        self.assertEqual(self.client.get(f'/api/v2/sites/{self.other.id}/plan').status_code,404)
    def test_server_power_catalog_phase_limits_and_stale_measurements(self):
        rack,p=self.configured();r=self.client.get(self.base+'/power').json();self.assertAlmostEqual(r['loadKw'],6.896);self.assertAlmostEqual(r['limitKw'],7.2);self.assertAlmostEqual(r['branches'][0]['load']['A'],5.36)
        keys={a['key'] for a in r['alerts']};self.assertIn('branch:br:A',keys);self.assertIn('cabinet:cab',keys)
        self.m.telemetry={'power_w':9000};self.m.last_seen_at=timezone.now()-timedelta(minutes=11);self.m.save();self.assertEqual(power_report(self.site)['machines'][0]['measuredWatts'],None)
        p['feeds'][rack['id']]['phase']='ABC';self.assertEqual(self.put('/plan',{'revision':1,'data':p}).status_code,200);self.assertAlmostEqual(power_report(self.site)['branches'][0]['load']['A'],5.36/3)
    def test_floor_rotation_collision_and_occupied_slots_preserved(self):
        r,p=self.configured();second=self.rack('Second');self.assertNotEqual(second['z'],r['z'])
        path='/racks/'+second['id'];self.assertEqual(self.client.patch(self.base+path,{'x':0,'z':0},format='json').status_code,400)
        p['floors'].append('Tầng 2');self.put('/plan',{'revision':1,'data':p})
        response=self.client.patch(self.base+path,{'floor':'Tầng 2','rotation':90,'x':0,'z':0},format='json');self.assertEqual(response.status_code,200,response.data)
        p['floors']=['Tầng 1'];self.assertEqual(self.put('/plan',{'revision':2,'data':p}).status_code,400)
        self.assertEqual(self.client.delete(self.base+'/racks/'+r['id'],{},format='json').status_code,400)
        self.assertEqual(Placement.objects.get(miner=self.m).slot_id,RackSlot.objects.get(id=r['slots'][0]['id']).id)
    def test_customer_group_scope_and_worker_not_overridden(self):
        c=self.client.post('/api/v2/customers',{'name':'Client A'},format='json').json();g=self.post('/groups',{'name':'Water loop','coolingLabel':'Radiator 2'}).json()
        response=self.put('/miners/'+str(self.m.id)+'/assignment',{'customerId':c['id'],'groupId':g['id'],'condition':'faulty','note':'leak'});self.assertEqual(response.status_code,200,response.data);self.assertEqual(response.json()['telemetry']['worker'],'real.worker');self.assertEqual(response.json()['customerName'],'Client A')
        foreign=Customer.objects.create(organization=self.otherorg,name='Other');self.assertEqual(self.put('/miners/'+str(self.m.id)+'/assignment',{'customerId':str(foreign.id)}).status_code,404)
    def test_viewer_cannot_modify_operational_resources(self):
        viewer=user('viewerfacility@example.test');Membership.objects.create(user=viewer,organization=self.org,role='viewer');self.client.force_login(viewer)
        for method,path,data in [('post','/groups',{'name':'x'}),('put','/plan',{'revision':0,'data':default_plan()}),('post','/rules',{'name':'x'}),('post','/maintenance/schedules',{'name':'x'}),('post','/repairs',{'minerId':str(self.m.id),'issue':'x'})]:
            self.assertEqual(getattr(self.client,method)(self.base+path,data,format='json').status_code,403,path)
        self.assertEqual(self.client.get(self.base+'/layout').status_code,200)
    def test_repairs_link_to_real_machine_and_no_auto_replace(self):
        r=self.post('/repairs',{'minerId':str(self.m.id),'issue':'pump leak'});self.assertEqual(r.status_code,201,r.data);rid=r.json()['id']
        self.assertEqual(self.post('/repairs/'+rid+'/close',{'resolution':'replaced seal'}).status_code,200);self.assertEqual(Repair.objects.get(id=rid).status,'closed');self.assertEqual(self.m.minerassignment.condition,'stored')
    def test_alert_rules_run_on_server_and_resolve(self):
        rule=self.post('/rules',{'name':'Heat','metric':'max_temp_c','threshold':60});self.assertEqual(rule.status_code,201)
        refresh_alerts(self.site);a=Alert.objects.get(active=True);self.assertIn('10.0.0.1',a.message)
        self.assertEqual(self.post('/alerts/'+str(a.id)+'/acknowledge',{}).status_code,200)
        self.m.telemetry['max_temp_c']=55;self.m.save();refresh_alerts(self.site);a.refresh_from_db();self.assertFalse(a.active)
        self.assertEqual(self.post('/rules',{'name':'Unsupported control','metric':'reboot','threshold':1}).status_code,400)
    def test_surge_alert_uses_actual_agent_ingest_and_expires(self):
        key='bsky_fixture-only-12345678901234567890';Agent.objects.create(site=self.site,name='A',key_hash=digest(key),key_prefix=key[:12]);c=APIClient();c.credentials(HTTP_AUTHORIZATION='Bearer '+key)
        response=c.post('/api/ingest',{'ts':timezone.now().timestamp()+1,'miners':[{'ip':self.m.ip,'mac_or_serial':'SER1','model':self.m.model,'power_w':7000}]},format='json');self.assertEqual(response.status_code,200,response.data)
        refresh_alerts(self.site);a=Alert.objects.get(key='surge:'+str(self.m.id));self.assertTrue(a.active);a.expires_at=timezone.now()-timedelta(seconds=1);a.save();refresh_alerts(self.site);a.refresh_from_db();self.assertFalse(a.active)

class MaintenanceTests(FacilityFixture):
    def schedule(self):
        r=self.post('/maintenance/schedules',{'name':'Monthly air','day':31,'template':'air','checklist':['Inspect fan'],'startMonth':timezone.now().strftime('%Y-%m')});self.assertEqual(r.status_code,201,r.data);return MaintenanceSchedule.objects.get(id=r.json()['id']),MaintenanceTicket.objects.get(schedule_id=r.json()['id'])
    def test_monthly_dedup_due_date_and_frozen_template(self):
        s,t=self.schedule();ensure_tickets(self.site);ensure_tickets(self.site);self.assertEqual(MaintenanceTicket.objects.count(),1);self.assertEqual(t.checklist[0]['label'],'Inspect fan');s.checklist=['Changed later'];s.save();ensure_tickets(self.site);t.refresh_from_db();self.assertEqual(t.checklist[0]['label'],'Inspect fan');self.assertLessEqual(t.due_date.day,31)
    def test_evidence_approval_revision_and_authenticated_photos(self):
        s,t=self.schedule();path='/maintenance/tickets/'+str(t.id);checks=[{'label':'Inspect fan','done':True,'note':'Cleaned'}]
        r=self.put(path,{'revision':0,'checklist':checks,'assignee':'Technician','note':'Complete'});self.assertEqual(r.status_code,200,r.data)
        self.assertEqual(self.put(path,{'revision':0,'checklist':checks}).status_code,409)
        self.assertEqual(self.post(path,{'revision':1,'action':'submit'}).status_code,400)
        b=io.BytesIO();Image.new('RGB',(20,20),'red').save(b,format='PNG');encoded=base64.b64encode(b.getvalue()).decode()
        for rev,stage in [(1,'before'),(2,'after')]:
            r=self.post(path+'/photos',{'revision':rev,'item':0,'stage':stage,'data':encoded});self.assertEqual(r.status_code,201,r.data)
        photo_url=self.client.get(self.base+path).json()['photos'][0]['url'];self.assertEqual(self.client.get(photo_url)['Content-Type'],'image/jpeg');anonymous=APIClient();self.assertIn(anonymous.get(photo_url).status_code,[401,403])
        self.assertEqual(self.post(path,{'revision':3,'action':'submit'}).status_code,200)
        admin=user('adminupkeep@example.test');Membership.objects.create(user=admin,organization=self.org,role='admin');self.client.force_login(admin);self.assertEqual(self.post(path,{'revision':4,'action':'approve'}).status_code,403)
        self.client.force_login(self.owner);self.assertEqual(self.post(path,{'revision':4,'action':'approve'}).status_code,200);self.assertEqual(self.client.delete(photo_url,{},format='json').status_code,400)
        self.assertEqual(self.put(path,{'revision':5,'checklist':checks}).status_code,400)
    def test_reject_invalid_images_and_cross_site_tickets(self):
        s,t=self.schedule();path='/maintenance/tickets/'+str(t.id)
        self.assertEqual(self.post(path+'/photos',{'revision':0,'item':0,'stage':'before','data':base64.b64encode(b'<svg onload=alert(1)>').decode()}).status_code,400)
        self.assertEqual(self.client.get(f'/api/v2/sites/{self.other.id}'+path).status_code,404)
        self.assertEqual(self.put(path,{'revision':0,'checklist':[{'label':'Forged','done':True}]}).status_code,400)
