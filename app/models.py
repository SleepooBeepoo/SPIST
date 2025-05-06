from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class Subject(db.Model):
    """Subject model representing a class or course"""
    __tablename__ = 'subject'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subject_code = db.Column(db.String(20), unique=True, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Enrollment verification fields
    domain_whitelist = db.Column(db.Text, nullable=True)  # Comma-separated list of allowed email domains
    student_id_pattern = db.Column(db.Text, nullable=True)  # Regex pattern for valid student IDs
    auto_approve_enabled = db.Column(db.Boolean, nullable=False, default=False)  # Whether to auto-approve matching students
    
    # Relationships
    teacher = db.relationship('User', backref='subjects_taught', foreign_keys=[teacher_id])
    enrolled_students = db.relationship('User', secondary='student_subjects', backref='enrolled_subjects')
    quizzes = db.relationship('Quiz', backref='subject', lazy=True, cascade='all, delete-orphan')
    announcements = db.relationship('Announcement', backref='subject', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Subject {self.name} ({self.subject_code})>'

class StudentSubject(db.Model):
    """Association table for student-subject enrollments"""
    __tablename__ = 'student_subjects'
    
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), primary_key=True)
    enrollment_status = db.Column(db.String(20), nullable=False, default='pending')  # pending, approved, rejected
    enrolled_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    student = db.relationship('User', backref=db.backref('subject_enrollments', lazy='dynamic'))
    subject = db.relationship('Subject', backref=db.backref('student_enrollments', lazy='dynamic'))
    
    def __repr__(self):
        return f'<StudentSubject {self.student_id}-{self.subject_id} ({self.enrollment_status})>'

class User(UserMixin, db.Model):
    """User model for authentication and user management"""
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False, default='student')
    
    # Relationships
    questions = db.relationship('Question', backref='author', lazy=True, cascade='all, delete-orphan')
    submissions = db.relationship('StudentSubmission', backref='student', lazy=True, cascade='all, delete-orphan')
    announcements = db.relationship('Announcement', backref='creator', lazy=True, cascade='all, delete-orphan')
    quiz_submissions = db.relationship('QuizSubmission', backref='student', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        """Set password hash using secure method"""
        # Ensure we're using a consistent hashing method that works across all environments
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        # Make sure to commit the change after setting the password
        # The actual commit happens at the route level

    def check_password(self, password):
        """Check password against stored hash"""
        if not self.password_hash:
            return False
            
        try:
            return check_password_hash(self.password_hash, password)
        except ValueError as e:
            # If the error is due to unsupported hash type, return False
            if 'unsupported hash type' in str(e):
                return False
            # Re-raise other errors
            raise

    def is_teacher(self):
        """Check if user is a teacher"""
        return self.role == 'teacher'
    
    def is_student(self):
        """Check if user is a student"""
        return self.role == 'student'

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

class Quiz(db.Model):
    """Quiz model representing a quiz or exam"""
    __tablename__ = 'quiz'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    quiz_type = db.Column(db.String(20), nullable=False, default='quiz')  # 'quiz' or 'exam'
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    duration = db.Column(db.Integer, nullable=True)  # Duration in minutes
    start_time = db.Column(db.DateTime, nullable=True)  # When the quiz becomes available
    
    # Relationships
    questions = db.relationship('Question', backref='quiz', lazy=True, order_by='Question.order_index', cascade='all, delete-orphan')
    submissions = db.relationship('QuizSubmission', backref='quiz', lazy=True, cascade='all, delete-orphan')
    announcements = db.relationship('Announcement', backref='quiz', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Quiz {self.title} ({self.quiz_type})>'

class Question(db.Model):
    """Question model representing a quiz/exam question"""
    __tablename__ = 'question'
    
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
    
    # Relationships
    submissions = db.relationship('StudentSubmission', backref='question', lazy=True, cascade='all, delete-orphan')

    def validate_answer(self, submitted_answer):
        """Validate a submitted answer against the correct answer"""
        if submitted_answer is None or submitted_answer == "Missing":
            return False
            
        try:
            submitted = str(submitted_answer).strip()
            if not submitted:
                return False
                
            if self.question_type == 'multiple_choice':
                if not self.options or str(submitted) not in [str(i) for i in range(len(self.options))]:
                    return False
                return submitted == str(self.correct_answer).strip()
            elif self.question_type == 'identification':
                # For identification questions, compare case-insensitively
                # If exact match (case-insensitive), return True for automatic grading
                # Otherwise, return False to allow manual grading
                exact_match = submitted.lower() == str(self.correct_answer).lower().strip()
                return exact_match
                # Note: Even when this returns False, teachers can manually mark it as correct
                # during the grading process if the answer is acceptable
            elif self.question_type == 'true_false':
                valid_answers = ['true', 'false']
                if submitted.lower() not in valid_answers:
                    return False
                return submitted.lower() == str(self.correct_answer).lower().strip()
            elif self.question_type == 'essay':
                # Essay questions always need manual grading, but return False instead of None
                return False
            # Default fallback - always return a boolean, never None
            return False
        except (ValueError, AttributeError):
            # Always return a boolean in case of exceptions
            return False

    def __repr__(self):
        return f'<Question {self.id}: {self.question_text[:20]}...>'

class QuizSubmission(db.Model):
    """Quiz submission model representing a student's quiz attempt"""
    __tablename__ = 'quiz_submission'
    
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
    
    # Relationships
    question_submissions = db.relationship('StudentSubmission', backref='quiz_submission', lazy=True, cascade='all, delete-orphan')
    announcements = db.relationship('Announcement', backref='submission', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<QuizSubmission {self.student_id}-{self.quiz_id}>' 

class StudentSubmission(db.Model):
    """Student submission model representing a student's answer to a question"""
    __tablename__ = 'student_submission'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    quiz_submission_id = db.Column(db.Integer, db.ForeignKey('quiz_submission.id'), nullable=False)
    submitted_answer = db.Column(db.String(500), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False, default=False)
    submitted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    score = db.Column(db.Float, nullable=False, default=0.0)
    graded = db.Column(db.Boolean, nullable=False, default=False)
    feedback = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<StudentSubmission {self.student_id}-{self.question_id}>'

class Announcement(db.Model):
    """Announcement model for system notifications"""
    __tablename__ = 'announcement'
    
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
    
    def __repr__(self):
        return f'<Announcement {self.title}>'