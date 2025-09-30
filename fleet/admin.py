from django.contrib import admin
from fleet.models import (
    Vehicle,
    PaymentModel,
    DriverPayment,
    PaymentDeduction,
    VehicleAssignmentLogs,
    DriverGroup,
    DriverProfile,
)


@admin.register(DriverGroup)
class DriverGroupAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "organisation",
        "payment_model",
        "is_active",
        "minimum_rating",
    ]
    list_filter = ["is_active", "organisation"]
    search_fields = ["name", "description"]


@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'vehicle', 'status', 'active', 'organisation', 'driver', 'driver_group']
    list_filter = ['driver', 'organisation', 'driver_group']
    search_fields = ['first_name', 'last_name']


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ["registration_number", "source", "vehicle_type", 'organisation']
    search_fields = ["registration_number"]
    list_filter = ["source", "vehicle_type"]


@admin.register(PaymentModel)
class PaymentModelAdmin(admin.ModelAdmin):
    list_display = ["name", "organisation", "model_type", "is_active"]
    list_filter = ["model_type", "is_active"]
    search_fields = ["name", "organisation__name"]


@admin.register(DriverPayment)
class DriverPaymentAdmin(admin.ModelAdmin):
    list_display = [
        "driver",
        "driver_group",
        "period_start",
        "period_end",
        "total_amount",
        "status",
    ]
    list_filter = ["status", "driver_group"]
    search_fields = ["driver__email", "payment_reference"]
    date_hierarchy = "period_start"


@admin.register(PaymentDeduction)
class PaymentDeductionAdmin(admin.ModelAdmin):
    list_display = ["payment", "description", "amount", "deduction_type"]
    list_filter = ["deduction_type"]
    search_fields = ["description", "payment__driver__email"]


@admin.register(VehicleAssignmentLogs)
class VehicleAssignmentLogsAdmin(admin.ModelAdmin):
    list_display = ["vehicle", "driver", "assigned_by", "created_at"]
    search_fields = ["vehicle__registration_number", "driver__email"]
    date_hierarchy = "created_at"
