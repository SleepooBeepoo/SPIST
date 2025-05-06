from flask import render_template, redirect, url_for, flash, request, Blueprint, jsonify, session
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from app.models import db, Quiz, Question
from app.import_document.forms import QuestionForm
from app.import_document import import_document_bp
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, IntegerField, BooleanField
from wtforms.validators import DataRequired, Optional

# Document import form
class DocumentImportForm(FlaskForm):
    title = StringField('Quiz/Exam Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    quiz_type = SelectField('Type', choices=[
        ('quiz', 'Quiz'),
        ('exam', 'Exam')
    ], validators=[DataRequired()])
    subject_id = SelectField('Subject', coerce=int, validators=[DataRequired()])
    duration = IntegerField('Duration (minutes)', validators=[Optional()])
    document_file = FileField('Document File', validators=[
        FileRequired(),
        FileAllowed(['docx', 'pdf'], 'Only .docx and .pdf files are allowed!')
    ])
    use_ai = BooleanField('Use AI to enhance question extraction', default=True)

@import_document_bp.route('/', methods=['GET', 'POST'])
@login_required
def import_document():
    """Import questions from a document"""
    if current_user.role != 'teacher':
        flash('Only teachers can import documents.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Create form and populate subject choices
    from app.models import Subject
    form = DocumentImportForm()
    subjects = Subject.query.filter_by(teacher_id=current_user.id).all()
    form.subject_id.choices = [(s.id, s.name) for s in subjects]
    
    if form.validate_on_submit():
        # Process document upload and extraction (placeholder)
        # In a real implementation, this would extract questions from the document
        
        # Create a new quiz
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
        
        # Store quiz ID in session for the review page
        session['imported_quiz_id'] = quiz.id
        
        # Redirect to review page where batch operations can be performed
        flash('Document uploaded successfully. Please review the extracted questions.', 'success')
        return redirect(url_for('import_document.review_imported', quiz_id=quiz.id))
    
    return render_template('import_document/import.html', form=form)

@import_document_bp.route('/review/<int:quiz_id>', methods=['GET'])
@login_required
def review_imported(quiz_id):
    """Review and manage imported questions"""
    if current_user.role != 'teacher':
        flash('Only teachers can review imported documents.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Get the quiz and verify ownership
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.user_id != current_user.id:
        flash('You do not have permission to review this quiz.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Get all questions for this quiz
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    
    return render_template('import_document/review_imported.html',
                          quiz=quiz,
                          questions=questions)

@import_document_bp.route('/batch_delete/<int:quiz_id>', methods=['POST'])
@login_required
def batch_delete(quiz_id):
    """Delete multiple questions at once during import review"""
    # Ensure the user is a teacher
    if current_user.role != 'teacher':
        flash('Only teachers can delete questions.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Get the quiz and verify ownership
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.user_id != current_user.id:
        flash('You do not have permission to manage this quiz.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Get the selected question IDs
    selected_questions = request.form.getlist('selected_questions')
    
    if not selected_questions:
        flash('No questions selected for deletion.', 'warning')
        return redirect(url_for('import_document.review_imported', quiz_id=quiz_id))
    
    try:
        # Delete the selected questions
        deleted_count = 0
        for question_id in selected_questions:
            question = Question.query.get(question_id)
            if question and question.quiz_id == quiz_id:
                db.session.delete(question)
                deleted_count += 1
        
        db.session.commit()
        flash(f'Successfully deleted {deleted_count} question(s).', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting questions: {str(e)}', 'danger')
    
    return redirect(url_for('import_document.review_imported', quiz_id=quiz_id))

@import_document_bp.route('/update_questions/<int:quiz_id>', methods=['POST'])
@login_required
def update_questions(quiz_id):
    """Update multiple questions at once during import review"""
    # Ensure the user is a teacher
    if current_user.role != 'teacher':
        flash('Only teachers can update questions.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Get the quiz and verify ownership
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.user_id != current_user.id:
        flash('You do not have permission to manage this quiz.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    try:
        updated_count = 0
        # Process form data for individual question updates
        for key, value in request.form.items():
            if key.startswith('question_text_'):
                question_id = key.split('_')[-1]
                question = Question.query.get(question_id)
                
                if question and question.quiz_id == quiz_id:
                    # Update question text
                    question.question_text = value
                    
                    # Update points if provided
                    points_key = f'points_{question_id}'
                    if points_key in request.form:
                        try:
                            question.points = float(request.form[points_key])
                        except ValueError:
                            pass
                    
                    updated_count += 1
        
        # Handle batch updates for selected questions
        selected_questions = request.form.getlist('selected_questions')
        if selected_questions and ('question_text' in request.form or 'points' in request.form):
            for question_id in selected_questions:
                question = Question.query.get(question_id)
                if question and question.quiz_id == quiz_id:
                    # Update question properties if provided
                    if 'question_text' in request.form:
                        question.question_text = request.form['question_text']
                    if 'points' in request.form:
                        question.points = float(request.form['points'])
                    updated_count += 1
        
        db.session.commit()
        flash(f'Successfully updated {updated_count} question(s).', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating questions: {str(e)}', 'danger')
    
    return redirect(url_for('import_document.review_imported', quiz_id=quiz_id))