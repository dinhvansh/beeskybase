import time
from django.core.management.base import BaseCommand
from django.db import close_old_connections
from core.services import deliver_mail_once

class Command(BaseCommand):
    help='Deliver encrypted email outbox with bounded retries.'
    def add_arguments(self,parser):
        parser.add_argument('--once',action='store_true')
        parser.add_argument('--interval',type=float,default=5)
    def handle(self,*args,**options):
        while True:
            close_old_connections()
            count=deliver_mail_once()
            if options['once']:
                self.stdout.write(f'Delivered {count} queued messages.');return
            time.sleep(max(.5,options['interval']))
