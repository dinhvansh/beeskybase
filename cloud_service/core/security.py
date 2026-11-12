import hashlib
import time
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import PermissionDenied, Throttled, ValidationError
from .models import Membership, RateBucket

class BrowserAuthentication(SessionAuthentication):
    def authenticate(self,request):
        # Login/register/reset also require CSRF; DRF's default only checks logged-in users.
        if request.method not in ('GET','HEAD','OPTIONS'):
            self.enforce_csrf(request)
        return super().authenticate(request)

def exception_handler(exc,context):
    from rest_framework.views import exception_handler as drf_exception_handler
    from django.core.exceptions import ValidationError as DjangoValidationError
    from django.db import IntegrityError
    from rest_framework.response import Response
    if isinstance(exc,DjangoValidationError):exc=ValidationError('Định danh hoặc dữ liệu không hợp lệ.')
    if isinstance(exc,IntegrityError):return Response({'detail':'Dữ liệu trùng hoặc không thỏa ràng buộc. Tải lại và kiểm tra.'},status=409)
    response=drf_exception_handler(exc,context)
    if response is not None:
        response['Cache-Control']='no-store'
    return response

def scope(request,write=False,owner=False):
    if not request.user or not request.user.is_authenticated or not request.user.email_verified_at:
        raise PermissionDenied('Cần đăng nhập bằng email đã xác thực.')
    memberships=Membership.objects.select_related('organization').filter(user=request.user,active=True)
    selected=request.session.get('organization_id')
    membership=memberships.filter(organization_id=selected).first() if selected else memberships.order_by('id').first()
    if not membership:
        raise PermissionDenied('Chưa có quyền trong tổ chức này.')
    if owner and membership.role!='owner':
        raise PermissionDenied('Chỉ chủ sở hữu được quản lý thành viên.')
    if write and membership.role not in ('owner','admin'):
        raise PermissionDenied('Tài khoản chỉ xem không có quyền ghi.')
    return membership

def throttle(request,action,account='',limit=10,seconds=900):
    now=timezone.now();window=int(time.time())//seconds
    # Do not trust client-supplied forwarding headers.
    address=request.META.get('REMOTE_ADDR','unknown')
    keys=[f'{action}:ip:{address}:{window}']
    if account:
        keys.append(f'{action}:account:{account.casefold()}:{window}')
    for raw in keys:
        key=hashlib.sha256(raw.encode()).hexdigest()
        with transaction.atomic():
            RateBucket.objects.get_or_create(key=key,defaults={'expires_at':now+timedelta(seconds=seconds)})
            bucket=RateBucket.objects.select_for_update().get(key=key)
            if bucket.count>=limit:
                raise Throttled(wait=seconds-int(time.time())%seconds,detail='Thử quá nhiều lần. Vui lòng chờ rồi thử lại.')
            bucket.count+=1;bucket.save(update_fields=['count'])

def strict(data,allowed):
    if not isinstance(data,dict) or set(data)-set(allowed):
        raise ValidationError('Dữ liệu có trường không được hỗ trợ.')

def clean_text(value,field,maximum=120,required=True):
    if not isinstance(value,str) or (required and not value.strip()) or len(value.strip())>maximum:
        raise ValidationError({field:'Giá trị bị thiếu hoặc quá dài.'})
    return value.strip()


class BodyLimitMiddleware:
    def __init__(self,get_response):self.get_response=get_response
    def __call__(self,request):
        from django.http import JsonResponse
        if request.method in ('POST','PUT','PATCH','DELETE'):
            try:length=int(request.META.get('CONTENT_LENGTH') or 0)
            except ValueError:return JsonResponse({'detail':'Content-Length không hợp lệ.'},status=400)
            if length>16*1024*1024:return JsonResponse({'detail':'Nội dung vượt giới hạn 16 MB.'},status=413)
        response=self.get_response(request)
        if request.path.startswith("/api/"):
            response["Cache-Control"]="no-store"
        return response
