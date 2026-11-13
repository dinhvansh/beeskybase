"""Tenant-scoped operational plans and server-side power calculation."""
import math
import re
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from .models import Site,SitePlan,Customer,MachineGroup,MinerAssignment,Miner,Rack,Alert,AlertRule,Event,Repair
from .operations import site_scope,integer,paginate,miner_data
from .security import scope,strict,clean_text
from .services import audit

PHASES=('A','B','C','ABC')
def number(value,label,low=0,high=100000):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not low<=value<=high:
        raise ValidationError({label:'Số không hợp lệ.'})
    return value

def identifier(value,label):return clean_text(value,label,80)
def default_plan():return {'station':None,'cabinets':[],'branches':[],'feeds':{},'phases':{},'modelWatts':{},'floors':['Tầng 1'],'effects':True}

def validate_plan(site,data):
    strict(data,default_plan().keys());result=default_plan();result.update(data)
    s=result['station']
    if s is not None:
        strict(s,['name','capacity','unit','pf','target','auxKw','margin'])
        clean_text(s.get('name'),'name',80)
        if s.get('unit') not in ('kw','kva'):raise ValidationError('Đơn vị trạm cần là kw hoặc kva.')
        for key,lo,hi in [('capacity',.001,100000),('pf',.01,1),('target',1,100),('auxKw',0,100000),('margin',0,100)]:number(s.get(key),key,lo,hi)
    if not isinstance(result['effects'],bool):raise ValidationError('Hiệu ứng không hợp lệ.')
    floors=result['floors']
    if not isinstance(floors,list) or not 1<=len(floors)<=20 or len(set(str(f) for f in floors))!=len(floors):raise ValidationError('Cần 1–20 tầng khác tên.')
    for floor in floors:clean_text(floor,'floor',80)
    for key in ('cabinets','branches'):
        if not isinstance(result[key],list) or len(result[key])>200:raise ValidationError('Quá nhiều tủ/nhánh.')
    cs=set();bs=set()
    for c in result['cabinets']:
        strict(c,['id','name','limitKw']);identifier(c.get('id'),'id');clean_text(c.get('name'),'name',80);number(c.get('limitKw'),'limitKw',.001)
        if c['id'] in cs:raise ValidationError('Trùng mã tủ.')
        cs.add(c['id'])
    for b in result['branches']:
        strict(b,['id','name','cabinet','phaseKw']);identifier(b.get('id'),'id');clean_text(b.get('name'),'name',80)
        if b.get('cabinet') not in cs or b['id'] in bs:raise ValidationError('Tủ cấp hoặc mã nhánh không hợp lệ.')
        bs.add(b['id']);strict(b.get('phaseKw'),['A','B','C'])
        for p in 'ABC':number(b['phaseKw'].get(p),p,.001)
    rack_ids={str(v) for v in site.racks.values_list('id',flat=True)};miner_ids={str(v) for v in site.miners.values_list('id',flat=True)}
    for key in ('feeds','phases','modelWatts'):
        if not isinstance(result[key],dict) or len(result[key])>10000:raise ValidationError('Cấu hình vượt giới hạn.')
    for rid,feed in result['feeds'].items():
        strict(feed,['branch','phase'])
        if rid not in rack_ids or feed.get('branch') not in bs or feed.get('phase') not in PHASES:raise ValidationError('Nguồn cấp kệ phải thuộc xưởng hiện tại.')
    for mid,phase in result['phases'].items():
        if mid not in miner_ids or phase not in PHASES:raise ValidationError('Máy hoặc pha không hợp lệ.')
    for model,w in result['modelWatts'].items():clean_text(model,'model',180);number(w,'watts',1,100000)
    if site.racks.exclude(floor__in=floors).exists():raise ValidationError('Chuyển kệ ra khỏi tầng trước khi bỏ tầng.')
    return result

@api_view(['GET','PUT'])
def plan(request,site_id):
    member,site=site_scope(request,site_id,request.method=='PUT')
    if request.method=='GET':
        row=SitePlan.objects.filter(site=site).first()
        return Response({'revision':row.revision if row else 0,'data':row.data if row else default_plan()})
    strict(request.data,['revision','data']);revision=integer(request.data.get('revision'),0,2147483646,'revision')
    with transaction.atomic():
        Site.objects.select_for_update().get(pk=site.id)
        row,_=SitePlan.objects.get_or_create(site=site)
        if row.revision!=revision:return Response({'detail':'Cấu hình đã đổi ở cửa sổ khác. Tải lại trước khi lưu.'},status=409)
        row.data=validate_plan(site,request.data.get('data'));row.revision+=1;row.save()
        audit(request,'power_plan.updated',member.organization,site.id,{'revision':row.revision})
    return Response({'revision':row.revision,'data':row.data})

