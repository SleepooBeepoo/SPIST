from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, EmailField, TextAreaField, SelectField, FloatField, IntegerField, BooleanField, FieldList, FormField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, NumberRange

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    role = SelectField('Role', choices=[('student', 'Student'), ('teacher', 'Teacher')], validators=[DataRequired()])
    subject_code = StringField('Subject Code', validators=[Optional(), Length(min=3, max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')
    
    def validate_email(self, email):
        # For students, validate that email ends with @spist.edu
        if self.role.data == 'student' and not email.data.endswith('@spist.edu'):
            raise ValueError('Student email must use the school domain (@spist.edu)')
        
        # Check if email is already registered
        from models import User
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValueError('Email already registered. Please use a different email.')
        
        return True

class QuizForm(FlaskForm):
    title = StringField('Quiz Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    quiz_type = SelectField('Type', choices=[('quiz', 'Quiz'), ('exam', 'Exam')], validators=[DataRequired()])
    duration = IntegerField('Duration (minutes)', validators=[Optional(), NumberRange(min=1)])
    start_time = StringField('Start Time (YYYY-MM-DD HH:MM)', validators=[Optional()])
    submit = SubmitField('Create Quiz')

class QuestionForm(FlaskForm):
    question_text = TextAreaField('Question Text', validators=[DataRequired(), Length(max=500)])
    question_type = SelectField('Question Type', 
        choices=[
            ('multiple_choice', 'Multiple Choice'), 
            ('identification', 'Identification'),
            ('true_false', 'True/False'),
            ('enumeration', 'Enumeration')
        ], 
        validators=[DataRequired()]
    )
    answer = TextAreaField('Answer', validators=[DataRequired(), Length(max=500)])
    points = FloatField('Points', validators=[DataRequired(), NumberRange(min=0.1)], default=1.0)
    submit = SubmitField('Add Question')

class BulkQuestionForm(FlaskForm):
    question_type = SelectField('Question Type', 
        choices=[
            ('multiple_choice', 'Multiple Choice'), 
            ('identification', 'Identification'),
            ('true_false', 'True/False'),
            ('enumeration', 'Enumeration')
        ], 
        validators=[DataRequired()]
    )
    question_count = IntegerField('Number of Questions', validators=[DataRequired(), NumberRange(min=1, max=100)])
    points_per_question = FloatField('Points per Question', validators=[DataRequired(), NumberRange(min=0.1)], default=1.0)
    submit = SubmitField('Create Questions')

class GradeSubmissionForm(FlaskForm):
    score = FloatField('Score', validators=[DataRequired(), NumberRange(min=0)])
    feedback = TextAreaField('Feedback', validators=[Optional(), Length(max=500)])
    visible_to_students = BooleanField('Make Score Visible to Students')
    show_answers = BooleanField('Show Correct Answers to Students')
    submit = SubmitField('Submit Grade')
    delete = SubmitField('Delete Submission')

class CSVImportForm(FlaskForm):
    from flask_wtf.file import FileField, FileRequired, FileAllowed
    csv_file = FileField('CSV File', validators=[FileRequired(), FileAllowed(['csv'], 'CSV files only!')])
    submit = SubmitField('Import Students')