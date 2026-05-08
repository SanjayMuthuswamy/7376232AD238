from app.database.postgres_connection import get_connection

def insert_student(student_id, email):
    """Insert a student"""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO students (id, email) 
            VALUES (%s, %s)
            ON CONFLICT (id) DO NOTHING;
        """, (student_id, email))
        conn.commit()
        cursor.close()
        conn.close()
        print(f"Student {student_id} inserted")
        return True
    except Exception as e:
        print(f"Error inserting student: {e}")
        return False

def insert_notification(student_id, notif_type, title, message):
    """Insert a notification"""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO notifications (student_id, type, title, message)
            VALUES (%s, %s, %s, %s);
        """, (student_id, notif_type, title, message))
        conn.commit()
        cursor.close()
        conn.close()
        print(f"Notification inserted for student {student_id}")
        return True
    except Exception as e:
        print(f"Error inserting notification: {e}")
        return False

def get_unread_notifications(student_id):
    """Get unread notifications for a student"""
    conn = get_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, student_id, type, title, message, is_read, created_at
            FROM notifications 
            WHERE student_id = %s AND is_read = false 
            ORDER BY created_at DESC;
        """, (student_id,))
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results
    except Exception as e:
        print(f"Error fetching notifications: {e}")
        return None

def mark_as_read(notification_id):
    """Mark notification as read"""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE notifications 
            SET is_read = true 
            WHERE id = %s;
        """, (notification_id,))
        conn.commit()
        cursor.close()
        conn.close()
        print(f"Notification {notification_id} marked as read")
        return True
    except Exception as e:
        print(f"Error marking as read: {e}")
        return False

def get_unread_count(student_id):
    """Get unread notification count"""
    conn = get_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM notifications 
            WHERE student_id = %s AND is_read = false;
        """, (student_id,))
        
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count
    except Exception as e:
        print(f"Error getting unread count: {e}")
        return None

def get_all_notifications(student_id):
    """Get all notifications for a student"""
    conn = get_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, student_id, type, title, message, is_read, created_at
            FROM notifications 
            WHERE student_id = %s
            ORDER BY created_at DESC;
        """, (student_id,))
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results
    except Exception as e:
        print(f"Error fetching all notifications: {e}")
        return None
