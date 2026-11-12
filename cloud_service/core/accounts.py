from datetime import timedelta
from django.contrib.auth import authenticate,login as django_login,logout as django_logout
from django.contrib.sessions.models import Session
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.db import IntegrityError,transaction
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view,permission_classes
from rest_framework.exceptions import PermissionDenied,ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import User,Organization,Membership,Site,EmailToken,UserSession
from .security import throttle,scope,strict,clean_text
from .services import audit,send_token,consume_token,validate_new_password,email_token,enqueue_mail
from django.conf import settings


def email_input(data):
    email=clean_text(data.get('email'),'email',254).casefold()
    try:validate_email(email)
    except DjangoValidationError:raise ValidationError({'email':'Địa chỉ email không hợp lệ.'})
    return email

def me_data(request):
    if not request.user or not request.user.is_authenticated:return {'authenticated':False}
    memberships=Membership.objects.select_related('organization').filter(user=request.user,active=True).order_by("id")
    return {'authenticated':True,'user':{'id':request.user.id,'email':request.user.email,'name':request.user.display_name,'verified':bool(request.user.email_verified_at)},'organizations':[{'id':m.organization_id,'name':m.organization.name,'role':m.role} for m in memberships],'selectedOrganization':request.session.get('organization_id')}

@api_view(['GET'])
@permission_classes([AllowAny])
def csrf(request):
    return Response({'csrfToken':get_token(request._request)})

@api_view(['GET'])
@permission_classes([AllowAny])
def me(request):
    response=Response(me_data(request));response['Cache-Control']='no-store';return response

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    strict(request.data,['email','password','name']);email=email_input(request.data)
    throttle(request,'register',email,limit=5,seconds=3600)
    name=clean_text(request.data.get('name'),'name')
    user=User(email=email,display_name=name)
    validate_new_password(request.data.get('password'),user)
    if not User.objects.filter(email=email).exists():
        try:
            with transaction.atomic():
                user=User.objects.create_user(email,request.data['password'],display_name=name)
                send_token(user,'verify')
                audit(request,'account.registered',target=user.id)
        except IntegrityError:
            pass  # Same generic response on concurrent registration/existing email.
    return Response({'message':'Nếu email có thể đăng ký, hướng dẫn xác thực đã được đưa vào hàng đợi gửi.'},status=202)

@api_view(['POST'])
@permission_classes([AllowAny])
def resend(request):
    strict(request.data,['email']);email=email_input(request.data);throttle(request,'resend',email,limit=3,seconds=900)
    user=User.objects.filter(email=email,is_active=True,email_verified_at__isnull=True).first()
    if user:
        with transaction.atomic():send_token(user,'verify')
    return Response({'message':'Nếu email cần xác thực, hướng dẫn đã được đưa vào hàng đợi gửi.'},status=202)

@api_view(['POST'])
@permission_classes([AllowAny])
def verify(request):
    strict(request.data,['token']);throttle(request,'verify',limit=20)
    with transaction.atomic():
        token=consume_token(request.data.get('token'),'verify')
        user=token.user
        if not user or not user.is_active:raise ValidationError('Đường dẫn không hợp lệ.')
        now=timezone.now();user.email_verified_at=now;user.save(update_fields=['email_verified_at'])
        EmailToken.objects.filter(user=user,kind='verify',used_at__isnull=True).update(used_at=now)
        audit(request,'account.email_verified',target=user.id)
    return Response({'message':'Email đã được xác thực. Bạn có thể đăng nhập.'})

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    strict(request.data,['email','password']);email=email_input(request.data);throttle(request,'login',email,limit=10)
    password=request.data.get('password')
    if not isinstance(password,str) or len(password)>256:raise ValidationError('Email hoặc mật khẩu không đúng.')
    user=authenticate(request._request,email=email,password=password)
    if not user:raise ValidationError('Email hoặc mật khẩu không đúng.')
    if not user.email_verified_at:raise PermissionDenied('Cần xác thực email trước khi đăng nhập.')
    django_login(request._request,user);request.user=user
    request.session.save()
    UserSession.objects.create(user=user,session_id=request.session.session_key,user_agent=request.META.get('HTTP_USER_AGENT','')[:240])
    audit(request,'account.login',target=user.id)
    return Response(me_data(request))

