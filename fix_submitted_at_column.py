from flask import Flask
import os
import sqlite3
import shutil
from datetime import datetime

# Create a backup of the database
instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
db_path = os.path.join(instance_path, 'users.db')
backup_path = f'{db_path}.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'

print(f'Creating backup of database at {backup_path}')
shutil.copy2(db_path, backup_path)
print(f'Backup created successfully')

# Connect directly to the SQLite database
print(f'Connecting to database at {db_path}')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if the quiz_submission table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='quiz_submission'")
if cursor.fetchone():
    # Check if the submitted_at column exists
    cursor.execute("PRAGMA table_info(quiz_submission)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'submitted_at' not in columns:
        print("The 'submitted_at' column is missing from the quiz_submission table. Adding it now...")
        
        # SQLite doesn't support ADD COLUMN with constraints directly
        # We need to create a new table, copy data, drop old table, and rename new table
        
        # Turn off foreign key constraints temporarily
        cursor.execute("PRAGMA foreign_keys=OFF")
        
        # Start a transaction
        cursor.execute("BEGIN TRANSACTION")
        
        try:
            # Create a new table with the correct schema
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
            
            # Get the list of columns from the old table (excluding the new column)
            cursor.execute("PRAGMA table_info(quiz_submission)")
            old_columns = [row[1] for row in cursor.fetchall()]
            column_list = ', '.join(old_columns)
            
            # Copy data from old table to new table, setting submitted_at to NULL
            cursor.execute(f'''
            INSERT INTO quiz_submission_new (id, student_id, quiz_id, submitted_at, 
                                           start_time, duration_taken, total_score, 
                                           graded, visible_to_students, show_answers, feedback)
            SELECT id, student_id, quiz_id, NULL, 
                   start_time, duration_taken, total_score, 
                   graded, visible_to_students, show_answers, feedback
            FROM quiz_submission
            ''')
            
            # Drop old table
            cursor.execute("DROP TABLE quiz_submission")
            
            # Rename new table
            cursor.execute("ALTER TABLE quiz_submission_new RENAME TO quiz_submission")
            
            # Commit the transaction
            conn.commit()
            print("Successfully added 'submitted_at' column to quiz_submission table")
            
        except Exception as e:
            # Rollback in case of error
            conn.rollback()
            print(f"Error updating database: {str(e)}")
        finally:
            # Turn foreign key constraints back on
            cursor.execute("PRAGMA foreign_keys=ON")
    else:
        print("The 'submitted_at' column already exists in the quiz_submission table.")
else:
    print("The quiz_submission table doesn't exist in the database.")

# Close the connection
conn.close()
print("Database update completed.")