def catalog(model):
    name=re.sub(r'\b(bitmain|antminer)\b','',model.casefold()).replace('.','');name=' '.join(name.split())
    if re.fullmatch(r's19 pro(?: 110\s*(?:t|th|th/s))?',name):return 3250,'110' not in name
    match=re.fullmatch(r's21 (?:hyd|hydro)(?: (335|319|302)\s*(?:t|th|th/s))?',name)
    if match:return {'335':5360,'319':5104,'302':4832}[match[1] or '335'],match[1] is None
    return None,False

def power_report(site):
    row=SitePlan.objects.filter(site=site).first();plan=default_plan();plan.update(row.data if row else {})
    now=timezone.now();branches={b['id']:{**b,'load':dict.fromkeys('ABC',0.0),'unknown':0} for b in plan['branches']};cabinets={c['id']:{**c,'loadKw':0} for c in plan['cabinets']}
    total=0;unknown=0;unfed=0;machines=[];alerts=[]
    miners=site.miners.select_related('placement__slot__rack').all()
    for m in miners:
        rated,variant=catalog(m.model);source='catalog' if rated is not None else 'unknown'
        if m.model in plan['modelWatts']:rated=plan['modelWatts'][m.model];source='manual';variant=False
        stale=(now-m.last_seen_at).total_seconds()>600
        measured=m.telemetry.get('power_w');measured=measured if not stale and isinstance(measured,(int,float)) and not isinstance(measured,bool) and math.isfinite(measured) and measured>=0 else None
        watts=max(rated,measured or 0) if rated is not None else measured
        if rated is None and measured is not None:source='reported'
        placement=getattr(m,'placement',None);rid=str(placement.slot.rack_id) if placement else None
        if not placement:continue
        feed=plan['feeds'].get(rid);phase=plan['phases'].get(str(m.id),feed['phase'] if feed else None)
        if watts is None:unknown+=1
        else:total+=watts/1000
        if not feed:unfed+=1
        if feed:
            b=branches[feed['branch']]
            if watts is None:b['unknown']+=1
            else:
                for p in ('ABC' if phase=='ABC' else phase):b['load'][p]+=watts/1000/(3 if phase=='ABC' else 1)
        machines.append({'id':str(m.id),'ip':m.ip,'model':m.model,'ratedWatts':rated,'measuredWatts':measured,'watts':watts,'source':source,'variantMissing':variant,'stale':stale,'rackId':rid,'phase':phase})
    def warn(key,message):alerts.append({'key':key,'message':message})
    for b in branches.values():
        cabinets[b['cabinet']]['loadKw']+=sum(b['load'].values())
        for p in 'ABC':
            if b['load'][p]>b['phaseKw'][p]:warn('branch:'+b['id']+':'+p,b['name']+' vượt tải pha '+p)
        avg=sum(b['load'].values())/3;b['imbalancePercent']=(max(b['load'].values())-min(b['load'].values()))/avg*100 if avg else 0
        if b['imbalancePercent']>30:warn('imbalance:'+b['id'],b['name']+' lệch tải 3 pha trên 30%')
    for c in cabinets.values():
        if c['loadKw']>c['limitKw']:warn('cabinet:'+c['id'],c['name']+' vượt công suất tủ')
    s=plan['station'];load=total*(1+(s['margin']/100 if s else 0))+(s['auxKw'] if s else 0);capacity=s['capacity']*(s['pf'] if s['unit']=='kva' else 1) if s else None;limit=capacity*s['target']/100 if s else None
    if limit is not None and load>limit:warn('station:overload','Tổng tải vượt ngưỡng vận hành trạm')
    if unknown:warn('power:unknown',str(unknown)+' máy đã xếp chưa biết công suất')
    if unfed:warn('power:unfed',str(unfed)+' máy đã xếp chưa gán nhánh cấp điện')
    for m in machines:
        if m['variantMissing']:warn('variant:'+m['id'],m['ip']+' cần xác nhận biến thể model hoặc nhập W định mức')
    return {'loadKw':load,'capacityKw':capacity,'limitKw':limit,'remainingKw':None if limit is None else limit-load,'unknownCount':unknown,'unfedCount':unfed,'machines':machines,'branches':list(branches.values()),'cabinets':list(cabinets.values()),'alerts':alerts,'generatedAt':now,'scope':'placed-miners','note':'Tải quy hoạch = max(định mức, số đo mới); ABC chia đều. Không thay cho đo điện từng pha.'}

