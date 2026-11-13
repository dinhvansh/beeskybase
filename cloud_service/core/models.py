import uuid
from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.sessions.models import Session
from django.db import models
from django.db.models.functions import Lower

class UserManager(BaseUserManager):
    def create_user(self,email,password=None,**extra):
        user=self.model(email=email.strip().casefold(),**extra)
        user.set_password(password);user.save(using=self._db);return user
    def create_superuser(self,email,password,**extra):
        extra.update(is_staff=True,is_superuser=True)
        return self.create_user(email,password,**extra)

class User(AbstractUser):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    username=None
    email=models.EmailField(unique=True)
    display_name=models.CharField(max_length=120)
    email_verified_at=models.DateTimeField(null=True,blank=True)
    USERNAME_FIELD='email'
    REQUIRED_FIELDS=['display_name']
    objects=UserManager()
    class Meta:
        constraints=[models.UniqueConstraint(Lower('email'),name='user_email_case_unique')]

class Organization(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    name=models.CharField(max_length=120)
    created_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    created_at=models.DateTimeField(auto_now_add=True)

class Membership(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    organization=models.ForeignKey(Organization,on_delete=models.CASCADE,related_name='memberships')
    role=models.CharField(max_length=10,choices=[('owner','Owner'),('admin','Admin'),('viewer','Viewer')])
    active=models.BooleanField(default=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['user','organization'],name='one_membership_per_org')]

class Site(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    organization=models.ForeignKey(Organization,on_delete=models.CASCADE,related_name='sites')
    name=models.CharField(max_length=120)
    location=models.CharField(max_length=240,blank=True)
    timezone=models.CharField(max_length=60,default='Asia/Ho_Chi_Minh')
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[models.UniqueConstraint('organization',Lower('name'),name='site_name_unique_in_org')]

class Agent(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    site=models.ForeignKey(Site,on_delete=models.CASCADE,related_name='agents')
    name=models.CharField(max_length=120)
    key_hash=models.CharField(max_length=64,unique=True)
    key_prefix=models.CharField(max_length=16)
    created_at=models.DateTimeField(auto_now_add=True)
    revoked_at=models.DateTimeField(null=True)
    last_heartbeat_at=models.DateTimeField(null=True)
    last_snapshot_at=models.DateTimeField(null=True)

class Miner(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    site=models.ForeignKey(Site,on_delete=models.CASCADE,related_name='miners')
    last_agent=models.ForeignKey(Agent,on_delete=models.SET_NULL,null=True)
    identity=models.CharField(max_length=300)
    identity_status=models.CharField(max_length=20,default='unverified')
    ip=models.GenericIPAddressField()
    serial=models.CharField(max_length=180,blank=True)
    model=models.CharField(max_length=180,blank=True)
    last_seen_at=models.DateTimeField()
    telemetry=models.JSONField(default=dict)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['site','identity'],name='miner_identity_unique_in_site')]
        indexes=[models.Index(fields=['site','last_seen_at']),models.Index(fields=['site','ip'])]

class Snapshot(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    agent=models.ForeignKey(Agent,on_delete=models.CASCADE)
    ts=models.DateTimeField()
    received_at=models.DateTimeField(auto_now_add=True)
    digest=models.CharField(max_length=64)
    count=models.PositiveIntegerField()
    class Meta:
        constraints=[models.UniqueConstraint(fields=['agent','digest'],name='snapshot_retries_deduplicated')]

class Observation(models.Model):
    snapshot=models.ForeignKey(Snapshot,on_delete=models.CASCADE)
    miner=models.ForeignKey(Miner,on_delete=models.CASCADE)
    record=models.JSONField()

class Event(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    agent=models.ForeignKey(Agent,on_delete=models.CASCADE)
    ts=models.DateTimeField()
    digest=models.CharField(max_length=64)
    record=models.JSONField()
    class Meta:
        constraints=[models.UniqueConstraint(fields=['agent','digest'],name='event_retries_deduplicated')]

class Rack(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    site=models.ForeignKey(Site,on_delete=models.CASCADE,related_name='racks')
    name=models.CharField(max_length=80)
    rows=models.PositiveSmallIntegerField(default=4)
    cols=models.PositiveSmallIntegerField(default=6)
    floor=models.CharField(max_length=80,default='Tầng 1')
    x=models.DecimalField(max_digits=9,decimal_places=2,default=0)
    z=models.DecimalField(max_digits=9,decimal_places=2,default=0)
    rotation=models.PositiveSmallIntegerField(default=0)
    class Meta:
        constraints=[models.UniqueConstraint('site',Lower('name'),name='rack_name_unique_in_site')]

class RackSlot(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    rack=models.ForeignKey(Rack,on_delete=models.CASCADE,related_name='slots')
    row=models.PositiveSmallIntegerField()
    col=models.PositiveSmallIntegerField()
    class Meta:
        constraints=[models.UniqueConstraint(fields=['rack','row','col'],name='rack_slot_unique')]

class Placement(models.Model):
    miner=models.OneToOneField(Miner,on_delete=models.CASCADE,related_name='placement')
    slot=models.OneToOneField(RackSlot,on_delete=models.CASCADE,related_name='placement')
    updated_at=models.DateTimeField(auto_now=True)

class EmailToken(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,null=True)
    organization=models.ForeignKey(Organization,on_delete=models.CASCADE,null=True)
    kind=models.CharField(max_length=12)
    digest=models.CharField(max_length=64,unique=True)
    expires_at=models.DateTimeField()
    used_at=models.DateTimeField(null=True)
    payload=models.JSONField(default=dict)

class Outbox(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    encrypted_payload=models.BinaryField()
    created_at=models.DateTimeField(auto_now_add=True)
    attempts=models.PositiveIntegerField(default=0)
    next_attempt_at=models.DateTimeField()
    sent_at=models.DateTimeField(null=True)
    last_error=models.CharField(max_length=80,blank=True)

class UserSession(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    session=models.OneToOneField(Session,on_delete=models.CASCADE)
    created_at=models.DateTimeField(auto_now_add=True)
    user_agent=models.CharField(max_length=240,blank=True)

class AuditLog(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    organization=models.ForeignKey(Organization,on_delete=models.CASCADE,null=True)
    actor=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True)
    agent=models.ForeignKey(Agent,on_delete=models.SET_NULL,null=True)
    action=models.CharField(max_length=80)
    target=models.CharField(max_length=180,blank=True)
    metadata=models.JSONField(default=dict)
    created_at=models.DateTimeField(auto_now_add=True)

class RateBucket(models.Model):
    key=models.CharField(primary_key=True,max_length=64)
    count=models.PositiveIntegerField(default=0)
    expires_at=models.DateTimeField()

class SitePlan(models.Model):
    site=models.OneToOneField(Site,on_delete=models.CASCADE,primary_key=True)
    revision=models.PositiveIntegerField(default=0)
    data=models.JSONField(default=dict)
    updated_at=models.DateTimeField(auto_now=True)

class Customer(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    organization=models.ForeignKey(Organization,on_delete=models.CASCADE)
    name=models.CharField(max_length=120)
    class Meta:
        constraints=[models.UniqueConstraint('organization',Lower('name'),name='customer_name_in_org')]

class MachineGroup(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    site=models.ForeignKey(Site,on_delete=models.CASCADE)
    name=models.CharField(max_length=120)
    cooling_label=models.CharField(max_length=120,blank=True)
    class Meta:
        constraints=[models.UniqueConstraint('site',Lower('name'),name='group_name_in_site')]

class MinerAssignment(models.Model):
    miner=models.OneToOneField(Miner,on_delete=models.CASCADE,primary_key=True)
    customer=models.ForeignKey(Customer,on_delete=models.PROTECT,null=True)
    group=models.ForeignKey(MachineGroup,on_delete=models.PROTECT,null=True)
    condition=models.CharField(max_length=20,default='operating')
    note=models.CharField(max_length=500,blank=True)

class MaintenanceSchedule(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    site=models.ForeignKey(Site,on_delete=models.CASCADE)
    name=models.CharField(max_length=120)
    day=models.PositiveSmallIntegerField(default=1)
    template=models.CharField(max_length=20)
    checklist=models.JSONField()
    active=models.BooleanField(default=True)
    start_month=models.DateField()
    created_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)

class MaintenanceTicket(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    schedule=models.ForeignKey(MaintenanceSchedule,on_delete=models.PROTECT)
    period=models.DateField()
    due_date=models.DateField()
    checklist=models.JSONField()
    status=models.CharField(max_length=20,default='open')
    revision=models.PositiveIntegerField(default=0)
    note=models.TextField(blank=True)
    assignee=models.CharField(max_length=120,blank=True)
    submitted_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,null=True,related_name='+')
    approved_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,null=True,related_name='+')
    approved_at=models.DateTimeField(null=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['schedule','period'],name='monthly_ticket_once')]

class MaintenancePhoto(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    ticket=models.ForeignKey(MaintenanceTicket,on_delete=models.CASCADE,related_name='photos')
    item=models.PositiveSmallIntegerField()
    stage=models.CharField(max_length=10)
    mime=models.CharField(max_length=30)
    body=models.BinaryField()
    created_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    created_at=models.DateTimeField(auto_now_add=True)

class Repair(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    miner=models.ForeignKey(Miner,on_delete=models.PROTECT)
    ticket=models.ForeignKey(MaintenanceTicket,on_delete=models.PROTECT,null=True)
    issue=models.CharField(max_length=500)
    resolution=models.CharField(max_length=1000,blank=True)
    status=models.CharField(max_length=20,default='open')
    created_at=models.DateTimeField(auto_now_add=True)
    closed_at=models.DateTimeField(null=True)

class AlertRule(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    site=models.ForeignKey(Site,on_delete=models.CASCADE)
    name=models.CharField(max_length=120)
    metric=models.CharField(max_length=30)
    threshold=models.FloatField()
    active=models.BooleanField(default=True)

class Alert(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    site=models.ForeignKey(Site,on_delete=models.CASCADE)
    key=models.CharField(max_length=180)
    message=models.CharField(max_length=500)
    active=models.BooleanField(default=True)
    first_seen=models.DateTimeField(auto_now_add=True)
    last_seen=models.DateTimeField(auto_now=True)
    acknowledged_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True)
    acknowledged_at=models.DateTimeField(null=True)
    expires_at=models.DateTimeField(null=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['site','key'],name='alert_key_in_site')]
