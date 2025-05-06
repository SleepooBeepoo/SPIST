"""Forms for submission module"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, HiddenField, SubmitField, FormField, FieldList
from wtforms.validators import DataRequired, Optional, NumberRange, Length

class AnswerForm(FlaskForm):
    """Form for submitting an answer to a question"""
    question_id = HiddenField('Question ID', validators=[DataRequired()])
    answer = TextAreaField('Your Answer', validators=[DataRequired()])

class GradeQuestionForm(FlaskForm):
    """Form for grading a single question submission"""
    question_id = HiddenField('Question ID', validators=[DataRequired()])
    score = FloatField('Score', validators=[DataRequired(), NumberRange(min=0)])
    feedback = TextAreaField('Feedback', validators=[Optional(), Length(max=500)])

class GradeSubmissionForm(FlaskForm):
    """Form for grading a quiz submission"""
    quiz_submission_id = HiddenField('Quiz Submission ID', validators=[DataRequired()])
    total_score = FloatField('Total Score', validators=[DataRequired(), NumberRange(min=0)])
    question_grades = FieldList(FormField(GradeQuestionForm), min_entries=0)
    submit = SubmitField('Submit Grades')