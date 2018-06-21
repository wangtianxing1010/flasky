#!/usr/bin/env python

import os
from app import create_app, db
from app.models import Post, User, Role, Follow
from flask_script import Shell, Manager
from flask_migrate import Migrate, MigrateCommand

app=create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate=Migrate(app,db)
manager=Manager(app)

def make_shell_context():
	return dict(app=app, db=db, User=User,Role=Role,Post=Post,Follow=Follow)

@manager.command
def deploy():
	from flask_migrate import upgrade
	from app.models import Role, User
	
	upgrade()
	
	Role.insert_roles()
	
	User.add_self_follows()


@manager.command
def test():
	"""Run the unit tests"""
	import unittest
	tests=unittest.TestLoader().discover('tests')
	unittest.TextTestRunner(verbosity=2).run(tests)
	
manager.add_command('shell',Shell(make_context=make_shell_context))
manager.add_command('db',MigrateCommand)

if __name__=='__main__':
	manager.run()
	
#https://stackoverflow.com/questions/5918582/bash-manage-py-permission-denied?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
#https://stackoverflow.com/questions/16069816/getting-python-error-from-cant-read-var-mail-bio?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa