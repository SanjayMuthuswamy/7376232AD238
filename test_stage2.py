from app.database.postgres_connection import create_tables
from app.database.notification_queries import (
    insert_student, insert_notification, get_unread_notifications,
    mark_as_read, get_unread_count, get_all_notifications
)

def test_stage2():
    """Test Stage 2: Database & Queries"""
    
    print("=" * 60)
    print("STAGE 2: PostgreSQL Database & Queries Testing")
    print("=" * 60)
    
    # Step 1: Create tables
    print("\n1. Creating tables...")
    create_tables()
    
    # Step 2: Insert sample students
    print("\n2. Inserting sample students...")
    insert_student(1042, "ram.krishna@abc.edu")
    insert_student(1043, "john.doe@abc.edu")
    
    # Step 3: Insert sample notifications
    print("\n3. Inserting sample notifications...")
    insert_notification(1042, "Placement", "Placement Drive", "TCS recruitment started")
    insert_notification(1042, "Event", "Tech Fest", "Join our annual tech fest")
    insert_notification(1042, "Result", "Exam Results", "Mid-sem results posted")
    insert_notification(1043, "Placement", "Amazon Drive", "Amazon is recruiting")
    
    # Step 4: Get unread count
    print("\n4. Getting unread notification count for student 1042...")
    count = get_unread_count(1042)
    print(f"   Unread count: {count}")
    
    # Step 5: Get all unread notifications
    print("\n5. Fetching unread notifications for student 1042...")
    notifications = get_unread_notifications(1042)
    if notifications:
        for notif in notifications:
            print(f"   ID: {notif[0]}, Type: {notif[2]}, Title: {notif[3]}, Read: {notif[5]}")
    
    # Step 6: Mark first notification as read
    print("\n6. Marking first notification as read...")
    if notifications:
        mark_as_read(notifications[0][0])
    
    # Step 7: Get updated unread count
    print("\n7. Getting updated unread count for student 1042...")
    updated_count = get_unread_count(1042)
    print(f"   Updated unread count: {updated_count}")
    
    # Step 8: Get all notifications
    print("\n8. Fetching all notifications for student 1042...")
    all_notifs = get_all_notifications(1042)
    if all_notifs:
        print(f"   Total notifications: {len(all_notifs)}")
        for notif in all_notifs:
            print(f"   ID: {notif[0]}, Type: {notif[2]}, Title: {notif[3]}, Read: {notif[5]}")
    
    print("\n" + "=" * 60)
    print("STAGE 2 Testing Complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_stage2()
