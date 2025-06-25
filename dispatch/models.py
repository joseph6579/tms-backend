from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.contrib.gis.db import models as geomodels
from commons.behaviour import CommonInfo
from commons.constants import OrderStatusChoices
from uuid import uuid4


class Location(CommonInfo):
    """
    Model to represent a geographical location in the dispatch system.
    """

    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    name = models.CharField(max_length=100, verbose_name='Location Name')
    description = models.TextField(blank=True, null=True, verbose_name='Description')
    coordinates = geomodels.PointField(verbose_name='Coordinates')
    address = models.CharField(max_length=255, verbose_name='Address', blank=True, null=True)
    city = models.CharField(max_length=100, verbose_name='City', blank=True, null=True)
    state = models.CharField(max_length=100, verbose_name='State', blank=True, null=True)
    country = models.CharField(max_length=100, verbose_name='Country', blank=True, null=True)
    postal_code = models.CharField(max_length=20, verbose_name='Postal Code', blank=True, null=True)
    is_active = models.BooleanField(default=True, verbose_name='Is Active', blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.city}"

    class Meta:
        verbose_name = 'Location'
        verbose_name_plural = 'Locations'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['city']),
            models.Index(fields=['postal_code']),
        ]


class Trip(CommonInfo):
    """
    Model to represent a trip in the dispatch system.
    """

    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    driver = models.ForeignKey('users.Driver', on_delete=models.SET_NULL, verbose_name='Driver', null=True, blank=True)
    vehicle = models.ForeignKey(
        'fleet.Vehicle', on_delete=models.SET_NULL, verbose_name='Vehicle', null=True, blank=True
    )
    status = models.CharField(max_length=20, default='scheduled', verbose_name='Trip Status')
    start_location = models.ForeignKey(
        Location, on_delete=models.PROTECT, related_name='trip_starts', verbose_name='Start Location'
    )
    end_location = models.ForeignKey(
        Location, on_delete=models.PROTECT, related_name='trip_ends', verbose_name='End Location'
    )
    scheduled_start_time = models.DateTimeField(verbose_name='Scheduled Start Time')
    actual_start_time = models.DateTimeField(null=True, blank=True, verbose_name='Actual Start Time')
    completed_time = models.DateTimeField(null=True, blank=True, verbose_name='Completed Time')
    distance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Distance (km)')
    estimated_duration = models.DurationField(null=True, blank=True, verbose_name='Estimated Duration')
    actual_duration = models.DurationField(null=True, blank=True, verbose_name='Actual Duration')
    notes = models.TextField(blank=True, null=True, verbose_name='Notes')

    def __str__(self):
        return f"Trip {self.id} - {self.driver}"

    class Meta:
        verbose_name = 'Trip'
        verbose_name_plural = 'Trips'
        ordering = ['-scheduled_start_time']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['scheduled_start_time']),
        ]


