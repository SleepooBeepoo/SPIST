"""Migration script to add enrollment verification fields to Subject model"""
from app.models import db
from sqlalchemy import text
import logging

def add_enrollment_verification_fields():
    """Add domain_whitelist and student_id_pattern fields to Subject table"""
    try:
        # Check if columns already exist
        try:
            db.session.execute(text("""SELECT domain_whitelist FROM subject LIMIT 1"""))
            print("Column 'domain_whitelist' already exists.")
        except Exception:
            # Add domain_whitelist column
            db.session.execute(text("""ALTER TABLE subject ADD COLUMN domain_whitelist TEXT"""))
            print("Successfully added 'domain_whitelist' column to subject table.")
        
        try:
            db.session.execute(text("""SELECT student_id_pattern FROM subject LIMIT 1"""))
            print("Column 'student_id_pattern' already exists.")
        except Exception:
            # Add student_id_pattern column
            db.session.execute(text("""ALTER TABLE subject ADD COLUMN student_id_pattern TEXT"""))
            print("Successfully added 'student_id_pattern' column to subject table.")
            
        try:
            db.session.execute(text("""SELECT auto_approve_enabled FROM subject LIMIT 1"""))
            print("Column 'auto_approve_enabled' already exists.")
        except Exception:
            # Add auto_approve_enabled column
            db.session.execute(text("""ALTER TABLE subject ADD COLUMN auto_approve_enabled BOOLEAN NOT NULL DEFAULT 0"""))
            print("Successfully added 'auto_approve_enabled' column to subject table.")
            
        db.session.commit()
        print("Migration completed successfully.")
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error adding enrollment verification fields: {str(e)}")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    add_enrollment_verification_fields()