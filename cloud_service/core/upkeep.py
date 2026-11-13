"""Monthly tickets, revisioned checklists and authenticated image evidence."""
import base64
import binascii
import calendar
import io
import warnings
from datetime import date
from zoneinfo import ZoneInfo
from PIL import Image,ImageOps,UnidentifiedImageError
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError,PermissionDenied
from rest_framework.response import Response
from .models import MaintenanceSchedule,MaintenanceTicket,MaintenancePhoto,Site,Membership
from .operations import site_scope,integer,paginate
from .security import strict,clean_text
from .services import audit

TEMPLATES={
'air':['Ghi nhiệt độ và hashrate trước bảo trì','Vệ sinh khe gió sau khi ngắt nguồn','Kiểm tra quạt, tiếng ồn và đầu nối','Kiểm tra dây điện, nguồn và điểm nóng','Chạy thử, ghi thông số sau bảo trì'],
'water':['Ghi nhiệt độ và hashrate trước bảo trì','Kiểm tra rò rỉ, ống và đầu nối','Kiểm tra bơm, bộ tản và thông số nước','Vệ sinh lọc và kiểm tra van sau khi cô lập','Chạy thử và ghi thông số sau bảo trì'],
'electrical':['Ghi tải trạm và từng pha','Kiểm tra nhiệt tủ, dây và đầu nối','Kiểm tra nhãn nhánh, pha và bất thường','Kiểm tra vệ sinh và tiếp địa','Ghi thông số và kiến nghị xử lý']}
def month(value):
    try:
        if not isinstance(value,str) or len(value)!=7:raise ValueError()
        result=date.fromisoformat(value+'-01')
        if not 2020<=result.year<=2100:raise ValueError()
        return result
    except ValueError:raise ValidationError('Tháng cần có dạng YYYY-MM (2020–2100).')
def today(site):return timezone.now().astimezone(ZoneInfo(site.timezone)).date()
def schedule_data(r):return {'id':r.id,'name':r.name,'day':r.day,'template':r.template,'checklist':r.checklist,'active':r.active,'startMonth':r.start_month.strftime('%Y-%m')}
def ticket_data(r,detail=False):
    result={'id':r.id,'scheduleId':r.schedule_id,'name':r.schedule.name,'period':r.period.strftime('%Y-%m'),'dueDate':r.due_date,'status':r.status,'revision':r.revision,'assignee':r.assignee,'note':r.note,'approvedAt':r.approved_at,'approvedBy':r.approved_by.display_name if r.approved_by else None,'submittedBy':r.submitted_by.display_name if r.submitted_by else None}
    if detail:result.update(checklist=r.checklist,photos=[{'id':p.id,'item':p.item,'stage':p.stage,'createdAt':p.created_at,'author':p.created_by.display_name,'url':f'/api/v2/sites/{r.schedule.site_id}/maintenance/photos/{p.id}'} for p in r.photos.select_related('created_by').defer('body').order_by('created_at')])
    return result

def ensure_tickets(site):
    current=today(site);period=current.replace(day=1)
    # Generate the current month's due sheet even before its due day. Never duplicate.
    for s in MaintenanceSchedule.objects.filter(site=site,active=True,start_month__lte=period):
        MaintenanceTicket.objects.get_or_create(schedule=s,period=period,defaults={'due_date':period.replace(day=min(s.day,calendar.monthrange(period.year,period.month)[1])),'checklist':[{'label':x,'done':False,'note':''} for x in s.checklist]})

