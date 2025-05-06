from flask import Flask, render_template, redirect, url_for, flash, request, session, Response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import timedelta,  datetime
from models import db, User, Question, StudentSubmission, Quiz, Subject, QuizSubmission, StudentSubject, Announcement
from forms import LoginForm, RegistrationForm, GradeSubmissionForm, QuizForm
from question_forms import get_question_form, MultipleChoiceQuestionForm, IdentificationQuestionForm, TrueFalseQuestionForm
from flask_wtf.csrf import CSRFProtect
from flask_wtf import FlaskForm
from quiz_module import quiz_bp
from subject_module import subject_bp
from settings_module import settings_bp
from import_document import import_document_bp

app = Flask(__name__)

# Configure session to ensure data persistence
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=5)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Register blueprints
app.register_blueprint(quiz_bp, url_prefix='/quiz')
app.register_blueprint(subject_bp, url_prefix='/subject')
app.register_blueprint(settings_bp, url_prefix='/user')
app.register_blueprint(import_document_bp, url_prefix='/import')

# Use absolute path for database to avoid permission issues
import os
instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
db_path = os.path.join(instance_path, 'users.db')

# Ensure instance directory exists
if not os.path.exists(instance_path):
    os.makedirs(instance_path, exist_ok=True)
    print(f"Created instance directory: {instance_path}")

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
try:
    db.init_app(app)
    with app.app_context():
        db.create_all()  # Ensure tables exist
except Exception as e:
    print(f"Database initialization error: {str(e)}")
    # If database is corrupted, you may need to run repair_db.py

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize CSRF protection with extended timeout
csrf = CSRFProtect()
csrf.init_app(app)

# Configure CSRF protection settings
app.config['WTF_CSRF_TIME_LIMIT'] = 86400  # Set CSRF token expiry to 24 hours (in seconds)

