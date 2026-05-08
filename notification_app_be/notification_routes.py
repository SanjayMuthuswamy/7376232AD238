from fastapi import APIRouter, HTTPException, status

from notification_app_be.notification_schema import NotificationCreate, NotificationResponse, UnreadCountResponse
from notification_app_be.notification_service import (
    add_notification, get_all_notifications, get_notification, mark_as_read, get_unread_count
)

router = APIRouter()


@router.get("/", response_model=list[NotificationResponse])
def list_notifications(student_id: int = None, unread_only: bool = False):
    return get_all_notifications(student_id, unread_only)


@router.get("/unread-count", response_model=UnreadCountResponse)
def unread_count(student_id: int):
    count = get_unread_count(student_id)
    return UnreadCountResponse(student_id=student_id, unread_count=count)


@router.get("/{notification_id}", response_model=NotificationResponse)
def one_notification(notification_id: int):
    notification = get_notification(notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    return notification


@router.post("/", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
def create_notification(payload: NotificationCreate):
    return add_notification(payload)


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def read_notification(notification_id: int):
    notification = mark_as_read(notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification
