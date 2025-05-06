from app import app, db

def add_columns():
    with app.app_context():
        try:
            with db.engine.connect() as conn:
                conn.execute(db.text('ALTER TABLE quiz_submission ADD COLUMN show_answers BOOLEAN NOT NULL DEFAULT 0'))
                conn.commit()
                print('Successfully added show_answers column to quiz_submission table')
        except Exception as e:
            print(f'Error during migration: {str(e)}')
            
if __name__ == '__main__':
    add_columns()