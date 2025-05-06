"""Forms for subject-related functionality"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, Regexp

class SubjectForm(FlaskForm):
    """Form for creating and editing subjects"""
    name = StringField('Subject Name', validators=[DataRequired(), Length(min=3, max=100)])
    subject_code = StringField('Subject Code', validators=[DataRequired(), Length(min=3, max=20)])
    submit = SubmitField('Create Subject')

class EnrollmentVerificationForm(FlaskForm):
    """Form for configuring enrollment verification settings"""
    domain_whitelist = TextAreaField('Email Domain Whitelist', 
                                   validators=[Optional()],
                                   description='Enter comma-separated list of allowed email domains (e.g., school.edu, university.edu)')
    
    student_id_pattern = StringField('Student ID Pattern', 
                                    validators=[Optional()],
                                    description='Enter a pattern that matches valid student IDs (e.g., "^STU\\d{6}$" for IDs like STU123456)')
    
    auto_approve_enabled = BooleanField('Enable Auto-Approval', 
                                       default=False,
                                       description='Automatically approve students who match the verification criteria')
    
    submit = SubmitField('Save Settings')