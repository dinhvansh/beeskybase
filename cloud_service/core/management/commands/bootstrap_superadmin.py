import getpass
from pathlib import Path
from datetime import timedelta
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils import timezone
from core.models import User, AuditLog
from core.services import email_token


class Command(BaseCommand):
    help = 'Create a verified platform administrator, prompting privately for a password.'

    def add_arguments(self, parser):
        parser.add_argument('--email', required=True)
        parser.add_argument('--name', default='BeeSky Admin')
        parser.add_argument('--promote-existing', action='store_true')
        parser.add_argument('--setup-link-file', help='Write a one-use, 15-minute password setup link to a new private file.')

    def handle(self, *args, **options):
        email = options['email'].strip().casefold()
        try: validate_email(email)
        except ValidationError: raise CommandError('Email không hợp lệ.')
        existing = User.objects.filter(email=email).first()
        setup_path = Path(options['setup_link_file']) if options.get('setup_link_file') else None
        if setup_path and (existing or options['promote_existing']):
            raise CommandError('Đường dẫn thiết lập chỉ dành cho tài khoản mới.')
        if setup_path and setup_path.exists():
            raise CommandError('File đã tồn tại; không ghi đè.')
        if existing:
            if not options['promote_existing']:
                raise CommandError('Email đã tồn tại. Dùng --promote-existing để cấp quyền cho tài khoản đã xác minh.')
            if not existing.is_active or not existing.email_verified_at or not existing.has_usable_password():
                raise CommandError('Tài khoản phải hoạt động, đã xác minh email và đã đặt mật khẩu.')
        else:
            if options['promote_existing']:
                raise CommandError('Tài khoản chưa tồn tại.')
            candidate = User(email=email, display_name=options['name'])
            password = None
            if not setup_path:
                password = getpass.getpass('Mật khẩu Super Admin: ')
                confirm = getpass.getpass('Nhập lại mật khẩu: ')
                if password != confirm: raise CommandError('Mật khẩu không khớp.')
                try: validate_password(password, candidate)
                except ValidationError as exc: raise CommandError(' '.join(exc.messages))
        with transaction.atomic():
            if existing:
                user = User.objects.select_for_update().get(pk=existing.pk)
                if not user.is_active or not user.email_verified_at:
                    raise CommandError('Trạng thái tài khoản đã thay đổi.')
                user.is_superuser = True; user.is_staff = True
                user.save(update_fields=['is_superuser', 'is_staff'])
            else:
                user = User.objects.create_superuser(email=email, password=password,
                    display_name=options['name'], email_verified_at=timezone.now())
            AuditLog.objects.create(action='platform.admin.bootstrap', target=str(user.pk),
                metadata={'source': 'management_command'})
            if setup_path:
                token, raw = email_token(user, 'reset')
                token.expires_at = timezone.now() + timedelta(minutes=15)
                token.save(update_fields=['expires_at'])
                import os
                fd = os.open(setup_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(fd, 'w', encoding='utf-8') as output:
                    output.write(settings.PUBLIC_URL + '/#/reset?token=' + raw)
        self.stdout.write(self.style.SUCCESS('Đã cấp quyền Super Admin cho ' + email))
        if setup_path: self.stdout.write('Đường dẫn đặt mật khẩu dùng một lần đã lưu vào file riêng; hết hạn sau 15 phút.')
