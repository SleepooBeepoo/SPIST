from app import app, db
from models import User, Subject, Quiz, Question, StudentSubmission

def clear_database():
    with app.app_context():
        # Drop all tables
        db.drop_all()
        
        # Recreate all tables with fresh schema
        db.create_all()
        
        print('Database cleared and tables recreated successfully!')

if __name__ == '__main__':
    clear_database()