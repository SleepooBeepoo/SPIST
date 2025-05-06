"""Routes for question module"""
from flask import render_template, redirect, url_for, flash, request, Blueprint
from flask_login import login_required, current_user
from app.models import Question, Quiz
from app.question.forms import get_question_form, BaseQuestionForm
from app.question.services import QuestionService
import json
import logging

question_bp = Blueprint('question', __name__)

@question_bp.route('/bank')
@login_required
def question_bank():
    """View all questions created by the current teacher"""
    if not current_user.is_teacher():
        flash('Only teachers can access the question bank.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    questions = QuestionService.get_questions_by_teacher(current_user.id)
    return render_template('auth/question_bank.html', questions=questions, title='Question Bank')

@question_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_question():
    """Create a new standalone question for the question bank"""
    if not current_user.is_teacher():
        flash('Only teachers can create questions.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Initialize form based on question type
    question_type = request.form.get('question_type', 'multiple_choice')
    form = get_question_form(question_type)
    
    if request.method == 'POST' and form.validate_on_submit():
        try:
            # Process form data based on question type
            options = None
            correct_answer = None
            word_limit = None
            
            if question_type == 'multiple_choice':
                options = [option.data for option in form.options]
                correct_answer = options[int(form.correct_option.data)]
            elif question_type == 'identification':
                correct_answer = form.correct_answer.data
            elif question_type == 'true_false':
                correct_answer = form.correct_answer.data
            elif question_type == 'essay':
                correct_answer = 'Essay question - manual grading required'
                word_limit = form.word_limit.data
            
            # Create question
            success, message, question = QuestionService.create_question(
                question_text=form.question_text.data,
                question_type=question_type,
                options=options,
                correct_answer=correct_answer,
                points=form.points.data,
                user_id=current_user.id,
                word_limit=word_limit,
                order_index=form.order_index.data
            )
            
            if success:
                flash(message, 'success')
                return redirect(url_for('question.question_bank'))
            else:
                flash(message, 'danger')
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'danger')
    
    return render_template('auth/add_question.html', form=form, standalone=True, title='Create Question')

@question_bp.route('/edit/<int:question_id>', methods=['GET', 'POST'])
@login_required
def edit_question(question_id):
    """Edit an existing question"""
    if not current_user.is_teacher():
        flash('Only teachers can edit questions.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Get the question
    question = QuestionService.get_question_by_id(question_id)
    if not question:
        flash('Question not found.', 'danger')
        return redirect(url_for('question.question_bank'))
    
    # Check if user has permission to edit this question
    if question.user_id != current_user.id:
        flash('You do not have permission to edit this question.', 'danger')
        return redirect(url_for('question.question_bank'))
    
    # Initialize form based on question type
    form = get_question_form(question.question_type)
    
    if request.method == 'GET':
        # Populate form with question data
        form.question_text.data = question.question_text
        form.question_type.data = question.question_type
        form.points.data = question.points
        form.order_index.data = question.order_index
        
        if question.question_type == 'multiple_choice' and question.options:
            options = json.loads(question.options)
            for i, option in enumerate(options):
                if i < len(form.options):
                    form.options[i].data = option
            
            # Find index of correct answer in options
            try:
                correct_index = options.index(question.correct_answer)
                form.correct_option.data = str(correct_index)
            except ValueError:
                pass
        elif question.question_type in ['identification', 'true_false']:
            form.correct_answer.data = question.correct_answer
        elif question.question_type == 'essay' and question.word_limit:
            form.word_limit.data = question.word_limit
    
    if request.method == 'POST' and form.validate_on_submit():
        try:
            # Process form data based on question type
            options = None
            correct_answer = None
            word_limit = None
            
            if question.question_type == 'multiple_choice':
                options = [option.data for option in form.options]
                correct_answer = options[int(form.correct_option.data)]
            elif question.question_type in ['identification', 'true_false']:
                correct_answer = form.correct_answer.data
            elif question.question_type == 'essay':
                correct_answer = 'Essay question - manual grading required'
                word_limit = form.word_limit.data
            
            # Update question
            success, message, updated_question = QuestionService.update_question(
                question_id=question_id,
                question_text=form.question_text.data,
                question_type=question.question_type,  # Don't allow changing question type
                options=options,
                correct_answer=correct_answer,
                points=form.points.data,
                word_limit=word_limit
            )
            
            if success:
                flash(message, 'success')
                return redirect(url_for('question.question_bank'))
            else:
                flash(message, 'danger')
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'danger')
    
    return render_template('auth/edit_question.html', form=form, question=question, title='Edit Question')

@question_bp.route('/delete/<int:question_id>', methods=['POST'])
@login_required
def delete_question(question_id):
    """Delete a question"""
    if not current_user.is_teacher():
        flash('Only teachers can delete questions.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Get the question
    question = QuestionService.get_question_by_id(question_id)
    if not question:
        flash('Question not found.', 'danger')
        return redirect(url_for('question.question_bank'))
    
    # Check if user has permission to delete this question
    if question.user_id != current_user.id:
        flash('You do not have permission to delete this question.', 'danger')
        return redirect(url_for('question.question_bank'))
    
    # Check if question is part of a quiz
    if question.quiz_id:
        flash('Cannot delete a question that is part of a quiz.', 'danger')
        return redirect(url_for('question.question_bank'))
    
    success, message = QuestionService.delete_question(question_id)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('question.question_bank'))