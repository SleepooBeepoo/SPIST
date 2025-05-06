from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, IntegerField, FloatField, FieldList, FormField, HiddenField, BooleanField
from wtforms.validators import DataRequired, Optional, NumberRange, Length
from datetime import datetime
from models import db, Quiz, Question, Subject
from question_forms import get_question_form
from document_processor import DocumentProcessor
import os

quiz_bp = Blueprint('quiz', __name__)

# Step 1: Basic Quiz Setup Form
class QuizSetupForm(FlaskForm):
    title = StringField('Quiz Title', validators=[DataRequired(), Length(max=100)])
    subject_id = SelectField('Subject', validators=[DataRequired()], coerce=int)
    quiz_type = SelectField('Type', choices=[('quiz', 'Quiz'), ('exam', 'Exam')], validators=[DataRequired()])
    creation_method = SelectField('Creation Method', 
                               choices=[('manual', 'Create Manually'), ('import', 'Import from Document')],
                               default='manual')
    question_count = IntegerField('Number of Questions', validators=[Optional(), NumberRange(min=1, max=50)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    duration = IntegerField('Time Limit (minutes)', validators=[Optional(), NumberRange(min=1)])
    start_time = StringField('Start Time (YYYY-MM-DD HH:MM)', validators=[Optional()])
    document_file = FileField('Import Questions from Document', 
                            validators=[Optional(), FileAllowed(['docx', 'pdf'], 'Only .docx and .pdf files are allowed!')])
    use_ai = BooleanField('Use AI to analyze document (recommended)', default=True)

# Step 2: Question Form (base for all question types)
class BaseQuestionForm(FlaskForm):
    quiz_id = HiddenField('Quiz ID', validators=[DataRequired()])
    current_question = HiddenField('Current Question', validators=[DataRequired()])
    total_questions = HiddenField('Total Questions', validators=[DataRequired()])
    question_text = TextAreaField('Question Text', validators=[DataRequired(), Length(max=500)])
    question_type = SelectField('Question Type', choices=[
        ('multiple_choice', 'Multiple Choice'),
        ('identification', 'Identification'),
        ('true_false', 'True/False'),
        ('essay', 'Essay')
    ], validators=[DataRequired()])
    points = FloatField('Points', validators=[DataRequired(), NumberRange(min=0.1)], default=1.0)

# Multiple Choice Question Form
class MultipleChoiceQuestionForm(BaseQuestionForm):
    option1 = StringField('Option 1', validators=[DataRequired(), Length(max=200)])
    option2 = StringField('Option 2', validators=[DataRequired(), Length(max=200)])
    option3 = StringField('Option 3', validators=[DataRequired(), Length(max=200)])
    option4 = StringField('Option 4', validators=[DataRequired(), Length(max=200)])
    correct_option = SelectField('Correct Answer', choices=[
        ('0', 'Option 1'),
        ('1', 'Option 2'),
        ('2', 'Option 3'),
        ('3', 'Option 4')
    ], validators=[DataRequired()])

# Identification Question Form
class IdentificationQuestionForm(BaseQuestionForm):
    correct_answer = StringField('Correct Answer', validators=[DataRequired(), Length(max=200)])

# True/False Question Form
class TrueFalseQuestionForm(BaseQuestionForm):
    correct_answer = SelectField('Correct Answer',
        choices=[('true', 'True'), ('false', 'False')],
        validators=[DataRequired()]
    )

# Essay Question Form
class EssayQuestionForm(BaseQuestionForm):
    word_limit = IntegerField('Word Limit', validators=[Optional(), NumberRange(min=1)], default=500)
    correct_answer = TextAreaField('Sample Answer (For Teacher Reference Only)', validators=[Optional(), Length(max=2000)])

# Get the appropriate question form based on question type
def get_question_form_class(question_type):
    form_map = {
        'multiple_choice': MultipleChoiceQuestionForm,
        'identification': IdentificationQuestionForm,
        'true_false': TrueFalseQuestionForm,
        'essay': EssayQuestionForm
    }
    return form_map.get(question_type, MultipleChoiceQuestionForm)

# Step 1: Quiz Setup
@quiz_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_quiz():
    if current_user.role != 'teacher':
        flash('Only teachers can create quizzes/exams.')
        return redirect(url_for('dashboard'))
    
    # Get all subjects taught by the teacher
    subjects = Subject.query.filter_by(teacher_id=current_user.id).all()
    if not subjects:
        flash('You need to create a subject before creating a quiz/exam.')
        return redirect(url_for('dashboard'))
    
    # Initialize the form
    form = QuizSetupForm()
    form.subject_id.choices = [(s.id, s.name) for s in subjects]
    
    # Handle form submission
    if form.validate_on_submit():
        try:
            # Parse start time if provided
            start_time = None
            if form.start_time.data:
                try:
                    start_time = datetime.fromisoformat(form.start_time.data.replace('Z', '+00:00'))
                except ValueError:
                    flash('Invalid date format. Please use YYYY-MM-DD HH:MM format.')
                    return render_template('quiz/setup.html', form=form)
            
            # Create the quiz
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
            
            # Check if we're importing questions from a document
            if form.creation_method.data == 'import' and form.document_file.data:
                # Process the document file
                return process_imported_document(form, quiz)
            else:
                # Manual creation - validate question count
                if not form.question_count.data or form.question_count.data < 1:
                    db.session.delete(quiz)
                    db.session.commit()
                    flash('Please specify the number of questions for manual creation.')
                    return render_template('quiz/setup.html', form=form)
                
                # Redirect to the first question for manual creation
                return redirect(url_for('quiz.add_question', quiz_id=quiz.id, question_num=1, total=form.question_count.data))
        
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while creating the quiz: {str(e)}')
    
    return render_template('quiz/setup.html', form=form)

def process_imported_document(form, quiz):
    """Process an imported document file to extract questions"""
    try:
        # Get the uploaded file
        file = form.document_file.data
        
        # Create uploads directory if it doesn't exist
        uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir, exist_ok=True)
        
        # Initialize document processor
        processor = DocumentProcessor()
        
        # Save the uploaded file
        file_path = processor.save_uploaded_file(file, uploads_dir)
        
        # Process the file to extract questions
        questions_data, error = processor.process_file(file_path)
        
        if error:
            db.session.delete(quiz)
            db.session.commit()
            flash(f'Error processing document: {error}')
            return redirect(url_for('quiz.create_quiz'))
        
        if not questions_data:
            db.session.delete(quiz)
            db.session.commit()
            flash('No questions could be extracted from the document.')
            return redirect(url_for('quiz.create_quiz'))
        
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
                        options = ['Option 1', 'Option 2', 'Option 3', 'Option 4']
                    question.options = options
                    
                    # Ensure correct_answer is a string
                    correct_answer = q_data.get('correct_answer', '0')
                    if correct_answer is None:
                        correct_answer = '0'
                    question.correct_answer = str(correct_answer)
                    
                elif q_data.get('question_type') == 'true_false':
                    correct_answer = q_data.get('correct_answer', 'true')
                    if correct_answer not in ['true', 'false']:
                        correct_answer = 'true'
                    question.correct_answer = correct_answer
                    
                elif q_data.get('question_type') == 'identification':
                    question.correct_answer = q_data.get('correct_answer', '')
                    
                elif q_data.get('question_type') == 'essay':
                    question.word_limit = int(q_data.get('word_limit', 500))
                    question.correct_answer = q_data.get('correct_answer', '')
                
                # Add to database
                db.session.add(question)
                question_count += 1
            except Exception as e:
                print(f"Error creating question: {str(e)}")
                continue
        
        # Commit all questions
        db.session.commit()
        
        # Check if any questions were created
        if question_count == 0:
            db.session.delete(quiz)
            db.session.commit()
            flash('No valid questions could be created from the document.')
            return redirect(url_for('quiz.create_quiz'))
        
        flash(f'Successfully imported {question_count} questions into {quiz.quiz_type} "{quiz.title}"!')
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        # Clean up on error
        if quiz and quiz.id:
            try:
                db.session.delete(quiz)
                db.session.commit()
            except:
                db.session.rollback()
        
        flash(f'An error occurred while importing questions: {str(e)}')
        return redirect(url_for('quiz.create_quiz'))

# Step 2: Add Questions
@quiz_bp.route('/add_question/<int:quiz_id>/<int:question_num>/<int:total>', methods=['GET', 'POST'])
@login_required
def add_question(quiz_id, question_num, total):
    if current_user.role != 'teacher':
        flash('Only teachers can add questions.')
        return redirect(url_for('dashboard'))
    
    # Verify the quiz exists and belongs to the current user
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.user_id != current_user.id:
        flash('You do not have permission to modify this quiz.')
        return redirect(url_for('dashboard'))
    
    # Determine question type (default to multiple choice)
    question_type = request.args.get('type', 'multiple_choice')
    
    # Get the appropriate form class
    FormClass = get_question_form_class(question_type)
    
    # Initialize the form
    form = FormClass()
    form.quiz_id.data = quiz_id
    form.current_question.data = question_num
    form.total_questions.data = total
    
    # Handle form submission
    if form.validate_on_submit():
        try:
            # Create the question
            question = Question(
                question_text=form.question_text.data,
                question_type=form.question_type.data,
                points=form.points.data,
                user_id=current_user.id,
                quiz_id=quiz_id,
                subject_id=quiz.subject_id,
                order_index=question_num - 1  # 0-indexed in database
            )
            
            # Set question-type specific fields
            if form.question_type.data == 'multiple_choice':
                question.options = [
                    form.option1.data,
                    form.option2.data,
                    form.option3.data,
                    form.option4.data
                ]
                question.correct_answer = form.correct_option.data
            elif form.question_type.data == 'identification':
                question.correct_answer = form.correct_answer.data
            elif form.question_type.data == 'true_false':
                question.correct_answer = form.correct_answer.data
            elif form.question_type.data == 'essay':
                question.word_limit = form.word_limit.data
                question.correct_answer = form.correct_answer.data or ''
            
            # Save the question
            db.session.add(question)
            db.session.commit()
            
            # Check if we've added all questions
            if question_num >= total:
                flash(f'Quiz "{quiz.title}" created successfully with {total} questions!')
                return redirect(url_for('dashboard'))
            
            # Redirect to the next question
            flash(f'Question {question_num} added successfully. Please add question {question_num + 1}.')
            return redirect(url_for('quiz.add_question', quiz_id=quiz_id, question_num=question_num + 1, total=total))
        
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while adding the question: {str(e)}')
    
    return render_template('quiz/add_question.html', form=form, quiz=quiz, question_num=question_num, total=total)

# Cancel quiz creation
@quiz_bp.route('/cancel/<int:quiz_id>', methods=['POST'])
@login_required
def cancel_quiz(quiz_id):
    if current_user.role != 'teacher':
        flash('Only teachers can manage quizzes.')
        return redirect(url_for('dashboard'))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.user_id != current_user.id:
        flash('You do not have permission to delete this quiz.')
        return redirect(url_for('dashboard'))
    
    try:
        # Delete all questions associated with this quiz
        Question.query.filter_by(quiz_id=quiz_id).delete()
        
        # Delete the quiz
        db.session.delete(quiz)
        db.session.commit()
        
        flash('Quiz creation cancelled.')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {str(e)}')
    
    return redirect(url_for('dashboard'))

# Register the blueprint
def init_app(app):
    app.register_blueprint(quiz_bp, url_prefix='/quiz')