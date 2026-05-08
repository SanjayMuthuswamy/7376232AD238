import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    """Create and return PostgreSQL connection"""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME", "affordmed"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres")
        )
        return conn
    except Exception as e:
        print(f"Connection failed: {e}")
        return None

def create_tables():
    """Create students and notifications tables"""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Create students table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id BIGINT PRIMARY KEY,
                email VARCHAR(150) UNIQUE NOT NULL
            );
        """)
        
        # Create notifications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id BIGSERIAL PRIMARY KEY,
                student_id BIGINT NOT NULL REFERENCES students(id),
                type VARCHAR(30) NOT NULL,
                title VARCHAR(150) NOT NULL,
                message TEXT NOT NULL,
                is_read BOOLEAN DEFAULT false,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create index
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_student_read 
            ON notifications(student_id, is_read);
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        print("Tables created successfully!")
        return True
    except Exception as e:
        print(f"Error creating tables: {e}")
        return False
