from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField,TextAreaField, SelectField, BooleanField
from wtforms.validators import Required, Length, Email, Regexp
from flask_pagedown.fields import PageDownField
from ..models import User, Role

class NameForm(Form):
	name = StringField('Your name please', validators=[Required()])
	submit=SubmitField('Submit')

class EditProfileForm(Form):
	name= StringField('name',validators=[Length(0,16)])
	location = StringField('location', validators=[Length(0,64)])
	about_me = TextAreaField('about me')
	submit = SubmitField('Submit')
	
class EditProfileAdminForm(Form):
	#administrative part
	email=StringField('email',validators=[Required(),Email(),Length(1,32)])
	username=StringField('username',validators=[Required(),Length(1,32),\
												Regexp('^[A-Za-z][A-Za-z0-9_.]*$',0,\
												'User name must only contain letters, numbers, dots, or underscores')])
	confirmed=BooleanField('confirmed')
	role=SelectField('role',coerce=int)
	#basic part
	name=StringField('name',validators=[Length(0,64)])
	location=StringField('location',validators=[Length(0,64)])
	about_me=TextAreaField('about me')
	submit=SubmitField('Submit')
	
	def __init__(self,user, *args,**kwargs):
		super(EditProfileAdminForm, self).__init__(*args, **kwargs)
		self.role.choices=[(role.id, role.name) for role in Role.query.order_by(Role.name).all()]
		self.user=user
		
	def validate_email(self, field):
		if field.data != self.user.email and \
			User.query.filter_by(email=field.data).first():
			raise ValidationError('Email already being used!')
			
	def validate_username(self, field):
		if field.data != self.user.username and \
			User.query.filter_by(username=field.data).first():
			raise ValidationError('Username already taken')

class PostForm(Form):
	body = PageDownField('What do you have in mind', validators=[Required()])
	submit=SubmitField('Submit')
	
class CommentForm(Form):
	body = StringField('enter your comment', validators=[Required()])
	submit = SubmitField('Submit')