"""Create a private production env; no account seeds and no deployment side effects."""
import argparse
import re
import secrets
from pathlib import Path
from cryptography.fernet import Fernet
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--domain',required=True)
p.add_argument('--smtp-host',required=True)
p.add_argument('--smtp-port',type=int,default=587)
p.add_argument('--from-email',required=True)
a=p.parse_args()
if not re.fullmatch(r'[a-zA-Z0-9](?:[a-zA-Z0-9.-]{0,250}[a-zA-Z0-9])?',a.domain) or '.' not in a.domain:p.error('Use a DNS domain without scheme/path.')
if any('\n' in x or '\r' in x for x in [a.smtp_host,a.from_email]):p.error('Invalid configuration.')
path=Path(__file__).resolve().parent/'.env.production'
if path.exists():raise SystemExit('Existing .env.production kept; edit it explicitly.')
password=secrets.token_urlsafe(32)
values={'BEESKY_DOMAIN':a.domain,'POSTGRES_PASSWORD':password,'DATABASE_URL':f'postgresql://beesky:{password}@db:5432/beesky','BEESKY_SECRET_KEY':secrets.token_urlsafe(64),'BEESKY_MAIL_ENCRYPTION_KEY':Fernet.generate_key().decode(),'BEESKY_DEBUG':'0','BEESKY_TRUST_PROXY':'1','BEESKY_ALLOWED_HOSTS':a.domain+',localhost','BEESKY_PUBLIC_URL':'https://'+a.domain,'BEESKY_CSRF_TRUSTED_ORIGINS':'https://'+a.domain,'BEESKY_SMTP_HOST':a.smtp_host,'BEESKY_SMTP_PORT':str(a.smtp_port),'BEESKY_SMTP_TLS':'1','BEESKY_SMTP_USER':'','BEESKY_SMTP_PASSWORD':'','BEESKY_FROM_EMAIL':a.from_email}
with path.open('x',encoding='utf-8') as f:
    path.chmod(0o600)
    f.write('\n'.join(k+'='+v for k,v in values.items())+'\n')
print('Created private .env.production. Fill SMTP user/password, then follow docs/cloud-deployment.md.')
