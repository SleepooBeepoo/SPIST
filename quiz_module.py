from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from models import db, Quiz, Question, Subject
from datetime import datetime
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import StringField, TextAreaField, SelectField, IntegerField, DateTimeField, HiddenField, BooleanField
from wtforms.validators import DataRequired, Length, Optional, NumberRange

quiz_bp = Blueprint('quiz', __name__)

class QuizSetupForm(FlaskForm):
    title = StringField('Quiz Title', validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    quiz_type = SelectField('Quiz Type', choices=[('quiz', 'Quiz'), ('exam', 'Exam')], validators=[DataRequired()])
    subject_id = SelectField('Subject', coerce=int, validators=[DataRequired()])
    creation_method = SelectField('Creation Method', choices=[('manual', 'Create Manually'), ('import', 'Import from Document')], default='manual', validators=[DataRequired()])
    question_count = IntegerField('Number of Questions', validators=[DataRequired(), NumberRange(min=1, max=50)])
    duration = IntegerField('Duration (minutes)', validators=[Optional(), NumberRange(min=1, max=180)])
    start_time = DateTimeField('Start Time', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    document_file = FileField('Document File', validators=[Optional()])
    use_ai = BooleanField('Use AI to analyze document', default=True)

class QuestionForm(FlaskForm):
    quiz_id = HiddenField('Quiz ID')
    current_question = HiddenField('Current Question')
    total_questions = HiddenField('Total Questions')
    question_text = TextAreaField('Question', validators=[DataRequired(), Length(max=500)])
    question_type = SelectField('Question Type', choices=[
        ('multiple_choice', 'Multiple Choice'),
        ('identification', 'Identification'),
        ('true_false', 'True/False'),
        ('essay', 'Essay')
    ], validators=[DataRequired()])
    options = TextAreaField('Options (one per line, for multiple choice)', validators=[Optional()])
    correct_answer = StringField('Correct Answer', validators=[Optional()])
    points = IntegerField('Points', validators=[Optional(), NumberRange(min=1, max=100)], default=1)
    word_limit = IntegerField('Word Limit', validators=[Optional(), NumberRange(min=1)], default=500)
    # Add fields for multiple choice options that are referenced in the template
    option1 = StringField('Option 1', validators=[Optional()])
    option2 = StringField('Option 2', validators=[Optional()])
    option3 = StringField('Option 3', validators=[Optional()])
    option4 = StringField('Option 4', validators=[Optional()])
    option5 = StringField('Option 5', validators=[Optional()])
    # Add correct_option field for multiple choice questions
    correct_option = SelectField('Correct Answer', choices=[
        ('0', 'Option 1'),
        ('1', 'Option 2'),
        ('2', 'Option 3'),
        ('3', 'Option 4'),
        ('4', 'Option 5')
    ], validators=[Optional()])

@quiz_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_quiz():
    if current_user.role != 'teacher':
        flash('Only teachers can create quizzes/exams.')
        return redirect(url_for('dashboard'))
    
    subjects = Subject.query.filter_by(teacher_id=current_user.id).all()
    if not subjects:
        flash('You need to create a subject before creating a quiz/exam.')
        return redirect(url_for('dashboard'))
    
    form = QuizSetupForm()
    form.subject_id.choices = [(s.id, s.name) for s in subjects]
    
    if form.validate_on_submit():
        try:
            start_time = None
            if form.start_time.data:
                start_time = form.start_time.data
            
            quiz = Quiz(
                title=form.title.data,
                description=form.description.data,
                quiz_type=form.quiz_type.data,
                duration=form.duration.data,
                start_time=start_time,
                user_id=current_user.id,
                subject_id=form.subject_id.data
            )
            db.session.add(quiz)
            db.session.commit()
            
            # Create announcement for the new quiz
            from models import Announcement
            subject = Subject.query.get(form.subject_id.data)
            announcement = Announcement(
                title=f'New {quiz.quiz_type.capitalize()} Available',
                content=f'A new {quiz.quiz_type} "{quiz.title}" has been created for {subject.name}.',
                user_id=current_user.id,
                subject_id=subject.id,
                quiz_id=quiz.id,
                announcement_type='quiz_created'
            )
            db.session.add(announcement)
            db.session.commit()
            
            # Handle different creation methods
            if form.creation_method.data == 'manual':
                session['quiz_setup'] = {
                    'quiz_id': quiz.id,
                    'question_count': form.question_count.data,
                    'questions_added': 0
                }
                session.modified = True
                
                flash('Quiz setup complete. Now add your questions.')
                return redirect(url_for('quiz.add_question', quiz_id=quiz.id))
            elif form.creation_method.data == 'import':
                # Handle document import
                if not form.document_file.data:
                    flash('Please upload a document file.')
                    return render_template('quiz/setup.html', form=form)
                
                # Ensure the form has the correct enctype
                if not request.content_type or 'multipart/form-data' not in request.content_type:
                    flash('Form submission error: incorrect form type for file upload. Please ensure your browser supports file uploads.')
                    return render_template('quiz/setup.html', form=form)
                
                try:
                    # Import document processor
                    from document_import import import_questions
                    
                    # Create upload directory
                    import os
                    upload_dir = os.path.join('uploads', 'documents')
                    
                    # Ensure the upload directory exists
                    if not os.path.exists(upload_dir):
                        os.makedirs(upload_dir, exist_ok=True)
                    
                    # Process the document using the document_import module
                    print(f"Processing document with AI: {form.use_ai.data}")
                    questions, error = import_questions(form.document_file.data, upload_dir, use_ai=form.use_ai.data)
                    
                    # Log the result for debugging
                    print(f"Document processing result: {len(questions)} questions extracted, error: {error}")
                    
                    if error:
                        flash(f'Warning: {error} - Proceeding with extracted questions.')
                        if not questions:
                            flash('No questions could be extracted from the document.')
                            return render_template('quiz/setup.html', form=form)
                    
                    if not questions:
                        flash('No questions were found in the document.')
                        return render_template('quiz/setup.html', form=form)
                    
                    # Save the extracted questions
                    for q_data in questions:
                        question = Question(
                            quiz_id=quiz.id,
                            question_text=q_data['question_text'],
                            question_type=q_data['question_type'],
                            options=q_data.get('options'),
                            correct_answer=q_data.get('correct_answer', ''),
                            points=q_data.get('points', 1.0)
                        )
                        
                        if q_data['question_type'] == 'essay' and 'word_limit' in q_data:
                            question.word_limit = q_data['word_limit']
                            
                        db.session.add(question)
                    
                    db.session.commit()
                    flash(f'Successfully imported {len(questions)} questions from the document.')
                    
                    # Set up session for editing imported questions
                    session['quiz_setup'] = {
                        'quiz_id': quiz.id,
                        'question_count': len(questions),
                        'questions_added': len(questions),
                        'imported': True
                    }
                    session.modified = True
                    
                    # Redirect to a page where the user can review and edit the imported questions
                    try:
                        # Print debug information
                        print(f"Redirecting to review_imported_questions with quiz_id: {quiz.id}")
                        print(f"Number of questions imported: {len(questions)}")
                        
                        # Ensure the session is properly saved before redirecting
                        session.modified = True
                        
                        # Redirect to the review page
                        return redirect(url_for('quiz.review_imported_questions', quiz_id=quiz.id))
                    except Exception as redirect_error:
                        print(f"Redirect error: {str(redirect_error)}")
                        flash(f'Error redirecting to review page. Please check the quiz from your dashboard.')
                        return redirect(url_for('dashboard'))
                    
                except Exception as e:
                    db.session.rollback()
                    flash(f'Error importing questions: {str(e)}')
                    return render_template('quiz/setup.html', form=form)
            
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while creating the quiz: {str(e)}')
    
    return render_template('quiz/setup.html', form=form)

@quiz_bp.route('/add_question/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def add_question(quiz_id):
    if current_user.role != 'teacher':
        flash('Only teachers can add questions.')
        return redirect(url_for('dashboard'))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.user_id != current_user.id:
        flash('You do not have permission to modify this quiz.')
        return redirect(url_for('dashboard'))
    
    quiz_setup = session.get('quiz_setup')
    if not quiz_setup or quiz_setup.get('quiz_id') != quiz_id:
        flash('Quiz setup information not found.')
        return redirect(url_for('quiz.create_quiz'))
    
    questions_added = quiz_setup.get('questions_added', 0)
    total_questions = quiz_setup.get('question_count', 0)
    
    # Check if this is an imported quiz where we want to add more questions
    if quiz_setup.get('imported') and questions_added >= total_questions:
        # For imported quizzes, allow adding more questions
        total_questions += 1
        quiz_setup['question_count'] = total_questions
        session.modified = True
    elif questions_added >= total_questions:
        flash('All questions have been added.')
        session.pop('quiz_setup')
        return redirect(url_for('dashboard'))
    
    form = QuestionForm()
    form.quiz_id.data = quiz_id
    form.current_question.data = questions_added + 1
    form.total_questions.data = total_questions
    
    if form.validate_on_submit():
        try:
            # Handle different question types
            options = None
            correct_answer = form.correct_answer.data or ''
            word_limit = None
            
            if form.question_type.data == 'multiple_choice':
                # For multiple choice, use the individual option fields and correct_option
                options = []
                if form.option1.data:
                    options.append(form.option1.data)
                if form.option2.data:
                    options.append(form.option2.data)
                if form.option3.data:
                    options.append(form.option3.data)
                if form.option4.data:
                    options.append(form.option4.data)
                if form.option5.data:
                    options.append(form.option5.data)
                
                if len(options) < 2:
                    flash('Multiple choice questions must have at least 2 options.')
                    return render_template('quiz/add_question.html', form=form, 
                                        question_num=questions_added + 1, 
                                        total=total_questions,
                                        quiz=quiz)
                
                # Use correct_option for multiple choice
                if form.correct_option.data:
                    correct_answer = form.correct_option.data
            elif form.question_type.data == 'true_false':
                # For true/false, ensure we have a valid answer
                if not correct_answer in ['true', 'false']:
                    correct_answer = 'true'
            elif form.question_type.data == 'essay':
                # For essay questions, get the word limit
                word_limit = form.word_limit.data
            
            # Set default points if not provided
            points = form.points.data or 1
            
            question = Question(
                question_text=form.question_text.data,
                question_type=form.question_type.data,
                options=options,
                correct_answer=correct_answer,
                points=points,
                order_index=questions_added,
                user_id=current_user.id,
                quiz_id=quiz_id
            )
            
            # Set word_limit if it's an essay question
            if form.question_type.data == 'essay' and word_limit:
                question.word_limit = word_limit
                
            db.session.add(question)
            db.session.commit()
            
            quiz_setup['questions_added'] = questions_added + 1
            session.modified = True
            
            if quiz_setup.get('imported'):
                # For imported quizzes, redirect back to the review page
                flash('Question added successfully!')
                quiz_setup['questions_added'] = questions_added + 1
                session.modified = True
                return redirect(url_for('quiz.review_imported_questions', quiz_id=quiz_id))
            elif questions_added + 1 >= total_questions:
                flash('All questions have been added successfully!')
                session.pop('quiz_setup')
                return redirect(url_for('dashboard'))
            else:
                flash('Question added successfully!')
                return redirect(url_for('quiz.add_question', quiz_id=quiz_id))
                
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while adding the question: {str(e)}')
    
    return render_template('quiz/add_question.html', form=form, 
                         question_num=questions_added + 1, 
                         total=total_questions,
                         quiz=quiz)

@quiz_bp.route('/review_imported_questions/<int:quiz_id>', methods=['GET'])
@login_required
def review_imported_questions(quiz_id):
    if current_user.role != 'teacher':
        flash('Only teachers can review imported questions.')
        return redirect(url_for('dashboard'))
    
    try:
        # Print debug information
        print(f"Accessing review_imported_questions for quiz_id: {quiz_id}")
        
        quiz = Quiz.query.get_or_404(quiz_id)
        if quiz.user_id != current_user.id:
            flash('You do not have permission to view this quiz.')
            return redirect(url_for('dashboard'))
        
        # Get all questions for this quiz
        questions = Question.query.filter_by(quiz_id=quiz_id).all()
        print(f"Found {len(questions)} questions for quiz_id: {quiz_id}")
        
        # Check if we have questions
        if not questions:
            print(f"No questions found for quiz_id: {quiz_id}")
            flash('No questions were found for this quiz. Please try importing again or add questions manually.')
            return redirect(url_for('quiz.add_question', quiz_id=quiz_id))
        
        # Check if the template exists
        import os
        template_path = os.path.join('templates', 'quiz', 'review_imported_questions.html')
        if not os.path.exists(template_path):
            print(f"Template not found: {template_path}")
            flash('Error: Template not found. Redirecting to manual question entry.')
            return redirect(url_for('quiz.add_question', quiz_id=quiz_id))
        
        # Set session data for quiz setup if not already set
        if 'quiz_setup' not in session or session.get('quiz_setup', {}).get('quiz_id') != quiz_id:
            session['quiz_setup'] = {
                'quiz_id': quiz_id,
                'question_count': len(questions),
                'questions_added': len(questions),
                'imported': True
            }
            session.modified = True
            print(f"Set up session for imported quiz: {session['quiz_setup']}")
        
        return render_template('quiz/review_imported_questions.html', quiz=quiz, questions=questions)
    except Exception as e:
        print(f"Error in review_imported_questions: {str(e)}")
        flash(f'An error occurred while reviewing imported questions: {str(e)}')
        return redirect(url_for('dashboard'))

@quiz_bp.route('/update_imported_question/<int:question_id>', methods=['POST'])
@login_required
def update_imported_question(question_id):
    if current_user.role != 'teacher':
        flash('Only teachers can update questions.')
        return redirect(url_for('dashboard'))
    
    question = Question.query.get_or_404(question_id)
    quiz = Quiz.query.get_or_404(question.quiz_id)
    
    if quiz.user_id != current_user.id:
        flash('You do not have permission to modify this question.')
        return redirect(url_for('dashboard'))
    
    try:
        # Update question text
        question.question_text = request.form.get('question_text')
        question.question_type = request.form.get('question_type')
        question.points = request.form.get('points', 1, type=int)
        
        # Handle different question types
        if question.question_type == 'multiple_choice':
            options = []
            for i in range(1, 6):
                option = request.form.get(f'option{i}')
                if option:
                    options.append(option)
            
            question.options = options
            question.correct_answer = request.form.get('correct_option')
            
        elif question.question_type == 'true_false':
            question.correct_answer = request.form.get('true_false_answer')
            
        elif question.question_type == 'identification':
            question.correct_answer = request.form.get('correct_answer')
            
        elif question.question_type == 'essay':
            question.word_limit = request.form.get('word_limit', 500, type=int)
        
        db.session.commit()
        flash('Question updated successfully!')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating question: {str(e)}')
    
    return redirect(url_for('quiz.review_imported_questions', quiz_id=quiz.id))

@quiz_bp.route('/delete_imported_question/<int:question_id>', methods=['POST'])
@login_required
def delete_imported_question(question_id):
    if current_user.role != 'teacher':
        flash('Only teachers can delete questions.')
        return redirect(url_for('dashboard'))
    
    question = Question.query.get_or_404(question_id)
    quiz_id = question.quiz_id
    quiz = Quiz.query.get_or_404(quiz_id)
    
    if quiz.user_id != current_user.id:
        flash('You do not have permission to delete this question.')
        return redirect(url_for('dashboard'))
    
    try:
        db.session.delete(question)
        db.session.commit()
        flash('Question deleted successfully!')
        
        # Check if there are any questions left
        remaining_questions = Question.query.filter_by(quiz_id=quiz_id).count()
        if remaining_questions == 0:
            # If no questions left, delete the quiz
            db.session.delete(quiz)
            db.session.commit()
            flash('Quiz deleted as it had no questions.')
            return redirect(url_for('dashboard'))
            
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting question: {str(e)}')
    
    return redirect(url_for('quiz.review_imported_questions', quiz_id=quiz_id))

@quiz_bp.route('/cancel_quiz/<int:quiz_id>', methods=['POST', 'GET'])
@login_required
def cancel_quiz(quiz_id):
    if current_user.role != 'teacher':
        flash('Only teachers can cancel quizzes/exams.')
        return redirect(url_for('dashboard'))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.user_id != current_user.id:
        flash('You do not have permission to cancel this quiz.')
        return redirect(url_for('dashboard'))
    
    try:
        # Delete all questions associated with this quiz
        Question.query.filter_by(quiz_id=quiz_id).delete()
        
        # Delete the quiz itself
        db.session.delete(quiz)
        db.session.commit()
        
        # Clear the quiz setup from session if it exists
        if 'quiz_setup' in session:
            session.pop('quiz_setup')
            session.modified = True
        
        flash('Quiz creation cancelled successfully.')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while cancelling the quiz: {str(e)}')
    
    return redirect(url_for('dashboard'))