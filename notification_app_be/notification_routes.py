from fastapi import APIRouter, HTTPException, status

from notification_app_be.notification_schema import NotificationCreate, NotificationResponse
from notification_app_be.notification_service import add_notification, get_all_notifications, get_notification

router = APIRouter()


@router.get("/", response_model=list[NotificationResponse])
def list_notifications():
    return get_all_notifications()


@router.get("/{notification_id}", response_model=NotificationResponse)
def one_notification(notification_id: int):
    notification = get_notification(notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    return notification


@router.post("/", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
def create_notification(payload: NotificationCreate):
    return add_notification(payload)
