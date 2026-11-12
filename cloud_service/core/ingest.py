import hashlib
import ipaddress
import json
import math
from datetime import datetime,timedelta,timezone as datetime_timezone
from django.db import transaction
from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.decorators import api_view,authentication_classes
from rest_framework.exceptions import AuthenticationFailed,ValidationError
from rest_framework.response import Response
from .models import Agent,Site,Miner,Snapshot,Observation,Event
from .services import digest,audit

class AgentPrincipal:
    is_authenticated=True
    is_active=True

class AgentAuthentication(BaseAuthentication):
    def authenticate_header(self,request):return 'Bearer'
    def authenticate(self,request):
        header=request.headers.get('Authorization','')
        raw=header[7:] if header.startswith('Bearer ') else request.headers.get('X-Agent-Key','')
        if not isinstance(raw,str) or not 20<=len(raw)<=200:raise AuthenticationFailed('Mã agent không hợp lệ.')
        agent=Agent.objects.select_related('site__organization').filter(key_hash=digest(raw),revoked_at__isnull=True).first()
        if not agent:raise AuthenticationFailed('Mã agent không hợp lệ hoặc đã thu hồi.')
        return AgentPrincipal(),agent

def timestamp(raw,default=None):
    value=default if raw is None else raw
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):raise ValidationError('Timestamp không hợp lệ.')
    now=timezone.now().timestamp()
    if not now-86400<=value<=now+60:raise ValidationError('Timestamp quá cũ hoặc vượt thời gian cho phép.')
    return datetime.fromtimestamp(value,datetime_timezone.utc)

def numeric(value,field,low=0,high=1e15):
    if value is not None and (isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not low<=value<=high):raise ValidationError({field:'Chỉ nhận số hữu hạn trong phạm vi hợp lệ.'})

def validate_records(data):
    records=data.get('miners')
    if not isinstance(records,list) or len(records)>5000:raise ValidationError('Mỗi bản quét tối đa 5.000 máy.')
    result=[];identities=set();ips=set()
    for record in records:
        if not isinstance(record,dict) or len(json.dumps(record,allow_nan=False).encode())>65536:raise ValidationError('Bản ghi máy không hợp lệ hoặc quá lớn.')
        raw_ip=record.get('ip')
        try:
            if not isinstance(raw_ip,str):raise ValueError()
            ip=str(ipaddress.ip_address(raw_ip))
        except ValueError:raise ValidationError('IP máy không hợp lệ.')
        model=record.get('model') or ''
        serial=record.get('mac_or_serial') or record.get('serial') or record.get('mac') or ''
        if not isinstance(model,str) or len(model)>180 or not isinstance(serial,str) or len(serial)>180:raise ValidationError('Model hoặc danh tính máy quá dài/sai kiểu.')
        serial=serial.strip();identity=('serial:'+serial.casefold()) if serial else 'ip:'+ip
        if identity in identities or ip in ips:raise ValidationError('Bản quét trùng IP hoặc serial/MAC; cần đối chiếu trước khi nhận.')
        identities.add(identity);ips.add(ip)
        for key in ['power_w','ths','ghs_5s','ghs_av','rate_value','elapsed_s']:
            numeric(record.get(key),key)
        for key in ['temp_c','max_temp_c']:
            numeric(record.get(key),key,-100,200)
        result.append((ip,model,serial,identity,{**record,'ip':ip}))
    return result

