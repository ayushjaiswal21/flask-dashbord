from wtforms import SelectField, DateTimeField
from flask_wtf import FlaskForm

class AssignQuizForm(FlaskForm):
    classroom_id = SelectField('Classroom', coerce=int)
    due_date = DateTimeField('Due Date', format='%Y-%m-%d %H:%M')