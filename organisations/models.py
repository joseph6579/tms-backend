import uuid

from django.db import models
from django.core.validators import MinValueValidator

from commons.behaviour import CommonInfo
from commons.constants import default_order_status_config, TimezoneChoices, LanguageChoices


class Permission(CommonInfo):
    """
    Model to represent custom permissions for organizations
    """
    name = models.CharField(max_length=100)
    codename = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    organisation = models.ForeignKey('Organisation', on_delete=models.CASCADE, related_name='permissions')

    class Meta:
        unique_together = [['organisation', 'codename']]
        ordering = ['name']
        verbose_name = 'Permission'
        verbose_name_plural = 'Permissions'

    def __str__(self):
        return f"{self.name} ({self.organisation.name})"

class Role(CommonInfo):
    """
    Model to represent custom roles for organizations
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    organisation = models.ForeignKey('Organisation', on_delete=models.CASCADE, related_name='roles')
    permissions = models.ManyToManyField(Permission, related_name='roles')
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [['organisation', 'name']]
        ordering = ['name']
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'

    def __str__(self):
        return f"{self.name} ({self.organisation.name})"

class Package(CommonInfo):
    """
    Model to represent subscription packages available to organizations
    """
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Duration in days"
    )
    max_users = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Maximum number of users allowed"
    )
    max_drivers = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Maximum number of drivers allowed"
    )
    features = models.JSONField(
        default=dict,
        help_text="Features included in this package"
    )
    is_active = models.BooleanField(default=True)
    has_route_optimization = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Package'
        verbose_name_plural = 'Packages'
        ordering = ['price']

class OrganisationSubscription(CommonInfo):
    """
    Model to track organization subscriptions
    """
    organisation = models.ForeignKey('Organisation', on_delete=models.CASCADE, related_name='subscriptions')
    package = models.ForeignKey(Package, on_delete=models.PROTECT)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('paid', 'Paid'),
            ('failed', 'Failed'),
            ('cancelled', 'Cancelled')
        ],
        default='pending'
    )
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    auto_renew = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.organisation.name} - {self.package.name}"

    class Meta:
        verbose_name = 'Organisation Subscription'
        verbose_name_plural = 'Organisation Subscriptions'
        ordering = ['-start_date']


class Organisation(CommonInfo):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    name = models.CharField(max_length=255, unique=True)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(unique=True)
    has_route_optimization = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = 'Organisations'
        db_table = 'organisations'
        ordering = ['-id']



class OrganisationConfiguration(CommonInfo):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    organisation = models.OneToOneField(Organisation, on_delete=models.CASCADE, related_name='configuration')
    max_users = models.PositiveIntegerField(default=10)
    max_drivers = models.PositiveIntegerField(default=10)
    allow_driver_signup = models.BooleanField(default=True)
    allow_user_signup = models.BooleanField(default=True)
    enable_audit_logs = models.BooleanField(default=True)
    data_retention_days = models.PositiveIntegerField(default=365)
    api_access_enabled = models.BooleanField(default=False)
    custom_terms_of_service = models.TextField(blank=True, null=True)
    custom_privacy_policy = models.TextField(blank=True, null=True)
    enable_two_factor_auth = models.BooleanField(default=False)
    password_expiration_days = models.PositiveIntegerField(default=90)
    session_timeout_minutes = models.PositiveIntegerField(default=30)
    max_login_attempts = models.PositiveIntegerField(default=5)
    lockout_duration_minutes = models.PositiveIntegerField(default=15)
    order_status_configuration = models.JSONField(
        default=default_order_status_config,
        help_text="Configuration for different order statuses"
    )
    timezone = models.CharField(max_length=50, default=TimezoneChoices.UTC.value, choices=TimezoneChoices.choices)
    default_language = models.CharField(max_length=10, default=LanguageChoices.English.value, choices=LanguageChoices.choices)


    class Meta:
        verbose_name = 'Organisation Configuration'
        verbose_name_plural = 'Organisation Configurations'