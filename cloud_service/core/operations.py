import math
import secrets
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError,transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError,PermissionDenied
from rest_framework.response import Response
from .models import Site,Agent,Miner,Rack,RackSlot,Placement,AuditLog,MinerAssignment,SitePlan
from .security import scope,strict,clean_text
from .services import audit,digest


def paginate(request,query):
    try:limit=int(request.query_params.get('limit',50));offset=int(request.query_params.get('offset',0))
    except (ValueError,TypeError):raise ValidationError('Phân trang không hợp lệ.')
    if not 1<=limit<=200 or not 0<=offset<=1000000:raise ValidationError('Giới hạn trang từ 1–200, offset không âm.')
    return query.count(),query[offset:offset+limit]

def site_scope(request,site_id,write=False):
    member=scope(request,write=write)
    return member,get_object_or_404(Site,pk=site_id,organization=member.organization)

def site_data(site):
    return {'id':site.id,'name':site.name,'location':site.location,'timezone':site.timezone,'minerCount':site.miners.count(),'agentCount':site.agents.filter(revoked_at__isnull=True).count()}

@api_view(['GET','POST'])
def sites(request):
    member=scope(request,write=request.method=='POST')
    if request.method=='GET':
        count,rows=paginate(request,Site.objects.filter(organization=member.organization).order_by('name','id'))
        return Response({'count':count,'results':[site_data(site) for site in rows]})
    strict(request.data,['name','location'])
    name=clean_text(request.data.get('name'),'name');location=clean_text(request.data.get('location',''),'location',240,False)
    with transaction.atomic():
        site=Site.objects.create(organization=member.organization,name=name,location=location)
        audit(request,'site.created',member.organization,site.id)
    return Response(site_data(site),status=201)

@api_view(['GET','PATCH'])
def site_detail(request,site_id):
    member,site=site_scope(request,site_id,request.method=='PATCH')
    if request.method=='PATCH':
        strict(request.data,['name','location'])
        with transaction.atomic():
            site=Site.objects.select_for_update().get(pk=site.id)
            if 'name' in request.data:site.name=clean_text(request.data['name'],'name')
            if 'location' in request.data:site.location=clean_text(request.data['location'],'location',240,False)
            site.save();audit(request,'site.updated',member.organization,site.id)
    return Response(site_data(site))

def agent_data(agent):
    return {'id':agent.id,'siteId':agent.site_id,'name':agent.name,'keyPrefix':agent.key_prefix,'createdAt':agent.created_at,'revokedAt':agent.revoked_at,'lastHeartbeatAt':agent.last_heartbeat_at,'lastSnapshotAt':agent.last_snapshot_at,'mode':'monitor'}

@api_view(['GET','POST'])
def agents(request,site_id):
    member,site=site_scope(request,site_id,request.method=='POST')
    if request.method=='GET':return Response({'results':[agent_data(a) for a in site.agents.order_by('-created_at')]})
    strict(request.data,['name']);name=clean_text(request.data.get('name'),'name')
    raw='bsky_'+secrets.token_urlsafe(32)
    with transaction.atomic():
        agent=Agent.objects.create(site=site,name=name,key_hash=digest(raw),key_prefix=raw[:12])
        audit(request,'agent.created',member.organization,agent.id)
    response=Response({**agent_data(agent),'key':raw},status=201);response['Cache-Control']='no-store';return response

@api_view(['DELETE','POST'])
def agent_detail(request,site_id,agent_id):
    member,site=site_scope(request,site_id,True)
    strict(request.data,[])
    with transaction.atomic():
        agent=get_object_or_404(Agent.objects.select_for_update(),pk=agent_id,site=site)
        if request.method=='DELETE':
            agent.revoked_at=timezone.now();agent.save(update_fields=['revoked_at']);audit(request,'agent.revoked',member.organization,agent.id)
            return Response(agent_data(agent))
        if agent.revoked_at:raise ValidationError('Agent đã thu hồi. Tạo agent mới để kết nối lại.')
        raw='bsky_'+secrets.token_urlsafe(32);agent.key_hash=digest(raw);agent.key_prefix=raw[:12];agent.save(update_fields=['key_hash','key_prefix'])
        audit(request,'agent.key_rotated',member.organization,agent.id)
    response=Response({**agent_data(agent),'key':raw});response['Cache-Control']='no-store';return response

