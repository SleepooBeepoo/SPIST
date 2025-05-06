from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, EmailField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password', message='Passwords must match')])
    submit = SubmitField('Change Password')

class UpdateProfileForm(FlaskForm):
    username = StringField('Username', validators=[Optional(), Length(min=4, max=20)])
    email = EmailField('Email', validators=[Optional(), Email()])
    submit = SubmitField('Update Profile')