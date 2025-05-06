import os
import shutil
import datetime
import sqlite3
import time

def backup_database():
    """Create a backup of the current database file"""
    instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    src = os.path.join(instance_dir, 'users.db')
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup = f"{src}.backup_{timestamp}"
    
    if os.path.exists(src):
        try:
            print(f"Creating backup of {src} to {backup}")
            shutil.copy2(src, backup)
            print("Backup completed successfully")
            return True
        except Exception as e:
            print(f"Error creating backup: {str(e)}")
            return False
    else:
        print("Database file not found")
        return False

def create_new_database():
    """Create a new empty database with the correct schema"""
    instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    db_path = os.path.join(instance_dir, 'users.db')
    
    # Ensure instance directory exists
    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir, exist_ok=True)
        print(f"Created instance directory: {instance_dir}")
    
    # Remove the corrupted database if it exists
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print(f"Removed corrupted database file")
        except Exception as e:
            print(f"Warning: Could not remove existing database: {str(e)}")
            print("Will attempt to create a new database anyway")
    
    # Create a new database with the schema
    try:
        # Connect to create the file
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create tables based on the models
        cursor.executescript('''
        -- User table
        CREATE TABLE user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(80) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password_hash VARCHAR(128),
            role VARCHAR(20) NOT NULL DEFAULT 'student'
        );
        
        -- Subject table
        CREATE TABLE subject (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            subject_code VARCHAR(20) UNIQUE NOT NULL,
            teacher_id INTEGER NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (teacher_id) REFERENCES user (id)
        );
        
        -- StudentSubject table
        CREATE TABLE student_subjects (
            student_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            enrollment_status VARCHAR(20) NOT NULL DEFAULT 'pending',
            enrolled_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (student_id, subject_id),
            FOREIGN KEY (student_id) REFERENCES user (id),
            FOREIGN KEY (subject_id) REFERENCES subject (id)
        );
        
        -- Quiz table
        CREATE TABLE quiz (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(100) NOT NULL,
            description TEXT,
            quiz_type VARCHAR(20) NOT NULL DEFAULT 'quiz',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            duration INTEGER,
            start_time DATETIME,
            FOREIGN KEY (user_id) REFERENCES user (id),
            FOREIGN KEY (subject_id) REFERENCES subject (id)
        );
        
        -- Question table
        CREATE TABLE question (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_text VARCHAR(500) NOT NULL,
            question_type VARCHAR(20) NOT NULL,
            word_limit INTEGER,
            options JSON,
            correct_answer VARCHAR(500) NOT NULL,
            points FLOAT NOT NULL DEFAULT 1.0,
            order_index INTEGER NOT NULL DEFAULT 0,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER NOT NULL,
            quiz_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES user (id),
            FOREIGN KEY (quiz_id) REFERENCES quiz (id)
        );
        
        -- StudentSubmission table
        CREATE TABLE student_submission (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            answer TEXT,
            is_correct BOOLEAN,
            score FLOAT,
            feedback TEXT,
            submitted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            student_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            quiz_submission_id INTEGER,
            visible_to_students BOOLEAN DEFAULT 0,
            show_answers BOOLEAN DEFAULT 0,
            FOREIGN KEY (student_id) REFERENCES user (id),
            FOREIGN KEY (question_id) REFERENCES question (id),
            FOREIGN KEY (quiz_submission_id) REFERENCES quiz_submission (id)
        );
        
        -- QuizSubmission table
        CREATE TABLE quiz_submission (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            completed_at DATETIME,
            total_score FLOAT,
            student_id INTEGER NOT NULL,
            quiz_id INTEGER NOT NULL,
            FOREIGN KEY (student_id) REFERENCES user (id),
            FOREIGN KEY (quiz_id) REFERENCES quiz (id)
        );
        ''')
        
        conn.commit()
        conn.close()
        print("Created new database with schema successfully")
        return True
    except Exception as e:
        print(f"Error creating new database: {str(e)}")
        return False

def fix_database():
    """Main function to fix the corrupted database"""
    print("Starting database repair process...")
    
    # First backup the corrupted database
    backup_success = backup_database()
    if backup_success:
        print("Backup created successfully")
    else:
        print("Warning: Could not create backup")
    
    # Create a new database with the schema
    if create_new_database():
        print("\nDatabase repair completed successfully!")
        print("Note: The database has been reset to empty state.")
        print("You will need to recreate all users and data.")
        if backup_success:
            print("A backup of your previous database was created.")
        return True
    else:
        print("\nDatabase repair failed.")
        print("Possible solutions:")
        print("1. Close all applications that might be using the database")
        print("2. Run this script with administrator privileges")
        print("3. Manually delete the database file and try again")
        return False

if __name__ == '__main__':
    # Wait a moment to ensure any file locks are released
    print("Waiting for any database locks to be released...")
    time.sleep(2)
    
    # Run the repair process
    fix_database()