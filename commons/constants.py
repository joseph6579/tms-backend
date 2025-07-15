from pydantic import BaseModel


class StatusConfig(BaseModel):
    name: str
    is_ative: bool = True


class StatusChoices(BaseModel):
    SCHEDULED: StatusConfig = StatusConfig(name='scheduled', is_ative=True)
    PENDING: StatusConfig = StatusConfig(name='pending', is_ative=True)
    BROADCASTED: StatusConfig = StatusConfig(name='broadcasted', is_ative=True)
    ARRIVED_AT_PICKUP: StatusConfig = StatusConfig(name='arrived_at_pickup', is_ative=True)
    IN_PROGRESS: StatusConfig = StatusConfig(name='in_progress', is_ative=True)
    ARRIVED_AT_DROP_OFF: StatusConfig = StatusConfig(name='arrived_at_drop_off', is_ative=True)
    COMPLETED: StatusConfig = StatusConfig(name='completed', is_ative=True)
    CANCELLED: StatusConfig = StatusConfig(name='cancelled', is_ative=True)
    FAILED: StatusConfig = StatusConfig(name='failed', is_ative=True)

    @classmethod
    def choices(cls):
        return [(value, value.replace('_', ' ').title()) for value in cls.__annotations__.values()]
