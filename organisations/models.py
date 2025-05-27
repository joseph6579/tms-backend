import uuid

from django.db import models
from django.core.validators import MinValueValidator

from commons.behaviour import CommonInfo

class Permission(CommonInfo):
    """
    Model to represent custom permissions for organizations
    """
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
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
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
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
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
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
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
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

class OrganisationPreferences(CommonInfo):
    """
    Model to store organization preferences
    """
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    organisation = models.OneToOneField('Organisation', on_delete=models.CASCADE, related_name='preferences')
    timezone = models.CharField(max_length=50, default='UTC')
    default_language = models.CharField(max_length=10, default='en')
    notification_settings = models.JSONField(
        default=dict,
        help_text="Notification preferences"
    )
    branding = models.JSONField(
        default=dict,
        help_text="Branding settings like colors, logo URL, etc."
    )
    operational_hours = models.JSONField(
        default=dict,
        help_text="Operating hours for each day"
    )
    delivery_settings = models.JSONField(
        default=dict,
        help_text="Delivery-related settings"
    )

    def __str__(self):
        return f"Preferences for {self.organisation.name}"

    class Meta:
        verbose_name = 'Organisation Preferences'
        verbose_name_plural = 'Organisation Preferences'

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