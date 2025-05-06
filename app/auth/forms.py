from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, EmailField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional

class LoginForm(FlaskForm):
    """Form for user login"""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    """Form for user registration"""
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    role = SelectField('Role', choices=[('student', 'Student'), ('teacher', 'Teacher')], validators=[DataRequired()])
    subject_code = StringField('Subject Code (for teachers)', validators=[Optional(), Length(min=3, max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')