def miner_data(miner):
    placement=getattr(miner,'placement',None)
    assignment=getattr(miner,'minerassignment',None)
    extra={'customerId':assignment.customer_id if assignment else None,'customerName':assignment.customer.name if assignment and assignment.customer_id else '', 'groupId':assignment.group_id if assignment else None,'groupName':assignment.group.name if assignment and assignment.group_id else '', 'coolingLabel':assignment.group.cooling_label if assignment and assignment.group_id else '', 'condition':assignment.condition if assignment else 'operating','note':assignment.note if assignment else ''}
    fresh=(timezone.now()-miner.last_seen_at).total_seconds()<=600
    return {**extra,'id':miner.id,'siteId':miner.site_id,'ip':miner.ip,'serial':miner.serial,'model':miner.model,'identityStatus':miner.identity_status,'lastSeenAt':miner.last_seen_at,'stale':not fresh,'telemetry':miner.telemetry,'placement':{'slotId':placement.slot_id,'rackId':placement.slot.rack_id,'rackName':placement.slot.rack.name,'row':placement.slot.row,'col':placement.slot.col} if placement else None}

@api_view(['GET'])
def miners(request,site_id):
    member,site=site_scope(request,site_id)
    query=site.miners.order_by('ip','id');q=request.query_params.get('q','').strip()
    if len(q)>120:raise ValidationError('Tìm kiếm tối đa 120 ký tự.')
    if q:query=query.filter(Q(ip__icontains=q)|Q(model__icontains=q)|Q(serial__icontains=q))
    count,rows=paginate(request,query)
    return Response({'count':count,'results':[miner_data(m) for m in rows],'staleAfterSeconds':600,'generatedAt':timezone.now()})

@api_view(['GET'])
def miner_detail(request,site_id,miner_id):
    member,site=site_scope(request,site_id)
    return Response(miner_data(get_object_or_404(Miner,pk=miner_id,site=site)))

def integer(value,low,high,field):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or int(value)!=value or not low<=value<=high:raise ValidationError({field:'Số không hợp lệ.'})
    return int(value)

def rack_geometry(rack,data,creating=False):
    from .facility import number,default_plan
    floor=clean_text(data.get('floor',rack.floor),'floor',80)
    plan=SitePlan.objects.filter(site=rack.site).first()
    floors=plan.data.get('floors',['Tầng 1']) if plan else ['Tầng 1']
    if floor not in floors:raise ValidationError('Tạo tầng trong cấu hình xưởng trước.')
    rotation=integer(data.get('rotation',rack.rotation),0,270,'rotation')
    if rotation%90:raise ValidationError('Kệ chỉ xoay theo bước 90 độ.')
    x=number(data.get('x',float(rack.x)),'x',-200,200);z=number(data.get('z',float(rack.z)),'z',-200,200)
    def bounds(cols,rotation,x,z):
        w=cols*1.18+.6;d=1.7
        if rotation%180:w,d=d,w
        return x-w/2,x+w/2,z-d/2,z+d/2
    a=bounds(rack.cols,rotation,x,z)
    for other in Rack.objects.filter(site=rack.site,floor=floor).exclude(pk=rack.pk):
        b=bounds(other.cols,other.rotation,float(other.x),float(other.z))
        if a[0]<b[1]+.3 and a[1]>b[0]-.3 and a[2]<b[3]+.3 and a[3]>b[2]-.3:
            if creating and 'x' not in data and 'z' not in data:
                # Find a free row for ordinary add-rack forms.
                return rack_geometry(rack,{**data,'x':0,'z':max(float(r.z) for r in Rack.objects.filter(site=rack.site,floor=floor))+4},False)
            raise ValidationError('Kệ đè lên kệ khác; để trống khoảng cách ít nhất 0,3 đơn vị.')
    rack.floor=floor;rack.x=x;rack.z=z;rack.rotation=rotation

def rack_data(rack):
    slots=rack.slots.select_related('placement__miner').order_by('row','col')
    return {'id':rack.id,'siteId':rack.site_id,'name':rack.name,'rows':rack.rows,'cols':rack.cols,'floor':rack.floor,'x':float(rack.x),'z':float(rack.z),'rotation':rack.rotation,'slots':[{'id':slot.id,'row':slot.row,'col':slot.col,'minerId':getattr(getattr(slot,'placement',None),'miner_id',None)} for slot in slots]}

@api_view(['GET','POST'])
def racks(request,site_id):
    member,site=site_scope(request,site_id,request.method=='POST')
    if request.method=='GET':
        count,rows=paginate(request,site.racks.order_by('name','id'))
        return Response({'count':count,'results':[rack_data(r) for r in rows]})
    strict(request.data,['name','rows','cols','floor','x','z','rotation'])
    name=clean_text(request.data.get('name'),'name',80);rows=integer(request.data.get('rows',4),1,12,'rows');cols=integer(request.data.get('cols',6),1,12,'cols')
    with transaction.atomic():
        Site.objects.select_for_update().get(pk=site.id)
        rack=Rack(site=site,name=name,rows=rows,cols=cols)
        rack_geometry(rack,request.data,creating=True);rack.save()
        RackSlot.objects.bulk_create([RackSlot(rack=rack,row=r,col=c) for r in range(1,rows+1) for c in range(1,cols+1)])
        audit(request,'rack.created',member.organization,rack.id,{'siteId':str(site.id)})
    return Response(rack_data(rack),status=201)

