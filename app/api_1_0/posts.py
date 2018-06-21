from flask import jsonify, request, g, abort, url_for, current_app
from .. import db
from ..models import Post, Permission
from . import api
from .decorators import permission_required
from flask_login import login_required
from .errors import forbidden

@api.route('/posts/', methods=['POST'])
@permission_required(Permission.WRITE_ARTICLES)
def new_post():
	post = Post.from_json(request.json)
	post.author = g.current_user
	db.session.add(post)
	db.session.commit()
	return jsonify(post.to_json()),201,{'location':url_for('api.get_post', id=post.id, _external=True)}
	
@api.route('/posts/')
@login_required
def get_posts():
	page = request.args.get('page', 1, type=int)
	pagination = Post.querry.paginate(page, current_app.config['FLASKY_POSTS_PER_PAGE'], error_out=False)
	posts = pagination.items
	prev = None
	if pagination.has_prev:
		prev = url_for('api.get_posts', page=page-1, _external=True)
	next= None
	if pagination.has_next:
		next = url_for('api.get_posts', page=page+1, _external=True)
	return jsonify({
		'posts':[post.to_json() for post in posts],
		'prev':prev,
		'next':next,
		'post count':pagination.total
	})
	
@api.route('/posts/<int:id>/')
@login_required
def get_post(id):
	post = Post.querry.get_or_404(id)
	return jsonify(post.to_json())
	
@api.route('/posts/<int:id>', methods=['PUT'])
@permission_required(Permission.WRITE_ARTICLES)
def edit_post(id):
	post = Post.querry.get_or_404(id)
	if g.current_user != post.author or not g.current_user.can(Permission.ADMINISTER):
		return forbidden('Insufficient Permissions')
	post.body = request.json.get('post', post.body)
	db.session.add(post)
	return jsonify(post.to_json())