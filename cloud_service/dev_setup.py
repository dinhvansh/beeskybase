import secrets
from pathlib import Path
from cryptography.fernet import Fernet

path=Path(__file__).resolve().parent/'.env'
if path.exists():
    print('Local configuration already exists; kept unchanged.')
else:
    password=secrets.token_urlsafe(32)
    values={
      'POSTGRES_PASSWORD':password,'DATABASE_URL':f'postgresql://beesky:{password}@db:5432/beesky',
      'BEESKY_SECRET_KEY':secrets.token_urlsafe(64),'BEESKY_MAIL_ENCRYPTION_KEY':Fernet.generate_key().decode(),
      'BEESKY_DEBUG':'1','BEESKY_ALLOWED_HOSTS':'localhost,127.0.0.1,web',
      'BEESKY_PUBLIC_URL':'http://127.0.0.1:8793','BEESKY_CSRF_TRUSTED_ORIGINS':'http://127.0.0.1:8793,http://localhost:8793',
      'BEESKY_SMTP_HOST':'mailpit','BEESKY_SMTP_PORT':'1025','BEESKY_FROM_EMAIL':'BeeSky <no-reply@beesky.local>',
      'BEESKY_LOCAL_MAILBOX':'http://127.0.0.1:8026',
    }
    path.write_text('\n'.join(f'{k}={v}' for k,v in values.items())+'\n',encoding='utf-8')
    print('Created private local configuration; no account or sample farm created.')

