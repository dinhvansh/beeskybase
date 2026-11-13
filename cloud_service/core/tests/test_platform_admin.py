from unittest.mock import patch
from io import StringIO
from tempfile import TemporaryDirectory
from pathlib import Path
from datetime import timedelta
from django.core.management import call_command, CommandError
from django.contrib.sessions.models import Session
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from core.models import User, Organization, Membership, Site, UserSession, AuditLog, Outbox, EmailToken
from core.services import email_token

PASSWORD = 'Private!Quartz-Cloud#2026'


class PlatformAdminTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('root@example.com', PASSWORD,
            display_name='Root', email_verified_at=timezone.now())
        self.user = User.objects.create_user('owner@example.com', PASSWORD,
            display_name='Owner', email_verified_at=timezone.now())
        self.pending = User.objects.create_user('pending@example.com', PASSWORD, display_name='Pending')
        self.org = Organization.objects.create(name='Private Org', created_by=self.user)
        Membership.objects.create(user=self.user, organization=self.org, role='owner')
        Site.objects.create(organization=self.org, name='Private Site')
        self.client = APIClient(); self.client.force_login(self.admin)

    def action(self, target, action, reason='Operator requested change'):
        return self.client.post(f'/api/v2/platform/users/{target.pk}/action',
            {'action': action, 'reason': reason}, format='json')

    def test_only_verified_active_superuser_can_access_every_endpoint(self):
        endpoints = ['overview', 'users', 'organizations', 'audit']
        for role in ('owner', 'admin', 'viewer'):
            Membership.objects.filter(user=self.user).update(role=role)
            self.client.force_login(self.user)
            for endpoint in endpoints:
                self.assertEqual(self.client.get('/api/v2/platform/'+endpoint).status_code, 403)
            self.assertEqual(self.action(self.pending, 'enable').status_code, 403)
        self.user.is_staff = True; self.user.save()
        self.assertEqual(self.client.get('/api/v2/platform/users').status_code, 403)
        self.admin.email_verified_at = None; self.admin.save()
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get('/api/v2/platform/users').status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get('/api/v2/platform/users').status_code, 403)

    def test_counts_filters_and_pagination_do_not_expose_secrets(self):
        summary = self.client.get('/api/v2/platform/overview').json()
        self.assertEqual(summary['users'], 3); self.assertEqual(summary['pending'], 1)
        self.assertEqual(summary['organizations'], 1); self.assertEqual(summary['sites'], 1)
        data = self.client.get('/api/v2/platform/users?status=pending&limit=1').json()
        self.assertEqual(data['count'], 1); self.assertEqual(data['results'][0]['email'], self.pending.email)
        self.assertNotIn('password', str(data)); self.assertNotIn('argon2', str(data))
        self.assertEqual(self.client.get('/api/v2/platform/users?q=owner').json()['results'][0]['organizationCount'], 1)
        self.assertEqual(self.client.get('/api/v2/platform/organizations').json()['results'][0]['sites'], 1)
        for query in ('limit=999', 'offset=-1', 'limit=abc', 'status=bad'):
            self.assertEqual(self.client.get('/api/v2/platform/users?'+query).status_code, 400)

    def test_disable_revokes_all_sessions_and_tokens_but_preserves_tenant(self):
        other = APIClient()
        self.assertEqual(other.post('/api/v2/auth/login', {'email': self.user.email, 'password': PASSWORD}, format='json').status_code, 200)
        token, _ = email_token(self.user, 'reset')
        self.assertTrue(UserSession.objects.filter(user=self.user).exists())
        self.assertEqual(self.action(self.user, 'disable').status_code, 200)
        self.user.refresh_from_db(); token.refresh_from_db()
        self.assertFalse(self.user.is_active); self.assertIsNotNone(token.used_at)
        self.assertFalse(UserSession.objects.filter(user=self.user).exists())
        self.assertEqual(other.get('/api/v2/platform/users').status_code, 403)
        self.assertFalse(other.get('/api/v2/auth/me').json()['authenticated'])
        self.assertTrue(Organization.objects.filter(pk=self.org.pk).exists())
        self.assertEqual(self.action(self.user, 'enable').status_code, 200)
        self.assertFalse(other.get('/api/v2/auth/me').json()['authenticated'])
        log = AuditLog.objects.get(action='platform.user.disable')
        self.assertEqual(log.actor, self.admin); self.assertEqual(log.target, str(self.user.pk))

    def test_superadmins_cannot_be_changed_or_created_through_user_api(self):
        for action in ('disable', 'enable', 'revoke_sessions', 'resend_verification'):
            self.assertEqual(self.action(self.admin, action).status_code, 400)
        self.assertEqual(self.action(self.user, 'grant_superadmin').status_code, 400)
        self.assertEqual(self.action(self.user, 'disable', '').status_code, 400)
        self.assertEqual(self.client.post(f'/api/v2/platform/users/{self.user.pk}/action',
            {'action': 'enable', 'reason': 'test', 'is_superuser': True}, format='json').status_code, 400)

    def test_resend_queue_and_csrf(self):
        self.assertEqual(self.action(self.pending, 'resend_verification').status_code, 200)
        self.assertEqual(Outbox.objects.count(), 1)
        self.assertEqual(self.action(self.user, 'resend_verification').status_code, 400)
        csrf_client = APIClient(enforce_csrf_checks=True); csrf_client.force_login(self.admin)
        self.assertEqual(csrf_client.post(f'/api/v2/platform/users/{self.user.pk}/action',
            {'action': 'disable', 'reason': 'test'}, format='json').status_code, 403)

    def test_superadmin_does_not_automatically_read_tenant_operational_data(self):
        self.assertEqual(self.client.get('/api/v2/overview').status_code, 403)
        self.assertEqual(self.client.get('/api/v2/auth/me').json()['user']['superadmin'], True)

    def test_bootstrap_promotes_only_verified_existing_user(self):
        with self.assertRaises(CommandError):
            call_command('bootstrap_superadmin', email=self.pending.email, promote_existing=True, stdout=StringIO())
        call_command('bootstrap_superadmin', email=self.user.email, promote_existing=True, stdout=StringIO())
        self.user.refresh_from_db(); self.assertTrue(self.user.is_superuser)
        self.assertTrue(self.user.check_password(PASSWORD))

    @patch('core.management.commands.bootstrap_superadmin.getpass.getpass', side_effect=[PASSWORD, PASSWORD])
    def test_bootstrap_prompts_privately_and_creates_verified_account(self, prompt):
        output = StringIO()
        call_command('bootstrap_superadmin', email='new@example.com', name='Admin', stdout=output)
        created = User.objects.get(email='new@example.com')
        self.assertTrue(created.is_superuser); self.assertIsNotNone(created.email_verified_at)
        self.assertNotIn(PASSWORD, output.getvalue())

    def test_private_setup_link_expires_and_cannot_overwrite_existing_account(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'setup.txt'
            output = StringIO()
            call_command('bootstrap_superadmin', email='setup@example.com',
                setup_link_file=str(path), stdout=output)
            created = User.objects.get(email='setup@example.com')
            self.assertFalse(created.has_usable_password())
            token = EmailToken.objects.get(user=created, kind='reset')
            self.assertLessEqual(token.expires_at, timezone.now()+timedelta(minutes=15))
            self.assertNotIn(path.read_text().split('token=')[1], output.getvalue())
            with self.assertRaises(CommandError):
                call_command('bootstrap_superadmin', email=created.email,
                    setup_link_file=str(path), stdout=StringIO())
