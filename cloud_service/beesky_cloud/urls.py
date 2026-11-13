import os
from django.conf import settings
from django.http import JsonResponse
from django.db import connection
from django.shortcuts import render
from django.urls import path
from django.views.generic import RedirectView
from core import accounts,operations,ingest,facility,upkeep,platform_admin

def index(request):
    response=render(request,'app.html',{'mailbox_url':os.getenv('BEESKY_LOCAL_MAILBOX','') if settings.DEBUG else ''})
    response['Cache-Control']='no-store'
    return response

def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM django_migrations WHERE app=%s AND name=%s",['core','0004_alert_expires_at'])
            if cursor.fetchone() is None:raise RuntimeError('Migrations not ready')
    except Exception:return JsonResponse({'status':'unavailable'},status=503)
    return JsonResponse({'status':'ok','database':connection.vendor,'service':'beesky-cloud'})

def control(request):
    response=render(request,'platform.html')
    response['Cache-Control']='no-store'
    return response

urlpatterns=[
    path('control/',control),
    path('api/v2/platform/overview',platform_admin.overview),
    path('api/v2/platform/users',platform_admin.users),
    path('api/v2/platform/users/<uuid:user_id>/action',platform_admin.user_action),
    path('api/v2/platform/organizations',platform_admin.organizations),
    path('api/v2/platform/audit',platform_admin.logs),
    path('assets/models/s21-hydro.glb',RedirectView.as_view(url='/static/assets/models/s21-hydro.glb')),
    path('assets/models/s19-pro-air.glb',RedirectView.as_view(url='/static/assets/models/s19-pro-air.glb')),
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
    path('api/v2/customers',facility.customers),
    path('api/v2/sites/<uuid:site_id>/plan',facility.plan),
    path('api/v2/sites/<uuid:site_id>/power',facility.power),
    path('api/v2/sites/<uuid:site_id>/layout',facility.layout),
    path('api/v2/sites/<uuid:site_id>/groups',facility.groups),
    path('api/v2/sites/<uuid:site_id>/miners/<uuid:miner_id>/assignment',facility.assignment),
    path('api/v2/sites/<uuid:site_id>/repairs',facility.repairs),
    path('api/v2/sites/<uuid:site_id>/repairs/<uuid:repair_id>/close',facility.close_repair),
    path('api/v2/sites/<uuid:site_id>/events',facility.events),
    path('api/v2/sites/<uuid:site_id>/rules',facility.rules),
    path('api/v2/sites/<uuid:site_id>/rules/<uuid:rule_id>',facility.delete_rule),
    path('api/v2/sites/<uuid:site_id>/alerts',facility.alerts),
    path('api/v2/sites/<uuid:site_id>/alerts/<uuid:alert_id>/acknowledge',facility.acknowledge),
    path('api/v2/sites/<uuid:site_id>/maintenance/schedules',upkeep.schedules),
    path('api/v2/sites/<uuid:site_id>/maintenance/schedules/<uuid:schedule_id>',upkeep.schedule_detail),
    path('api/v2/sites/<uuid:site_id>/maintenance/tickets',upkeep.tickets),
    path('api/v2/sites/<uuid:site_id>/maintenance/tickets/<uuid:ticket_id>',upkeep.ticket),
    path('api/v2/sites/<uuid:site_id>/maintenance/tickets/<uuid:ticket_id>/photos',upkeep.photos),
    path('api/v2/sites/<uuid:site_id>/maintenance/photos/<uuid:photo_id>',upkeep.photo),
]
