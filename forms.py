from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, IntegerField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Length, EqualTo, NumberRange

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=50)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=0, max=120)])
    gender = SelectField('Gender', choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], validators=[DataRequired()])
    weight = IntegerField('Weight (kg)', validators=[DataRequired()])
    height = IntegerField('Height (cm)', validators=[DataRequired()])

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

class MedicalHistoryForm(FlaskForm):
    past_medications = TextAreaField('Past Medications')
    allergies = TextAreaField('Allergies')
    medical_conditions = TextAreaField('Medical Conditions')

class ProfileUpdateForm(FlaskForm):
    age = IntegerField('Age', validators=[NumberRange(min=0, max=120)])
    gender = SelectField('Gender', choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')])
    weight = IntegerField('Weight (kg)', validators=[NumberRange(min=0)])
    height = IntegerField('Height (cm)', validators=[NumberRange(min=0)])

class ForgotPasswordForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])

class AdminLoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])