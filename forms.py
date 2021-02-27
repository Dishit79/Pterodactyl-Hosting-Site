from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SubmitField,SelectField
from connection import ApiConnection


class SignUpForm(FlaskForm):
    password = PasswordField('Password')
class Dropdown(FlaskForm):
    eggs = ApiConnection().get_egg()
    nodes = ApiConnection().get_nodes()
    eggs = SelectField('Eggs',choices=[name['name'] for name in eggs])
    nodes = SelectField('Nodes',choices=[name['name'] for name in nodes])
    submit = SubmitField('Sign Up')
