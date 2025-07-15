from django.db import models


class TripStopTypesChoices(models.TextChoices):
    START = 'start', 'Start'
    END = 'end', 'End'
    AT_STORE = 'at_store', 'At Store'
    PICKUP = 'pickup', 'Pickup'
    AT_DROP_OFF = 'at_drop_off', 'At Drop Off'
    DROP_OFF = 'drop_off', 'Drop Off'


class OrderStatusChoices(models.TextChoices):
    SCHEDULED = 'scheduled', 'Scheduled'
    PENDING = 'pending', 'Pending'
    BROADCASTED = 'broadcasted', 'Broadcasted'
    ASSIGNED = 'assigned', 'Assigned'
    AT_STORE = 'at_store', 'At Store'
    IN_TRANSIT = 'in_transit', 'In Transit'
    AT_DROP_OFF = 'at_drop_off', 'At Drop Off'
    COMPLETED = 'delivered', 'Delivered'
    CANCELLED = 'cancelled', 'Cancelled'
    FAILED = 'failed', 'Failed'

    @classmethod
    def unassigned_statuses(cls) -> list[str]:
        return [cls.SCHEDULED.value, cls.PENDING.value]