@api_view(['POST'])
@authentication_classes([AgentAuthentication])
def ingest(request):
    if not isinstance(request.data,dict):raise ValidationError('Snapshot cần là object JSON.')
    try:records=validate_records(request.data)
    except (ValueError,TypeError,OverflowError):raise ValidationError('Snapshot có dữ liệu số hoặc JSON không hợp lệ.')
    ts=timestamp(request.data.get('ts'),timezone.now().timestamp());agent=request.auth
    fingerprint=digest(json.dumps({'ts':ts.timestamp(),'miners':request.data['miners']},sort_keys=True,separators=(',',':'),allow_nan=False))
    with transaction.atomic():
        Site.objects.select_for_update().get(pk=agent.site_id)
        # Re-read revocation/key under lock so revoke/rotation takes effect on new requests.
        locked=Agent.objects.select_for_update().get(pk=agent.id)
        if locked.revoked_at or locked.key_hash!=agent.key_hash:raise AuthenticationFailed('Mã agent đã thu hồi hoặc đổi.')
        locked.last_heartbeat_at=timezone.now()
        if not locked.last_snapshot_at or ts>locked.last_snapshot_at:locked.last_snapshot_at=ts
        locked.save(update_fields=['last_heartbeat_at','last_snapshot_at'])
        snapshot,created=Snapshot.objects.get_or_create(agent=locked,digest=fingerprint,defaults={'ts':ts,'count':len(records)})
        if not created:return Response({'ok':True,'site':str(agent.site_id),'agent_id':str(agent.id),'miners':snapshot.count,'duplicate':True})
        observations=[]
        for ip,model,serial,identity,record in records:
            miner=Miner.objects.filter(site=agent.site,identity=identity).first()
            if miner and serial and miner.ip!=ip and miner.last_agent_id and miner.last_agent_id!=agent.id and (timezone.now()-miner.last_seen_at).total_seconds()<600:
                raise ValidationError('Hai agent báo cùng serial/MAC ở IP khác nhau. Cần đối chiếu danh tính.')
            if not miner:
                miner=Miner(site=agent.site,identity=identity,ip=ip,model=model,serial=serial,identity_status='reported' if serial else 'unverified',last_seen_at=ts,telemetry=record,last_agent=agent)
                miner.save()
            elif ts>=miner.last_seen_at:
                miner.ip=ip;miner.model=model;miner.serial=serial;miner.last_seen_at=ts;miner.telemetry=record;miner.last_agent=agent;miner.save()
            observations.append(Observation(snapshot=snapshot,miner=miner,record=record))
        Observation.objects.bulk_create(observations)
        keep=Snapshot.objects.filter(agent=agent).order_by('-ts','-received_at').values('id')[:100]
        Snapshot.objects.filter(agent=agent).exclude(id__in=keep).delete()
        audit(request,'agent.snapshot_ingested',agent.site.organization,snapshot.id,{'count':len(records)},agent=agent)
    return Response({'ok':True,'site':str(agent.site_id),'agent_id':str(agent.id),'miners':len(records),'duplicate':False})

@api_view(['POST'])
@authentication_classes([AgentAuthentication])
def ingest_events(request):
    data=request.data;agent=request.auth
    events=data.get('events') if isinstance(data,dict) else None
    if not isinstance(events,list) or len(events)>1000:raise ValidationError('Mỗi lần gửi tối đa 1.000 sự kiện.')
    now=timezone.now();validated=[]
    for event in events:
        if not isinstance(event,dict):raise ValidationError('Sự kiện không hợp lệ.')
        try:encoded=json.dumps(event,sort_keys=True,allow_nan=False)
        except (ValueError,TypeError):raise ValidationError('Sự kiện không hợp lệ.')
        if len(encoded.encode())>65536:raise ValidationError('Sự kiện quá lớn.')
        ts=timestamp(event.get('ts'),now.timestamp());validated.append((ts,digest(encoded),event))
    with transaction.atomic():
        locked=Agent.objects.select_for_update().get(id=agent.id)
        if locked.revoked_at or locked.key_hash!=agent.key_hash:raise AuthenticationFailed('Mã agent đã thu hồi hoặc đổi.')
        count=0
        for ts,hash_value,event in validated:
            _,created=Event.objects.get_or_create(agent=agent,digest=hash_value,defaults={'ts':ts,'record':event});count+=int(created)
        locked.last_heartbeat_at=now;locked.save(update_fields=['last_heartbeat_at'])
    return Response({'ok':True,'stored':count})

@api_view(['GET'])
@authentication_classes([AgentAuthentication])
def commands(request):
    return Response({'commands':[],'control_available':False})
