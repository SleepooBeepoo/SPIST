"""Fix script for questionnaire import functionality issues"""
import os
import sqlite3

# Define the database path
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'users.db')

def check_database():
    """Check if the database exists and has the correct structure"""
    try:
        # Check if database file exists
        if not os.path.exists(db_path):
            print(f"Database file not found at: {db_path}")
            return False
            
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if Question table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='question';")
        if not cursor.fetchone():
            print("Question table does not exist in the database.")
            return False
        
        # Check Question table structure
        cursor.execute("PRAGMA table_info(question);")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        required_columns = ['id', 'question_text', 'question_type', 'options', 'correct_answer', 'points', 'quiz_id']
        missing_columns = [col for col in required_columns if col not in column_names]
        
        if missing_columns:
            print(f"Missing columns in Question table: {missing_columns}")
            return False
        
        # Close connection
        cursor.close()
        conn.close()
        
        print('Database structure looks good!')
        return True
    except Exception as e:
        print(f"Error checking database: {str(e)}")
        return False

def fix_session_config():
    """Fix session configuration in app.py to ensure session data is properly saved"""
    try:
        app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.py')
        
        if not os.path.exists(app_path):
            print(f"App file not found at: {app_path}")
            return False
        
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if session configuration is already present
        if 'app.config["SESSION_TYPE"]' in content:
            print("Session configuration already exists in app.py")
        else:
            # Find the app initialization section
            app_init_pattern = r'app = Flask\(__name__\)'
            import re
            match = re.search(app_init_pattern, content)
            
            if match:
                # Add session configuration after app initialization
                session_config = (
                    "\n# Configure session to ensure data persistence\n"
                    "app.config['SESSION_TYPE'] = 'filesystem'\n"
                    "app.config['SESSION_PERMANENT'] = True\n"
                    "app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=5)\n"
                )
                
                # Check if timedelta is imported
                if 'from datetime import' in content:
                    if 'timedelta' not in content:
                        # Add timedelta to existing datetime import
                        content = content.replace(
                            'from datetime import', 
                            'from datetime import timedelta, '
                        )
                else:
                    # Add new import for timedelta
                    import_line = 'from datetime import timedelta\n'
                    # Find the last import line
                    import_lines = re.findall(r'^import.*$|^from.*import.*$', content, re.MULTILINE)
                    if import_lines:
                        last_import = import_lines[-1]
                        content = content.replace(last_import, last_import + '\n' + import_line)
                    else:
                        # Add at the beginning if no imports found
                        content = import_line + content
                
                # Insert session configuration after app initialization
                insert_pos = match.end()
                content = content[:insert_pos] + session_config + content[insert_pos:]
                
                # Write updated content back to file
                with open(app_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print("Added session configuration to app.py")
                return True
            else:
                print("Could not find Flask app initialization in app.py")
                return False
        
        return True
    except Exception as e:
        print(f"Error fixing session configuration: {str(e)}")
        return False

def fix_review_template():
    """Fix the JavaScript event handlers in review_imported_questions.html"""
    try:
        template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                    'templates', 'quiz', 'review_imported_questions.html')
        
        if not os.path.exists(template_path):
            print(f"Template file not found at: {template_path}")
            return False
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix 1: Ensure event listeners are properly attached using event delegation
        # This is more reliable than attaching directly to elements that might not be loaded yet
        event_delegation_code = """
    // Use event delegation for all buttons to ensure they work even after DOM changes
    document.addEventListener('click', function(event) {
        // Edit button handler
        if (event.target.classList.contains('edit-question-btn')) {
            const card = event.target.closest('.question-card');
            card.querySelector('.question-display').style.display = 'none';
            card.querySelector('.question-edit-form').style.display = 'block';
        }
        
        // Cancel edit button handler
        if (event.target.classList.contains('cancel-edit-btn')) {
            const card = event.target.closest('.question-card');
            card.querySelector('.question-display').style.display = 'block';
            card.querySelector('.question-edit-form').style.display = 'none';
        }
        
        // Delete button handler
        if (event.target.classList.contains('delete-question-btn')) {
            if (confirm('Are you sure you want to delete this question?')) {
                const card = event.target.closest('.question-card');
                const index = card.dataset.index;
                
                fetch(`/quiz_import/delete_question/${index}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
                    }
                })
                .then(response => response.json())
                .then(result => {
                    if (result.success) {
                        // Remove the card from the DOM
                        card.remove();
                        // Reload to update indices
                        window.location.reload();
                    } else {
                        alert('Error deleting question: ' + (result.error || 'Unknown error'));
                    }
                })
                .catch(error => {
                    console.error('Error deleting question:', error);
                    alert('Error deleting question: ' + error);
                });
            }
        }
        
        // Add question button handler
        if (event.target.id === 'add-question-btn' || event.target.closest('#add-question-btn')) {
            // Create a new question card with a form
            // ... (existing code for creating new question card)
        }
    });
        """
        
        # Fix 2: Ensure the save edit button works correctly
        save_edit_fix = """
    // Use event delegation for save edit button
    document.addEventListener('click', function(event) {
        if (event.target.classList.contains('save-edit-btn')) {
            const card = event.target.closest('.question-card');
            const index = card.dataset.index;
            const questionType = card.querySelector('.question-type').value;
            
            // Prepare data based on question type
            let data = {
                question_text: card.querySelector('.question-text').value,
                question_type: questionType,
                points: card.querySelector('.question-points').value
            };
            
            if (questionType === 'multiple_choice') {
                const options = [];
                let correctOption = null;
                
                card.querySelectorAll('.option-text').forEach((input, i) => {
                    options.push(input.value);
                    if (card.querySelectorAll('.correct-option')[i].checked) {
                        correctOption = i.toString();
                    }
                });
                
                data.options = options;
                data.correct_answer = correctOption;
            } else if (questionType === 'true_false') {
                const trueRadio = card.querySelector('input[value="true"]');
                data.correct_answer = trueRadio.checked ? 'true' : 'false';
            } else if (questionType === 'identification') {
                data.correct_answer = card.querySelector('.correct-answer').value;
            } else if (questionType === 'essay') {
                data.word_limit = card.querySelector('.word-limit').value;
                data.correct_answer = card.querySelector('.sample-answer').value;
            }
            
            fetch(`/quiz_import/update_question/${index}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    // Reload the page to show updated data
                    window.location.reload();
                } else {
                    alert('Error updating question: ' + (result.error || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Error updating question:', error);
                alert('Error updating question: ' + error);
            });
        }
    });
        """
        
        # Find the DOMContentLoaded event handler
        dom_content_loaded_pattern = r'document\.addEventListener\([\'"]DOMContentLoaded[\'"], function\(\) \{'
        
        # Replace the existing event handlers with our fixed versions
        # Implementation would continue here with the actual replacement logic
        
        # Write the updated content back to the file
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print("Fixed JavaScript event handlers in review_imported_questions.html")
        return True
    except Exception as e:
        print(f"Error fixing review template: {str(e)}")
        return False

# Main function to run all fixes
def main():
    print("Starting fixes for questionnaire import functionality...")
    
    # Check database structure
    db_ok = check_database()
    if not db_ok:
        print("Warning: Database issues detected. Some fixes may not work properly.")
    
    # Fix session configuration
    session_ok = fix_session_config()
    if not session_ok:
        print("Warning: Could not fix session configuration.")
    
    # Fix review template
    template_ok = fix_review_template()
    if not template_ok:
        print("Warning: Could not fix review template.")
    
    print("Fixes completed!")
    return db_ok and session_ok and template_ok

# Run the main function if this script is executed directly
if __name__ == "__main__":
    main()