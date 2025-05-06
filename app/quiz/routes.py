"""Routes for quiz module"""
from flask import render_template, redirect, url_for, flash, request, session, Blueprint
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from app.models import db, Quiz, Question, Subject, Announcement, QuizSubmission, StudentSubmission
from app.quiz.forms import QuizSetupForm, get_question_form
from app.quiz.services import QuizService
from datetime import datetime
import json
import logging

quiz_bp = Blueprint('quiz', __name__)

# Additional routes for teacher review interface

@quiz_bp.route('/review_submissions/<int:quiz_id>', methods=['GET'])
@login_required
def review_submissions(quiz_id):
    """Display the teacher review interface for manually grading submissions"""
    # Ensure the user is a teacher
    if current_user.role != 'teacher':
        flash('Only teachers can access this page.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Get the quiz and verify ownership
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.user_id != current_user.id:
        flash('You do not have permission to review this quiz.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Get all submissions for this quiz
    submissions = db.session.query(StudentSubmission)\
        .join(QuizSubmission, StudentSubmission.quiz_submission_id == QuizSubmission.id)\
        .join(Question, StudentSubmission.question_id == Question.id)\
        .filter(QuizSubmission.quiz_id == quiz_id)\
        .order_by(StudentSubmission.submitted_at.desc())\
        .all()
    
    # Separate submissions by grading status
    pending_submissions = []
    graded_submissions = []
    auto_graded_submissions = []
    
    for submission in submissions:
        if not submission.graded:
            # Only add essay questions and non-matching identification questions to pending review
            if submission.question.question_type == 'essay' or \
               (submission.question.question_type == 'identification' and not submission.is_correct):
                pending_submissions.append(submission)
        else:
            if submission.question.question_type in ['multiple_choice', 'true_false'] or \
               (submission.question.question_type == 'identification' and submission.is_correct):
                auto_graded_submissions.append(submission)
            else:
                graded_submissions.append(submission)
    
    return render_template('quiz/review_submissions.html',
                          quiz=quiz,
                          submissions=submissions,
                          pending_submissions=pending_submissions,
                          graded_submissions=graded_submissions + auto_graded_submissions,
                          pending_count=len(pending_submissions),
                          graded_count=len(graded_submissions),
                          auto_graded_count=len(auto_graded_submissions))

@quiz_bp.route('/grade_submission/<int:submission_id>', methods=['POST'])
@login_required
def grade_submission(submission_id):
    """Handle the submission of manual grading for a student answer"""
    # Ensure the user is a teacher
    if current_user.role != 'teacher':
        flash('Only teachers can grade submissions.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Get the submission
    submission = StudentSubmission.query.get_or_404(submission_id)
    
    # Verify the teacher owns the quiz
    quiz = Quiz.query.join(QuizSubmission).filter(
        QuizSubmission.id == submission.quiz_submission_id
    ).first()
    
    if not quiz or quiz.user_id != current_user.id:
        flash('You do not have permission to grade this submission.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Get form data
    score = float(request.form.get('score', 0))
    feedback = request.form.get('feedback', '')
    is_correct = 'is_correct' in request.form
    
    # Validate score
    max_points = submission.question.points
    if score < 0 or score > max_points:
        flash(f'Score must be between 0 and {max_points}.', 'danger')
        return redirect(url_for('quiz.review_submissions', quiz_id=quiz.id))
    
    # Update the submission
    submission.score = score
    submission.feedback = feedback
    submission.is_correct = is_correct
    submission.graded = True
    
    # Save changes
    db.session.commit()
    
    flash('Submission graded successfully.', 'success')
    return redirect(url_for('quiz.review_submissions', quiz_id=quiz.id))

@quiz_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_quiz():
    """Create a new quiz"""
    if not current_user.is_teacher():
        flash('Only teachers can create quizzes/exams.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    subjects = Subject.query.filter_by(teacher_id=current_user.id).all()
    if not subjects:
        flash('You need to create a subject before creating a quiz/exam.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    form = QuizSetupForm()
    form.subject_id.choices = [(s.id, s.name) for s in subjects]
    
    if form.validate_on_submit():
        try:
            start_time = None
            if form.start_time.data:
                try:
                    start_time = datetime.strptime(form.start_time.data, '%Y-%m-%dT%H:%M')
                except ValueError:
                    flash('Invalid date format. Please use YYYY-MM-DDTHH:MM format.', 'danger')
                    return render_template('quiz/setup.html', form=form, title='Create Quiz')
            
            success, message, quiz = QuizService.create_quiz(
                title=form.title.data,
                description=form.description.data,
                quiz_type=form.quiz_type.data,
                duration=form.duration.data,
                start_time=start_time,
                user_id=current_user.id,
                subject_id=form.subject_id.data
            )
            
            if success:
                # Store quiz setup info in session for question creation
                session['quiz_setup'] = {
                    'quiz_id': quiz.id,
                    'question_count': form.question_count.data,
                    'questions_added': 0
                }
                flash(message, 'success')
                return redirect(url_for('quiz.add_question'))
            else:
                flash(message, 'danger')
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'danger')
    
    return render_template('quiz/setup.html', form=form, title='Create Quiz')

@quiz_bp.route('/add_question', methods=['GET', 'POST'])
@login_required
def add_question():
    """Add a question to a quiz"""
    if not current_user.is_teacher():
        flash('Only teachers can add questions.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Check if quiz setup exists in session
    quiz_setup = session.get('quiz_setup')
    if not quiz_setup:
        flash('Please set up a quiz first.', 'danger')
        return redirect(url_for('quiz.create_quiz'))
    
    quiz_id = quiz_setup.get('quiz_id')
    question_count = quiz_setup.get('question_count')
    questions_added = quiz_setup.get('questions_added', 0)
    
    # Check if all questions have been added
    if questions_added >= question_count:
        # Clear quiz setup from session
        session.pop('quiz_setup', None)
        flash('All questions have been added successfully!', 'success')
        return redirect(url_for('dashboard.index'))
    
    # Get the quiz
    quiz = QuizService.get_quiz_by_id(quiz_id)
    if not quiz:
        flash('Quiz not found.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Initialize form based on question type
    question_type = request.form.get('question_type', 'multiple_choice')
    form = get_question_form(question_type)
    
    # Set hidden fields
    form.quiz_id.data = quiz_id
    form.current_question.data = questions_added + 1
    form.total_questions.data = question_count
    
    if request.method == 'POST' and form.validate_on_submit():
        try:
            # Process form data based on question type
            options = None
            correct_answer = None
            word_limit = None
            
            if question_type == 'multiple_choice':
                options = [
                    form.option1.data,
                    form.option2.data,
                    form.option3.data,
                    form.option4.data
                ]
                correct_answer = options[int(form.correct_option.data)]
            elif question_type == 'identification':
                correct_answer = form.correct_answer.data
            elif question_type == 'true_false':
                correct_answer = form.correct_answer.data
            elif question_type == 'essay':
                correct_answer = 'Essay question - manual grading required'
                word_limit = form.word_limit.data
            
            # Add question to database
            success, message, question = QuizService.add_question(
                quiz_id=quiz_id,
                question_text=form.question_text.data,
                question_type=question_type,
                options=options,
                correct_answer=correct_answer,
                points=form.points.data,
                order_index=questions_added,
                word_limit=word_limit
            )
            
            if success:
                # Update questions added count in session
                questions_added += 1
                session['quiz_setup']['questions_added'] = questions_added
                
                if questions_added >= question_count:
                    # All questions added
                    session.pop('quiz_setup', None)
                    flash('All questions have been added successfully!', 'success')
                    return redirect(url_for('dashboard.index'))
                else:
                    # More questions to add
                    flash(f'Question {questions_added} of {question_count} added successfully!', 'success')
                    return redirect(url_for('quiz.add_question'))
            else:
                flash(message, 'danger')
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'danger')
    
    return render_template('auth/add_question.html', form=form, 
                          current_question=questions_added + 1,
                          total_questions=question_count,
                          title=f'Add Question {questions_added + 1}/{question_count}')

@quiz_bp.route('/view/<int:quiz_id>')
@login_required
def view_quiz(quiz_id):
    """View a quiz's details"""
    quiz = QuizService.get_quiz_by_id(quiz_id)
    if not quiz:
        flash('Quiz not found.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Check if user has permission to view this quiz
    if current_user.is_teacher() and quiz.user_id != current_user.id:
        flash('You do not have permission to view this quiz.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # For students, check if they are enrolled in the subject
    if current_user.is_student():
        subject = Subject.query.get(quiz.subject_id)
        if subject not in current_user.enrolled_subjects:
            flash('You are not enrolled in this subject.', 'danger')
            return redirect(url_for('dashboard.index'))
    
    # Get quiz submissions if user is teacher
    submissions = []
    if current_user.is_teacher():
        submissions = QuizService.get_quiz_submissions(quiz_id)
    
    return render_template('auth/view_quiz.html', quiz=quiz, submissions=submissions, title=quiz.title)

@quiz_bp.route('/delete/<int:quiz_id>', methods=['POST'])
@login_required
def delete_quiz(quiz_id):
    """Delete a quiz"""
    if not current_user.is_teacher():
        flash('Only teachers can delete quizzes.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    quiz = QuizService.get_quiz_by_id(quiz_id)
    if not quiz:
        flash('Quiz not found.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Check if user has permission to delete this quiz
    if quiz.user_id != current_user.id:
        flash('You do not have permission to delete this quiz.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    success, message = QuizService.delete_quiz(quiz_id)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('dashboard.index'))