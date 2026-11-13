from django.contrib.sessions.models import Session
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from .models import User, Organization, Site, Agent, AuditLog, EmailToken
from .security import strict, throttle
from .services import audit, send_token


class IsPlatformAdmin(BasePermission):
    message = 'Chỉ Super Admin được quản trị hệ thống.'

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_active and
                    user.is_superuser and user.email_verified_at)


def page(request):
    try:
        limit = int(request.query_params.get('limit', 25))
        offset = int(request.query_params.get('offset', 0))
    except (TypeError, ValueError):
        raise ValidationError('Phân trang không hợp lệ.')
    if not 1 <= limit <= 100 or not 0 <= offset <= 1000000:
        raise ValidationError('Phân trang vượt giới hạn.')
    return limit, offset


@api_view(['GET'])
@permission_classes([IsPlatformAdmin])
def overview(request):
    return Response({
        'users': User.objects.count(),
        'pending': User.objects.filter(email_verified_at__isnull=True, is_active=True).count(),
        'disabled': User.objects.filter(is_active=False).count(),
        'organizations': Organization.objects.count(), 'sites': Site.objects.count(),
        'agents': Agent.objects.filter(revoked_at__isnull=True).count(),
    })


@api_view(['GET'])
@permission_classes([IsPlatformAdmin])
def users(request):
    limit, offset = page(request)
    search = request.query_params.get('q', '').strip()
    if len(search) > 120:
        raise ValidationError('Từ khóa quá dài.')
    status = request.query_params.get('status', '')
    if status not in ('', 'pending', 'active', 'disabled', 'superadmin'):
        raise ValidationError('Trạng thái không hợp lệ.')
    rows = User.objects.all()
    if search:
        rows = rows.filter(Q(email__icontains=search) | Q(display_name__icontains=search))
    if status == 'pending': rows = rows.filter(email_verified_at__isnull=True, is_active=True)
    if status == 'active': rows = rows.filter(email_verified_at__isnull=False, is_active=True)
    if status == 'disabled': rows = rows.filter(is_active=False)
    if status == 'superadmin': rows = rows.filter(is_superuser=True)
    count = rows.count()
    rows = rows.annotate(org_count=Count('membership', filter=Q(membership__active=True), distinct=True)).order_by('-date_joined', 'id')[offset:offset+limit]
    return Response({'count': count, 'results': [{
        'id': u.id, 'email': u.email, 'name': u.display_name,
        'active': u.is_active, 'verifiedAt': u.email_verified_at,
        'superadmin': u.is_superuser, 'joinedAt': u.date_joined,
        'lastLogin': u.last_login, 'organizationCount': u.org_count,
    } for u in rows]})


@api_view(['POST'])
@permission_classes([IsPlatformAdmin])
def user_action(request, user_id):
    strict(request.data, ['action', 'reason'])
    action = request.data.get('action')
    if action not in ('disable', 'enable', 'revoke_sessions', 'resend_verification'):
        raise ValidationError('Thao tác không hợp lệ.')
    reason = request.data.get('reason', '')
    if not isinstance(reason, str) or not 3 <= len(reason.strip()) <= 300:
        raise ValidationError({'reason': 'Nhập lý do từ 3 đến 300 ký tự.'})
    throttle(request, 'platform_user_action', str(request.user.id), limit=60, seconds=3600)
    with transaction.atomic():
        target = get_object_or_404(User.objects.select_for_update(), id=user_id)
        if target.is_superuser or target.id == request.user.id:
            raise ValidationError('Tài khoản Super Admin được quản lý bằng công cụ máy chủ.')
        if action == 'resend_verification':
            if not target.is_active or target.email_verified_at:
                raise ValidationError('Chỉ gửi xác minh cho tài khoản đang hoạt động và chưa xác minh.')
            throttle(request, 'platform_resend', str(target.id), limit=3, seconds=3600)
            send_token(target, 'verify')
        else:
            if action in ('disable', 'enable'):
                target.is_active = action == 'enable'
                target.save(update_fields=['is_active'])
            if action in ('disable', 'revoke_sessions'):
                Session.objects.filter(usersession__user=target).delete()
            if action == 'disable':
                EmailToken.objects.filter(user=target, used_at__isnull=True).update(used_at=timezone.now())
        audit(request, 'platform.user.' + action, target=target.id,
              metadata={'reason': reason.strip()})
    return Response({'message': 'Đã gửi vào hàng đợi email.' if action == 'resend_verification' else 'Đã cập nhật tài khoản.'})


@api_view(['GET'])
@permission_classes([IsPlatformAdmin])
def organizations(request):
    limit, offset = page(request)
    rows = Organization.objects.annotate(site_count=Count('sites', distinct=True),
        member_count=Count('memberships', filter=Q(memberships__active=True), distinct=True)).select_related('created_by').order_by('-created_at', 'id')
    return Response({'count': rows.count(), 'results': [{
        'id': o.id, 'name': o.name, 'ownerEmail': o.created_by.email,
        'sites': o.site_count, 'members': o.member_count, 'createdAt': o.created_at,
    } for o in rows[offset:offset+limit]]})


@api_view(['GET'])
@permission_classes([IsPlatformAdmin])
def logs(request):
    limit, offset = page(request)
    rows = AuditLog.objects.filter(action__startswith='platform.').select_related('actor').order_by('-created_at', '-id')
    return Response({'count': rows.count(), 'results': [{
        'id': row.id, 'actor': row.actor.email if row.actor else '',
        'action': row.action, 'target': row.target,
        'reason': row.metadata.get('reason', ''), 'createdAt': row.created_at,
    } for row in rows[offset:offset+limit]]})
