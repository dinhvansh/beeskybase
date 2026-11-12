import re
from datetime import timedelta
from django.core import mail
from django.db import IntegrityError,transaction
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from core.models import User,Organization,Membership,Site,EmailToken,Outbox,UserSession,Agent,Miner,Rack,RackSlot,Placement,Snapshot,Observation,AuditLog
from core.services import deliver_mail_once,email_token,digest

PASSWORD='Quartz!Mango-Cloud#2026'

def user(email,name='User'):
    return User.objects.create_user(email,PASSWORD,display_name=name,email_verified_at=timezone.now())

def organization(owner,name):
    org=Organization.objects.create(name=name,created_by=owner);Membership.objects.create(user=owner,organization=org,role='owner');return org

class AccountTests(TestCase):
    def setUp(self):self.client=APIClient()
    def test_registration_email_is_encrypted_and_verification_is_single_use(self):
        body={'email':'TEST@Example.com','name':'Test User','password':PASSWORD}
        self.assertEqual(self.client.post('/api/v2/auth/register',body,format='json').status_code,202)
        u=User.objects.get(email='test@example.com');self.assertTrue(u.password.startswith('argon2$'));self.assertIsNone(u.email_verified_at)
        self.assertEqual(self.client.post('/api/v2/auth/login',{'email':u.email,'password':PASSWORD},format='json').status_code,403)
        self.assertNotIn(b'test@example.com',bytes(Outbox.objects.get().encrypted_payload))
        self.assertEqual(deliver_mail_once(),1);self.assertEqual(bytes(Outbox.objects.get().encrypted_payload),b'')
        token=re.search(r'token=([\w-]+)',mail.outbox[-1].body)[1]
        self.assertEqual(self.client.post('/api/v2/auth/verify',{'token':token},format='json').status_code,200)
        self.assertEqual(self.client.post('/api/v2/auth/verify',{'token':token},format='json').status_code,400)
        self.assertEqual(self.client.post('/api/v2/auth/login',{'email':u.email,'password':PASSWORD},format='json').status_code,200)
        self.assertEqual(self.client.get('/api/v2/auth/me').json()['organizations'],[])
        self.assertEqual(UserSession.objects.filter(user=u).count(),1)
    def test_csrf_covers_anonymous_login_and_origin(self):
        u=user('csrf@example.com');client=APIClient(enforce_csrf_checks=True)
        body={'email':u.email,'password':PASSWORD}
        self.assertEqual(client.post('/api/v2/auth/login',body,format='json').status_code,403)
        token=client.get('/api/v2/auth/csrf').json()['csrfToken']
        self.assertEqual(client.post('/api/v2/auth/login',body,format='json',HTTP_X_CSRFTOKEN=token,HTTP_ORIGIN='https://attacker.invalid').status_code,403)
        response=client.post('/api/v2/auth/login',body,format='json',HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code,200);self.assertTrue(response.cookies['beesky_cloud_session']['httponly']);self.assertEqual(response.cookies['beesky_cloud_session']['samesite'],'Lax')
    def test_expired_token_and_generic_forgot_responses(self):
        u=user('reset@example.com');record,raw=email_token(u,'verify');record.expires_at=timezone.now()-timedelta(seconds=1);record.save()
        self.assertEqual(self.client.post('/api/v2/auth/verify',{'token':raw},format='json').status_code,400)
        known=self.client.post('/api/v2/auth/forgot',{'email':u.email},format='json');unknown=self.client.post('/api/v2/auth/forgot',{'email':'absent@example.com'},format='json')
        self.assertEqual(known.status_code,unknown.status_code);self.assertEqual(known.json(),unknown.json())
    def test_reset_revokes_existing_sessions_and_cannot_be_replayed(self):
        u=user('reset2@example.com');a=APIClient();b=APIClient()
        for client in (a,b):self.assertEqual(client.post('/api/v2/auth/login',{'email':u.email,'password':PASSWORD},format='json').status_code,200)
        _,raw=email_token(u,'reset');data={'token':raw,'password':'River!Octagon-New#2027'}
        self.assertEqual(self.client.post('/api/v2/auth/reset',data,format='json').status_code,200)
        self.assertFalse(a.get('/api/v2/auth/me').json()['authenticated']);self.assertFalse(b.get('/api/v2/auth/me').json()['authenticated'])
        self.assertEqual(UserSession.objects.filter(user=u).count(),0);self.assertEqual(self.client.post('/api/v2/auth/reset',data,format='json').status_code,400)
    def test_login_rate_limit_and_casefolded_email_uniqueness(self):
        u=user('lower@example.com')
        response=self.client.post('/api/v2/auth/register',{'email':'LOWER@EXAMPLE.COM','name':'Duplicate','password':PASSWORD},format='json')
        self.assertEqual(response.status_code,202);self.assertEqual(User.objects.filter(email__iexact=u.email).count(),1)
        for _ in range(10):self.assertEqual(self.client.post('/api/v2/auth/login',{'email':u.email,'password':'wrong'},format='json').status_code,400)
        self.assertEqual(self.client.post('/api/v2/auth/login',{'email':u.email,'password':'wrong'},format='json').status_code,429)
    def test_onboarding_creates_organization_site_and_owner_atomically(self):
        u=user('new@example.com');self.client.force_login(u)
        response=self.client.post('/api/v2/organizations',{'name':'Org','siteName':'Xưởng','location':'VN'},format='json')
        self.assertEqual(response.status_code,201);org=Organization.objects.get();self.assertEqual(Membership.objects.get(organization=org).role,'owner')
        self.assertEqual(self.client.get('/api/v2/overview').json()['minerCount'],0)
        self.assertEqual(self.client.get('/api/v2/sites').json()['results'][0]['minerCount'],0)