@api_view(['POST'])
def logout(request):
    strict(request.data,[]);audit(request,'account.logout',target=request.user.id);django_logout(request._request)
    return Response({'message':'Đã đăng xuất.'})

@api_view(['POST'])
@permission_classes([AllowAny])
def forgot(request):
    strict(request.data,['email']);email=email_input(request.data);throttle(request,'forgot',email,limit=3)
    user=User.objects.filter(email=email,is_active=True,email_verified_at__isnull=False).first()
    if user:
        with transaction.atomic():send_token(user,'reset')
    return Response({'message':'Nếu tài khoản phù hợp, hướng dẫn đặt lại mật khẩu đã được đưa vào hàng đợi gửi.'},status=202)

@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    strict(request.data,['token','password']);throttle(request,'reset',limit=10)
    with transaction.atomic():
        token=consume_token(request.data.get('token'),'reset');user=token.user
        if not user or not user.is_active:raise ValidationError('Đường dẫn không hợp lệ.')
        validate_new_password(request.data.get('password'),user)
        user.set_password(request.data['password']);user.save(update_fields=['password'])
        EmailToken.objects.filter(user=user,kind='reset',used_at__isnull=True).update(used_at=timezone.now())
        Session.objects.filter(usersession__user=user).delete()
        audit(request,'account.password_reset',target=user.id)
    return Response({'message':'Đã đặt lại mật khẩu và thu hồi các phiên đăng nhập.'})

@api_view(['GET','POST'])
def sessions(request):
    if request.method=='GET':
        return Response({'results':[{'id':row.id,'created_at':row.created_at,'user_agent':row.user_agent,'current':row.session_id==request.session.session_key} for row in UserSession.objects.filter(user=request.user,session__expire_date__gt=timezone.now()).order_by('-created_at')]})
    strict(request.data,['id','allOthers'])
    rows=UserSession.objects.filter(user=request.user)
    if request.data.get('allOthers') is True:rows=rows.exclude(session_id=request.session.session_key)
    else:
        try:rows=rows.filter(id=request.data.get('id'))
        except (ValueError,DjangoValidationError):raise ValidationError('Phiên không hợp lệ.')
    keys=list(rows.values_list('session_id',flat=True));Session.objects.filter(session_key__in=keys).delete()
    audit(request,'account.sessions_revoked',target=request.user.id,metadata={'count':len(keys)})
    return Response({'revoked':len(keys)})

@api_view(['POST'])
def change_password(request):
    strict(request.data,['currentPassword','password'])
    throttle(request,'change_password',str(request.user.id),limit=5)
    current=request.data.get('currentPassword')
    if not isinstance(current,str) or len(current)>256 or not request.user.check_password(current):raise ValidationError('Mật khẩu hiện tại không đúng.')
    validate_new_password(request.data.get('password'),request.user)
    with transaction.atomic():
        user=User.objects.select_for_update().get(id=request.user.id);user.set_password(request.data['password']);user.save(update_fields=['password'])
        Session.objects.filter(usersession__user=user).delete();audit(request,'account.password_changed',target=user.id)
    django_logout(request._request)
    return Response({'message':'Đã đổi mật khẩu và đăng xuất các phiên. Hãy đăng nhập lại.'})

@api_view(['POST'])
def organizations(request):
    strict(request.data,['name','siteName','location'])
    if not request.user.email_verified_at:raise PermissionDenied('Cần xác thực email.')
    throttle(request,'organization_create',str(request.user.id),limit=5,seconds=3600)
    name=clean_text(request.data.get('name'),'name');site_name=clean_text(request.data.get('siteName'),'siteName');location=clean_text(request.data.get('location',''),'location',240,False)
    with transaction.atomic():
        org=Organization.objects.create(name=name,created_by=request.user)
        Membership.objects.create(user=request.user,organization=org,role='owner')
        site=Site.objects.create(organization=org,name=site_name,location=location)
        audit(request,'organization.created',org,org.id);audit(request,'site.created',org,site.id)
    request.session['organization_id']=str(org.id)
    return Response({'organization':{'id':org.id,'name':org.name},'site':{'id':site.id,'name':site.name}},status=201)

