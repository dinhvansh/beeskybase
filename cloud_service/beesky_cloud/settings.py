import os
from pathlib import Path
from urllib.parse import urlparse, unquote
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG = os.getenv('BEESKY_DEBUG') == '1'
TESTING = os.getenv('BEESKY_TESTING') == '1' or 'test' in __import__('sys').argv
SECRET_KEY = os.getenv('BEESKY_SECRET_KEY', '')
if not SECRET_KEY:
    if TESTING:
        SECRET_KEY = 'only-for-isolated-test-processes-not-a-runtime-secret'
    else:
        raise ImproperlyConfigured('BEESKY_SECRET_KEY is required; no open mode.')
MAIL_ENCRYPTION_KEY = os.getenv('BEESKY_MAIL_ENCRYPTION_KEY', '')
if not MAIL_ENCRYPTION_KEY and not TESTING:
    raise ImproperlyConfigured('BEESKY_MAIL_ENCRYPTION_KEY is required.')
ALLOWED_HOSTS = os.getenv('BEESKY_ALLOWED_HOSTS', 'localhost,127.0.0.1' if DEBUG else '').split(',')
ROOT_URLCONF = 'beesky_cloud.urls'
WSGI_APPLICATION = 'beesky_cloud.wsgi.application'
INSTALLED_APPS = ['django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','django.contrib.staticfiles','rest_framework','core']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware','whitenoise.middleware.WhiteNoiseMiddleware','core.security.BodyLimitMiddleware','django.contrib.sessions.middleware.SessionMiddleware','django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware','django.contrib.auth.middleware.AuthenticationMiddleware','django.middleware.clickjacking.XFrameOptionsMiddleware']
TEMPLATES = [{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[BASE_DIR/'templates'],'APP_DIRS':True,'OPTIONS':{'context_processors':[]}}]
DATABASE_URL = os.getenv('DATABASE_URL', '')
if DATABASE_URL:
    parsed = urlparse(DATABASE_URL)
    if parsed.scheme not in ('postgres','postgresql'):
        raise ImproperlyConfigured('The cloud database must be PostgreSQL.')
    DATABASES = {'default':{'ENGINE':'django.db.backends.postgresql','NAME':unquote(parsed.path.lstrip('/')),'USER':unquote(parsed.username or ''),'PASSWORD':unquote(parsed.password or ''),'HOST':parsed.hostname,'PORT':parsed.port or 5432,'CONN_MAX_AGE':60,'OPTIONS':{'connect_timeout':5}}}
elif TESTING:
    DATABASES = {'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}}
else:
    raise ImproperlyConfigured('DATABASE_URL for PostgreSQL is required.')
AUTH_USER_MODEL = 'core.User'
AUTH_PASSWORD_VALIDATORS = [{'NAME':'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},{'NAME':'django.contrib.auth.password_validation.MinimumLengthValidator','OPTIONS':{'min_length':12}},{'NAME':'django.contrib.auth.password_validation.CommonPasswordValidator'},{'NAME':'django.contrib.auth.password_validation.NumericPasswordValidator'}]
PASSWORD_HASHERS = ['django.contrib.auth.hashers.Argon2PasswordHasher','django.contrib.auth.hashers.PBKDF2PasswordHasher']
REST_FRAMEWORK = {'DEFAULT_AUTHENTICATION_CLASSES':['core.security.BrowserAuthentication'],'DEFAULT_PERMISSION_CLASSES':['rest_framework.permissions.IsAuthenticated'],'DEFAULT_RENDERER_CLASSES':['rest_framework.renderers.JSONRenderer'],'DEFAULT_PARSER_CLASSES':['rest_framework.parsers.JSONParser'],'EXCEPTION_HANDLER':'core.security.exception_handler','UNAUTHENTICATED_USER':None}
LANGUAGE_CODE = 'vi'
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR/'collected_static'
STATICFILES_DIRS = [BASE_DIR/'static', BASE_DIR.parent/'cloud-preview']
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_NAME = 'beesky_cloud_session'
SESSION_COOKIE_AGE = 86400
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = not DEBUG and not TESTING
CSRF_COOKIE_NAME = 'beesky_cloud_csrf'
CSRF_COOKIE_SECURE = not DEBUG and not TESTING
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = [v for v in os.getenv('BEESKY_CSRF_TRUSTED_ORIGINS','').split(',') if v]
SECURE_SSL_REDIRECT = not DEBUG and not TESTING
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000 if not DEBUG and not TESTING else 0
DATA_UPLOAD_MAX_MEMORY_SIZE = 16*1024*1024
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend' if TESTING else 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('BEESKY_SMTP_HOST', 'mailpit')
EMAIL_PORT = int(os.getenv('BEESKY_SMTP_PORT', '1025'))
EMAIL_HOST_USER = os.getenv('BEESKY_SMTP_USER','')
EMAIL_HOST_PASSWORD = os.getenv('BEESKY_SMTP_PASSWORD','')
EMAIL_USE_TLS = os.getenv('BEESKY_SMTP_TLS','0') == '1'
EMAIL_TIMEOUT = 10
DEFAULT_FROM_EMAIL = os.getenv('BEESKY_FROM_EMAIL', 'BeeSky <no-reply@beesky.local>')
PUBLIC_URL = os.getenv('BEESKY_PUBLIC_URL','http://127.0.0.1:8793' if DEBUG else '').rstrip('/')
if not PUBLIC_URL and not TESTING:
    raise ImproperlyConfigured('BEESKY_PUBLIC_URL is required.')
if not DEBUG and not TESTING and not PUBLIC_URL.startswith('https://'):
    raise ImproperlyConfigured('Production PUBLIC_URL must use HTTPS.')

STORAGES = {'default':{'BACKEND':'django.core.files.storage.FileSystemStorage'},'staticfiles':{'BACKEND':'whitenoise.storage.CompressedStaticFilesStorage'}}

SECURE_REDIRECT_EXEMPT = ['^health/ready$']