@api_view(['GET','POST'])
def schedules(request,site_id):
    member,site=site_scope(request,site_id,request.method=='POST')
    if request.method=='POST':
        strict(request.data,['name','day','template','checklist','startMonth']);kind=request.data.get('template')
        if kind not in TEMPLATES:raise ValidationError('Loại bảo trì không hợp lệ.')
        checks=request.data.get('checklist',TEMPLATES[kind])
        if not isinstance(checks,list) or not 1<=len(checks)<=50:raise ValidationError('Cần 1–50 mục kiểm tra.')
        checks=[clean_text(v,'checklist',300) for v in checks]
        with transaction.atomic():
            Site.objects.select_for_update().get(pk=site.id)
            r=MaintenanceSchedule.objects.create(site=site,name=clean_text(request.data.get('name'),'name'),day=integer(request.data.get('day',1),1,31,'day'),template=kind,checklist=checks,start_month=month(request.data.get('startMonth',today(site).strftime('%Y-%m'))),created_by=request.user)
            ensure_tickets(site);audit(request,'maintenance.schedule_created',member.organization,r.id)
        return Response(schedule_data(r),status=201)
    count,rows=paginate(request,MaintenanceSchedule.objects.filter(site=site).order_by('name','id'))
    return Response({'count':count,'templates':TEMPLATES,'results':[schedule_data(r) for r in rows]})

@api_view(['PATCH'])
def schedule_detail(request,site_id,schedule_id):
    member,site=site_scope(request,site_id,True);strict(request.data,['active'])
    if not isinstance(request.data.get('active'),bool):raise ValidationError('Trạng thái không hợp lệ.')
    with transaction.atomic():
        Site.objects.select_for_update().get(pk=site.id);r=get_object_or_404(MaintenanceSchedule,pk=schedule_id,site=site);r.active=request.data['active'];r.save();audit(request,'maintenance.schedule_changed',member.organization,r.id)
    return Response(schedule_data(r))

@api_view(['GET'])
def tickets(request,site_id):
    _,site=site_scope(request,site_id);q=MaintenanceTicket.objects.filter(schedule__site=site).select_related('schedule','approved_by','submitted_by').order_by('-period','due_date','id')
    if request.query_params.get('period'):q=q.filter(period=month(request.query_params['period']))
    count,rows=paginate(request,q);return Response({'count':count,'results':[ticket_data(r) for r in rows]})

def get_ticket(site,ticket_id,lock=False):
    q=MaintenanceTicket.objects.select_for_update() if lock else MaintenanceTicket.objects.all()
    return get_object_or_404(q,pk=ticket_id,schedule__site=site)

@api_view(['GET','PUT','POST'])
def ticket(request,site_id,ticket_id):
    member,site=site_scope(request,site_id,request.method!='GET')
    if request.method=='GET':return Response(ticket_data(get_ticket(site,ticket_id),True))
    with transaction.atomic():
        r=get_ticket(site,ticket_id,True)
        revision=integer(request.data.get('revision'),0,2147483646,'revision')
        if revision!=r.revision:return Response({'detail':'Phiếu đã thay đổi. Tải lại trước khi lưu.'},status=409)
        if request.method=='PUT':
            strict(request.data,['revision','checklist','assignee','note'])
            if r.status not in ('open','rejected'):raise ValidationError('Phiếu đã gửi hoặc đã duyệt; không thể sửa.')
            checks=request.data.get('checklist')
            if not isinstance(checks,list) or len(checks)!=len(r.checklist):raise ValidationError('Không được đổi mẫu checklist của phiếu.')
            for old,new in zip(r.checklist,checks):
                strict(new,['label','done','note'])
                if new.get('label')!=old['label'] or not isinstance(new.get('done'),bool):raise ValidationError('Nhãn và kết quả checklist không hợp lệ.')
                clean_text(new.get('note',''),'note',1000,False)
            r.checklist=checks;r.note=clean_text(request.data.get('note',''),'note',5000,False);r.assignee=clean_text(request.data.get('assignee',''),'assignee',120,False)
            event='maintenance.ticket_updated'
        else:
            strict(request.data,['revision','action']);action=request.data.get('action')
            if action=='submit':
                if r.status not in ('open','rejected') or not all(c['done'] for c in r.checklist):raise ValidationError('Hoàn tất checklist trước khi gửi duyệt.')
                # Evidence before/after is required for each completed task.
                evidence={(p.item,p.stage) for p in r.photos.all()}
                if any((i,stage) not in evidence for i in range(len(r.checklist)) for stage in ('before','after')):raise ValidationError('Mỗi mục cần ảnh trước và sau để báo cáo.')
                r.status='submitted';r.submitted_by=request.user
            elif action in ('approve','reject'):
                if member.role!='owner':raise PermissionDenied('Chỉ chủ sở hữu được duyệt báo cáo.')
                if r.status!='submitted':raise ValidationError('Phiếu chưa gửi duyệt.')
                if action=='approve':r.status='approved';r.approved_by=request.user;r.approved_at=timezone.now()
                else:r.status='rejected'
            else:raise ValidationError('Hành động không hợp lệ.')
            event='maintenance.'+action
        r.revision+=1;r.save();audit(request,event,member.organization,r.id,{'revision':r.revision})
    return Response(ticket_data(r,True))