@api_view(['PATCH','DELETE'])
def rack_detail(request,site_id,rack_id):
    member,site=site_scope(request,site_id,True)
    with transaction.atomic():
        Site.objects.select_for_update().get(pk=site.id)
        rack=get_object_or_404(Rack.objects.select_for_update(),pk=rack_id,site=site)
        if request.method=='DELETE':
            strict(request.data,[])
            if Placement.objects.filter(slot__rack=rack).exists():raise ValidationError('Tháo máy khỏi kệ trước khi xóa kệ.')
            plan=SitePlan.objects.filter(site=site).first()
            if plan and str(rack.id) in plan.data.get('feeds',{}):raise ValidationError('Gỡ nguồn cấp kệ trong cấu hình điện trước khi xóa.')
            rack.delete();audit(request,'rack.deleted',member.organization,rack_id);return Response(status=204)
        strict(request.data,['name','rows','cols','floor','x','z','rotation'])
        rows=integer(request.data.get('rows',rack.rows),1,12,'rows');cols=integer(request.data.get('cols',rack.cols),1,12,'cols')
        removed=rack.slots.filter(Q(row__gt=rows)|Q(col__gt=cols))
        if Placement.objects.filter(slot__in=removed).exists():raise ValidationError('Không thu nhỏ kệ qua vị trí đang có máy.')
        removed.delete();existing=set(rack.slots.values_list('row','col'))
        RackSlot.objects.bulk_create([RackSlot(rack=rack,row=r,col=c) for r in range(1,rows+1) for c in range(1,cols+1) if (r,c) not in existing])
        rack.rows=rows;rack.cols=cols
        if 'name' in request.data:rack.name=clean_text(request.data['name'],'name',80)
        rack_geometry(rack,request.data);rack.save();audit(request,'rack.updated',member.organization,rack.id)
    return Response(rack_data(rack))

@api_view(['POST'])
def place(request,site_id,miner_id):
    member,site=site_scope(request,site_id,True)
    strict(request.data,['slotId','reason','confirmIdentity'])
    reason=clean_text(request.data.get('reason'),'reason',500)
    with transaction.atomic():
        Site.objects.select_for_update().get(pk=site.id)
        miner=get_object_or_404(Miner.objects.select_for_update(),pk=miner_id,site=site)
        if miner.identity_status!='reported' and request.data.get('slotId') and request.data.get('confirmIdentity') is not True:
            raise ValidationError('Máy chưa có serial/MAC báo về. Cần xác nhận đối chiếu danh tính trước khi gắn.')
        old=Placement.objects.filter(miner=miner).first();old_slot=str(old.slot_id) if old else None
        slot_id=request.data.get('slotId');slot=None
        if slot_id:
            slot=get_object_or_404(RackSlot.objects.select_for_update(),pk=slot_id,rack__site=site)
            occupied=Placement.objects.filter(slot=slot).exclude(miner=miner).exists()
            if occupied:raise ValidationError('Ô đã có máy; chọn ô trống.')
        if old:old.delete()
        if slot:Placement.objects.create(miner=miner,slot=slot)
        audit(request,'placement.changed',member.organization,miner.id,{'from':old_slot,'to':str(slot.id) if slot else None,'reason':reason})
    return Response(miner_data(miner))

@api_view(['GET'])
def audit_logs(request):
    member=scope(request)
    count,rows=paginate(request,AuditLog.objects.filter(organization=member.organization).select_related('actor').order_by('-created_at','id'))
    return Response({'count':count,'results':[{'id':row.id,'actor':row.actor.display_name if row.actor else None,'agentId':row.agent_id,'action':row.action,'target':row.target,'metadata':row.metadata,'at':row.created_at} for row in rows]})

@api_view(['GET'])
def overview(request):
    from datetime import timedelta
    member=scope(request);org=member.organization
    machines=Miner.objects.filter(site__organization=org)
    fresh=machines.filter(last_seen_at__gte=timezone.now()-timedelta(seconds=600)).count()
    total=machines.count()
    return Response({'siteCount':org.sites.count(),'minerCount':total,'freshCount':fresh,'staleCount':total-fresh,'agentCount':Agent.objects.filter(site__organization=org,revoked_at__isnull=True).count(),'generatedAt':timezone.now()})
