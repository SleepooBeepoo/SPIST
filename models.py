from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib
from datetime import datetime
import json

db = SQLAlchemy()

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subject_code = db.Column(db.String(20), unique=True, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    teacher = db.relationship('User', backref='subjects_taught', foreign_keys=[teacher_id])
    enrolled_students = db.relationship('User', secondary='student_subjects', backref='enrolled_subjects', overlaps="student_enrollments,subject_enrollments")
    quizzes = db.relationship('Quiz', backref='subject', lazy=True)

class StudentSubject(db.Model):
    __tablename__ = 'student_subjects'
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), primary_key=True)
    enrollment_status = db.Column(db.String(20), nullable=False, default='pending')  # pending, approved, rejected
    enrolled_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    student = db.relationship('User', backref=db.backref('subject_enrollments', lazy='dynamic'), overlaps="enrolled_students,enrolled_subjects")
    subject = db.relationship('Subject', backref=db.backref('student_enrollments', lazy='dynamic'), overlaps="enrolled_students,enrolled_subjects")

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False, default='student')
    questions = db.relationship('Question', backref='author', lazy=True)
    submissions = db.relationship('StudentSubmission', backref='student', lazy=True)
    announcements = db.relationship('Announcement', backref='creator', lazy=True)

    def set_password(self, password):
        # Use sha256 instead of the default scrypt which is not supported in Python 3.13
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        # For existing passwords that might be using scrypt, we need to handle the error
        try:
            return check_password_hash(self.password_hash, password)
        except ValueError as e:
            # If the error is due to unsupported hash type, return False
            if 'unsupported hash type' in str(e):
                return False
            # Re-raise other errors
            raise

    def __repr__(self):
        return f'<User {self.username}>'

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    quiz_type = db.Column(db.String(20), nullable=False, default='quiz')  # 'quiz' or 'exam'
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    questions = db.relationship('Question', backref='quiz', lazy=True, order_by='Question.order_index')
    duration = db.Column(db.Integer, nullable=True)  # Duration in minutes
    start_time = db.Column(db.DateTime, nullable=True)  # When the quiz becomes available
    
    def __repr__(self):
        return f'<Quiz {self.title}>'

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.String(500), nullable=False)
    question_type = db.Column(db.String(20), nullable=False)  # multiple_choice, identification, true_false, essay
    word_limit = db.Column(db.Integer, nullable=True)  # For essay questions
    options = db.Column(db.JSON, nullable=True)  # For multiple choice questions
    correct_answer = db.Column(db.String(500), nullable=False)
    points = db.Column(db.Float, nullable=False, default=1.0)
    order_index = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=True)
    submissions = db.relationship('StudentSubmission', backref='question_obj', lazy=True, cascade='all, delete-orphan')


    def validate_answer(self, submitted_answer):
        """Validate a submitted answer against the correct answer
        
        This method has been enhanced to handle all question types:
        - multiple_choice: Checks if the selected option index matches the correct option
        - true_false: Checks if the boolean value matches the correct answer
        - identification: Returns None as these require manual grading
        - essay: Returns None as these require manual grading
        
        Args:
            submitted_answer: The student's submitted answer
            
        Returns:
            bool: True if correct, False if incorrect, None if manual grading required
        """
        if submitted_answer is None:
            return False
            
        try:
            submitted = str(submitted_answer).strip()
            if not submitted:
                return False
                
            # For multiple choice questions
            if self.question_type == 'multiple_choice':
                if not self.options or str(submitted) not in [str(i) for i in range(len(self.options))]:
                    return False
                    
                # Auto-grade multiple choice
                return str(submitted) == str(self.correct_answer)
                
            # For true/false questions
            elif self.question_type == 'true_false':
                # Normalize the submitted answer to lowercase
                submitted_lower = submitted.lower()
                correct_lower = str(self.correct_answer).lower()
                
                # Handle different formats of true/false answers
                submitted_bool = submitted_lower in ['true', 't', '1', 'yes', 'y']
                correct_bool = correct_lower in ['true', 't', '1', 'yes', 'y']
                
                return submitted_bool == correct_bool
                
            # For identification questions - case insensitive comparison if needed
            elif self.question_type == 'identification':
                # Return None to indicate manual grading is required
                # Teachers can implement custom grading logic for identification questions
                return None
                
            # For essay questions
            elif self.question_type == 'essay':
                # Essay questions always require manual grading
                return None
                
            # Default fallback
            return False
            
        except Exception as e:
            print(f"Error validating answer: {str(e)}")
            return False

    def __repr__(self):
        return f'<Question {self.question_text[:20]}...>'



class QuizSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    submitted_at = db.Column(db.DateTime, nullable=True)  # Nullable to track in-progress quizzes
    start_time = db.Column(db.DateTime, nullable=True)  # When student starts the quiz
    duration_taken = db.Column(db.Integer, nullable=True)  # Time spent in minutes
    total_score = db.Column(db.Float, nullable=False, default=0.0)
    graded = db.Column(db.Boolean, nullable=False, default=False)
    visible_to_students = db.Column(db.Boolean, nullable=False, default=False)
    show_answers = db.Column(db.Boolean, nullable=False, default=False)  # Control whether students can see correct answers
    feedback = db.Column(db.Text, nullable=True)
    
    student = db.relationship('User', backref='quiz_submissions')
    quiz = db.relationship('Quiz', backref='submissions')
    question_submissions = db.relationship('StudentSubmission', backref='quiz_submission', lazy=True, cascade='all, delete-orphan')

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('quiz_submission.id'), nullable=True)
    announcement_type = db.Column(db.String(20), nullable=False)  # 'quiz_created', 'submission_received'
    is_read = db.Column(db.Boolean, default=False)
    
    # Relationships
    subject = db.relationship('Subject', backref='announcements')
    quiz = db.relationship('Quiz', backref='announcements')
    submission = db.relationship('QuizSubmission', backref='announcements')

    def __repr__(self):
        return f'<QuizSubmission {self.student_id}-{self.quiz_id}>'

class StudentSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    quiz_submission_id = db.Column(db.Integer, db.ForeignKey('quiz_submission.id'), nullable=False)
    submitted_answer = db.Column(db.String(500), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    submitted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    score = db.Column(db.Float, nullable=False, default=0.0)
    graded = db.Column(db.Boolean, nullable=False, default=False)
    feedback = db.Column(db.Text, nullable=True)
    
    # Explicitly define the relationship to the question
    question = db.relationship('Question', backref=db.backref('student_submissions', overlaps='submissions,question_obj'), foreign_keys=[question_id])

    def __repr__(self):
        return f'<StudentSubmission {self.student_id}-{self.question_id}>'