@api_view(['GET'])
def power(request,site_id):
    _,site=site_scope(request,site_id);return Response(power_report(site))

@api_view(['GET','POST'])
def customers(request):
    member=scope(request,write=request.method=='POST')
    if request.method=='POST':
        strict(request.data,['name']);row=Customer.objects.create(organization=member.organization,name=clean_text(request.data.get('name'),'name'));audit(request,'customer.created',member.organization,row.id)
        return Response({'id':row.id,'name':row.name},status=201)
    count,rows=paginate(request,Customer.objects.filter(organization=member.organization).order_by('name','id'))
    return Response({'count':count,'results':[{'id':r.id,'name':r.name} for r in rows]})

@api_view(['GET','POST'])
def groups(request,site_id):
    member,site=site_scope(request,site_id,request.method=='POST')
    if request.method=='POST':
        strict(request.data,['name','coolingLabel']);r=MachineGroup.objects.create(site=site,name=clean_text(request.data.get('name'),'name'),cooling_label=clean_text(request.data.get('coolingLabel',''),'coolingLabel',120,False));audit(request,'group.created',member.organization,r.id)
        return Response({'id':r.id,'name':r.name,'coolingLabel':r.cooling_label},status=201)
    count,rows=paginate(request,MachineGroup.objects.filter(site=site).order_by('name','id'))
    return Response({'count':count,'results':[{'id':r.id,'name':r.name,'coolingLabel':r.cooling_label} for r in rows]})

@api_view(['PUT'])
def assignment(request,site_id,miner_id):
    member,site=site_scope(request,site_id,True);strict(request.data,['customerId','groupId','condition','note'])
    customer=get_object_or_404(Customer,pk=request.data['customerId'],organization=member.organization) if request.data.get('customerId') else None
    group=get_object_or_404(MachineGroup,pk=request.data['groupId'],site=site) if request.data.get('groupId') else None
    condition=request.data.get('condition','operating')
    if condition not in ('operating','faulty','repair','stored'):raise ValidationError('Trạng thái máy không hợp lệ.')
    with transaction.atomic():
        Site.objects.select_for_update().get(pk=site.id);miner=get_object_or_404(Miner,pk=miner_id,site=site)
        MinerAssignment.objects.update_or_create(miner=miner,defaults={'customer':customer,'group':group,'condition':condition,'note':clean_text(request.data.get('note',''),'note',500,False)})
        audit(request,'miner.assignment_changed',member.organization,miner.id,{'customer':str(customer.id) if customer else None,'group':str(group.id) if group else None,'condition':condition})
    return Response(miner_data(miner))

@api_view(['GET'])
def layout(request,site_id):
    from .operations import rack_data
    _,site=site_scope(request,site_id)
    # Explicit bounded complete layout; never silently truncate a fleet.
    if site.miners.count()>10000:raise ValidationError('Xưởng vượt 10.000 máy; cần chia khu trước khi mở sơ đồ.')
    return Response({'racks':[rack_data(r) for r in site.racks.prefetch_related('slots').order_by('name')],'miners':[miner_data(m) for m in site.miners.select_related('placement__slot__rack','minerassignment__customer','minerassignment__group').order_by('ip')],'plan':(SitePlan.objects.filter(site=site).first().data if SitePlan.objects.filter(site=site).exists() else default_plan())})

@api_view(['GET','POST'])
def repairs(request,site_id):
    from .models import MaintenanceTicket
    member,site=site_scope(request,site_id,request.method=='POST')
    if request.method=='POST':
        strict(request.data,['minerId','ticketId','issue']);miner=get_object_or_404(Miner,pk=request.data.get('minerId'),site=site)
        ticket=get_object_or_404(MaintenanceTicket,pk=request.data['ticketId'],schedule__site=site) if request.data.get('ticketId') else None
        with transaction.atomic():
            r=Repair.objects.create(miner=miner,ticket=ticket,issue=clean_text(request.data.get('issue'),'issue',500));a,_=MinerAssignment.objects.get_or_create(miner=miner);a.condition='faulty';a.save();audit(request,'repair.opened',member.organization,r.id)
        return Response({'id':r.id},status=201)
    count,rows=paginate(request,Repair.objects.filter(miner__site=site).select_related('miner').order_by('-created_at'))
    return Response({'count':count,'results':[{'id':r.id,'minerId':r.miner_id,'ip':r.miner.ip,'issue':r.issue,'status':r.status,'resolution':r.resolution,'createdAt':r.created_at,'closedAt':r.closed_at} for r in rows]})

