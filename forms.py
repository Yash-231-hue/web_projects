from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, DateField, TimeField
from wtforms.validators import DataRequired, Email, EqualTo, Length

# --- Register Form ---
class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=30)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    contact = StringField('Contact Number', validators=[DataRequired(), Length(min=10, max=15)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

# --- Login Form ---
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# --- Doctor Form (admin only) ---
class DoctorForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    degree = StringField('Degree', validators=[DataRequired()])
    specialization = StringField('Specialization', validators=[DataRequired()])
    bio = TextAreaField('Bio', validators=[DataRequired(), Length(max=500)])
    submit = SubmitField('Add Doctor')

# --- Appointment Form (for users) ---
class AppointmentForm(FlaskForm):
    date = DateField('Date', validators=[DataRequired()])
    time = TimeField('Time', validators=[DataRequired()])
    submit = SubmitField('Book Appointment')
