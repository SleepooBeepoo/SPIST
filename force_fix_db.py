import os
import sys
import time
import shutil
import subprocess

def install_psutil():
    print("Installing required dependency: psutil")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
        print("Successfully installed psutil")
        return True
    except Exception as e:
        print(f"Failed to install psutil: {e}")
        return False

def find_and_kill_locking_processes(db_path):
    try:
        import psutil
    except ImportError:
        if not install_psutil():
            print("Cannot proceed without psutil")
            return False
        import psutil
    
    found = False
    for proc in psutil.process_iter(['pid', 'name', 'open_files']):
        try:
            for file in proc.info.get('open_files', []) or []:
                if db_path in file.path:
                    print(f"Found process locking database: {proc.info['name']} (PID: {proc.info['pid']})")
                    found = True
                    try:
                        print(f"Terminating process {proc.info['pid']}...")
                        if sys.platform == 'win32':
                            import signal
                            os.kill(proc.info['pid'], signal.SIGTERM)
                        else:
                            os.kill(proc.info['pid'], 9)  # SIGKILL
                        print(f"Process terminated successfully")
                    except Exception as e:
                        print(f"Failed to terminate process: {e}")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return found

def fix_corrupted_database():
    print('Forcefully fixing corrupted database...')
    
    # Define paths
    instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    db_path = os.path.join(instance_path, 'users.db')
    
    # Create backup of corrupted database
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    backup_path = f"{db_path}.backup_{timestamp}"
    
    print(f'Creating backup at {backup_path}')
    if os.path.exists(db_path):
        try:
            # Try to copy the file first
            shutil.copy2(db_path, backup_path)
            print('Backup created successfully')
        except Exception as e:
            print(f'Warning: Could not create backup: {e}')
    
    # Find and kill processes locking the database
    print("Looking for processes locking the database...")
    if find_and_kill_locking_processes(db_path):
        print("Waiting for processes to terminate...")
        time.sleep(2)  # Give processes time to terminate
    
    # Now try to remove the corrupted database
    print('Removing corrupted database...')
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
            print('Database removed successfully')
        print('\nDatabase has been reset. Please restart your Flask application.')
        print('A new empty database will be created automatically when you start the app.')
        return True
    except Exception as e:
        print(f'Error removing database: {e}')
        print('\nPlease try the following steps:')
        print('1. Close all applications manually')
        print('2. Run this script again or manually delete the database file')
        return False

if __name__ == '__main__':
    success = fix_corrupted_database()
    if success:
        print('\nTo start your application with a fresh database, run:')
        print('python app.py')
    else:
        print('\nDatabase repair failed. Please try again after closing all applications.')
        sys.exit(1)