import os
import shutil
import datetime
import stat
from flask import Flask
from models import db

# Create a backup of the corrupted database
def backup_database():
    # Ensure instance directory exists with proper permissions
    instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    if not os.path.exists(instance_dir):
        try:
            os.makedirs(instance_dir, exist_ok=True)
            # Set directory permissions to be writable
            os.chmod(instance_dir, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH)
            print(f"Created instance directory: {instance_dir}")
        except Exception as e:
            print(f"Error creating instance directory: {str(e)}")
            print(f"Current working directory: {os.getcwd()}")
            print(f"Attempting to create directory with full permissions")
            try:
                # Try with different permissions
                os.makedirs(instance_dir, exist_ok=True)
                os.chmod(instance_dir, 0o777)  # Full permissions as fallback
                print(f"Created instance directory with full permissions: {instance_dir}")
            except Exception as e2:
                print(f"Still failed to create directory: {str(e2)}")
                return False
    
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
        print("Database file not found or already corrupted")
        return False

# Initialize Flask app with correct database path
app = Flask(__name__)
# Use absolute path for database to avoid permission issues
instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
db_path = os.path.join(instance_path, 'users.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Recreate the database with the existing schema
def recreate_database():
    # Ensure instance directory exists and is writable
    instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    if not os.path.exists(instance_dir):
        try:
            os.makedirs(instance_dir, exist_ok=True)
            os.chmod(instance_dir, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH)
            print(f"Created instance directory: {instance_dir}")
        except Exception as e:
            print(f"Error creating instance directory: {str(e)}")
            try:
                # Try with different permissions
                os.makedirs(instance_dir, exist_ok=True)
                os.chmod(instance_dir, 0o777)  # Full permissions as fallback
                print(f"Created instance directory with full permissions: {instance_dir}")
            except Exception as e2:
                print(f"Still failed to create directory: {str(e2)}")
                return False
    else:
        # Ensure the existing directory is writable
        try:
            os.chmod(instance_dir, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH)
            print(f"Updated permissions on existing instance directory: {instance_dir}")
        except Exception as e:
            print(f"Warning: Could not update permissions on existing directory: {str(e)}")
            # Continue anyway as the directory exists
    
    # Check if database file exists and remove it if corrupted
    db_file = os.path.join(instance_dir, 'users.db')
    if os.path.exists(db_file):
        try:
            # Always remove the existing database file to ensure a clean start
            print(f"Removing existing database file: {db_file}")
            os.remove(db_file)
            print(f"Successfully removed existing database file")
        except Exception as e:
            print(f"Error removing database file: {str(e)}")
            try:
                # Try to change permissions and remove again
                os.chmod(db_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP)
                os.remove(db_file)
                print(f"Successfully removed database file after changing permissions")
            except Exception as e2:
                print(f"Failed to remove database file: {str(e2)}")
                # Check if file is locked by another process
                import psutil
                for proc in psutil.process_iter(['pid', 'name', 'open_files']):
                    try:
                        for file in proc.info.get('open_files', []) or []:
                            if db_file in file.path:
                                print(f"Database file is locked by process: {proc.info['name']} (PID: {proc.info['pid']})")
                                print("Please close this application and try again")
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass
                print("Please manually delete the database file and try again")
                return False
    
    # Ensure the instance directory is writable before creating the database
    try:
        # Create an empty file to test write permissions
        test_file = os.path.join(instance_dir, '.write_test')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        print("Verified write permissions in instance directory")
    except Exception as e:
        print(f"Warning: Instance directory may not be writable: {str(e)}")
        try:
            # Try to fix permissions
            os.chmod(instance_dir, 0o777)  # Full permissions as fallback
            print("Applied full permissions to instance directory")
        except Exception as e2:
            print(f"Failed to update directory permissions: {str(e2)}")
            # Continue anyway and see if it works
    
    with app.app_context():
        try:
            # Create all tables with fresh schema
            db.create_all()
            print("Created all tables with fresh schema")
            # Test database connection
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            db.session.commit()
            print("Database connection test successful")
            return True
        except Exception as e:
            print(f"Error recreating database: {str(e)}")
            print("Detailed error information:")
            print(f"- Error type: {type(e).__name__}")
            print(f"- Error message: {str(e)}")
            # Try to provide more specific error information
            if 'unable to open database file' in str(e).lower():
                print("\nThis error typically indicates a permission problem:")
                print("1. The application doesn't have write access to the instance directory")
                print("2. The parent directory permissions are too restrictive")
                print("3. Another process might be locking the database file")
            return False

# Main function to repair the database
def repair_database():
    print("Starting database repair process...")
    print(f"Working directory: {os.getcwd()}")
    
    # First backup the corrupted database
    backup_success = backup_database()
    
    # Then recreate the database
    if recreate_database():
        print("Database repair completed successfully!")
        print("Note: The database has been reset to empty state.")
        print("You will need to recreate all users and data.")
        if backup_success:
            print(f"A backup of your previous database was created.")
        
        # Verify the database is now accessible
        try:
            with app.app_context():
                from sqlalchemy import text
                db.session.execute(text('SELECT 1'))
                print("Database connection verified successfully.")
        except Exception as e:
            print(f"Warning: Database was recreated but connection test failed: {str(e)}")
            print("You may need to check file permissions or restart your application.")
    else:
        print("Database repair failed.")
        print("Possible solutions:")
        print("1. Run this script with administrator privileges")
        print("2. Check if another process is locking the database file")
        print("3. Ensure the 'instance' directory is writable")

if __name__ == '__main__':
    # Add psutil to requirements if not already installed
    try:
        import psutil
    except ImportError:
        print("Installing required dependency: psutil")
        import subprocess
        try:
            subprocess.check_call(["pip", "install", "psutil"])
            print("Successfully installed psutil")
            import psutil
        except Exception as e:
            print(f"Warning: Could not install psutil: {str(e)}")
            print("Continuing without process checking capability")
    
    repair_database()