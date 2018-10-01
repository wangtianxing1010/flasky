# coding=utf-8
from flask import render_template, session, redirect, url_for, request, flash, current_app, \
    abort, make_response
import os
from ..email import send_email
from datetime import datetime
from .forms import EditProfileForm, EditProfileAdminForm, PostForm, PhotoUploadForm, AlbumForm
from . import main
from .. import db, photos
from ..models import User, Permission, Post, Role, Follow, Comment, Album, Photo
from flask_login import login_required, current_user
from ..decorators import admin_required, permission_required

import hashlib


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
        # no this means to show last post on top and then calculate the page that contains the post for rendering.
        page = (post.comments.count() - 1) // current_app.config['FLASKY_POSTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(page,
                                                                          current_app.config['FLASKY_POSTS_PER_PAGE'],
                                                                          error_out=False)
    comments = pagination.items
    return render_template('post.html', posts=[post], form=form, comments=comments, pagination=pagination)


@main.route('/edit_post/<int:id>', methods=['POST', 'GET'])
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
def unfollow(username):
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
    return render_template('follows.html', title='Followers of ', user=user, endpoint='.followers',
                           pagination=pagination,
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
    return render_template('follows.html', title='Followed by ', user=user, endpoint='.followed_by',
                           pagination=pagination,
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


import PIL
from PIL import Image

from flask import send_from_directory


@main.route('/uploads/<photo_filename>')
def uploaded_file(photo_filename):
    return send_from_directory(current_app.config['UPLOADED_PHOTOS_DEST'],
                               photo_filename)


def crop_medium(image):
    name_root, ext = os.path.splitext(image)
    base_width = 80
    img = Image.open(photos.path(image))
    if not img.size[0]<=80:
        # return photos.url(image)
        w_percent = (base_width/float(img.size[0]))
        height = int((float(img.size[1])*float(w_percent)))
        img = img.resize((base_width, height), PIL.Image.ANTIALIAS)
    img.save(os.path.join(current_app.config["UPLOADED_PHOTOS_DEST"], name_root+'_m'+ext))
    return url_for(".uploaded_file", photo_filename=name_root+'_m'+ext)


def crop_small(image):
    name_root, ext = os.path.splitext(image)
    base_width = 50
    img = Image.open(photos.path(image))
    if not img.size[0]<=50:
        w_percent = (base_width/float(img.size[0]))
        height = int((float(img.size[1])*float(w_percent)))
        img = img.resize((base_width, height), PIL.Image.ANTIALIAS)
    img.save(os.path.join(current_app.config["UPLOADED_PHOTOS_DEST"], name_root+'_s'+ext))
    return url_for(".uploaded_file", photo_filename=name_root+'_s'+ext)


# photo upload
@login_required
def upload_photos(album=None):
    for f in request.files.getlist('photos'):
        # user_root_folder = hashlib.md5(username[5].encode("utf-8")).hexdigest()
        photo_filename = photos.save(f)  # save to the disk
        photo_url = photos.url(photo_filename)
        url_s = crop_small(photo_filename)
        url_m = crop_medium(photo_filename)
        foto = Photo(url=photo_url, url_s=url_s, url_m=url_m, filename=photo_filename,
                     album=album, author=current_user._get_current_object())  # photo instance representation in database
        db.session.add(foto)


@main.route('/<username>/albums/', methods=['POST','GET'])
def albums(username):
    title = "ALBUMS"
    form = PhotoUploadForm()
    user = User.query.filter_by(username=username).first()
    page = request.args.get('page', 1, type=int)
    pagination = user.photos.order_by(Photo.timestamp.desc()).paginate(page, current_app.config['FLASKY_POSTS_PER_PAGE'],
                                                                     error_out=False)
    album_list = user.albums.order_by(Album.timestamp.desc()).all()
    foto_instance_list = pagination.items
    if form.validate_on_submit() and user.is_authenticated and user == current_user._get_current_object():
        if request.method == "POST" and "photos" in request.files:
            upload_photos()
        return redirect(url_for(".albums", username=username))
    return render_template('albums.html', user=user, form=form, foto_instance_list=foto_instance_list, album_list=album_list, title=title)


@main.route('/albums/<int:id>/', methods=['POST','GET'])
def album(id):
    album = Album.query.get_or_404(id)
    user = album.author
    form = PhotoUploadForm()
    title = "Album: %s" % album.title
    page = request.args.get('page', 1, type=int)
    pagination = album.photos.order_by(Photo.timestamp.desc()).paginate(page, current_app.config['FLASKY_POSTS_PER_PAGE'],
                                                                     error_out=False)

    foto_instance_list = pagination.items
    return render_template('albums.html', user=user, form=form, foto_instance_list=foto_instance_list, title=title)


@main.route("/albums/create_album/", methods=["POST", "GET"])
@login_required
def create_album():
    form = AlbumForm()
    if form.validate_on_submit():
        title = form.title.data
        about = form.about.data
        author = current_user._get_current_object()
        album = Album(title=title, about=about, author=author)
        db.session.add(album)
        if request.method == "POST" and "photos" in request.files:
            upload_photos(album)
        return redirect(url_for(".albums", username=current_user.username))
    return render_template("create_album.html", form=form)


@login_required
@main.route('/albums/delete_album/<int:id>', methods=['POST','GET'])
def delete_album(id):
    album = Album.query.get_or_404(id)
    username = album.author.username
    if current_user != album.author:
        abort(403)
    db.session.delete(album)
    return redirect(url_for('.albums', username=username))


@main.route("/open/<int:id>/")
def open_photo(id):
    photo_filename = Photo.query.get_or_404(id).filename
    file_url = photos.url(photo_filename)
    return render_template('photo.html', file_url=file_url)


def delete_foto_and_file(foto):
    if not current_user.is_authenticated or foto.author != current_user:
        abort(403)
    photo_filename = foto.filename
    file_path = photos.path(photo_filename)
    if file_path:
        try:
            os.remove(file_path)
            flash("file regular size deleted")
        except OSError:
            flash("file regular size doesn't exist")
            pass
    name_root, ext = os.path.splitext(photo_filename)
    medium_file_path = photos.path(name_root+'_m'+ext)
    if medium_file_path:
        try:
            os.remove(medium_file_path)
            flash("file medium size deleted")
        except OSError:
            flash("file medium doesn't exist")
    small_file_path = photos.path(name_root+'_s'+ext)
    if small_file_path:
        try:
            os.remove(small_file_path)
            flash("file small size deleted")
        except OSError:
            flash("file small doesn't exist")
    db.session.delete(foto)
    db.session.commit()
    flash("foto deleted")


@main.route("/delete_photo/<int:id>/")
@login_required
def delete_photo(id):
    foto = Photo.query.get_or_404(id)
    username = foto.author.username
    delete_foto_and_file(foto)
    # if redirection:
    #     return redirect(url_for(".album", id=redirection))
    return redirect(url_for('.albums', username=username))


@main.route("/delete_all_photo/")
@login_required
def delete_all():
    fotos = Photo.query.filter_by(author=current_user).all()
    username = current_user.username
    for foto in fotos:
        delete_foto_and_file(foto)
    return redirect(url_for('.albums', username=username))
