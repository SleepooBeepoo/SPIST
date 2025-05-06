"""Routes for submission module"""
from flask import render_template, redirect, url_for, flash, request, Blueprint, current_app
from flask_login import login_required, current_user
from app.models import db, Quiz, Question, QuizSubmission, StudentSubmission, Announcement
from app.submission.forms import AnswerForm, GradeSubmissionForm, GradeQuestionForm
from app.submission.services import SubmissionService
from app.question.services import QuestionService
from app.services.ai_detection_service import AIDetectionService
from datetime import datetime
import json
import logging

# Configure logger
logger = logging.getLogger(__name__)

submission_bp = Blueprint('submission', __name__)

@submission_bp.route('/take_quiz/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def take_quiz(quiz_id):
    """Take a quiz"""
    if not current_user.is_student():
        flash('Only students can take quizzes.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Get the quiz
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check if student is enrolled in the subject
    if quiz.subject not in current_user.enrolled_subjects:
        flash('You are not enrolled in this subject.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Check if quiz is available
    if quiz.start_time and quiz.start_time > datetime.utcnow():
        flash('This quiz is not yet available.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Check if student has already submitted this quiz
    existing_submission = QuizSubmission.query.filter_by(quiz_id=quiz_id, student_id=current_user.id).first()
    if existing_submission:
        flash('You have already submitted this quiz.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Get questions for the quiz
    questions = QuestionService.get_questions_by_quiz(quiz_id)
    if not questions:
        flash('This quiz has no questions.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        try:
            # Create quiz submission
            success, message, quiz_submission = SubmissionService.create_quiz_submission(
                quiz_id=quiz_id,
                student_id=current_user.id
            )
            
            if not success:
                flash(message, 'danger')
                return redirect(url_for('dashboard.index'))
            
            # Process each question submission
            total_score = 0.0
            for question in questions:
                answer = request.form.get(f'answer_{question.id}')
                
                # Skip if no answer provided
                if not answer:
                    continue
                
                # Check if answer is correct
                is_correct, score, feedback = QuestionService.validate_answer(question.id, answer)
                
                # For essay questions, use AI detection
                ai_feedback = None
                if question.question_type == 'essay':
                    try:
                        ai_detector = AIDetectionService()
                        ai_result = ai_detector.analyze_text(answer)
                        ai_feedback = f"AI Detection Score: {ai_result['ai_score']:.2f}\n"
                        ai_feedback += f"Confidence: {ai_result['confidence']:.2f}\n"
                        ai_feedback += f"Analysis: {ai_result['analysis']}"
                    except Exception as e:
                        logger.error(f"Error in AI detection for question {question.id}: {str(e)}")
                        current_app.logger.error(f"Error in AI detection for question {question.id}: {str(e)}")
                        ai_feedback = "AI detection unavailable - Technical issue encountered"
                
                # Create student submission
                submission_success, submission_message, student_submission = SubmissionService.create_student_submission(
                    quiz_submission_id=quiz_submission.id,
                    question_id=question.id,
                    answer=answer,
                    is_correct=is_correct,
                    score=score,
                    feedback=ai_feedback if question.question_type == 'essay' else feedback
                )
                
                if not submission_success:
                    logger.error(f"Error submitting answer for question {question.id}: {submission_message}")
                    current_app.logger.error(f"Error submitting answer for question {question.id}: {submission_message}")
                    # Continue processing other questions even if one fails
                
                total_score += score
            
            # Update quiz submission with total score
            try:
                quiz_submission.total_score = total_score
                quiz_submission.is_graded = all(q.question_type != 'essay' for q in questions)
                
                # Create announcement for the teacher about the submission
                announcement = Announcement(
                    title=f'New Submission Received',
                    content=f'{current_user.username} has submitted {quiz.quiz_type} "{quiz.title}" for {quiz.subject.name}.',
                    user_id=current_user.id,
                    subject_id=quiz.subject_id,
                    quiz_id=quiz.id,
                    submission_id=quiz_submission.id,
                    announcement_type='submission_received'
                )
                db.session.add(announcement)
                
                db.session.commit()
                
                flash('Quiz submitted successfully!', 'success')
                return redirect(url_for('dashboard.index'))
            except Exception as e:
                logger.error(f"Error updating quiz submission: {str(e)}")
                current_app.logger.error(f"Error updating quiz submission: {str(e)}")
                db.session.rollback()
                flash(f'An error occurred while saving your submission: {str(e)}', 'danger')
                return redirect(url_for('dashboard.index'))
        except Exception as e:
            logger.error(f"Unexpected error in quiz submission: {str(e)}")
            current_app.logger.error(f"Unexpected error in quiz submission: {str(e)}")
            flash(f'An error occurred while processing your submission: {str(e)}', 'danger')
    
    return render_template('auth/take_quiz.html', quiz=quiz, questions=questions, title=f'Take {quiz.title}')

@submission_bp.route('/view_submission/<int:submission_id>')
@login_required
def view_submission(submission_id):
    """View a quiz submission"""
    try:
        # Get the submission
        submission = SubmissionService.get_quiz_submission_by_id(submission_id)
        if not submission:
            flash('Submission not found.', 'danger')
            return redirect(url_for('dashboard.index'))
        
        # Check if user has permission to view this submission
        if current_user.is_student() and submission.student_id != current_user.id:
            logger.warning(f"Unauthorized access attempt to submission {submission_id} by student {current_user.id}")
            flash('You do not have permission to view this submission.', 'danger')
            return redirect(url_for('dashboard.index'))
        
        if current_user.is_teacher() and submission.quiz.user_id != current_user.id:
            logger.warning(f"Unauthorized access attempt to submission {submission_id} by teacher {current_user.id}")
            flash('You do not have permission to view this submission.', 'danger')
            return redirect(url_for('dashboard.index'))
        
        # Get student submissions for each question
        student_submissions = SubmissionService.get_student_submissions_by_quiz_submission(submission_id)
        
        # Get questions for the quiz
        questions = QuestionService.get_questions_by_quiz(submission.quiz_id)
        
        return render_template('auth/view_submission.html', 
                              submission=submission, 
                              student_submissions=student_submissions,
                              questions=questions,
                              title=f'Submission for {submission.quiz.title}')
    except Exception as e:
        logger.error(f"Error viewing submission {submission_id}: {str(e)}")
        current_app.logger.error(f"Error viewing submission {submission_id}: {str(e)}")
        flash('An error occurred while retrieving the submission details.', 'danger')
        return redirect(url_for('dashboard.index'))

@submission_bp.route('/grade_submission/<int:submission_id>', methods=['GET', 'POST'])
@login_required
def grade_submission(submission_id):
    """Grade a quiz submission"""
    try:
        # Check user role
        if not current_user.is_teacher():
            logger.warning(f"Non-teacher user {current_user.id} attempted to access grading function")
            flash('Only teachers can grade submissions.', 'danger')
            return redirect(url_for('dashboard.index'))
        
        # Get the submission
        submission = SubmissionService.get_quiz_submission_by_id(submission_id)
        if not submission:
            logger.warning(f"Attempted to grade non-existent submission {submission_id}")
            flash('Submission not found.', 'danger')
            return redirect(url_for('dashboard.index'))
        
        # Check if user has permission to grade this submission
        if submission.quiz.user_id != current_user.id:
            logger.warning(f"Unauthorized grading attempt for submission {submission_id} by teacher {current_user.id}")
            flash('You do not have permission to grade this submission.', 'danger')
            return redirect(url_for('dashboard.index'))
        
        # Check if submission is already graded
        if submission.is_graded:
            logger.info(f"Re-grading already graded submission {submission_id}")
            flash('This submission has already been graded. Your changes will update the existing grades.', 'info')
        
        # Get student submissions for each question
        student_submissions = SubmissionService.get_student_submissions_by_quiz_submission(submission_id)
        if not student_submissions:
            logger.warning(f"No student submissions found for quiz submission {submission_id}")
            flash('No answers found for this submission.', 'warning')
            return redirect(url_for('dashboard.index'))
        
        # Get questions for the quiz
        questions = QuestionService.get_questions_by_quiz(submission.quiz_id)
        
        # Create form
        form = GradeSubmissionForm()
        
        # If GET request, populate form with existing data
        if request.method == 'GET':
            form.quiz_submission_id.data = submission_id
            form.total_score.data = submission.total_score
            
            # Clear existing question grades
            while len(form.question_grades) > 0:
                form.question_grades.pop_entry()
            
            # Add question grades for each submission
            for student_submission in student_submissions:
                question_form = GradeQuestionForm()
                question_form.question_id.data = student_submission.question_id
                question_form.score.data = student_submission.score
                question_form.feedback.data = student_submission.feedback
                form.question_grades.append_entry(question_form.data)
        
        if request.method == 'POST':
            if not form.validate_on_submit():
                for field, errors in form.errors.items():
                    for error in errors:
                        flash(f"Error in {field}: {error}", 'danger')
                return render_template('auth/grade_submission.html', 
                                      form=form,
                                      submission=submission, 
                                      student_submissions=student_submissions,
                                      questions=questions,
                                      title=f'Grade Submission for {submission.quiz.title}')
            
            try:
                # Validate scores are within reasonable range
                total_points = sum(q.points for q in questions)
                if form.total_score.data < 0 or form.total_score.data > total_points:
                    flash(f'Total score must be between 0 and {total_points}.', 'danger')
                    return render_template('auth/grade_submission.html', 
                                          form=form,
                                          submission=submission, 
                                          student_submissions=student_submissions,
                                          questions=questions,
                                          title=f'Grade Submission for {submission.quiz.title}')
                
                # Prepare feedback dictionary
                feedback = {}
                for question_grade in form.question_grades.entries:
                    question_id = int(question_grade.question_id.data)
                    # Find the question to get its point value
                    question = next((q for q in questions if q.id == question_id), None)
                    if question and (question_grade.score.data < 0 or question_grade.score.data > question.points):
                        flash(f'Score for question {question_id} must be between 0 and {question.points}.', 'danger')
                        return render_template('auth/grade_submission.html', 
                                              form=form,
                                              submission=submission, 
                                              student_submissions=student_submissions,
                                              questions=questions,
                                              title=f'Grade Submission for {submission.quiz.title}')
                    
                    feedback[question_id] = {
                        'score': float(question_grade.score.data),
                        'feedback': question_grade.feedback.data
                    }
                
                # Grade submission
                success, message, graded_submission = SubmissionService.grade_submission(
                    quiz_submission_id=submission_id,
                    total_score=form.total_score.data,
                    feedback=feedback
                )
                
                if success:
                    # Log the successful grading
                    logger.info(f"Teacher {current_user.id} successfully graded submission {submission_id}")
                    flash(message, 'success')
                    return redirect(url_for('submission.view_submission', submission_id=submission_id))
                else:
                    logger.warning(f"Failed to grade submission {submission_id}: {message}")
                    flash(message, 'danger')
            except ValueError as e:
                logger.error(f"Value error while grading submission {submission_id}: {str(e)}")
                current_app.logger.error(f"Value error while grading submission {submission_id}: {str(e)}")
                flash(f'Invalid value entered: {str(e)}', 'danger')
            except Exception as e:
                logger.error(f"Error grading submission {submission_id}: {str(e)}")
                current_app.logger.error(f"Error grading submission {submission_id}: {str(e)}")
                db.session.rollback()
                flash(f'An error occurred while grading the submission: {str(e)}', 'danger')
        
        return render_template('auth/grade_submission.html', 
                              form=form,
                              submission=submission, 
                              student_submissions=student_submissions,
                              questions=questions,
                              title=f'Grade Submission for {submission.quiz.title}')
    except Exception as e:
        logger.error(f"Unexpected error in grade_submission route: {str(e)}")
        current_app.logger.error(f"Unexpected error in grade_submission route: {str(e)}")
        flash('An unexpected error occurred. Please try again later.', 'danger')
        return redirect(url_for('dashboard.index'))