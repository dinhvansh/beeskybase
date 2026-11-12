import os
from django.conf import settings
from django.http import JsonResponse
from django.db import connection
from django.shortcuts import render
from django.urls import path
from core import accounts,operations,ingest

def index(request):
    response=render(request,'app.html',{'mailbox_url':os.getenv('BEESKY_LOCAL_MAILBOX','') if settings.DEBUG else ''})
    response['Cache-Control']='no-store'
    return response

def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM django_migrations WHERE app=%s AND name=%s",['core','0002_placement_site_guard'])
            if cursor.fetchone() is None:raise RuntimeError('Migrations not ready')
    except Exception:return JsonResponse({'status':'unavailable'},status=503)
    return JsonResponse({'status':'ok','database':connection.vendor,'service':'beesky-cloud'})

urlpatterns=[
    path('',index),path('health/ready',health),
    path('api/v2/auth/csrf',accounts.csrf),path('api/v2/auth/me',accounts.me),
    path('api/v2/auth/register',accounts.register),path('api/v2/auth/verify',accounts.verify),path('api/v2/auth/resend',accounts.resend),
    path('api/v2/auth/login',accounts.login),path('api/v2/auth/logout',accounts.logout),path('api/v2/auth/forgot',accounts.forgot),path('api/v2/auth/reset',accounts.reset_password),
    path('api/v2/auth/sessions',accounts.sessions),path('api/v2/auth/password',accounts.change_password),
    path('api/v2/organizations',accounts.organizations),path('api/v2/organizations/select',accounts.select_organization),
    path('api/v2/members',accounts.members),path('api/v2/members/<int:member_id>',accounts.member_detail),path('api/v2/invitations',accounts.invite),path('api/v2/invitations/accept',accounts.accept_invite),
    path('api/v2/overview',operations.overview),
    path('api/v2/sites',operations.sites),path('api/v2/sites/<uuid:site_id>',operations.site_detail),
    path('api/v2/sites/<uuid:site_id>/agents',operations.agents),path('api/v2/sites/<uuid:site_id>/agents/<uuid:agent_id>',operations.agent_detail),
    path('api/v2/sites/<uuid:site_id>/miners',operations.miners),path('api/v2/sites/<uuid:site_id>/miners/<uuid:miner_id>',operations.miner_detail),
    path('api/v2/sites/<uuid:site_id>/miners/<uuid:miner_id>/placement',operations.place),
    path('api/v2/sites/<uuid:site_id>/racks',operations.racks),path('api/v2/sites/<uuid:site_id>/racks/<uuid:rack_id>',operations.rack_detail),
    path('api/v2/audit',operations.audit_logs),
    path('api/ingest',ingest.ingest),path('api/ingest/events',ingest.ingest_events),path('api/agent/commands',ingest.commands),
]
