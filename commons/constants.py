from typing import Optional
from pydantic import BaseModel

from django.db import models
from pydantic import BaseModel, Field, model_validator

class StatusConfig(BaseModel):
    name: str
    is_ative: bool = True




class DriverStatusChoices(models.TextChoices):
    OFFLINE = 'offline', 'Offline'
    BUSY = 'busy', 'Busy'
    AVAILABLE = 'available', 'available'


class OrderStatusChoices(models.TextChoices):
    SCHEDULED = 'scheduled', 'Scheduled'
    PENDING = 'pending', 'Pending'
    BROADCASTED = 'broadcasted', 'Broadcasted'
    ASSIGNED = 'assigned', 'Assigned'
    IN_PROGRESS = 'in_progress', 'In Progress'
    ARRIVED_AT_PICKUP = 'arrived_at_pickup', 'Arrived at Pickup'
    ARRIVED_AT_DROP_OFF = 'arrived_at_drop_off', 'Arrived at Drop-off'
    COMPLETED = 'delivered', 'delivered'
    CANCELLED = 'cancelled', 'Cancelled'
    FAILED = 'failed', 'Failed'

    @staticmethod
    def final_statues():
        return[
            OrderStatusChoices.COMPLETED.value,
            OrderStatusChoices.CANCELLED.value,
            OrderStatusChoices.FAILED.value,
            ]

    @staticmethod
    def assignable_statuses():
        return [
            OrderStatusChoices.PENDING.value,
        ]


class TripStopTypeChoices(models.TextChoices):
    PICKUP = 'pickup', 'Pickup'
    DROPOFF = 'delivery', 'Drop-off'


class StatusNotificationConfig(BaseModel):
    send_webhook: bool = False
    send_store_email: bool = False
    send_store_sms: bool = False
    send_customer_email: bool = False
    send_customer_sms: bool = False


class StatusSLAConfig(BaseModel):
    max_duration_seconds: int = 0
    notify_before_seconds: int = 0
    notify_after_seconds: int = 0


class StatusCombinedConfig(BaseModel):
    is_active: bool = False
    is_trip_stop: bool = False
    stop_type: Optional[str] = None  # e.g., 'PICKUP' or 'DROPOFF'
    notifications: Optional[StatusNotificationConfig] = None
    sla: Optional[StatusSLAConfig] = None


class OrderStatusConfiguration(BaseModel):
    SCHEDULED: StatusCombinedConfig = Field(
        default_factory=lambda: StatusCombinedConfig(is_active=False),
        description='Order is scheduled for pickup',
        alias=OrderStatusChoices.SCHEDULED.value
    )
    PENDING: StatusCombinedConfig = Field(
        default_factory=lambda: StatusCombinedConfig(is_active=True),
        description='Order is pending and waiting for driver assignment',
        alias=OrderStatusChoices.PENDING.value
    )
    BROADCASTED: StatusCombinedConfig = Field(
        default_factory=lambda: StatusCombinedConfig(is_active=True),
        description='Order has been broadcasted to drivers',
        alias=OrderStatusChoices.BROADCASTED.value
    )
    ASSIGNED: StatusCombinedConfig = Field(
        default_factory=lambda: StatusCombinedConfig(is_active=True),
        description='Order has been assigned to a driver',
        alias=OrderStatusChoices.ASSIGNED.value
    )
    IN_PROGRESS: StatusCombinedConfig = Field(
        default_factory=lambda: StatusCombinedConfig(is_active=True, is_trip_stop=True, stop_type=TripStopTypeChoices.PICKUP.value),
        description='Order is currently being delivered',
        alias=OrderStatusChoices.IN_PROGRESS.value
    )
    ARRIVED_AT_PICKUP: StatusCombinedConfig = Field(
        default_factory=lambda: StatusCombinedConfig(is_active=False, is_trip_stop=True, stop_type=TripStopTypeChoices.PICKUP.value),
        description='Driver has arrived at the pickup location',
        alias=OrderStatusChoices.ARRIVED_AT_PICKUP.value
    )
    ARRIVED_AT_DROP_OFF: StatusCombinedConfig = Field(
        default_factory=lambda: StatusCombinedConfig(is_active=False, is_trip_stop=True, stop_type=TripStopTypeChoices.DROPOFF.value),
        description='Driver has arrived at the drop-off location',
        alias=OrderStatusChoices.ARRIVED_AT_DROP_OFF.value
    )
    COMPLETED: StatusCombinedConfig = Field(
        default_factory=lambda: StatusCombinedConfig(is_active=True, is_trip_stop=True, stop_type=TripStopTypeChoices.DROPOFF.value),
        description='Order has been successfully delivered',
        alias=OrderStatusChoices.COMPLETED.value
    )
    CANCELLED: StatusCombinedConfig = Field(
        default=StatusCombinedConfig(is_active=True),
        description='Order has been cancelled',
        alias=OrderStatusChoices.CANCELLED.value
    )
    FAILED: StatusCombinedConfig = Field(
        default=StatusCombinedConfig(is_active=False),
        description='Order delivery has failed',
        alias=OrderStatusChoices.FAILED.value
    )

    @model_validator(mode="after")
    def check_core_statuses(self):
        if not self.PENDING.is_active:
            raise ValueError("Pending must always be active")
        if not self.IN_PROGRESS.is_active:
            raise ValueError("In Progress must always be active")
        if not self.COMPLETED.is_active:
            raise ValueError("Completed must always be active")
        if not self.CANCELLED.is_active:
            raise ValueError("Cancelled must always be active")

        # steps
        if not self.IN_PROGRESS.is_trip_stop:
            raise ValueError("In Progress must always be a trip stop")
        if not self.COMPLETED.is_trip_stop:
            raise ValueError("Completed must always be a trip stop")
        if not self.ARRIVED_AT_PICKUP.is_trip_stop:
            raise ValueError("Arrived at Pickup must always be a trip stop")
        if not self.ARRIVED_AT_DROP_OFF.is_trip_stop:
            raise ValueError("Arrived at Drop-off must always be a trip stop")

        return self

    @model_validator(mode="after")
    def assign_stop_types(self):
        self.IN_PROGRESS.stop_type = TripStopTypeChoices.PICKUP.value
        self.ARRIVED_AT_PICKUP.stop_type = TripStopTypeChoices.PICKUP.value
        self.COMPLETED.stop_type = TripStopTypeChoices.DROPOFF.value
        self.ARRIVED_AT_DROP_OFF.stop_type = TripStopTypeChoices.DROPOFF.value

        return self

class TimezoneChoices(models.TextChoices):
    UTC = 'UTC', 'UTC'
    EST = 'EST', 'Eastern Standard Time'
    CST = 'CST', 'Central Standard Time'
    MST = 'MST', 'Mountain Standard Time'
    PST = 'PST', 'Pacific Standard Time'
    IST = 'IST', 'India Standard Time'


class LanguageChoices(models.TextChoices):
    English = 'en', 'English'
    Spanish = 'es', 'Spanish'
    French = 'fr', 'French'
    German = 'de', 'German'
    Chinese = 'zh', 'Chinese'
    Hindi = 'hi', 'Hindi'


def default_order_status_config():
    return OrderStatusConfiguration().model_dump(by_alias=True)


#     @classmethod
#   def choices(cls):
#       return [(value, value.replace('_', ' ').title()) for value in cls.__annotations__.values()]