# Error handler for CSRF errors
@app.errorhandler(400)
def handle_csrf_error(e):
    if 'CSRF' in str(e):
        flash('Your session has expired. Please try again.', 'error')
        return redirect(url_for('login'))
    return e

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception as e:
        print(f"Error loading user: {str(e)}")
        return None

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('auth/login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        # Validate student email domain
        if form.role.data == 'student' and not form.email.data.endswith('@spist.edu'):
            flash('Student email must use the school domain (@spist.edu)')
            return render_template('auth/register.html', form=form)
            
        # Check if email is already registered
        if User.query.filter_by(email=form.email.data).first():
            flash('Email address already registered. Please use a different email.')
            return render_template('auth/register.html', form=form)
            
        # Create user
        user = User(username=form.username.data, email=form.email.data, role=form.role.data)
        user.set_password(form.password.data)
        db.session.add(user)
        
        # Create subject for teacher if subject code provided
        if form.role.data == 'teacher' and form.subject_code.data:
            # Check if subject code already exists
            existing_subject = Subject.query.filter_by(subject_code=form.subject_code.data).first()
            if existing_subject:
                db.session.rollback()
                flash('Subject code already exists. Please choose a different code.')
                return render_template('auth/register.html', form=form)
                
            subject = Subject(name=form.username.data + "'s Class", 
                            subject_code=form.subject_code.data,
                            teacher_id=user.id)
            db.session.add(subject)
            
        try:
            db.session.commit()
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            if 'UNIQUE constraint' in str(e):
                if 'username' in str(e):
                    flash('Username already taken. Please choose a different username.')
                else:
                    flash('Email address already registered. Please use a different email.')
            else:
                flash('An error occurred during registration. Please try again.')
            return render_template('auth/register.html', form=form)
    return render_template('auth/register.html', form=form)

# Subject creation is now handled by the subject blueprint

@app.route('/dashboard')
@login_required
def dashboard():
    # Create a form instance for CSRF token
    form = FlaskForm()
    
    # For teachers, we need to explicitly query their subjects
    # The subjects_taught backref might not be loaded automatically
    subjects = []
    if current_user.role == 'teacher':
        subjects = Subject.query.filter_by(teacher_id=current_user.id).all()
    
    # Render the unified dashboard template
    return render_template('dashboard.html', form=form, subjects=subjects)

# Subject routes are now handled by the subject blueprint

@app.route('/grade_submission/<int:submission_id>', methods=['GET', 'POST'])
@login_required
def grade_submission(submission_id):
    if current_user.role != 'teacher':
        flash('Only teachers can grade submissions.')
        return redirect(url_for('dashboard'))
    
    # Use joinedload to eagerly load the question_submissions relationship and related questions
    from sqlalchemy.orm import joinedload
    quiz_submission = QuizSubmission.query.options(
        joinedload(QuizSubmission.question_submissions).joinedload(StudentSubmission.question)
    ).get_or_404(submission_id)
    
    quiz = quiz_submission.quiz
    
    # Verify teacher owns the quiz
    if quiz.user_id != current_user.id:
        flash('You do not have permission to grade this submission.')
        return redirect(url_for('dashboard'))
    
    # If question_submissions relationship isn't working, manually load them
    if not quiz_submission.question_submissions:
        # Get submissions directly from StudentSubmission table
        direct_submissions = StudentSubmission.query.filter_by(
            student_id=quiz_submission.student_id,
            quiz_submission_id=quiz_submission.id
        ).all()
        
        # Manually assign them to the quiz_submission object
        if direct_submissions:
            quiz_submission.question_submissions = direct_submissions
    
    form = GradeSubmissionForm()
    if form.validate_on_submit():
        try:
            quiz_submission.total_score = form.score.data
            quiz_submission.feedback = form.feedback.data
            quiz_submission.visible_to_students = form.visible_to_students.data
            quiz_submission.show_answers = form.show_answers.data
            quiz_submission.graded = True
            quiz_submission.graded_at = datetime.utcnow()
            db.session.commit()
            flash('Submission graded successfully!')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while grading the submission: {str(e)}')
    else:
        # Pre-fill the form with existing data if available
        if quiz_submission.graded:
            form.score.data = quiz_submission.total_score
            form.feedback.data = quiz_submission.feedback
            form.visible_to_students.data = quiz_submission.visible_to_students
            form.show_answers.data = quiz_submission.show_answers
    
    return render_template('auth/grade_submission.html', form=form, quiz_submission=quiz_submission)

@app.route('/check_ai_content/<int:submission_id>', methods=['POST'])
@login_required
def check_ai_content(submission_id):
    """Check if an essay submission contains AI-generated content"""
    from flask import jsonify
    from ai_detection_service_new import AIContentDetector
    
    try:
        if current_user.role != 'teacher':
            return jsonify({'error': 'Unauthorized', 'level': 'danger'}), 403
        
        # Validate submission exists
        submission = StudentSubmission.query.get(submission_id)
        if not submission:
            return jsonify({
                'error': 'Submission not found',
                'level': 'danger',
                'score': 0,
                'confidence': 'Error: Submission not found',
                'features': []
            }), 404
            
        # Validate quiz_submission exists
        if not submission.quiz_submission:
            return jsonify({
                'error': 'Quiz submission not found',
                'level': 'danger',
                'score': 0,
                'confidence': 'Error: Quiz submission not found',
                'features': []
            }), 404
            
        quiz = submission.quiz_submission.quiz
        
        # Verify teacher owns the quiz
        if quiz.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized', 'level': 'danger'}), 403
        
        # Get the essay text
        essay_text = submission.submitted_answer
        if not essay_text or len(essay_text.strip()) < 10:
            return jsonify({
                'error': 'Essay text too short for analysis',
                'level': 'warning',
                'score': 0,
                'confidence': 'Text too short for analysis',
                'features': []
            }), 200
        
        # Initialize the detector with the new simplified implementation
        detector = AIContentDetector()
        
        # Get the detection result
        result = detector.detect(essay_text)
        
        # Return JSON response
        return jsonify(result)
    
    except Exception as e:
        # Log the error for debugging
        print(f"Error in check_ai_content: {str(e)}")
        # Always return a JSON response even when an error occurs
        return jsonify({
            'error': 'The AI detection service encountered an error. Please try again later.',
            'level': 'danger',
            'score': 0,
            'confidence': 'Error during analysis',
            'features': [{'name': 'Error Details', 'value': str(e)}]
        }), 500

# This duplicate route was removed to fix the AssertionError
# The route is already defined earlier in the file

# Student removal is now handled by the subject blueprint



# Subject enrollment is now handled by the subject blueprint

@app.route('/submit_answer/<int:question_id>', methods=['POST'])
@login_required
def submit_answer(question_id):
    if current_user.role != 'student':
        flash('Only students can submit answers.')
        return redirect(url_for('dashboard'))
    
    try:
        question = Question.query.get_or_404(question_id)
        quiz = question.quiz
        if not quiz:
            flash('This question is not part of any quiz.')
            return redirect(url_for('dashboard'))
            
        subject = quiz.subject
        if subject not in current_user.enrolled_subjects:
            flash('You are not enrolled in this subject.')
            return redirect(url_for('dashboard'))
        
        # Check if quiz has started
        now = datetime.utcnow()
        if quiz.start_time:
            # Ensure both times are naive UTC for comparison
            start_time_naive = quiz.start_time
            if hasattr(quiz.start_time, 'tzinfo') and quiz.start_time.tzinfo:
                import pytz
                # Convert to UTC then remove timezone info
                start_time_naive = quiz.start_time.astimezone(pytz.UTC).replace(tzinfo=None)
            
            if now < start_time_naive:
                # Format the time with timezone information for clarity
                formatted_time = quiz.start_time.strftime("%Y-%m-%d %H:%M")
                flash(f'This {quiz.quiz_type} has not started yet. It starts at {formatted_time} UTC')
                return redirect(url_for('dashboard'))
        
        # Get or create quiz submission with transaction
        quiz_submission = None
        try:
            # First check if there's a completed submission
            completed_submission = QuizSubmission.query.filter_by(
                student_id=current_user.id,
                quiz_id=quiz.id,
                submitted_at=db.not_(None)  # Only get submissions that have been completed
            ).first()
            
            if completed_submission:
                flash(f'You have already submitted this {quiz.quiz_type}.')
                return redirect(url_for('dashboard'))
                
            # Get or create an in-progress submission
            quiz_submission = QuizSubmission.query.filter_by(
                student_id=current_user.id,
                quiz_id=quiz.id,
                submitted_at=None  # Only get submissions that haven't been completed
            ).with_for_update().first()
            
            if not quiz_submission:
                quiz_submission = QuizSubmission(
                    student_id=current_user.id,
                    quiz_id=quiz.id,
                    start_time=now
                )
                db.session.add(quiz_submission)
                db.session.commit()
        except Exception:
            db.session.rollback()
            flash('Error accessing quiz submission. Please try again.')
            return redirect(url_for('dashboard'))
        
        # Check time limit
        if quiz.duration:
            time_elapsed = (now - quiz_submission.start_time).total_seconds() / 60
            if time_elapsed >= quiz.duration:
                try:
                    # Mark the current question as answered
                    submitted_answer = request.form.get('answer')
                    if submitted_answer is None or not submitted_answer.strip():
                        submitted_answer = "Missing"
                    
                    # For essay questions, we need manual grading
                    if question.question_type == 'essay':
                        is_correct = False  # Essays require manual grading
                        score = 0.0  # Initial score is 0 until teacher grades it
                    else:
                        is_correct = False if submitted_answer == "Missing" else question.validate_answer(submitted_answer)
                        score = question.points if is_correct else 0.0
                    
                    # Create the submission for current question
                    submission = StudentSubmission(
                        student_id=current_user.id,
                        question_id=question_id,
                        quiz_submission_id=quiz_submission.id,
                        submitted_answer=submitted_answer,
                        is_correct=is_correct,
                        score=score,
                        submitted_at=now
                    )
                    db.session.add(submission)
                    
                    # Get all questions that haven't been answered yet
                    answered_questions = StudentSubmission.query.filter(
                        StudentSubmission.student_id == current_user.id,
                        StudentSubmission.quiz_submission_id == quiz_submission.id
                    ).all()
                    answered_question_ids = [sub.question_id for sub in answered_questions]
                    
                    # Create "Missing" submissions for all unanswered questions
                    for q in quiz.questions:
                        if q.id not in answered_question_ids and q.id != question_id:  # Skip current question
                            missing_submission = StudentSubmission(
                                student_id=current_user.id,
                                question_id=q.id,
                                quiz_submission_id=quiz_submission.id,
                                submitted_answer="Missing",
                                is_correct=False,
                                score=0.0,
                                submitted_at=now
                            )
                            db.session.add(missing_submission)
                    
                    # Mark quiz as submitted
                    quiz_submission.submitted_at = now
                    quiz_submission.duration_taken = quiz.duration
                    quiz_submission.total_score = sum([sub.score for sub in answered_questions]) + score
                    
                    # Create announcement for the teacher
                    missing_count = len(quiz.questions) - len(answered_questions) - 1  # -1 for current question
                    missing_info = f" ({missing_count} questions unanswered)" if missing_count > 0 else ""
                    announcement = Announcement(
                        title=f'New Submission Received (Time Expired){missing_info}',
                        content=f'{current_user.username} ran out of time on {quiz.quiz_type} "{quiz.title}" for {subject.name}.{missing_info}',
                        user_id=current_user.id,
                        subject_id=subject.id,
                        quiz_id=quiz.id,
                        submission_id=quiz_submission.id,
                        announcement_type='submission_received'
                    )
                    db.session.add(announcement)
                    
                    db.session.commit()
                    flash(f'Time limit for this {quiz.quiz_type} has expired! Your answers have been automatically submitted.')
                    return redirect(url_for('dashboard'))
                except Exception as e:
                    db.session.rollback()
                    flash(f'Error submitting quiz: {str(e)}. Please try again.')
                    return redirect(url_for('dashboard'))
        
        # Check for existing submission with transaction
        try:
            existing_submission = StudentSubmission.query.filter_by(
                student_id=current_user.id,
                question_id=question_id,
                quiz_submission_id=quiz_submission.id
            ).with_for_update().first()
            
            if existing_submission:
                flash('You have already submitted an answer for this question.')
                return redirect(url_for('dashboard'))
            
            submitted_answer = request.form.get('answer')
            if submitted_answer is None:
                flash('Please provide an answer.')
                return redirect(url_for('dashboard'))
            
            # For essay questions, we need manual grading
            if question.question_type == 'essay':
                is_correct = False  # Essays require manual grading
                score = 0.0  # Initial score is 0 until teacher grades it
            else:
                is_correct = question.validate_answer(submitted_answer)
                score = question.points if is_correct else 0.0
            
            # Create the submission with explicit relationship to quiz_submission
            submission = StudentSubmission(
                student_id=current_user.id,
                question_id=question_id,
                quiz_submission_id=quiz_submission.id,
                submitted_answer=submitted_answer,
                is_correct=is_correct,
                score=score,
                submitted_at=now
            )
            
            db.session.add(submission)
            
            # Update quiz submission status
            total_questions = len(quiz.questions)
            answered_questions = StudentSubmission.query.filter(
                StudentSubmission.student_id == current_user.id,
                StudentSubmission.question_id.in_([q.id for q in quiz.questions])
            ).count() + 1  # Include current submission
            
            if answered_questions == total_questions:
                total_score = sum([sub.score for sub in quiz_submission.question_submissions]) + score
                quiz_submission.total_score = total_score
                quiz_submission.submitted_at = now
                if quiz.duration:
                    quiz_submission.duration_taken = int((now - quiz_submission.start_time).total_seconds() / 60)
                flash(f'You have completed all questions in this {quiz.quiz_type}!')
            else:
                flash('Your answer has been submitted successfully!')
                
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while submitting your answer. Please try again.')
            return redirect(url_for('dashboard'))
            
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        flash('An unexpected error occurred. Please try again.')
        return redirect(url_for('dashboard'))

@app.route('/add_question/<int:subject_id>', methods=['GET', 'POST'])
@login_required
def add_question(subject_id):
    if current_user.role != 'teacher':
        flash('Only teachers can add questions.')
        return redirect(url_for('dashboard'))
        
    subject = Subject.query.filter_by(id=subject_id, teacher_id=current_user.id).first()
    if not subject:
        flash('Invalid subject selected.')
        return redirect(url_for('dashboard'))

    question_type = request.args.get('question_type', request.form.get('question_type', 'multiple_choice'))
    form_class = get_question_form(question_type)
    form = form_class()

    if request.method == 'POST':
        form = form_class(request.form)
        if form.validate_on_submit():
            try:
                # Get the quiz if it exists
                quiz_id = request.args.get('quiz_id')
                next_order_index = 0
                
                if quiz_id:
                    quiz = Quiz.query.get(quiz_id)
                    if quiz:
                        next_order_index = len(quiz.questions)
                
                question = Question(
                    question_text=form.question_text.data,
                    question_type=question_type,
                    user_id=current_user.id,
                    subject_id=subject_id,
                    points=form.points.data,
                    quiz_id=quiz_id if quiz_id else None,
                    order_index=next_order_index
                )
                
                if question_type == 'multiple_choice':
                    question.options = [opt.data.strip() for opt in form.options]
                    question.correct_answer = form.correct_option.data
                elif question_type == 'true_false':
                    question.correct_answer = form.correct_answer.data.lower()
                elif question_type == 'identification':
                    question.correct_answer = form.correct_answer.data.strip()
                elif question_type == 'essay':
                    question.word_limit = form.word_limit.data if hasattr(form, 'word_limit') else None
                    question.correct_answer = form.correct_answer.data.strip() if form.correct_answer.data else ''


                
                db.session.add(question)
                db.session.commit()
                flash('Question added successfully!')
                return redirect(url_for('dashboard'))
            except Exception as e:
                db.session.rollback()
                flash(f'An error occurred while adding the question: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'Error in {field}: {error}')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('auth/add_question.html', form=form, subject_id=subject_id)
    
    return render_template('auth/add_question.html', form=form, subject_id=subject_id)

@app.route('/delete_question/<int:question_id>', methods=['POST'])
@login_required
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    if question.user_id != current_user.id:
        flash('You do not have permission to delete this question.')
        return redirect(url_for('dashboard'))
    
    try:
        db.session.delete(question)
        db.session.commit()
        flash('Question deleted successfully!')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the question.')
    
    return redirect(url_for('dashboard'))

@app.route('/edit_question/<int:question_id>', methods=['GET', 'POST'])
@login_required
def edit_question(question_id):
    question = Question.query.get_or_404(question_id)
    if question.user_id != current_user.id:
        flash('You do not have permission to edit this question.')
        return redirect(url_for('dashboard'))
    
    form = get_question_form(question.question_type)()
    
    if request.method == 'GET':
        form.question_text.data = question.question_text
        form.points.data = question.points
        form.points.data = question.points
        
        if question.question_type == 'multiple_choice':
            for i, option in enumerate(question.options):
                form.options[i].data = option
            form.correct_option.data = question.correct_answer
        elif question.question_type in ['identification', 'true_false']:
            form.correct_answer.data = question.correct_answer


    
    if form.validate_on_submit():
        question.question_text = form.question_text.data
        question.points = form.points.data
        question.order_index = form.order_index.data
        
        if question.question_type == 'multiple_choice':
            question.options = [form.options[i].data for i in range(4)]
            question.correct_answer = form.correct_option.data
        elif question.question_type == 'identification':
            question.correct_answer = form.correct_answer.data
        elif question.question_type == 'true_false':
            question.correct_answer = form.correct_answer.data
        
        db.session.commit()
        flash('Question updated successfully!')
        return redirect(url_for('dashboard'))
    
    return render_template('auth/edit_question.html', form=form, question=question)

def get_question_form(question_type):
    if question_type == 'multiple_choice':
        return MultipleChoiceQuestionForm
    elif question_type == 'identification':
        return IdentificationQuestionForm
    elif question_type == 'true_false':
        return TrueFalseQuestionForm

@app.route('/handle_enrollment/<int:student_id>/<int:subject_id>/<string:action>', methods=['POST'])
@login_required
def handle_enrollment(student_id, subject_id, action):
    # Redirect to the subject blueprint's handle_enrollment function
    return redirect(url_for('subject.handle_enrollment', student_id=student_id, subject_id=subject_id, action=action))
    flash(f'An error occurred while processing the enrollment request: {str(e)}')
    
    return redirect(url_for('dashboard'))

@app.route('/drop_subject/<int:subject_id>', methods=['POST'])
@login_required
def drop_subject(subject_id):
    # Check if the user is a student
    if current_user.role != 'student':
        flash('Only students can drop subjects.')
        return redirect(url_for('dashboard'))
    
    # Find the enrollment record
    enrollment = StudentSubject.query.filter_by(
        student_id=current_user.id,
        subject_id=subject_id
    ).first_or_404()
    
    try:
        # Delete the enrollment
        db.session.delete(enrollment)
        db.session.commit()
        flash('You have successfully dropped the subject.')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while dropping the subject.')
    
    return redirect(url_for('dashboard'))

@app.route('/delete_quiz/<int:quiz_id>', methods=['POST'])
@login_required
def delete_quiz(quiz_id):
    if current_user.role != 'teacher':
        flash('Only teachers can delete quizzes.')
        return redirect(url_for('dashboard'))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.user_id != current_user.id:
        flash('You do not have permission to delete this quiz.')
        return redirect(url_for('dashboard'))
    
    try:
        # Delete all related submissions first
        QuizSubmission.query.filter_by(quiz_id=quiz.id).delete()
        
        # Delete all questions associated with this quiz
        Question.query.filter_by(quiz_id=quiz.id).delete()
        
        # Finally delete the quiz
        db.session.delete(quiz)
        db.session.commit()
        flash(f'Quiz "{quiz.title}" deleted successfully!')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the quiz.')
    
    return redirect(url_for('dashboard'))

@app.route('/view_quiz/<int:quiz_id>')
@login_required
def view_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    subject = quiz.subject
    
    # Check if user has permission to view this quiz
    if current_user.role == 'teacher' and subject.teacher_id != current_user.id:
        flash('You do not have permission to view this quiz.')
        return redirect(url_for('dashboard'))
    elif current_user.role == 'student':
        if subject not in current_user.enrolled_subjects:
            flash('You are not enrolled in this subject.')
            return redirect(url_for('dashboard'))
        
        # Check if student has submitted the quiz
        submission = QuizSubmission.query.filter_by(
            student_id=current_user.id,
            quiz_id=quiz_id
        ).first()
        
        if not submission or not submission.submitted_at:
            # If no submission or quiz not submitted, redirect to take quiz page
            return redirect(url_for('take_quiz', quiz_id=quiz_id))
    
    return render_template('auth/view_quiz.html', quiz=quiz)

@app.route('/enroll_student', methods=['POST'])
@login_required
def enroll_student():
    if current_user.role != 'student':
        flash('Only students can enroll in subjects.')
        return redirect(url_for('dashboard'))
    
    subject_code = request.form.get('subject_code')
    if not subject_code:
        flash('Please provide a subject code.')
        return redirect(url_for('dashboard'))
    
    subject = Subject.query.filter_by(subject_code=subject_code).first()
    if not subject:
        flash('Invalid subject code. Please check and try again.')
        return redirect(url_for('dashboard'))
    
    if subject in current_user.enrolled_subjects:
        flash('You are already enrolled in this subject.')
        return redirect(url_for('dashboard'))
    
    try:
        current_user.enrolled_subjects.append(subject)
        db.session.commit()
        flash(f'Successfully enrolled in {subject.name}')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while enrolling in the subject.')
    
    return redirect(url_for('dashboard'))

@app.route('/take_quiz/<int:quiz_id>')
@login_required
def take_quiz(quiz_id):
    try:
        if current_user.role != 'student':
            flash('Only students can take quizzes/exams.')
            return redirect(url_for('dashboard'))
        
        quiz = Quiz.query.get_or_404(quiz_id)
        subject = quiz.subject
        
        if subject not in current_user.enrolled_subjects:
            flash('You are not enrolled in this subject.')
            return redirect(url_for('dashboard'))
        
        # Check if quiz has started
        now = datetime.utcnow()
        if quiz.start_time:
            # Ensure both times are naive UTC for comparison
            start_time_naive = quiz.start_time
            if hasattr(quiz.start_time, 'tzinfo') and quiz.start_time.tzinfo:
                import pytz
                # Convert to UTC then remove timezone info
                start_time_naive = quiz.start_time.astimezone(pytz.UTC).replace(tzinfo=None)
            
            if now < start_time_naive:
                # Format the time with timezone information for clarity
                formatted_time = quiz.start_time.strftime("%Y-%m-%d %H:%M")
                flash(f'This {quiz.quiz_type} is not yet available. It starts at {formatted_time} UTC')
                return redirect(url_for('dashboard'))
        
        # Get or create quiz submission with transaction
        try:
            # First check if there's a completed submission
            completed_submission = QuizSubmission.query.filter_by(
                student_id=current_user.id,
                quiz_id=quiz_id,
                submitted_at=db.not_(None)  # Only get submissions that have been completed
            ).first()
            
            if completed_submission:
                flash(f'You have already completed this {quiz.quiz_type}.')
                return redirect(url_for('dashboard'))
            
            # Get or create an in-progress submission
            quiz_submission = QuizSubmission.query.filter_by(
                student_id=current_user.id,
                quiz_id=quiz_id,
                submitted_at=None  # Only get submissions that haven't been completed
            ).with_for_update().first()
            
            # Create new quiz submission if none exists
            if not quiz_submission:
                quiz_submission = QuizSubmission(
                    student_id=current_user.id,
                    quiz_id=quiz_id,
                    start_time=now
                )
                db.session.add(quiz_submission)
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'Error accessing quiz. Please try again. {str(e)}')
            return redirect(url_for('dashboard'))
        
        # Check if time limit has expired
        remaining_time = None
        if quiz.duration:
            time_elapsed = (now - quiz_submission.start_time).total_seconds() / 60
            if time_elapsed >= quiz.duration:
                try:
                    # Get existing submissions
                    existing_submissions = StudentSubmission.query.filter_by(
                        student_id=current_user.id,
                        quiz_submission_id=quiz_submission.id
                    ).all()
                    existing_question_ids = [sub.question_id for sub in existing_submissions]
                    
                    # Create "Missing" submissions for unanswered questions
                    for question in quiz.questions:
                        if question.id not in existing_question_ids:
                            missing_submission = StudentSubmission(
                                student_id=current_user.id,
                                question_id=question.id,
                                quiz_submission_id=quiz_submission.id,
                                submitted_answer="Missing",  # Mark as missing
                                is_correct=False,
                                score=0.0,
                                submitted_at=now
                            )
                            db.session.add(missing_submission)
                    
                    # Mark quiz as submitted
                    quiz_submission.submitted_at = now
                    quiz_submission.duration_taken = quiz.duration
                    quiz_submission.total_score = sum([sub.score for sub in existing_submissions])
                    
                    # Create announcement for the teacher
                    missing_count = len(quiz.questions) - len(existing_submissions)
                    missing_info = f" ({missing_count} questions unanswered)" if missing_count > 0 else ""
                    announcement = Announcement(
                        title=f'New Submission Received (Time Expired){missing_info}',
                        content=f'{current_user.username} ran out of time on {quiz.quiz_type} "{quiz.title}" for {subject.name}.{missing_info}',
                        user_id=current_user.id,
                        subject_id=subject.id,
                        quiz_id=quiz.id,
                        submission_id=quiz_submission.id,
                        announcement_type='submission_received'
                    )
                    db.session.add(announcement)
                    
                    db.session.commit()
                    flash(f'Time limit for this {quiz.quiz_type} has expired! Your answers have been automatically submitted.')
                    return redirect(url_for('dashboard'))
                except Exception as e:
                    db.session.rollback()
                    flash(f'Error submitting quiz: {str(e)}. Please try again.')
                    return redirect(url_for('dashboard'))
            remaining_time = quiz.duration - int(time_elapsed)
        
        # Get unanswered questions with transaction
        try:
            answered_questions = StudentSubmission.query.filter(
                StudentSubmission.student_id == current_user.id,
                StudentSubmission.question_id.in_([q.id for q in quiz.questions])
            ).with_for_update().all()
            
            answered_question_ids = [sub.question_id for sub in answered_questions]
            unanswered_questions = [q for q in quiz.questions if q.id not in answered_question_ids]
            
            if not unanswered_questions:
                quiz_submission.submitted_at = now
                quiz_submission.total_score = sum([sub.score for sub in quiz_submission.question_submissions])
                if quiz.duration:
                    quiz_submission.duration_taken = int((now - quiz_submission.start_time).total_seconds() / 60)
                db.session.commit()
                flash(f'You have completed this {quiz.quiz_type}!')
                return redirect(url_for('dashboard'))
            
            # Create a form for CSRF protection
            form = FlaskForm()
            
            return render_template('auth/take_quiz.html',
                                quiz=quiz,
                                questions=quiz.questions,
                                remaining_time=remaining_time,
                                form=form)
        except Exception:
            db.session.rollback()
            flash('Error loading questions. Please try again.')
            return redirect(url_for('dashboard'))
            
    except Exception as e:
        flash('An unexpected error occurred. Please try again.')
        return redirect(url_for('dashboard'))

@app.route('/submit_quiz/<int:quiz_id>', methods=['POST'])
@login_required
def submit_quiz(quiz_id):
    if current_user.role != 'student':
        flash('Only students can submit quizzes/exams.')
        return redirect(url_for('dashboard'))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    subject = quiz.subject
    
    if subject not in current_user.enrolled_subjects:
        flash('You are not enrolled in this subject.')
        return redirect(url_for('dashboard'))
    
    # Get quiz submission - only get in-progress submissions
    quiz_submission = QuizSubmission.query.filter_by(
        student_id=current_user.id,
        quiz_id=quiz_id,
        submitted_at=None  # Only get submissions that haven't been completed
    ).first()
    
    if not quiz_submission:
        # Check if there's a completed submission
        completed_submission = QuizSubmission.query.filter_by(
            student_id=current_user.id,
            quiz_id=quiz_id,
            submitted_at=db.not_(None)  # Only get submissions that have been completed
        ).first()
        
        if completed_submission:
            flash(f'You have already submitted this {quiz.quiz_type}.')
        else:
            flash('No active quiz session found.')
        return redirect(url_for('dashboard'))
    
    form = FlaskForm()  # For CSRF protection
    if form.validate_on_submit():
        try:
            # First clear any existing submissions that might be orphaned
            StudentSubmission.query.filter_by(
                student_id=current_user.id,
                quiz_submission_id=quiz_submission.id
            ).delete()
            
            quiz_submission.submitted_at = datetime.utcnow()
            
            total_score = 0.0
            missing_questions = 0
            
            for question in quiz.questions:
                answer = request.form.get(f'answer_{question.id}')
                
                # Handle missing answers - mark as "Missing" instead of requiring all answers
                if answer is None or not answer.strip():
                    # Create a submission with "Missing" as the answer
                    submission = StudentSubmission(
                        student_id=current_user.id,
                        question_id=question.id,
                        quiz_submission_id=quiz_submission.id,
                        submitted_answer="Missing",  # Mark as missing
                        is_correct=False,  # Explicitly set to False for missing answers
                        score=0.0,
                        submitted_at=datetime.utcnow()
                    )
                    missing_questions += 1
                else:
                    # Process normal answer
                    is_correct = question.validate_answer(answer)
                    
                    # Ensure is_correct is always a boolean, never None
                    if is_correct is None:
                        is_correct = False
                        
                    score = question.points if is_correct else 0.0
                    total_score += score
                    
                    submission = StudentSubmission(
                        student_id=current_user.id,
                        question_id=question.id,
                        quiz_submission_id=quiz_submission.id,
                        submitted_answer=answer,
                        is_correct=is_correct,
                        score=score,
                        submitted_at=datetime.utcnow()
                    )
                
                db.session.add(submission)
            
            quiz_submission.total_score = total_score
            if quiz.duration:
                now = datetime.utcnow()
                quiz_submission.duration_taken = int((now - quiz_submission.start_time).total_seconds() / 60)
            
            # Create announcement for the teacher about the submission
            missing_info = f" ({missing_questions} questions unanswered)" if missing_questions > 0 else ""
            announcement = Announcement(
                title=f'New Submission Received{missing_info}',
                content=f'{current_user.username} has submitted {quiz.quiz_type} "{quiz.title}" for {subject.name}.{missing_info}',
                user_id=current_user.id,
                subject_id=subject.id,
                quiz_id=quiz.id,
                submission_id=quiz_submission.id,
                announcement_type='submission_received'
            )
            db.session.add(announcement)
            
            db.session.commit()
            
            if missing_questions > 0:
                flash(f'Your {quiz.quiz_type} has been submitted with {missing_questions} unanswered questions.')
            else:
                flash(f'Your {quiz.quiz_type} has been submitted successfully!')
                
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while submitting your answers: {str(e)}')
            return redirect(url_for('take_quiz', quiz_id=quiz_id))
    
    flash('Invalid form submission.')
    return redirect(url_for('take_quiz', quiz_id=quiz_id))

# Logout route is already defined at the top of the file
# Removed duplicate route to fix AssertionError

# Redirect old quiz creation route to new blueprint
@app.route('/create_quiz')
@login_required
def create_quiz_redirect():
    return redirect(url_for('quiz.create_quiz'))

@app.route('/mark_announcement_read/<int:announcement_id>', methods=['POST'])
@login_required
def mark_announcement_read(announcement_id):
    announcement = Announcement.query.get_or_404(announcement_id)
    
    # Check if user has permission to mark this announcement as read
    if current_user.role == 'teacher' and announcement.announcement_type == 'submission_received':
        # For teachers, they can mark submission announcements as read
        quiz = announcement.quiz
        if quiz.user_id != current_user.id:
            flash('You do not have permission to mark this announcement as read.')
            return redirect(url_for('dashboard'))
    elif current_user.role == 'student' and announcement.announcement_type == 'quiz_created':
        # For students, they can mark quiz announcements as read
        subject = announcement.subject
        if subject not in current_user.enrolled_subjects:
            flash('You do not have permission to mark this announcement as read.')
            return redirect(url_for('dashboard'))
    else:
        flash('You do not have permission to mark this announcement as read.')
        return redirect(url_for('dashboard'))
    
    announcement.is_read = True
    db.session.commit()
    
    return redirect(url_for('dashboard'))

    
@app.route('/add_quiz_question', methods=['POST'])
@login_required
def add_quiz_question():
    if current_user.role != 'teacher':
        flash('Only teachers can add questions.')
        return redirect(url_for('dashboard'))
    
    quiz_setup = session.get('quiz_setup')
    if not quiz_setup:
        flash('No active quiz setup session.')
        return redirect(url_for('create_quiz'))
    
    quiz = Quiz.query.get_or_404(quiz_setup['quiz_id'])
    if quiz.user_id != current_user.id:
        flash('You do not have permission to modify this quiz.')
        return redirect(url_for('dashboard'))
    
    try:
        question_text = request.form.get('question_text')
        question_type = request.form.get('question_type')
        points = request.form.get('points', type=float)
        
        if not all([question_text, question_type, points]):
            flash('Please fill in all required fields.')
            return redirect(url_for('create_quiz'))
        
        question = Question(
            question_text=question_text,
            question_type=question_type,
            points=points,
            user_id=current_user.id,
            subject_id=quiz.subject_id,
            quiz_id=quiz.id,
            order_index=quiz_setup['questions_added']
        )
        
        if question_type == 'multiple_choice':
            options = [request.form.get(f'options-{i}') for i in range(4)]
            if not all(options):
                flash('Please fill in all options for multiple choice question.')
                return redirect(url_for('create_quiz'))
            question.options = options
            question.correct_answer = request.form.get('correct_option')
        elif question_type in ['identification', 'true_false']:
            question.correct_answer = request.form.get('correct_answer')
        elif question_type == 'essay':
            word_limit = request.form.get('word_limit', type=int)
            correct_answer = request.form.get('correct_answer', '')
            
            question.word_limit = word_limit
            question.correct_answer = correct_answer
        
        db.session.add(question)
        db.session.commit()  # Commit before updating session to ensure question is saved
        
        quiz_setup['questions_added'] += 1
        session.modified = True
        
        if quiz_setup['questions_added'] >= quiz_setup['question_count']:
            session.pop('quiz_setup')
            flash('All questions have been added successfully!')
            return redirect(url_for('dashboard'))
        
        flash('Question added successfully!')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while adding the question: {str(e)}')
    
    return redirect(url_for('create_quiz'))

@app.route('/chess_game')
def chess_game():
    return render_template('chess.html')

if __name__ == '__main__':
    app.run(debug=True)