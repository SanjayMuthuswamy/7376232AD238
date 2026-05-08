from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional, List

class NotificationCreate(BaseModel):
    student_id: int
    type: str
    title: str
    message: str

    @field_validator("title", "message", "type")
    @classmethod
    def text_required(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("This field is required")
        return value

class BulkNotificationCreate(BaseModel):
    student_ids: List[int]
    type: str
    title: str
    message: str

class NotificationResponse(BaseModel):
    id: int
    student_id: int
    type: str
    title: str
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UnreadCountResponse(BaseModel):
    student_id: int
    unread_count: int
