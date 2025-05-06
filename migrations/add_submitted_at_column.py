from flask import Flask
import os
import sys
import shutil
from datetime import datetime

# Add parent directory to path so we can import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import db

# Initialize Flask app
app = Flask(__name__)
instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'instance')
db_path = os.path.join(instance_path, 'users.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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
        # Check if the column already exists
        result = conn.execute(db.text("PRAGMA table_info(quiz_submission)"))
        columns = [row[1] for row in result.fetchall()]
        
        if 'submitted_at' not in columns:
            print("Adding 'submitted_at' column to quiz_submission table...")
            # Add the submitted_at column
            conn.execute(db.text('''
            ALTER TABLE quiz_submission ADD COLUMN submitted_at DATETIME
            '''))
            print("Column 'submitted_at' added successfully.")
        else:
            print("Column 'submitted_at' already exists in quiz_submission table.")
        
        conn.execute(db.text('COMMIT'))
        print('Migration completed successfully.')
    except Exception as e:
        conn.execute(db.text('ROLLBACK'))
        print(f'Error updating database: {str(e)}')
    finally:
        conn.execute(db.text('PRAGMA foreign_keys=ON'))
        conn.close()

print('Migration completed.')