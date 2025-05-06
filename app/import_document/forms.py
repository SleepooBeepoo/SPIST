from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, FloatField, IntegerField, FieldList, FormField, RadioField, HiddenField
from wtforms.validators import DataRequired, NumberRange, Optional

class QuestionForm(FlaskForm):
    """Form for creating and editing questions"""
    question_text = TextAreaField('Question Text', validators=[DataRequired()])
    question_type = SelectField('Question Type', choices=[
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('identification', 'Identification'),
        ('essay', 'Essay')
    ], validators=[DataRequired()])
    points = FloatField('Points', validators=[DataRequired(), NumberRange(min=0)], default=1.0)
    
    # For multiple choice questions
    options = FieldList(StringField('Option'), min_entries=5)
    correct_option = RadioField('Correct Option', choices=[(str(i), f'Option {i+1}') for i in range(5)], validators=[Optional()])
    
    # For identification questions
    correct_answer = StringField('Correct Answer', validators=[Optional()])
    
    # For essay questions
    word_limit = IntegerField('Word Limit', validators=[Optional(), NumberRange(min=0)], default=500)
    
    # For ordering questions in a quiz
    order_index = IntegerField('Order', validators=[Optional()], default=0)
    
    # For associating with a quiz
    quiz_id = HiddenField('Quiz ID')
    current_question = HiddenField('Current Question')
    total_questions = HiddenField('Total Questions')