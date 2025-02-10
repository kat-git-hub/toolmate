from flask_wtf import FlaskForm
from app.models import User
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    name = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    zip_code = StringField("ZIP Code", validators=[DataRequired(), Length(min=5, max=10)])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[
                              DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, name):
        user = User.query.filter_by(name=name.data).first()
        if user is not None:
            raise ValidationError('User already exists.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Email is in use.')
