from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import os

app = Flask(__name__)
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'users.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy()
db.init_app(app)

def add_enrolled_at_column():
    with app.app_context():
        try:
            # Check if column exists
            db.session.execute(text("""SELECT enrolled_at FROM student_subjects LIMIT 1"""))
            print("Column 'enrolled_at' already exists.")
        except Exception:
            # Add the column with default value as current timestamp
            db.session.execute(text("""ALTER TABLE student_subjects ADD COLUMN enrolled_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"""))
            db.session.commit()
            print("Successfully added 'enrolled_at' column to student_subjects table.")

if __name__ == '__main__':
    add_enrolled_at_column()