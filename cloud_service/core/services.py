import base64
import hashlib
import json
import secrets
from datetime import timedelta
from cryptography.fernet import Fernet
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from django.template.loader import render_to_string
from rest_framework.exceptions import ValidationError
from .models import AuditLog, EmailToken, Outbox, RateBucket, User, Organization


def digest(raw):
    return hashlib.sha256(raw.encode()).hexdigest()

def cipher():
    key=settings.MAIL_ENCRYPTION_KEY
    if not key and settings.TESTING:
        key=base64.urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode()).digest())
    return Fernet(key)

def audit(request,action,organization=None,target='',metadata=None,agent=None):
    user=getattr(request,'user',None)
    return AuditLog.objects.create(organization=organization,actor=user if isinstance(user,User) else None,agent=agent,action=action,target=str(target),metadata=metadata or {})

def validate_new_password(password,user):
    if not isinstance(password,str) or len(password)>256:
        raise ValidationError({'password':'Mật khẩu không hợp lệ hoặc quá dài.'})
    try:validate_password(password,user)
    except __import__('django.core.exceptions',fromlist=['ValidationError']).ValidationError as exc:
        raise ValidationError({'password':exc.messages})

def email_token(user,kind,organization=None,payload=None):
    raw=secrets.token_urlsafe(32)
    ttl=timedelta(hours=24 if kind=='verify' else 48 if kind=='invite' else 1)
    token=EmailToken.objects.create(user=user,kind=kind,organization=organization,digest=digest(raw),expires_at=timezone.now()+ttl,payload=payload or {})
    return token,raw

def enqueue_mail(recipient,subject,message,html_message=None):
    if html_message is None:
        html_message=render_to_string('email/account.html',{'title':subject.removeprefix('BeeSky · '),'intro':'Bạn có thông báo mới từ BeeSky Mine.','body':message,'safety_note':'Nếu bạn không nhận ra yêu cầu này, vui lòng liên hệ quản trị viên của tổ chức.','public_url':settings.PUBLIC_URL})
    data=json.dumps({'to':recipient,'subject':subject,'body':message,'html':html_message},ensure_ascii=False).encode()
    return Outbox.objects.create(encrypted_payload=cipher().encrypt(data),next_attempt_at=timezone.now())

def send_token(user,kind):
    token,raw=email_token(user,kind)
    route='verify' if kind=='verify' else 'reset'
    link=settings.PUBLIC_URL+'/#/'+route+'?token='+raw
    verify=kind=='verify'
    title='Xác thực email của bạn' if verify else 'Đặt lại mật khẩu'
    ttl='24 giờ' if verify else '1 giờ'
    action='Xác thực email' if verify else 'Đặt mật khẩu mới'
    intro=('Cảm ơn bạn đã đăng ký BeeSky Mine. Xác thực địa chỉ email này để kích hoạt tài khoản và bắt đầu quản lý xưởng của bạn.' if verify else 'Chúng tôi nhận được yêu cầu đặt lại mật khẩu cho tài khoản BeeSky Mine của bạn. Bấm nút bên dưới để chọn mật khẩu mới.')
    safety=('Nếu bạn không tạo tài khoản này, bạn có thể bỏ qua email. Tài khoản sẽ chưa được kích hoạt khi email chưa được xác thực.' if verify else 'Nếu bạn không yêu cầu đặt lại mật khẩu, hãy bỏ qua email này. Mật khẩu hiện tại của bạn vẫn giữ nguyên. Không chia sẻ liên kết này với người khác.')
    html=render_to_string('email/account.html',{'title':title,'preheader':title+' · Liên kết có hiệu lực trong '+ttl+'.','name':user.display_name,'intro':intro,'action_url':link,'action_label':action,'ttl':ttl,'safety_note':safety,'public_url':settings.PUBLIC_URL})
    text=f"Xin chào {user.display_name or 'bạn'},\n\n{intro}\n\n{action}:\n{link}\n\nLiên kết có hiệu lực trong {ttl} và chỉ sử dụng một lần.\n\n{safety}\n\nBeeSky Mine\n{settings.PUBLIC_URL}"
    outbox=enqueue_mail(user.email,'BeeSky Mine · '+title,text,html_message=html)
    token.outbox_id=outbox.id
    return token

def consume_token(raw,kind):
    if not isinstance(raw,str) or not 20<=len(raw)<=200:
        raise ValidationError('Đường dẫn không hợp lệ hoặc đã hết hạn.')
    candidate=EmailToken.objects.filter(digest=digest(raw),kind=kind,used_at__isnull=True,expires_at__gt=timezone.now()).first()
    if candidate:
        if candidate.user_id:User.objects.select_for_update().get(id=candidate.user_id)
        if candidate.organization_id:Organization.objects.select_for_update().get(id=candidate.organization_id)
    token=EmailToken.objects.select_for_update().filter(digest=digest(raw),kind=kind,used_at__isnull=True,expires_at__gt=timezone.now()).first()
    if not token:
        raise ValidationError('Đường dẫn không hợp lệ, đã dùng hoặc hết hạn.')
    return token

def deliver_mail_once(outbox_id=None):
    sent=0
    for _ in range(1 if outbox_id else 20):
        with transaction.atomic():
            query=Outbox.objects.filter(sent_at__isnull=True,next_attempt_at__lte=timezone.now()).order_by('created_at')
            if outbox_id:query=query.filter(id=outbox_id)
            from django.db import connection
            row=query.select_for_update(skip_locked=not outbox_id and connection.features.has_select_for_update_skip_locked).first()
            if not row:break
            row.attempts+=1
            try:
                data=json.loads(cipher().decrypt(bytes(row.encrypted_payload)))
                accepted=send_mail(data['subject'],data['body'],settings.DEFAULT_FROM_EMAIL,[data['to']],fail_silently=False,html_message=data.get('html'))
                if accepted!=1:raise RuntimeError('Mail provider did not accept the message')
                row.sent_at=timezone.now();row.encrypted_payload=b'';row.last_error='';sent+=1
            except Exception as exc:
                row.last_error=type(exc).__name__[:80]
                row.next_attempt_at=timezone.now()+timedelta(seconds=min(3600,30*2**min(row.attempts,7)))
            row.save()
    RateBucket.objects.filter(expires_at__lt=timezone.now()-timedelta(days=1)).delete()
    return sent