@api_view(['POST'])
def photos(request,site_id,ticket_id):
    member,site=site_scope(request,site_id,True);strict(request.data,['revision','item','stage','data'])
    stage=request.data.get('stage')
    if stage not in ('before','after'):raise ValidationError('Ảnh cần là trước hoặc sau bảo trì.')
    raw=request.data.get('data')
    if not isinstance(raw,str) or len(raw)>8*1024*1024:raise ValidationError('Ảnh tối đa 6 MB.')
    try:
        body=base64.b64decode(raw,validate=True)
        with warnings.catch_warnings():
            warnings.simplefilter('error',Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(body)) as im:
                if im.format not in ('JPEG','PNG','WEBP') or im.width*im.height>24000000:raise ValueError()
                im=ImageOps.exif_transpose(im);im.thumbnail((2400,2400));out=io.BytesIO();im.convert('RGB').save(out,format='JPEG',quality=85);body=out.getvalue()
    except (ValueError,binascii.Error,UnidentifiedImageError,OSError,Image.DecompressionBombError,Image.DecompressionBombWarning):raise ValidationError('Ảnh JPEG/PNG/WebP không hợp lệ hoặc quá lớn.')
    with transaction.atomic():
        r=get_ticket(site,ticket_id,True)
        if request.data.get('revision')!=r.revision:return Response({'detail':'Phiếu đã đổi. Tải lại.'},status=409)
        if r.status not in ('open','rejected'):raise ValidationError('Phiếu đã khóa chỉnh sửa.')
        index=integer(request.data.get('item'),0,len(r.checklist)-1,'item')
        if r.photos.count()>=100:raise ValidationError('Mỗi phiếu tối đa 100 ảnh.')
        p=MaintenancePhoto.objects.create(ticket=r,item=index,stage=stage,mime='image/jpeg',body=body,created_by=request.user);r.revision+=1;r.save();audit(request,'maintenance.photo_added',member.organization,r.id,{'photoId':str(p.id)})
    return Response({'id':p.id,'revision':r.revision},status=201)

@api_view(['GET','DELETE'])
def photo(request,site_id,photo_id):
    member,site=site_scope(request,site_id,request.method=='DELETE')
    if request.method=='GET':
        p=get_object_or_404(MaintenancePhoto,pk=photo_id,ticket__schedule__site=site);response=HttpResponse(bytes(p.body),content_type=p.mime);response['Cache-Control']='no-store';response['X-Content-Type-Options']='nosniff';return response
    with transaction.atomic():
        p=get_object_or_404(MaintenancePhoto,pk=photo_id,ticket__schedule__site=site);r=get_ticket(site,p.ticket_id,True)
        if r.status not in ('open','rejected'):raise ValidationError('Phiếu đã khóa chỉnh sửa.')
        p.delete();r.revision+=1;r.save();audit(request,'maintenance.photo_removed',member.organization,r.id,{'photoId':str(photo_id)})
    return Response(status=204)
