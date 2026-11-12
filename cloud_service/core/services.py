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

def enqueue_mail(recipient,subject,message):
    data=json.dumps({'to':recipient,'subject':subject,'body':message},ensure_ascii=False).encode()
    Outbox.objects.create(encrypted_payload=cipher().encrypt(data),next_attempt_at=timezone.now())

def send_token(user,kind):
    token,raw=email_token(user,kind)
    route='verify' if kind=='verify' else 'reset'
    link=settings.PUBLIC_URL+'/#/'+route+'?token='+raw
    enqueue_mail(user.email,'BeeSky · '+('Xác thực email' if kind=='verify' else 'Đặt lại mật khẩu'),'Mở đường dẫn sau để '+('xác thực email' if kind=='verify' else 'đặt lại mật khẩu')+':\n'+link+'\nĐường dẫn chỉ dùng một lần và sẽ hết hạn.')
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

def deliver_mail_once():
    sent=0
    for _ in range(20):
        with transaction.atomic():
            query=Outbox.objects.filter(sent_at__isnull=True,next_attempt_at__lte=timezone.now()).order_by('created_at')
            from django.db import connection
            row=query.select_for_update(skip_locked=connection.features.has_select_for_update_skip_locked).first()
            if not row:break
            row.attempts+=1
            try:
                data=json.loads(cipher().decrypt(bytes(row.encrypted_payload)))
                send_mail(data['subject'],data['body'],settings.DEFAULT_FROM_EMAIL,[data['to']],fail_silently=False)
                row.sent_at=timezone.now();row.encrypted_payload=b'';row.last_error='';sent+=1
            except Exception as exc:
                row.last_error=type(exc).__name__[:80]
                row.next_attempt_at=timezone.now()+timedelta(seconds=min(3600,30*2**min(row.attempts,7)))
            row.save()
    RateBucket.objects.filter(expires_at__lt=timezone.now()-timedelta(days=1)).delete()
    return sent
