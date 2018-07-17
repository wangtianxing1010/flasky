from flask import render_template, session, redirect, url_for, request, flash, current_app, \
    abort, make_response

from ..email import send_email
from datetime import datetime
from .forms import NameForm, EditProfileForm, EditProfileAdminForm, PostForm, CommentForm
from . import main
from .. import db
from ..models import User, Permission, Post, Role, Follow, Comment
from flask_login import login_required, current_user
from ..decorators import admin_required, permission_required


@main.route('/', methods=['GET', 'POST'])
def index():
    form = PostForm()
    if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit():
        post = Post(body=form.body.data, author=current_user._get_current_object())
        db.session.add(post)
        return redirect(url_for('.index'))
    show_followed = False
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed', ''))
    if show_followed:
        query = current_user.followed_posts
    else:
        query = Post.query
    page = request.args.get('page', 1, type=int)
    pagination = query.order_by(Post.timestamp.desc()).paginate(page,
                                                                per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
                                                                error_out=False)
    posts = pagination.items
    return render_template('index.html', form=form, posts=posts, show_followed=show_followed, pagination=pagination)


'''	form = NameForm()
	user_agent= request.headers.get('User-Agent')
	if form.validate_on_submit():
		user = User.query.filter_by(username=form.name.data).first()
		if user is None:
			user = User(username = form.name.data)
			db.session.add(user)
			session['known'] = False
			if current_app.config['FLASKY_ADMIN']:
				#exported FLASKY_USERNAME INSTEAD
				send_email(current_app.config['FLASKY_ADMIN'],'New User',\
				'mail/new_user',user=user)
				flash('email sent successfully')
		else:
			session['known'] = True
			send_email(current_app.config['FLASKY_ADMIN'],'Returned',\
				'mail/old_user',user=user)
		session['name'] = form.name.data
		form.name.data = ''
		return redirect(url_for('.index'))
	return render_template('index.html', form = form, user_agent=user_agent,\
    current_time=datetime.utcnow(), name = session.get('name'),\
     known =session.get('known', False))	'''


@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    page = request.args.get('page', 1, type=int)
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(page, current_app.config['FLASKY_POSTS_PER_PAGE'],
                                                                     error_out=False)
    posts = pagination.items
    return render_template('user.html', user=user, posts=posts)


@main.route('/editprofile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me = current_user.about_me
    return render_template('edit_profile.html', form=form)


@main.route('/editprofile_admin/<int:id>', methods=['POST', 'GET'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.about_me = form.about_me.data
        user.location = form.location.data
        db.session.add(user)
        flash('user info has been updated')
        return redirect(url_for('.user',
                                username=user.username))  # why username=user.username Because username is the argument taken by endpoint function user()
    form.username.data = user.username
    form.email.data = user.email
    form.confirmed.data = user.confirmed
    form.role.data = user.role
    form.name.data = user.name
    form.about_me.data = user.about_me
    form.location.data = user.location
    return render_template('edit_profile_admin.html', form=form, user=user)


@main.route('/post/<int:id>', methods=['POST', 'GET'])
def post(id):
    post = Post.query.get_or_404(id)
    form = PostForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data, post=post, author=current_user._get_current_object())
        db.session.add(comment)
        flash('Your comment is posted successfully')
        return redirect(url_for('.post', id=post.id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:  # does this block mean paginate() can not take parameter 'page' as -1? therefore a calculation is needed?
        #no this means to show last post on top and then calculate the page that contains the post for rendering.
        page = (post.comments.count() - 1) // current_app.config['FLASKY_POSTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(page,
                                                                          current_app.config['FLASKY_POSTS_PER_PAGE'],
                                                                          error_out=False)
    comments = pagination.items
    return render_template('post.html', posts=[post], form=form, comments=comments, pagination=pagination)


@main.route('/edit_post/<int:id>', methods=['POST','GET'])
@login_required
def edit_post(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and not current_user.can(Permission.ADMINISTRATOR):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        flash('post has been updated!')
        redirect(url_for('.post', id=post.id))
    form.body.data = post.body
    return render_template('edit_post.html', form=form)

@main.route('/delete_post/<int:id>')
@login_required
def delete_post(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and not current_user.can(Permission.ADMINISTRATOR):
        abort(403)
    db.session.delete(post)
    flash('post deleted')
    return redirect(url_for('.user', username=post.author.username))


@main.route('/follow/<username>/')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid User')
        return redirect(url_for('.index'))
    if current_user.is_following(user):
        flash('you are already following this user')
        return redirect(url_for('.user', username=username))
    current_user.follow(user)
    flash('you are now following %s.' % username)
    return redirect(url_for('.user', username=username))


@main.route('/unfollow/<username>/')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(user):
    user = User.query.filter_by(username=username).first()
    # what is different for this condition block compared to the one above??
    if user is None:
        flash('Invalid User')
        return redirect(url_for('.index'))
    elif not current_user.is_following(user):
        flash("you haven\'t followed this user yet")
        return redirect(url_for('.user', username=username))
    else:
        current_user.unfollow(user)
        flash('you unfollowed %s.' % username)
        return redirect(url_for('.user', username=username))


@main.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('user is invalid')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
                                         error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp} for item in pagination.items]
    return render_template('follows.html', title='Followers of ', user=user, endpoint='.followers', pagination=pagination,
                           follows=follows)


@main.route('/followed_by/<username>')
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('user is invalid')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
                                        error_out=False)
    follows = [{'user': item.followed, 'timestamp': item.timestamp} for item in pagination.items]
    return render_template('follows.html', title='Followed by ', user=user, endpoint='.followed_by', pagination=pagination,
                           follows=follows)


@main.route('/all/')
@login_required
def show_all():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '', max_age=30 * 24 * 60 * 60)
    return resp


@main.route('/followed/')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '1', max_age=30 * 24 * 60 * 60)
    return resp


@main.route('/moderate/')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(page, per_page=current_app.config[
        'FLASKY_POSTS_PER_PAGE'], error_out=False)
    comments = pagination.items
    return render_template('moderate.html', page=page, pagination=pagination, comments=comments)


@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    return redirect(url_for('.moderate', page=request.args.get('page', 1, type=int)))


@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    return redirect(url_for('.moderate', page=request.args.get('page', 1, type=int)))

@main.route('/upload_photos/', methods=['POST','GET'])
def upload_photos():
    file = request.files['file']
    file.save(path + filename)
    return render_template('upload_photos.html')