@api_view(['POST'])
def close_repair(request,site_id,repair_id):
    member,site=site_scope(request,site_id,True);strict(request.data,['resolution'])
    with transaction.atomic():
        r=get_object_or_404(Repair.objects.select_for_update(),id=repair_id,miner__site=site)
        if r.status!='open':raise ValidationError('Phiếu sửa đã đóng.')
        r.resolution=clean_text(request.data.get('resolution'),'resolution',1000);r.status='closed';r.closed_at=timezone.now();r.save()
        if not Repair.objects.filter(miner=r.miner,status='open').exists():a,_=MinerAssignment.objects.get_or_create(miner=r.miner);a.condition='stored';a.save()
        audit(request,'repair.closed',member.organization,r.id)
    return Response({'ok':True})

@api_view(['GET'])
def events(request,site_id):
    _,site=site_scope(request,site_id);count,rows=paginate(request,Event.objects.filter(agent__site=site).order_by('-ts','id'))
    return Response({'count':count,'results':[{'id':r.id,'at':r.ts,'agentId':r.agent_id,'data':r.record} for r in rows]})

@api_view(['GET','POST'])
def rules(request,site_id):
    member,site=site_scope(request,site_id,request.method=='POST')
    if request.method=='POST':
        strict(request.data,['name','metric','threshold','active']);metric=request.data.get('metric')
        if metric not in ('max_temp_c','power_w','stale_minutes'):raise ValidationError('Chỉ hỗ trợ nhiệt độ, công suất và thời gian mất dữ liệu.')
        if not isinstance(request.data.get('active',True),bool):raise ValidationError('Trạng thái không hợp lệ.')
        r=AlertRule.objects.create(site=site,name=clean_text(request.data.get('name'),'name'),metric=metric,threshold=number(request.data.get('threshold'),'threshold',.01,100000),active=request.data.get('active',True));audit(request,'alert_rule.created',member.organization,r.id)
        return Response({'id':r.id},status=201)
    count,rows=paginate(request,AlertRule.objects.filter(site=site).order_by('name','id'))
    return Response({'count':count,'results':[{'id':r.id,'name':r.name,'metric':r.metric,'threshold':r.threshold,'active':r.active} for r in rows]})

@api_view(['DELETE'])
def delete_rule(request,site_id,rule_id):
    member,site=site_scope(request,site_id,True);r=get_object_or_404(AlertRule,id=rule_id,site=site);r.delete();audit(request,'alert_rule.deleted',member.organization,rule_id);return Response(status=204)

def refresh_alerts(site):
    current={a['key']:a['message'] for a in power_report(site)['alerts']};now=timezone.now()
    for r in AlertRule.objects.filter(site=site,active=True):
        for m in site.miners.all():
            value=(now-m.last_seen_at).total_seconds()/60 if r.metric=='stale_minutes' else m.telemetry.get(r.metric)
            if r.metric!='stale_minutes' and (now-m.last_seen_at).total_seconds()>600:continue
            if isinstance(value,(float,int)) and not isinstance(value,bool) and value>r.threshold:current['rule:'+str(r.id)+':'+str(m.id)]=r.name+' · '+m.ip+' · '+str(round(value,2))
    current.update({a.key:a.message for a in Alert.objects.filter(site=site,key__startswith='surge:',expires_at__gt=now)})
    with transaction.atomic():
        Site.objects.select_for_update().get(pk=site.id)
        Alert.objects.filter(site=site,active=True).exclude(key__in=current).update(active=False)
        for key,message in current.items():
            a,created=Alert.objects.get_or_create(site=site,key=key,defaults={'message':message})
            if not created:
                if not a.active:a.acknowledged_by=None;a.acknowledged_at=None;a.first_seen=now
                a.active=True;a.message=message;a.save()

@api_view(['GET'])
def alerts(request,site_id):
    _,site=site_scope(request,site_id);count,rows=paginate(request,Alert.objects.filter(site=site,active=True).order_by('-last_seen','id'))
    return Response({'count':count,'results':[{'id':r.id,'message':r.message,'firstSeen':r.first_seen,'lastSeen':r.last_seen,'acknowledgedAt':r.acknowledged_at} for r in rows]})

@api_view(['POST'])
def acknowledge(request,site_id,alert_id):
    member,site=site_scope(request,site_id,True);strict(request.data,[])
    a=get_object_or_404(Alert,pk=alert_id,site=site);a.acknowledged_by=request.user;a.acknowledged_at=timezone.now();a.save();audit(request,'alert.acknowledged',member.organization,a.id);return Response({'ok':True})
