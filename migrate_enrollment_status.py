import sqlite3
import os

def migrate_database():
    db_path = 'instance/users.db'
    
    # Ensure the instance directory exists
    os.makedirs('instance', exist_ok=True)
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if the column exists
        cursor.execute("PRAGMA table_info(student_subjects)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'enrollment_status' not in columns:
            # Add the enrollment_status column
            cursor.execute("ALTER TABLE student_subjects ADD COLUMN enrollment_status VARCHAR(20) NOT NULL DEFAULT 'pending'")
            conn.commit()
            print("Successfully added 'enrollment_status' column to student_subjects table.")
        else:
            print("Column 'enrollment_status' already exists.")
            
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database()