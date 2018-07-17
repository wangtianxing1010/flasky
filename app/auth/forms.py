from flask_wtf import Form
from ..models import User
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import Required, Email, Length, Regexp, EqualTo
from wtforms import ValidationError

class LoginForm(Form):
	email = StringField('Your email please', validators=[Email(),Required(),Length(1,50)])
	password=PasswordField('password', validators=[Required()])
	remember_me=BooleanField('Keep me logged in')
	submit=SubmitField('Log In')
	
class RegisterForm(Form):
	email = StringField('your email here', validators=[Required(),Length(1,50),Email()])
	username=StringField('your username here', validators=[Required(),
							Length(1,20), Regexp('^[A-Za-z][A-Za-z0-9_.]*$',0,
							'username can only contain letters, numbers, dots or underscores'
							)])
	password=PasswordField('enter your password', validators=[Required()])
	re_enter=PasswordField('re-enter your password',validators=[Required(),\
						EqualTo('password',message='password must match')])
	#agree=BooleanField('agree or no?')
	submit=SubmitField('Register')

	def validate_username(self, field):
		if User.query.filter_by(username=field.data).first():
			raise ValidationError('username already exists')
		
	def validate_email(self, field): #variable field belongs to what? what is this method called on?
		if User.query.filter_by(email=field.data).first():
			raise ValidationError('email already being registered')