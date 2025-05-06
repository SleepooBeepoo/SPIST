"""Simplified database clearing script that doesn't rely on dotenv"""
import os
import sqlite3

# Define the database path
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'users.db')

def clear_database():
    """Drop and recreate all tables in the database"""
    try:
        # Check if database file exists
        if not os.path.exists(db_path):
            print(f"Database file not found at: {db_path}")
            return
            
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        # Drop all tables
        for table in tables:
            table_name = table[0]
            if table_name != 'sqlite_sequence':  # Skip SQLite internal tables
                print(f"Dropping table: {table_name}")
                cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
        
        conn.commit()
        print('All tables dropped successfully!')
        
        # Close connection
        cursor.close()
        conn.close()
        
        print('Database cleared successfully!')
        print('Note: You will need to run init_db.py to recreate the tables.')
    except Exception as e:
        print(f"Error clearing database: {str(e)}")

if __name__ == '__main__':
    clear_database()