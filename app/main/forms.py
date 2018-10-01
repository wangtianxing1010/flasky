from flask_wtf import Form
from wtforms import StringField, SubmitField, TextAreaField, SelectField, BooleanField
from wtforms.validators import DataRequired, Length, Email, Regexp, Required
from flask_pagedown.fields import PageDownField
from ..models import User, Role
from app.exceptions import ValidationError
from flask_wtf.file import FileField, FileAllowed, FileRequired
from .. import photos


# class NameForm(Form):
#     name = StringField('Your name please', validators=[DataRequired()])
#     submit = SubmitField('Submit')
#

class EditProfileForm(Form):
    name = StringField('name', validators=[Length(0, 16)])
    location = StringField('location', validators=[Length(0, 64)])
    about_me = TextAreaField('about me')
    submit = SubmitField('Submit')


class EditProfileAdminForm(Form):
    # administrative part
    email = StringField('email', validators=[DataRequired(), Email(), Length(1, 32)])
    username = StringField('username', validators=[DataRequired(), Length(1, 32),
                                                   Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                                          'User name must only contain letters, numbers, dots, or underscores')])
    confirmed = BooleanField('confirmed')
    role = SelectField('role', coerce=int)
    # basic part
    name = StringField('name', validators=[Length(0, 64)])
    location = StringField('location', validators=[Length(0, 64)])
    about_me = TextAreaField('about me')
    submit = SubmitField('Submit')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and \
                User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already being used!')

    def validate_username(self, field):
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already taken')


class PostForm(Form):
    body = PageDownField('What do you have in mind', validators=[DataRequired()])
    submit = SubmitField('Submit')


class CommentForm(Form):
    body = StringField('enter your comment', validators=[DataRequired()])
    submit = SubmitField('Submit')


class PhotoUploadForm(Form):
    photos = FileField('Upload Pictures', validators=[FileRequired('No files selected!'),
                                                     FileAllowed(photos, 'Please select only photos!')])
    submit = SubmitField('Upload')


class AlbumForm(Form):
    title = StringField("title", validators=[DataRequired()])
    about = TextAreaField("about", render_kw={"rows": 8})
    photos = FileField("pictures", render_kw={'multiple': True}, validators=[FileAllowed(photos, "only pictures"),
                                                                             FileRequired("please select photo")])
    # cover = db.Column(db.String(64))
    submit = SubmitField("Submit")