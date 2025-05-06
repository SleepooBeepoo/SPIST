from flask import Flask
from models import db
from sqlalchemy import text

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def add_enrollment_status_column():
    with app.app_context():
        try:
            # Check if column exists
            db.session.execute(text("""SELECT enrollment_status FROM student_subjects LIMIT 1"""))
            print("Column 'enrollment_status' already exists.")
        except Exception:
            # Add the column
            db.session.execute(text("""ALTER TABLE student_subjects ADD COLUMN enrollment_status VARCHAR(20) NOT NULL DEFAULT 'pending'"""))
            db.session.commit()
            print("Successfully added 'enrollment_status' column to student_subjects table.")

if __name__ == '__main__':
    add_enrollment_status_column()