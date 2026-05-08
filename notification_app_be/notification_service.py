from logging_middleware import Log
from notification_app_be.data import notifications
from notification_app_be.notification_schema import NotificationCreate


def get_all_notifications():
    Log("backend", "info", "service", "notification list requested")
    return notifications.copy()


def get_notification(notification_id: int):
    for notification in notifications:
        if notification["id"] == notification_id:
            Log("backend", "info", "service", "single notification fetched")
            return notification
    return None


def add_notification(data: NotificationCreate):
    notification = {
        "id": next_id(),
        "user_id": data.user_id,
        "title": data.title,
        "message": data.message,
        "channel": data.channel,
        "status": "pending",
    }

    notifications.append(notification)
    Log("backend", "info", "service", "new notification created")
    return notification


def next_id():
    if len(notifications) == 0:
        return 1
    return max(item["id"] for item in notifications) + 1
