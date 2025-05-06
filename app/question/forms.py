"""Forms for question module"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, FloatField, FieldList, FormField, HiddenField
from wtforms.validators import DataRequired, Optional, NumberRange, Length, ValidationError

class BaseQuestionForm(FlaskForm):
    """Base form for all question types"""
    question_text = TextAreaField('Question Text', validators=[DataRequired(), Length(max=500)])
    question_type = SelectField('Question Type', choices=[
        ('multiple_choice', 'Multiple Choice'),
        ('identification', 'Identification'),
        ('true_false', 'True/False'),
        ('essay', 'Essay')
    ], validators=[DataRequired()])
    points = FloatField('Points', validators=[DataRequired(), NumberRange(min=0.1)], default=1.0)
    order_index = IntegerField('Order Index', validators=[DataRequired(), NumberRange(min=0)], default=0)

class MultipleChoiceQuestionForm(BaseQuestionForm):
    """Form for multiple choice questions"""
    options = FieldList(StringField('Option', validators=[DataRequired(), Length(max=200)]), min_entries=4, max_entries=4)
    correct_option = SelectField('Correct Answer', choices=[], validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.question_type.data = 'multiple_choice'
        self.correct_option.choices = [(str(i), f'Option {i+1}') for i in range(4)]

    def validate_options(self, field):
        # First check if all options have data
        if any(not option.data for option in field):
            raise ValidationError('All options must be filled out')
        # Then check for uniqueness after stripping whitespace
        stripped_options = [option.data.strip() for option in field]
        if len(set(stripped_options)) != len(field):
            raise ValidationError('All options must be unique')

class IdentificationQuestionForm(BaseQuestionForm):
    """Form for identification questions"""
    correct_answer = StringField('Correct Answer', validators=[DataRequired(), Length(max=200)])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.question_type.data = 'identification'

class TrueFalseQuestionForm(BaseQuestionForm):
    """Form for true/false questions"""
    correct_answer = SelectField('Correct Answer',
        choices=[('true', 'True'), ('false', 'False')],
        validators=[DataRequired()],
        default='true'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.question_type.data = 'true_false'

class EssayQuestionForm(BaseQuestionForm):
    """Form for essay questions"""
    word_limit = IntegerField('Word Limit', validators=[Optional(), NumberRange(min=1)], default=500)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.question_type.data = 'essay'

def get_question_form(question_type):
    """Factory function to get the appropriate question form based on type"""
    form_classes = {
        'multiple_choice': MultipleChoiceQuestionForm,
        'identification': IdentificationQuestionForm,
        'true_false': TrueFalseQuestionForm,
        'essay': EssayQuestionForm
    }
    return form_classes.get(question_type, BaseQuestionForm)()