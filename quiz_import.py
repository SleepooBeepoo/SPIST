"""Quiz Import Module

This module handles the importing of quizzes and questions from document files.
It serves as a bridge between the quiz module and the document import functionality.
"""

from document_import import import_questions
from models import db, Quiz, Question
from flask import flash, session
from flask_login import current_user

def import_quiz_from_document(quiz, file, upload_dir=None, use_ai=True):
    """Import questions from a document file and add them to a quiz
    
    Args:
        quiz: The Quiz object to add questions to
        file: The uploaded file object
        upload_dir: The directory to save the file to (optional)
        use_ai: Whether to use AI to extract questions
        
    Returns:
        Tuple[int, Optional[str]]: A tuple containing the number of questions imported
            and an optional error message
    """
    try:
        # Import questions from the document
        questions_data, error = import_questions(file, upload_dir, use_ai)
        
        if error:
            return 0, error
        
        if not questions_data:
            return 0, "No questions could be extracted from the document."
        
        # Create questions from the extracted data
        question_count = 0
        for index, q_data in enumerate(questions_data):
            try:
                # Create a new question object
                question = Question(
                    question_text=q_data.get('question_text', 'No question text'),
                    question_type=q_data.get('question_type', 'essay'),
                    points=float(q_data.get('points', 1.0)),
                    quiz_id=quiz.id,
                    user_id=current_user.id,
                    subject_id=quiz.subject_id,
                    order_index=index
                )
                
                # Set type-specific fields
                if q_data.get('question_type') == 'multiple_choice':
                    # Ensure options is a list
                    options = q_data.get('options', [])
                    if not options or not isinstance(options, list) or len(options) < 2:
                        # Default options if none provided
                        options = ['Option 1', 'Option 2']
                    question.options = options
                    
                    # Set correct answer (default to first option if not specified)
                    correct_answer = q_data.get('correct_answer')
                    if correct_answer is None or not isinstance(correct_answer, (int, str)):
                        correct_answer = '0'  # Default to first option
                    question.correct_answer = str(correct_answer)
                    
                elif q_data.get('question_type') == 'true_false':
                    # Ensure correct answer is 'true' or 'false'
                    correct_answer = q_data.get('correct_answer', '').lower()
                    if correct_answer not in ['true', 'false']:
                        correct_answer = 'true'  # Default to true
                    question.correct_answer = correct_answer
                    
                elif q_data.get('question_type') == 'identification':
                    # Set correct answer
                    question.correct_answer = q_data.get('correct_answer', '')
                    
                elif q_data.get('question_type') == 'essay':
                    # Set word limit if provided
                    if 'word_limit' in q_data:
                        question.word_limit = int(q_data['word_limit'])
                    else:
                        question.word_limit = 500  # Default word limit
                    
                    # Set sample answer if provided
                    question.correct_answer = q_data.get('correct_answer', '')
                
                db.session.add(question)
                question_count += 1
                
            except Exception as e:
                print(f"Error creating question: {str(e)}")
                continue
        
        # Commit all questions to the database
        db.session.commit()
        
        # Update session data
        session['quiz_setup'] = {
            'quiz_id': quiz.id,
            'question_count': question_count,
            'questions_added': question_count,
            'imported': True
        }
        session.modified = True
        
        return question_count, None
        
    except Exception as e:
        db.session.rollback()
        return 0, f"Error importing questions: {str(e)}"