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


def default_steps_config():
    return Steps().model_dump()
