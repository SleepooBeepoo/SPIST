"""Forms for quiz module"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, FloatField, FieldList, FormField, HiddenField
from wtforms.validators import DataRequired, Optional, NumberRange, Length
from datetime import datetime

class QuizSetupForm(FlaskForm):
    """Form for setting up a new quiz"""
    title = StringField('Quiz Title', validators=[DataRequired(), Length(max=100)])
    subject_id = SelectField('Subject', validators=[DataRequired()], coerce=int)
    quiz_type = SelectField('Type', choices=[('quiz', 'Quiz'), ('exam', 'Exam')], validators=[DataRequired()])
    question_count = IntegerField('Number of Questions', validators=[DataRequired(), NumberRange(min=1, max=50)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    duration = IntegerField('Time Limit (minutes)', validators=[Optional(), NumberRange(min=1)])
    start_time = StringField('Start Time (YYYY-MM-DD HH:MM)', validators=[Optional()])

class BaseQuestionForm(FlaskForm):
    """Base form for all question types"""
    quiz_id = HiddenField('Quiz ID', validators=[DataRequired()])
    current_question = HiddenField('Current Question', validators=[DataRequired()])
    total_questions = HiddenField('Total Questions', validators=[DataRequired()])
    question_text = TextAreaField('Question Text', validators=[DataRequired(), Length(max=500)])
    question_type = SelectField('Question Type', choices=[
        ('multiple_choice', 'Multiple Choice'),
        ('identification', 'Identification'),
        ('true_false', 'True/False'),
        ('essay', 'Essay')
    ], validators=[DataRequired()])
    points = FloatField('Points', validators=[DataRequired(), NumberRange(min=0.1)], default=1.0)
    order_index = IntegerField('Order Index', validators=[Optional(), NumberRange(min=0)], default=0)

class MultipleChoiceQuestionForm(BaseQuestionForm):
    """Form for multiple choice questions"""
    option1 = StringField('Option 1', validators=[DataRequired(), Length(max=200)])
    option2 = StringField('Option 2', validators=[DataRequired(), Length(max=200)])
    option3 = StringField('Option 3', validators=[DataRequired(), Length(max=200)])
    option4 = StringField('Option 4', validators=[DataRequired(), Length(max=200)])
    correct_option = SelectField('Correct Answer', choices=[
        ('0', 'Option 1'),
        ('1', 'Option 2'),
        ('2', 'Option 3'),
        ('3', 'Option 4')
    ], validators=[DataRequired()])

class IdentificationQuestionForm(BaseQuestionForm):
    """Form for identification questions"""
    correct_answer = StringField('Correct Answer', validators=[DataRequired(), Length(max=200)])

class TrueFalseQuestionForm(BaseQuestionForm):
    """Form for true/false questions"""
    correct_answer = SelectField('Correct Answer',
        choices=[('true', 'True'), ('false', 'False')],
        validators=[DataRequired()],
        default='true'
    )

class EssayQuestionForm(BaseQuestionForm):
    """Form for essay questions"""
    word_limit = IntegerField('Word Limit', validators=[Optional(), NumberRange(min=1)], default=500)

def get_question_form(question_type):
    """Factory function to get the appropriate question form based on type"""
    form_classes = {
        'multiple_choice': MultipleChoiceQuestionForm,
        'identification': IdentificationQuestionForm,
        'true_false': TrueFalseQuestionForm,
        'essay': EssayQuestionForm
    }
    return form_classes.get(question_type, BaseQuestionForm)()