from flask import render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from . import auth
from .forms import LoginForm, RegisterForm
from .. import db
from ..models import User
from ..email import send_email
from wtforms import SubmitField

# @auth.route('/login', methods=['GET', 'POST'])
# def login():
#     form = LoginForm()
#     if form.validate_on_submit():
#         user = User.query.filter_by(email=form.email.data).first()
#         if user is not None and user.verify_password(form.password.data):
#             login_user(user, form.remember_me.data)
#             return redirect(request.args.get('next') or url_for('main.index'))
#         flash('Invalid username or password')
#     return render_template('auth/login.html', form=form)


@auth.route('/logout/')
@login_required
def logout():
    logout_user()
    flash('You are logged out')
    return redirect(url_for('main.index'))


# @auth.route('/register/', methods=['GET', 'POST'])
# def register():
#     form = RegisterForm()
#     if form.validate_on_submit():
#         user = User(username=form.username.data,
#                     email=form.email.data,
#                     password=form.password.data)
#         db.session.add(user)
#         db.session.commit()
#         token = user.generate_confirmation_token()
#         send_email(user.email, 'Confirm your email', 'auth/email/confirm', user=user, token=token)
#         flash('A Confirmation Email has been sent to you')
#         return redirect(url_for('main.index'))
#     return render_template('auth/register.html', form=form)

@auth.route('/sign_in_and_up/', methods=['GET', 'POST'])
def sign_in_and_up():
    class SignIn_Form(LoginForm):
        pass
    setattr(SignIn_Form, "signIn_submit", SubmitField('Sign In'))
    form1 = SignIn_Form()
    del form1.submit

    class SignUp_Form(RegisterForm):
        pass
    setattr(SignUp_Form, "signUp_submit", SubmitField('Sign Up'))
    form2 = SignUp_Form()
    del form2.submit

    if form1.signIn_submit.data and form1.validate():
        user = User.query.filter_by(email=form1.email.data).first() #if both email fields are filled what would happen when form is submitted?
        if user is not None and user.verify_password(form1.password.data):
            login_user(user, form1.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid username or password')

    if form2.signUp_submit.data and form2.validate():
        user = User(username=form2.username.data,
                    email=form2.email.data,
                    password=form2.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(user.email, 'Confirm your email', 'auth/email/confirm', user=user, token=token)
        flash('A Confirmation Email has been sent to you')
        return redirect(url_for('main.index'))
    return render_template('auth/sign_in_and_up.html', signIn_form=form1, signUp_form=form2)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash('You have confirmed your account!')
    else:
        flash('Your confirmation Link is expired or invalid!')
    return redirect(url_for('main.index'))


@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed and request.endpoint[:5] != 'auth.':
            return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, "Confirm your account",
               'auth/email/confirm', user=current_user, token=token)
    flash('A new confirmation has been sent to you')
    return redirect(url_for('main.index'))

# password updates

# password resets

# email address changes
