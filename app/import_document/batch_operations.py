from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from app.models import db, Quiz, Question
from app.import_document.forms import QuestionForm

batch_bp = Blueprint('batch_operations', __name__, url_prefix='/batch')

@batch_bp.route('/manage_questions/<int:quiz_id>', methods=['GET'])
@login_required
def manage_questions(quiz_id):
    """Display the batch operations interface for managing questions"""
    # Ensure the user is a teacher
    if current_user.role != 'teacher':
        flash('Only teachers can access this page.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Get the quiz and verify ownership
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.user_id != current_user.id:
        flash('You do not have permission to manage this quiz.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Get all questions for this quiz
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    
    return render_template('import_document/batch_operations.html',
                          quiz=quiz,
                          questions=questions)

@batch_bp.route('/batch_delete/<int:quiz_id>', methods=['POST'])
@login_required
def batch_delete(quiz_id):
    """Delete multiple questions at once"""
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
        return redirect(url_for('batch_operations.manage_questions', quiz_id=quiz_id))
    
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
    
    return redirect(url_for('batch_operations.manage_questions', quiz_id=quiz_id))

@batch_bp.route('/batch_edit/<int:quiz_id>', methods=['GET'])
@login_required
def batch_edit(quiz_id):
    """Display the batch edit interface for multiple questions"""
    # Ensure the user is a teacher
    if current_user.role != 'teacher':
        flash('Only teachers can edit questions.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Get the quiz and verify ownership
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.user_id != current_user.id:
        flash('You do not have permission to manage this quiz.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Get the selected question IDs from the request
    selected_questions = request.args.getlist('selected_questions')
    
    if not selected_questions:
        flash('No questions selected for editing.', 'warning')
        return redirect(url_for('batch_operations.manage_questions', quiz_id=quiz_id))
    
    # Get the questions and verify they belong to this quiz
    questions = Question.query.filter(Question.id.in_(selected_questions), Question.quiz_id == quiz_id).all()
    
    if not questions:
        flash('No valid questions found for editing.', 'warning')
        return redirect(url_for('batch_operations.manage_questions', quiz_id=quiz_id))
    
    return render_template('import_document/batch_edit.html',
                          quiz=quiz,
                          questions=questions)

@batch_bp.route('/update_questions/<int:quiz_id>', methods=['POST'])
@login_required
def update_questions(quiz_id):
    """Update multiple questions at once"""
    # Ensure the user is a teacher
    if current_user.role != 'teacher':
        flash('Only teachers can update questions.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Get the quiz and verify ownership
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.user_id != current_user.id:
        flash('You do not have permission to manage this quiz.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Process the form data
    try:
        updated_count = 0
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
        
        db.session.commit()
        flash(f'Successfully updated {updated_count} question(s).', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating questions: {str(e)}', 'danger')
    
    return redirect(url_for('batch_operations.manage_questions', quiz_id=quiz_id))