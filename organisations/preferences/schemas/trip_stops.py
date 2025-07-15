from pydantic import BaseModel, Field


class StepNotification(BaseModel):
    order_webhook: bool = Field(..., description='Send webhook on step completion')
    recipient_sms: bool = Field(..., description='Send an SMS to the recipient on step completion')
    recipient_email: bool = Field(..., description='Send an email to the recipient on step completion')
    buyer_email: bool = Field(..., description='Send an email to the buyer on step completion')
    buyer_sms: bool = Field(..., description='Send an SMS to the buyer on step completion')


class StepConfig(BaseModel):
    is_active: bool = Field(..., description='Defines if a step is active or not')
    sequence: int = Field(..., description='Defines the step sequence')
    notifications: StepNotification = Field(..., description='The step notification configuration')


class Steps(BaseModel):
    arrived_at_store: StepConfig
    pickup: StepConfig
    arrived_at_destination: StepConfig
    drop_off: StepConfig


def default_step_config(sequence: int) -> StepConfig:
    return StepConfig(
        is_active=True,
        sequence=sequence,
        notifications=StepNotification(
            order_webhook=True,
            recipient_sms=False,
            recipient_email=False,
            buyer_email=True,
            buyer_sms=False,
        ),
    )


def default_steps_config() -> dict:
    return Steps(
        arrived_at_store=default_step_config(1),
        pickup=default_step_config(2),
        arrived_at_destination=default_step_config(3),
        drop_off=default_step_config(4),
    ).model_dump()
