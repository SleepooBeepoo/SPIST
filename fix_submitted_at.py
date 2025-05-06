import sqlite3
import os
import shutil
from datetime import datetime

# Path to the database
instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
db_path = os.path.join(instance_path, 'users.db')

# Create a backup
backup_path = f'{db_path}.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
print(f'Creating backup at {backup_path}')
shutil.copy2(db_path, backup_path)
print('Backup created successfully')

# Connect to the database
print(f'Connecting to database at {db_path}')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Disable foreign keys temporarily
    cursor.execute('PRAGMA foreign_keys=OFF')
    
    # Start transaction
    cursor.execute('BEGIN TRANSACTION')
    
    # Check if the quiz_submission table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='quiz_submission'")
    if cursor.fetchone():
        # Check if submitted_at column exists
        cursor.execute("PRAGMA table_info(quiz_submission)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'submitted_at' not in columns:
            print("Adding 'submitted_at' column to quiz_submission table...")
            
            # Create new table with correct schema
            cursor.execute('''
            CREATE TABLE quiz_submission_new (
                id INTEGER PRIMARY KEY,
                student_id INTEGER NOT NULL,
                quiz_id INTEGER NOT NULL,
                submitted_at DATETIME,
                start_time DATETIME,
                duration_taken INTEGER,
                total_score FLOAT NOT NULL DEFAULT 0.0,
                graded BOOLEAN NOT NULL DEFAULT 0,
                visible_to_students BOOLEAN NOT NULL DEFAULT 0,
                show_answers BOOLEAN NOT NULL DEFAULT 0,
                feedback TEXT,
                FOREIGN KEY (student_id) REFERENCES user (id),
                FOREIGN KEY (quiz_id) REFERENCES quiz (id)
            )
            ''')
            
            # Copy data from old table to new table
            cursor.execute('''
            INSERT INTO quiz_submission_new (
                id, student_id, quiz_id, submitted_at, start_time, duration_taken,
                total_score, graded, visible_to_students, show_answers, feedback
            )
            SELECT 
                id, student_id, quiz_id, NULL, start_time, duration_taken,
                total_score, graded, visible_to_students, show_answers, feedback
            FROM quiz_submission
            ''')
            
            # Drop old table and rename new one
            cursor.execute('DROP TABLE quiz_submission')
            cursor.execute('ALTER TABLE quiz_submission_new RENAME TO quiz_submission')
            
            print("Successfully added 'submitted_at' column to quiz_submission table")
        else:
            print("The 'submitted_at' column already exists in the quiz_submission table")
    else:
        print("The quiz_submission table doesn't exist in the database")
    
    # Commit changes
    conn.commit()
    print("Database update completed successfully")
    
except Exception as e:
    # Rollback in case of error
    conn.rollback()
    print(f"Error updating database: {str(e)}")
    
finally:
    # Re-enable foreign keys and close connection
    cursor.execute('PRAGMA foreign_keys=ON')
    conn.close()

print("\nInstructions for the user:")
print("1. Run this script using: python fix_submitted_at.py")
print("2. After running this script, restart your Flask application")
print("3. The 'submitted_at' column should now be available in the quiz_submission table")