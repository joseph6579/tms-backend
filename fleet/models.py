import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from commons.behaviour import CommonInfo

VEHICLE_SOURCES = (
    ('in_house', 'in_house'),
    ('third_party', 'third_party'),
)

PAYMENT_MODEL_TYPES = (
    ('fixed', 'Fixed Rate'),
    ('commission', 'Commission Based'),
    ('distance', 'Distance Based'),
    ('time', 'Time Based'),
    ('hybrid', 'Hybrid'),
)

class Vehicle(CommonInfo):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    registration_number = models.CharField(max_length=20, unique=True)
    driver = models.OneToOneField('users.Driver', on_delete=models.CASCADE, null=True, blank=True, related_name='vehicle')
    source = models.CharField(max_length=11, choices=VEHICLE_SOURCES, default='in_house')

    def __str__(self):
        return self.registration_number

class PaymentModel(CommonInfo):
    """Model to define how drivers are paid"""
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    organisation = models.ForeignKey('organisations.Organisation', on_delete=models.CASCADE, related_name='payment_models')
    name = models.CharField(max_length=100)
    model_type = models.CharField(max_length=20, choices=PAYMENT_MODEL_TYPES)
    is_active = models.BooleanField(default=True)
    
    # Fixed Rate Settings
    base_rate = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Base rate per delivery/trip"
    )
    
    # Commission Settings
    commission_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Commission percentage of the delivery fee"
    )
    
    # Distance Based Settings
    rate_per_km = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Rate per kilometer"
    )
    minimum_distance_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Minimum fee for short distances"
    )
    
    # Time Based Settings
    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Rate per hour"
    )
    minimum_hours = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Minimum billable hours"
    )
    
    # Hybrid Settings
    hybrid_config = models.JSONField(
        null=True,
        blank=True,
        help_text="Configuration for hybrid payment model"
    )
    
    # Bonus Settings
    bonus_rules = models.JSONField(
        null=True,
        blank=True,
        help_text="Rules for performance bonuses"
    )

    def __str__(self):
        return f"{self.name} - {self.get_model_type_display()}"

    class Meta:
        verbose_name = 'Payment Model'
        verbose_name_plural = 'Payment Models'
        unique_together = ['organisation', 'name']

class DriverPayment(CommonInfo):
    """Model to track driver payments"""
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    driver = models.ForeignKey('users.Driver', on_delete=models.CASCADE, related_name='payments')
    payment_model = models.ForeignKey(PaymentModel, on_delete=models.PROTECT)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    base_amount = models.DecimalField(max_digits=10, decimal_places=2)
    bonus_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('paid', 'Paid'),
            ('failed', 'Failed')
        ],
        default='pending'
    )
    payment_date = models.DateTimeField(null=True, blank=True)
    payment_reference = models.CharField(max_length=100, null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Payment for {self.driver} - {self.period_start.date()} to {self.period_end.date()}"

    class Meta:
        verbose_name = 'Driver Payment'
        verbose_name_plural = 'Driver Payments'
        ordering = ['-period_end']

class PaymentDeduction(CommonInfo):
    """Model to track deductions from driver payments"""
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    payment = models.ForeignKey(DriverPayment, on_delete=models.CASCADE, related_name='deduction_records')
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    deduction_type = models.CharField(
        max_length=20,
        choices=[
            ('vehicle_maintenance', 'Vehicle Maintenance'),
            ('insurance', 'Insurance'),
            ('penalty', 'Penalty'),
            ('other', 'Other')
        ]
    )

    def __str__(self):
        return f"{self.get_deduction_type_display()} - {self.amount}"

    class Meta:
        verbose_name = 'Payment Deduction'
        verbose_name_plural = 'Payment Deductions'

class VehicleAssignmentLogs(CommonInfo):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    vehicle = models.ForeignKey('fleet.Vehicle', on_delete=models.CASCADE)
    driver = models.ForeignKey('users.Driver', on_delete=models.CASCADE, related_name='vehicle_assignments')
    assigned_by = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='user_vehicle_assignments')

    class Meta:
        verbose_name = 'Vehicle Assignment Log'
        verbose_name_plural = 'Vehicle Assignment Logs'