@api_view(['POST'])
def select_organization(request):
    strict(request.data,['id'])
    member=get_object_or_404(Membership,user=request.user,organization_id=request.data.get('id'),active=True)
    request.session['organization_id']=str(member.organization_id)
    return Response(me_data(request))

@api_view(['GET'])
def members(request):
    membership=scope(request)
    return Response({'results':[{'id':m.id,'userId':m.user_id,'name':m.user.display_name,'email':m.user.email,'role':m.role,'active':m.active} for m in Membership.objects.select_related('user').filter(organization=membership.organization)]})

@api_view(['PATCH','DELETE'])
def member_detail(request,member_id):
    current=scope(request,owner=True)
    with transaction.atomic():
        Organization.objects.select_for_update().get(id=current.organization_id)
        # Recheck role after acquiring the organization lock.
        scope(request,owner=True)
        target=get_object_or_404(Membership,pk=member_id,organization_id=current.organization_id)
        strict(request.data,['role'] if request.method=='PATCH' else [])
        role=request.data.get('role') if request.method=='PATCH' else target.role
        if role not in ('owner','admin','viewer'):raise ValidationError('Vai trò không hợp lệ.')
        if target.active and target.role=='owner' and (request.method=='DELETE' or role!='owner') and Membership.objects.filter(organization=current.organization,active=True,role='owner').count()<=1:
            raise ValidationError('Không thể thu hồi hoặc hạ quyền chủ sở hữu cuối cùng.')
        target.role=role;target.active=request.method!='DELETE';target.save(update_fields=['role','active'])
        audit(request,'membership.changed',current.organization,target.id,{'role':role,'active':target.active})
    return Response({'id':target.id,'role':target.role,'active':target.active})

@api_view(['POST'])
def invite(request):
    member=scope(request,owner=True);strict(request.data,['email','role']);email=email_input(request.data)
    role=request.data.get('role','viewer')
    if role not in ('admin','viewer'):raise ValidationError('Chỉ mời quản trị viên hoặc người xem.')
    throttle(request,'invite',str(request.user.id),limit=10,seconds=3600)
    with transaction.atomic():
        token,raw=email_token(None,'invite',member.organization,{'email':email,'role':role})
        link=settings.PUBLIC_URL+'/#/accept-invite?token='+raw
        enqueue_mail(email,'BeeSky · Lời mời tham gia tổ chức',f'Bạn được mời vào {member.organization.name}. Đăng ký/xác thực email {email}, đăng nhập rồi mở:\n{link}\nLời mời dùng một lần trong 48 giờ.')
        audit(request,'membership.invited',member.organization,token.id,{'role':role})
    return Response({'message':'Đã đưa lời mời vào hàng đợi gửi.'},status=202)

@api_view(['POST'])
def accept_invite(request):
    strict(request.data,['token'])
    if not request.user.email_verified_at:raise PermissionDenied('Cần xác thực email.')
    with transaction.atomic():
        token=consume_token(request.data.get('token'),'invite')
        if token.payload.get('email')!=request.user.email:raise PermissionDenied('Lời mời dành cho email khác.')
        existing=Membership.objects.filter(user=request.user,organization=token.organization).first()
        if existing and existing.active:raise ValidationError('Bạn đã là thành viên tổ chức này.')
        Membership.objects.update_or_create(user=request.user,organization=token.organization,defaults={'role':token.payload['role'],'active':True})
        token.used_at=timezone.now();token.save(update_fields=['used_at'])
        audit(request,'membership.invite_accepted',token.organization,token.id)
    request.session['organization_id']=str(token.organization_id)
    return Response(me_data(request))
