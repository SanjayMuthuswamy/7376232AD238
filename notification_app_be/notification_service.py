from datetime import datetime
from logging_middleware import Log
from notification_app_be.data import notifications
from notification_app_be.notification_schema import NotificationCreate


def get_all_notifications(student_id: int = None, unread_only: bool = False):
    Log("backend", "info", "service", "notification list requested")
    res = notifications.copy()
    if student_id is not None:
        res = [n for n in res if n.get("student_id") == student_id]
    if unread_only:
        res = [n for n in res if n.get("is_read") is False]
    return res


def get_notification(notification_id: int):
    for notification in notifications:
        if notification["id"] == notification_id:
            Log("backend", "info", "service", "single notification fetched")
            return notification
    return None


def add_notification(data: NotificationCreate):
    notification = {
        "id": next_id(),
        "student_id": data.student_id,
        "type": data.type,
        "title": data.title,
        "message": data.message,
        "is_read": False,
        "created_at": datetime.now()
    }

    notifications.append(notification)
    Log("backend", "info", "service", "new notification created")
    return notification


def mark_as_read(notification_id: int):
    for notification in notifications:
        if notification["id"] == notification_id:
            notification["is_read"] = True
            Log("backend", "info", "service", "notification marked as read")
            return notification
    return None


def get_unread_count(student_id: int):
    count = sum(1 for n in notifications if n.get("student_id") == student_id and not n.get("is_read"))
    Log("backend", "info", "service", "unread count fetched")
    return count


def next_id():
    if len(notifications) == 0:
        return 1
    return max(item["id"] for item in notifications) + 1
