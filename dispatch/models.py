from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.contrib.gis.db import models as geomodels
from commons.behaviour import CommonInfo
from uuid import uuid4



class Location(CommonInfo):
    """
    Model to represent a geographical location in the dispatch system.
    """
    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    name = models.CharField(max_length=100, verbose_name='Location Name')
    description = models.TextField(blank=True, null=True, verbose_name='Description')
    coordinates = geomodels.PointField(verbose_name='Coordinates')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Locations'
        verbose_name = 'Location'
        ordering = ['name']


class Customer(CommonInfo):
    """
    Model to represent a customer in the dispatch system.
    """
    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    name = models.CharField(max_length=100, verbose_name='Customer Name')
    email = models.EmailField(verbose_name='Email Address', blank=True, null=True)
    phone_number = models.CharField(max_length=15, verbose_name='Phone Number', blank=True, null=True)
    location = models.ForeignKey(Location, on_delete=models.PROTECT, verbose_name='Location', related_name='customers',
                                 null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Customers'
        verbose_name = 'Customer'
        ordering = ['name']


class Trip(CommonInfo):
    """
    Model to represent a trip in the dispatch system.
    """
    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    driver = models.ForeignKey('users.Driver', on_delete=models.SET_NULL, verbose_name='Driver', null=True, blank=True)
    vehicle = models.CharField(max_length=100, verbose_name='Vehicle', blank=True, null=True,)
    status = models.CharField(max_length=20, default='scheduled', verbose_name='Trip Status')

    def __str__(self):
        return f'Trip {self.driver}'

    class Meta:
        verbose_name_plural = 'Trips'
        verbose_name = 'Trip'
        ordering = ['-created_at']


class Order(CommonInfo):
    """
    Model to represent an order in the dispatch system.
    """
    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    reference = models.CharField(max_length=100, verbose_name='Order Reference')
    status = models.CharField(max_length=20, default='pending')
    priority = models.PositiveIntegerField(
        verbose_name='Priority', default=1, help_text='1 is highest priority, 5 is lowest priority',
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    pickup = models.ForeignKey(Location, on_delete=models.PROTECT, verbose_name='Pickup Location', related_name='pickup_orders')
    drop_off = models.ForeignKey(Location, on_delete=models.PROTECT, verbose_name='Drop Off Location', related_name='drop_off_orders')
    recipient = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name='Recipient', related_name='orders')
    buyer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name='Buyer', related_name='buyer_orders', null=True, blank=True)
    driver = models.ForeignKey('users.Driver', on_delete=models.SET_NULL, verbose_name='Driver', null=True, blank=True)

    # package info
    weight = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name='Package Weight (kg)', null=True, blank=True,
        help_text='Weight of the package in kilograms'
    )
    dimensions = models.JSONField(
        verbose_name='Package Dimensions (LxWxH)', null=True, blank=True,
        help_text= 'Dimensions of the package in the format {"length": 0, "width": 0, "height": 0, "unit": "cm"}'
    )
    description = models.TextField(
        verbose_name='Order Description', blank=True, null=True,
        help_text='Description of the order or package'
    )
    instructions = models.TextField(
        verbose_name='Special Instructions', blank=True, null=True,
        help_text='Any special instructions for the order'
    )
    trip = models.ForeignKey(
        Trip, on_delete=models.SET_NULL, verbose_name='Trip', null=True, blank=True,
        related_name='orders', help_text='The trip associated with this order'
    )





    # timestamps
    scheduled_date = models.DateTimeField(verbose_name='Scheduled Date', null=True, blank=True)
    date_delivered = models.DateTimeField(verbose_name='Date Delivered', null=True, blank=True)
    date_cancelled = models.DateTimeField(verbose_name='Date Cancelled', null=True, blank=True)
    date_failed = models.DateTimeField(verbose_name='Date Failed', null=True, blank=True)

    # meta
    meta_data = models.JSONField(verbose_name='Meta Data', blank=True, null=True, help_text='Additional metadata for the order')

    def __str__(self):
        return f'Order {self.reference}'

    class Meta:
        verbose_name_plural = 'Orders'
        verbose_name = 'Order'
        ordering = ['-created_at']


class TripStop(CommonInfo):
    STOP_TYPE_CHOICES = [
        ('start', 'Start Location'),
        ('pickup', 'Pickup'),
        ('drop_off', 'Dropoff'),
        ('end', 'End Location'),
    ]

    """
    Model to represent a stop in a trip.
    """
    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    order = models.ForeignKey(Order, null=True, blank=True, on_delete=models.SET_NULL)  # Null for depot stops
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='trip_stops', null=True, blank=True)
    driver = models.ForeignKey(
        'users.Driver', on_delete=models.SET_NULL, null=True, blank=True, related_name='trip_stops'
    )
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    stop_type = models.CharField(max_length=10, choices=STOP_TYPE_CHOICES, default='drop_off')
    sequence = models.PositiveIntegerField()
    eta = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(
        'users.Driver', on_delete=models.SET_NULL, null=True, blank=True, related_name='completed_stops'
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('arrived', 'Arrived'),
            ('done', 'Done'),
            ('skipped', 'Skipped'),
        ],
        default='pending'
    )