class Order(CommonInfo):
    """
    Model to represent an order in the dispatch system.
    """

    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    reference = models.CharField(max_length=100, verbose_name='Order Reference', unique=True)
    status = models.CharField(
        max_length=20,
        choices=OrderStatusChoices.choices,
        default=OrderStatusChoices.PENDING,
        verbose_name='Order Status',
    )
    priority = models.PositiveIntegerField(
        verbose_name='Priority',
        default=1,
        help_text='1 is highest priority, 5 is lowest priority',
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    pickup = models.ForeignKey(
        Location, on_delete=models.PROTECT, verbose_name='Pickup Location', related_name='pickup_orders'
    )
    drop_off = models.ForeignKey(
        Location, on_delete=models.PROTECT, verbose_name='Drop Off Location', related_name='drop_off_orders'
    )
    recipient = models.ForeignKey(
        'organisations.Customer', on_delete=models.CASCADE, verbose_name='Recipient', related_name='orders'
    )
    buyer = models.ForeignKey(
        'organisations.Customer',
        on_delete=models.CASCADE,
        verbose_name='Buyer',
        related_name='buyer_orders',
        null=True,
        blank=True,
    )
    driver = models.ForeignKey('users.Driver', on_delete=models.SET_NULL, verbose_name='Driver', null=True, blank=True)
    organization = models.ForeignKey('organisations.Organisation', on_delete=models.CASCADE, related_name='orders')

    # Package info
    weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Package Weight (kg)',
        null=True,
        blank=True,
        help_text='Weight of the package in kilograms',
    )
    dimensions = models.JSONField(
        verbose_name='Package Dimensions (LxWxH)',
        null=True,
        blank=True,
        help_text='Dimensions of the package in the format {"length": 0, "width": 0, "height": 0, "unit": "cm"}',
    )
    description = models.TextField(
        verbose_name='Order Description', blank=True, null=True, help_text='Description of the order or package'
    )
    instructions = models.TextField(
        verbose_name='Special Instructions', blank=True, null=True, help_text='Any special instructions for the order'
    )
    trip = models.ForeignKey(
        Trip, on_delete=models.SET_NULL, verbose_name='Trip', null=True, blank=True, related_name='orders'
    )

    # Timestamps
    scheduled_date = models.DateTimeField(verbose_name='Scheduled Date', null=True, blank=True)
    pickup_window_start = models.DateTimeField(verbose_name='Pickup Window Start', null=True, blank=True)
    pickup_window_end = models.DateTimeField(verbose_name='Pickup Window End', null=True, blank=True)
    delivery_window_start = models.DateTimeField(verbose_name='Delivery Window Start', null=True, blank=True)
    delivery_window_end = models.DateTimeField(verbose_name='Delivery Window End', null=True, blank=True)
    date_delivered = models.DateTimeField(verbose_name='Date Delivered', null=True, blank=True)
    date_cancelled = models.DateTimeField(verbose_name='Date Cancelled', null=True, blank=True)
    date_failed = models.DateTimeField(verbose_name='Date Failed', null=True, blank=True)

    # Meta
    meta_data = models.JSONField(
        verbose_name='Meta Data', blank=True, null=True, help_text='Additional metadata for the order'
    )
    is_active = models.BooleanField(default=True, verbose_name='Is Active')

    def __str__(self):
        return f"Order {self.reference}"

    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['reference']),
            models.Index(fields=['status']),
            models.Index(fields=['scheduled_date']),
        ]


class TripStop(CommonInfo):
    """
    Model to represent a stop in a trip.
    """

    STOP_TYPE_CHOICES = [
        ('start', 'Start Location'),
        ('pickup', 'Pickup'),
        ('drop_off', 'Dropoff'),
        ('end', 'End Location'),
    ]

    STOP_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('arrived', 'Arrived'),
        ('completed', 'Completed'),
        ('skipped', 'Skipped'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    order = models.ForeignKey(Order, null=True, blank=True, on_delete=models.SET_NULL, related_name='stops')
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='stops')
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='stops')
    stop_type = models.CharField(max_length=10, choices=STOP_TYPE_CHOICES, default='pickup')
    sequence = models.PositiveIntegerField()
    eta = models.DateTimeField(null=True, blank=True, verbose_name='Estimated Time of Arrival')
    actual_arrival = models.DateTimeField(null=True, blank=True, verbose_name='Actual Arrival Time')
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='Started At')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Completed At')
    completed_by = models.ForeignKey(
        'users.Driver', on_delete=models.SET_NULL, null=True, blank=True, related_name='completed_stops'
    )
    status = models.CharField(max_length=20, choices=STOP_STATUS_CHOICES, default='pending', verbose_name='Stop Status')
    notes = models.TextField(blank=True, null=True, verbose_name='Notes')

    def __str__(self):
        return f"{self.get_stop_type_display()} - {self.location.name}"

    class Meta:
        verbose_name = 'Trip Stop'
        verbose_name_plural = 'Trip Stops'
        ordering = ['trip', 'sequence']
        indexes = [
            models.Index(fields=['trip', 'sequence']),
            models.Index(fields=['status']),
        ]


class OrderReview(CommonInfo):
    """
    Model to store order reviews and ratings
    """

    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='reviews')
    driver = models.ForeignKey('users.Driver', on_delete=models.CASCADE, related_name='order_reviews')
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], help_text='Rating from 1 to 5'
    )
    driver_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], help_text='Driver rating from 1 to 5'
    )
    comments = models.TextField(blank=True, null=True)
    reviewed_by = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Review for Order {self.order.reference}"

    class Meta:
        verbose_name = 'Order Review'
        verbose_name_plural = 'Order Reviews'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['rating']),
            models.Index(fields=['driver_rating']),
        ]
