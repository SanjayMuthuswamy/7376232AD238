from datetime import datetime, timedelta
import asyncio
from logging_middleware import Log
from notification_app_be.data import notifications
from notification_app_be.notification_schema import NotificationCreate, BulkNotificationCreate

unread_counts_cache = {}

def get_all_notifications(student_id: int = None, unread_only: bool = False):
    Log("backend", "info", "service", "notification list requested")
    res = notifications.copy()
    if student_id is not None:
        res = [n for n in res if n.get("student_id") == student_id]
    if unread_only:
        res = [n for n in res if n.get("is_read") is False]
    return res

def get_recent_placements():
    seven_days_ago = datetime.now() - timedelta(days=7)
    placements = set()
    for n in notifications:
        if n.get("type") == "Placement" and n.get("created_at") >= seven_days_ago:
            placements.add(n.get("student_id"))
    Log("backend", "info", "service", "fetched recent placement notifications")
    return list(placements)

def get_notification(notification_id: int):
    for notification in notifications:
        if notification["id"] == notification_id:
            Log("backend", "info", "service", "single notification fetched")
            return notification
    return None

def update_cache(student_id: int, increment: int):
    if student_id in unread_counts_cache:
        unread_counts_cache[student_id] += increment

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
    update_cache(data.student_id, 1)
    Log("backend", "info", "service", "new notification created")
    return notification

def bulk_save_notifications(data: BulkNotificationCreate):
    new_notifs = []
    base_id = next_id()
    for i, sid in enumerate(data.student_ids):
        new_notifs.append({
            "id": base_id + i,
            "student_id": sid,
            "type": data.type,
            "title": data.title,
            "message": data.message,
            "is_read": False,
            "created_at": datetime.now()
        })
        update_cache(sid, 1)
    
    notifications.extend(new_notifs)
    Log("backend", "info", "service", f"Bulk inserted {len(new_notifs)} notifications")

async def process_email_queue(student_ids: list[int], message: str):
    for sid in student_ids:
        await asyncio.sleep(0.01)
        Log("backend", "info", "worker", f"Email successfully sent to student {sid}")

def mark_as_read(notification_id: int):
    for notification in notifications:
        if notification["id"] == notification_id:
            notification["is_read"] = True
            update_cache(notification["student_id"], -1)
            Log("backend", "info", "service", "notification marked as read")
            return notification
    return None

def get_unread_count(student_id: int):
    if student_id not in unread_counts_cache:
        count = sum(1 for n in notifications if n.get("student_id") == student_id and not n.get("is_read"))
        unread_counts_cache[student_id] = count
        
    Log("backend", "info", "service", "unread count fetched from cache")
    return unread_counts_cache[student_id]

def next_id():
    if len(notifications) == 0:
        return 1
    return max(item["id"] for item in notifications) + 1
