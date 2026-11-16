import logging
import time
from django.core.management.base import BaseCommand
from django.db import close_old_connections,transaction
from core.services import deliver_mail_once
from core.models import Site
from core.facility import refresh_alerts
from core.upkeep import ensure_tickets
log=logging.getLogger(__name__)
class Command(BaseCommand):
    help='Deliver mail, generate monthly maintenance and evaluate alert rules without a browser.'
    def add_arguments(self,parser):
        parser.add_argument('--once',action='store_true')
        parser.add_argument('--interval',type=float,default=5)
    def handle(self,*args,**options):
        next_scan=0
        while True:
            close_old_connections()
            try:
                deliver_mail_once()
                if time.monotonic()>=next_scan:
                    for site in Site.objects.iterator():
                        try:
                            with transaction.atomic():
                                Site.objects.select_for_update().get(pk=site.pk)
                                ensure_tickets(site);refresh_alerts(site)
                        except Exception:log.exception('Facility worker failed for site %s',site.id)
                    next_scan=time.monotonic()+30
            except Exception:log.exception('Cloud worker cycle failed')
            if options['once']:return
            time.sleep(max(.5,options['interval']))
