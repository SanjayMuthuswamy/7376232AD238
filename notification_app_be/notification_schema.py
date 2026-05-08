from pydantic import BaseModel, field_validator


class NotificationCreate(BaseModel):
    user_id: int
    title: str
    message: str
    channel: str = "email"

    @field_validator("title", "message")
    @classmethod
    def text_required(cls, value):
        value = value.strip()
        if value == "":
            raise ValueError("This field is required")
        return value

    @field_validator("channel")
    @classmethod
    def valid_channel(cls, value):
        channel = value.strip().lower()
        if channel not in ["email", "sms", "push"]:
            raise ValueError("Channel must be email, sms, or push")
        return channel


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    channel: str
    status: str
