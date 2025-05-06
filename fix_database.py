from flask import Flask
import os
import sys
import shutil
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
db_path = os.path.join(instance_path, 'users.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Import db after configuring app
from models import db
db.init_app(app)

with app.app_context():
    # Create a backup of the database
    backup_path = f'{db_path}.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    shutil.copy2(db_path, backup_path)
    print(f'Created database backup at {backup_path}')
    
    # Execute the migration
    conn = db.engine.connect()
    conn.execute(db.text('PRAGMA foreign_keys=OFF'))
    conn.execute(db.text('BEGIN TRANSACTION'))
    try:
        # Check if the quiz_submission table exists
        result = conn.execute(db.text("SELECT name FROM sqlite_master WHERE type='table' AND name='quiz_submission'"))
        if result.fetchone():
            # Get the current schema of the quiz_submission table
            result = conn.execute(db.text("PRAGMA table_info(quiz_submission)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'start_time' not in columns:
                print("The 'start_time' column is missing from the quiz_submission table. Recreating the table...")
                
                # Create a temporary table with the correct schema
                conn.execute(db.text('''
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
                '''))
                
                # Copy data from old table to new table, handling the missing column
                conn.execute(db.text('''
                INSERT INTO quiz_submission_new 
                SELECT id, student_id, quiz_id, submitted_at, NULL, duration_taken, 
                       total_score, graded, visible_to_students, show_answers, feedback 
                FROM quiz_submission
                '''))
                
                # Drop old table and rename new table
                conn.execute(db.text('DROP TABLE quiz_submission'))
                conn.execute(db.text('ALTER TABLE quiz_submission_new RENAME TO quiz_submission'))
                
                print('Successfully updated quiz_submission table - start_time column added')
            elif 'submitted_at' not in columns:
                print("The 'submitted_at' column is missing from the quiz_submission table. Recreating the table...")
                
                # Create a temporary table with the correct schema
                conn.execute(db.text('''
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
                '''))
                
                # Copy data from old table to new table, handling the missing column
                conn.execute(db.text('''
                INSERT INTO quiz_submission_new 
                SELECT id, student_id, quiz_id, NULL, start_time, duration_taken, 
                       total_score, graded, visible_to_students, show_answers, feedback 
                FROM quiz_submission
                '''))
                
                # Drop old table and rename new table
                conn.execute(db.text('DROP TABLE quiz_submission'))
                conn.execute(db.text('ALTER TABLE quiz_submission_new RENAME TO quiz_submission'))
                
                print('Successfully updated quiz_submission table - submitted_at column added')
            else:
                print("The 'submitted_at' column already exists in the quiz_submission table.")
        else:
            print("The quiz_submission table doesn't exist. Creating it...")
            # Create the quiz_submission table with the correct schema
            conn.execute(db.text('''
            CREATE TABLE quiz_submission (
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
            '''))
            print('Successfully created quiz_submission table with submitted_at column')
        
        conn.execute(db.text('COMMIT'))
        print('Database schema update completed successfully.')
    except Exception as e:
        conn.execute(db.text('ROLLBACK'))
        print(f'Error updating database: {str(e)}')
    finally:
        conn.execute(db.text('PRAGMA foreign_keys=ON'))
        conn.close()

print('Database schema update completed.')