from app import app, db
from models import QuizSubmission

def migrate_database():
    with app.app_context():
        # Add new columns to quiz_submission table
        with db.engine.connect() as conn:
            # SQLite only allows adding one column at a time
            conn.execute(db.text("ALTER TABLE quiz_submission ADD COLUMN start_time DATETIME"))
            conn.execute(db.text("ALTER TABLE quiz_submission ADD COLUMN duration_taken INTEGER"))
            conn.commit()

if __name__ == '__main__':
    migrate_database()
    print('Database migration completed successfully!')