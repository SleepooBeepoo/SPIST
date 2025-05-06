"""Import Document Module

This module provides a separate workflow for importing questions from document files.
It includes dedicated routes and handlers for the document import process.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, SelectField, IntegerField, BooleanField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from models import db, Quiz, Question, Subject
import os
from werkzeug.utils import secure_filename
from document_processor import DocumentProcessor

# Create blueprint for document import functionality
import_document_bp = Blueprint('import_document', __name__)

# Form for document import
class DocumentImportForm(FlaskForm):
    title = StringField('Quiz Title', validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    quiz_type = SelectField('Quiz Type', choices=[('quiz', 'Quiz'), ('exam', 'Exam')], validators=[DataRequired()])
    subject_id = SelectField('Subject', coerce=int, validators=[DataRequired()])
    duration = IntegerField('Duration (minutes)', validators=[Optional(), NumberRange(min=1, max=180)])
    document_file = FileField('Document File', validators=[FileRequired(), FileAllowed(['docx', 'pdf'], 'Only .docx and .pdf files are allowed!')])
    use_ai = BooleanField('Use AI to analyze document', default=True)

@import_document_bp.route('/import', methods=['GET', 'POST'])
@login_required
def import_document():
    """Handle document import for quiz/exam creation"""
    if current_user.role != 'teacher':
        flash('Only teachers can import documents for quizzes/exams.')
        return redirect(url_for('dashboard'))
    
    # Get subjects taught by the teacher
    subjects = Subject.query.filter_by(teacher_id=current_user.id).all()
    if not subjects:
        flash('You need to create a subject before importing a document.')
        return redirect(url_for('dashboard'))
    
    # Initialize form
    form = DocumentImportForm()
    form.subject_id.choices = [(s.id, s.name) for s in subjects]
    
    if form.validate_on_submit():
        try:
            # Create the quiz
            quiz = Quiz(
                title=form.title.data,
                description=form.description.data,
                quiz_type=form.quiz_type.data,
                duration=form.duration.data,
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
            
            # Process the document file
            if not form.document_file.data:
                flash('Please upload a document file.')
                return render_template('import_document/import.html', form=form)
            
            # Create upload directory
            upload_dir = os.path.join('uploads', 'documents')
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir, exist_ok=True)
            
            # Initialize document processor
            processor = DocumentProcessor()
            
            # Save the uploaded file
            file = form.document_file.data
            file_path = processor.save_uploaded_file(file, upload_dir)
            
            # Process the file to extract questions
            print(f"Processing document with AI: {form.use_ai.data}")
            questions_data, error = processor.process_file(file_path, use_ai=form.use_ai.data)
            
            # Log the result for debugging
            print(f"Document processing result: {len(questions_data)} questions extracted, error: {error}")
            
            if error:
                flash(f'Warning: {error} - Proceeding with extracted questions.')
                if not questions_data:
                    flash('No questions could be extracted from the document.')
                    db.session.delete(quiz)
                    db.session.commit()
                    return render_template('import_document/import.html', form=form)
            
            if not questions_data:
                flash('No questions were found in the document.')
                db.session.delete(quiz)
                db.session.commit()
                return render_template('import_document/import.html', form=form)
            
            # Save the extracted questions
            for index, q_data in enumerate(questions_data):
                question = Question(
                    quiz_id=quiz.id,
                    question_text=q_data.get('question_text', 'No question text'),
                    question_type=q_data.get('question_type', 'essay'),
                    options=q_data.get('options'),
                    correct_answer=q_data.get('correct_answer', ''),
                    points=float(q_data.get('points', 1.0)),
                    order_index=index,
                    user_id=current_user.id
                )
                
                if q_data.get('question_type') == 'essay' and 'word_limit' in q_data:
                    question.word_limit = q_data.get('word_limit')
                    
                db.session.add(question)
            
            db.session.commit()
            flash(f'Successfully imported {len(questions_data)} questions from the document.')
            
            # Store quiz info in session for the review page
            session['imported_quiz'] = {
                'quiz_id': quiz.id,
                'question_count': len(questions_data)
            }
            session.modified = True
            
            # Redirect to the review page
            return redirect(url_for('import_document.review_questions', quiz_id=quiz.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error importing document: {str(e)}')
    
    return render_template('import_document/import.html', form=form)

@import_document_bp.route('/review/<int:quiz_id>', methods=['GET'])
@login_required
def review_questions(quiz_id):
    """Review imported questions"""
    if current_user.role != 'teacher':
        flash('Only teachers can review imported questions.')
        return redirect(url_for('dashboard'))
    
    # Get the quiz
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.user_id != current_user.id:
        flash('You do not have permission to view this quiz.')
        return redirect(url_for('dashboard'))
    
    # Get all questions for this quiz
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    
    # Check if we have questions
    if not questions:
        flash('No questions were found for this quiz.')
        return redirect(url_for('dashboard'))
    
    return render_template('import_document/review.html', quiz=quiz, questions=questions)

@import_document_bp.route('/update_question/<int:question_id>', methods=['POST'])
@login_required
def update_question(question_id):
    """Update an imported question"""
    if current_user.role != 'teacher':
        flash('Only teachers can update questions.')
        return redirect(url_for('dashboard'))
    
    # Get the question
    question = Question.query.get_or_404(question_id)
    quiz = Quiz.query.get_or_404(question.quiz_id)
    
    if quiz.user_id != current_user.id:
        flash('You do not have permission to modify this question.')
        return redirect(url_for('dashboard'))
    
    try:
        # Update question text
        question.question_text = request.form.get('question_text')
        question.question_type = request.form.get('question_type')
        question.points = float(request.form.get('points', 1.0))
        
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
            question.word_limit = int(request.form.get('word_limit', 500))
        
        db.session.commit()
        flash('Question updated successfully!')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating question: {str(e)}')
    
    return redirect(url_for('import_document.review_questions', quiz_id=quiz.id))

@import_document_bp.route('/delete_question/<int:question_id>', methods=['POST'])
@login_required
def delete_question(question_id):
    """Delete an imported question"""
    if current_user.role != 'teacher':
        flash('Only teachers can delete questions.')
        return redirect(url_for('dashboard'))
    
    # Get the question
    question = Question.query.get_or_404(question_id)
    quiz = Quiz.query.get_or_404(question.quiz_id)
    
    if quiz.user_id != current_user.id:
        flash('You do not have permission to delete this question.')
        return redirect(url_for('dashboard'))
    
    try:
        # Delete the question
        quiz_id = question.quiz_id
        db.session.delete(question)
        db.session.commit()
        flash('Question deleted successfully!')
        
        # Check if there are any questions left
        remaining_questions = Question.query.filter_by(quiz_id=quiz_id).count()
        if remaining_questions == 0:
            # Delete the quiz if no questions remain
            quiz = Quiz.query.get(quiz_id)
            if quiz:
                db.session.delete(quiz)
                db.session.commit()
                flash('Quiz deleted as it had no questions.')
                return redirect(url_for('dashboard'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting question: {str(e)}')
    
    return redirect(url_for('import_document.review_questions', quiz_id=quiz.id))

@import_document_bp.route('/add_question/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def add_question(quiz_id):
    """Add a new question to an imported quiz"""
    if current_user.role != 'teacher':
        flash('Only teachers can add questions.')
        return redirect(url_for('dashboard'))
    
    # Get the quiz
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.user_id != current_user.id:
        flash('You do not have permission to modify this quiz.')
        return redirect(url_for('dashboard'))
    
    # Use the existing question form from quiz_module
    from quiz_module import QuestionForm
    form = QuestionForm()
    form.quiz_id.data = quiz_id
    
    # Get the current question count
    question_count = Question.query.filter_by(quiz_id=quiz_id).count()
    
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
                    return render_template('import_document/add_question.html', form=form, quiz=quiz)
                
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
                order_index=question_count,
                user_id=current_user.id,
                quiz_id=quiz_id
            )
            
            # Set word_limit if it's an essay question
            if form.question_type.data == 'essay' and word_limit:
                question.word_limit = word_limit
                
            db.session.add(question)
            db.session.commit()
            
            flash('Question added successfully!')
            return redirect(url_for('import_document.review_questions', quiz_id=quiz_id))
                
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while adding the question: {str(e)}')
    
    return render_template('import_document/add_question.html', form=form, quiz=quiz)

@import_document_bp.route('/finish/<int:quiz_id>', methods=['POST'])
@login_required
def finish_import(quiz_id):
    """Finish the import process"""
    if current_user.role != 'teacher':
        flash('Only teachers can finish the import process.')
        return redirect(url_for('dashboard'))
    
    # Get the quiz
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.user_id != current_user.id:
        flash('You do not have permission to modify this quiz.')
        return redirect(url_for('dashboard'))
    
    # Clear the session data
    if 'imported_quiz' in session:
        session.pop('imported_quiz')
    
    flash('Quiz import completed successfully!')
    return redirect(url_for('dashboard'))