class IsolationTests(TestCase):
    def setUp(self):
        self.a=user('a@example.com','A');self.b=user('b@example.com','B');self.orga=organization(self.a,'Org A');self.orgb=organization(self.b,'Org B')
        self.sa=Site.objects.create(organization=self.orga,name='Same name');self.sb=Site.objects.create(organization=self.orgb,name='Same name')
        self.client=APIClient();self.client.force_login(self.a)
        self.agent=Agent.objects.create(site=self.sa,name='Agent',key_hash=digest('bsky_test-key-00000000000000000'),key_prefix='bsky_test')
        self.ma=Miner.objects.create(site=self.sa,identity='serial:a',identity_status='reported',ip='10.0.0.1',serial='a',model='S19 Pro',last_seen_at=timezone.now())
        self.mb=Miner.objects.create(site=self.sb,identity='serial:a',identity_status='reported',ip='10.0.0.1',serial='a',model='S19 Pro',last_seen_at=timezone.now())
        self.ra=Rack.objects.create(site=self.sa,name='Rack A');self.rb=Rack.objects.create(site=self.sb,name='Rack B')
        self.slota=RackSlot.objects.create(rack=self.ra,row=1,col=1);self.slotb=RackSlot.objects.create(rack=self.rb,row=1,col=1)
    def test_every_list_detail_and_nested_write_is_scoped(self):
        result=self.client.get('/api/v2/sites').json();self.assertEqual(result['count'],1);self.assertEqual(result['results'][0]['id'],str(self.sa.id))
        for path in [f'/api/v2/sites/{self.sb.id}',f'/api/v2/sites/{self.sb.id}/miners',f'/api/v2/sites/{self.sb.id}/agents',f'/api/v2/sites/{self.sb.id}/racks',f'/api/v2/sites/{self.sa.id}/miners/{self.mb.id}']:
            self.assertEqual(self.client.get(path).status_code,404,path)
        path=f'/api/v2/sites/{self.sa.id}/miners/{self.ma.id}/placement'
        self.assertEqual(self.client.post(path,{'slotId':str(self.slotb.id),'reason':'test'},format='json').status_code,404)
        self.assertFalse(Placement.objects.exists())
    def test_viewer_writes_and_admin_membership_changes_are_forbidden(self):
        viewer=user('viewer@example.com');member=Membership.objects.create(user=viewer,organization=self.orga,role='viewer');self.client.force_login(viewer)
        self.assertEqual(self.client.get('/api/v2/sites').status_code,200)
        for path,data in [('/api/v2/sites',{'name':'blocked'}),(f'/api/v2/sites/{self.sa.id}/agents',{'name':'blocked'}),(f'/api/v2/sites/{self.sa.id}/racks',{'name':'blocked'})]:
            self.assertEqual(self.client.post(path,data,format='json').status_code,403)
        member.role='admin';member.save();owner=Membership.objects.get(user=self.a)
        self.assertEqual(self.client.patch('/api/v2/members/'+str(owner.id),{'role':'viewer'},format='json').status_code,403)
        self.assertEqual(self.client.post('/api/v2/invitations',{'email':'other@example.com'},format='json').status_code,403)
    def test_revocation_takes_effect_in_existing_session_and_last_owner_is_protected(self):
        owner=Membership.objects.get(user=self.a)
        self.assertEqual(self.client.delete('/api/v2/members/'+str(owner.id),{},format='json').status_code,400)
        self.assertEqual(self.client.patch('/api/v2/members/'+str(owner.id),{'role':'viewer'},format='json').status_code,400)
        owner.active=False;owner.save();self.assertEqual(self.client.get('/api/v2/sites').status_code,403)
    def test_invite_is_single_use_and_bound_to_verified_recipient(self):
        recipient=user('invited@example.com');response=self.client.post('/api/v2/invitations',{'email':recipient.email,'role':'viewer'},format='json');self.assertEqual(response.status_code,202)
        deliver_mail_once();raw=re.search(r'token=([\w-]+)',mail.outbox[-1].body)[1]
        other=APIClient();other.force_login(self.b);self.assertEqual(other.post('/api/v2/invitations/accept',{'token':raw},format='json').status_code,403)
        invited=APIClient();invited.force_login(recipient);self.assertEqual(invited.post('/api/v2/invitations/accept',{'token':raw},format='json').status_code,200)
        self.assertEqual(invited.post('/api/v2/sites',{'name':'blocked'},format='json').status_code,403)
        self.assertEqual(invited.post('/api/v2/invitations/accept',{'token':raw},format='json').status_code,400)
    def test_database_guard_blocks_cross_site_placements_and_parent_changes(self):
        with self.assertRaises(IntegrityError),transaction.atomic():Placement.objects.create(miner=self.ma,slot=self.slotb)
        Placement.objects.create(miner=self.ma,slot=self.slota)
        with self.assertRaises(IntegrityError),transaction.atomic():Miner.objects.filter(id=self.ma.id).update(site=self.sb)
        with self.assertRaises(IntegrityError),transaction.atomic():Rack.objects.filter(id=self.ra.id).update(site=self.sb)
        with self.assertRaises(IntegrityError),transaction.atomic():RackSlot.objects.filter(id=self.slota.id).update(rack=self.rb)
    def test_occupied_slot_rejection_preserves_existing_placements_and_audits_detach(self):
        other=Miner.objects.create(site=self.sa,identity='serial:other',identity_status='reported',ip='10.0.0.2',last_seen_at=timezone.now())
        Placement.objects.create(miner=other,slot=self.slota)
        path=f'/api/v2/sites/{self.sa.id}/miners/{self.ma.id}/placement'
        self.assertEqual(self.client.post(path,{'slotId':str(self.slota.id),'reason':'move'},format='json').status_code,400)
        self.assertEqual(Placement.objects.get(slot=self.slota).miner_id,other.id)
        detach=f'/api/v2/sites/{self.sa.id}/miners/{other.id}/placement'
        self.assertEqual(self.client.post(detach,{'slotId':None,'reason':'Repair'},format='json').status_code,200)
        log=AuditLog.objects.get(action='placement.changed');self.assertEqual(log.actor_id,self.a.id);self.assertIsNone(log.metadata['to'])
    def test_unverified_identity_requires_explicit_acknowledgment(self):
        self.ma.identity_status='unverified';self.ma.save();path=f'/api/v2/sites/{self.sa.id}/miners/{self.ma.id}/placement';body={'slotId':str(self.slota.id),'reason':'Physical check'}
        self.assertEqual(self.client.post(path,body,format='json').status_code,400);body['confirmIdentity']=True
        self.assertEqual(self.client.post(path,body,format='json').status_code,200)
    def test_unknown_fields_uuid_and_duplicate_names_fail_cleanly(self):
        self.assertEqual(self.client.post('/api/v2/sites',{'name':'Bad','organization_id':str(self.orgb.id)},format='json').status_code,400)
        self.assertEqual(self.client.post('/api/v2/sites',{'name':self.sa.name.lower()},format='json').status_code,409)
        self.assertEqual(self.client.post(f'/api/v2/sites/{self.sa.id}/miners/{self.ma.id}/placement',{'slotId':'invalid','reason':'test'},format='json').status_code,400)
