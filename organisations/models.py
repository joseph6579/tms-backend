import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.contrib.gis.db import models as geomodels

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

class DriverAppSettings(CommonInfo):
    """
    Model to store driver app settings per organisation
    """
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    organisation = models.OneToOneField('Organisation', on_delete=models.CASCADE, related_name='driver_app_settings')
    
    # Cancellation settings
    allow_pickup_cancellation = models.BooleanField(default=False, help_text="Allow drivers to cancel at pickup")
    allow_dropoff_cancellation = models.BooleanField(default=False, help_text="Allow drivers to cancel at drop-off")
    
    # Delivery confirmation settings
    require_confirmation_code = models.BooleanField(default=True, help_text="Require confirmation code for delivery")
    require_recipient_name = models.BooleanField(default=True, help_text="Require recipient name for delivery")
    require_recipient_signature = models.BooleanField(default=False, help_text="Require recipient signature for delivery")
    require_delivery_photo = models.BooleanField(default=True, help_text="Require photo proof of delivery")
    require_driver_notes = models.BooleanField(default=True, help_text="Require driver notes for delivery")
    
    # Photo settings
    photo_quality = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High')
        ],
        default='medium',
        help_text="Quality setting for delivery photos"
    )
    max_photo_size_mb = models.PositiveIntegerField(
        default=5,
        help_text="Maximum photo size in megabytes"
    )
    
    # Additional settings
    enable_route_optimization = models.BooleanField(default=True, help_text="Enable route optimization for drivers")
    offline_mode_enabled = models.BooleanField(default=True, help_text="Allow offline mode in driver app")
    max_offline_duration_hours = models.PositiveIntegerField(
        default=24,
        help_text="Maximum duration (in hours) for offline mode"
    )

    def __str__(self):
        return f"Driver App Settings for {self.organisation.name}"

    class Meta:
        verbose_name = 'Driver App Settings'
        verbose_name_plural = 'Driver App Settings'

class Store(CommonInfo):
    """
    Model to represent organization stores/pickup locations with broadcast settings
    """
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    organisation = models.ForeignKey('Organisation', on_delete=models.CASCADE, related_name='stores')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, help_text="Unique store code")
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    contact_person = models.CharField(max_length=100)
    contact_phone = models.CharField(max_length=20)
    contact_email = models.EmailField()
    is_active = models.BooleanField(default=True)
    
    # Location
    coordinates = geomodels.PointField(help_text="Store location coordinates")
    
    # Geofence settings
    geofence_type = models.CharField(
        max_length=10,
        choices=[
            ('none', 'None'),
            ('soft', 'Soft'),
            ('hard', 'Hard')
        ],
        default='none',
        help_text="Type of geofence enforcement"
    )
    geofence_radius_km = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.00,
        help_text="Geofence radius in kilometers"
    )
    geofence_polygon = geomodels.PolygonField(
        null=True,
        blank=True,
        help_text="Custom geofence boundary"
    )
    allow_geofence_override = models.BooleanField(
        default=False,
        help_text="Allow authorized users to override geofence restrictions"
    )
    geofence_grace_period_minutes = models.PositiveIntegerField(
        default=5,
        help_text="Grace period for soft geofence violations"
    )
    
    # Operating hours
    operating_hours = models.JSONField(
        default=dict,
        help_text="Operating hours for each day"
    )
    
    # Broadcast settings
    enable_auto_broadcast = models.BooleanField(
        default=True,
        help_text="Automatically broadcast orders from this store"
    )
    broadcast_radius_km = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=5.00,
        help_text="Radius in kilometers for driver broadcasts"
    )
    min_driver_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=4.00,
        help_text="Minimum driver rating for broadcasts"
    )
    broadcast_batch_size = models.PositiveIntegerField(
        default=5,
        help_text="Maximum number of orders in a broadcast batch"
    )
    broadcast_interval_minutes = models.PositiveIntegerField(
        default=5,
        help_text="Time between broadcast attempts"
    )
    max_broadcast_attempts = models.PositiveIntegerField(
        default=3,
        help_text="Maximum number of broadcast attempts per order"
    )
    
    # Capacity settings
    max_daily_orders = models.PositiveIntegerField(
        default=100,
        help_text="Maximum number of orders per day"
    )
    max_concurrent_orders = models.PositiveIntegerField(
        default=20,
        help_text="Maximum number of concurrent orders"
    )

    def __str__(self):
        return f"{self.name} - {self.organisation.name}"

    class Meta:
        verbose_name = 'Store'
        verbose_name_plural = 'Stores'
        unique_together = [['organisation', 'code']]
        ordering = ['name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['city']),
            models.Index(fields=['postal_code']),
            geomodels.Index(fields=['coordinates']),
        ]

class StoreDriverGroup(CommonInfo):
    """
    Model to associate driver groups with stores and their specific settings
    """
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='driver_groups')
    driver_group = models.ForeignKey('fleet.DriverGroup', on_delete=models.CASCADE, related_name='store_assignments')
    
    # Priority settings
    priority = models.PositiveIntegerField(
        default=1,
        help_text="Broadcast priority (1 is highest)"
    )
    
    # Distance and order limits
    max_delivery_distance_km = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Maximum delivery distance in kilometers"
    )
    max_orders_per_trip = models.PositiveIntegerField(
        help_text="Maximum number of orders per trip"
    )
    
    # Additional settings
    is_active = models.BooleanField(default=True)
    custom_broadcast_settings = models.JSONField(
        null=True,
        blank=True,
        help_text="Custom broadcast settings for this group"
    )

    def __str__(self):
        return f"{self.store.name} - {self.driver_group.name}"

    class Meta:
        verbose_name = 'Store Driver Group'
        verbose_name_plural = 'Store Driver Groups'
        unique_together = [['store', 'driver_group']]
        ordering = ['store', 'priority']
        indexes = [
            models.Index(fields=['priority']),
        ]

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