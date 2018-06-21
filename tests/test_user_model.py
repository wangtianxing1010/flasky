import unittest
from app.models import User, Role, AnonymousUser, Permission, Follow
from app import create_app, db
import time
from datetime import datetime

class UserModelTestCase(unittest.TestCase):
	def setUp(self):
		self.app= create_app('testing')
		self.app_context=self.app.app_context()
		self.app_context.push()
		db.create_all()
		Role.insert_roles()
		
	def tearDown(self):
		db.session.remove()
		db.drop_all()
		self.app_context.pop()
	
	def test_password_setter(self):
		u=User(password='cat')
		self.assertTrue(u.password_hash is not None)
				
	def test_no_password_getter(self):
		u=User(password='cat')
		with self.assertRaises(AttributeError):
			u.password
		
	def test_password_verification(self):
		u=User(password='cat')
		self.assertTrue(u.verify_password('cat'))
		self.assertFalse(u.verify_password('dog'))
		
	def test_password_salts_are_random(self):# what is self here? how does the func work actually? A:User table??
		u1=User(password='cat')
		u2=User(password='cat')
		self.assertTrue(u1.password_hash != u2.password_hash)
		
	def test_valide_confirmation_token(self):
		u=User(password='cat')
		db.session.add(u)
		db.session.commit()
		token=u.generate_confirmation_token()
		self.assertTrue(u.confirm(token))
		
	'''	s=Serializer(current_app.config['SECRET_KEY'],expiration)
		token=s.dumps({'confirm':self.id})
		data.loads(token)
		self.assertFalse(data is not None)'''
		
	def test_invalide_confirmation_token(self):
		u1=User(password='cat')
		u2=User(password='dog')
		db.session.add(u1)
		db.session.add(u2)
		db.session.commit()
		token=u1.generate_confirmation_token()
		self.assertFalse(u2.confirm(token))
		
	def test_expired_confirmation_token(self):
		u=User(password='cat')
		db.session.add(u)
		db.session.commit()
		token=u.generate_confirmation_token(1)
		time.sleep(2)
		self.assertFalse(u.confirm(token))

	def test_roles_and_permissions(self):#test user default as user role.
		Role.insert_roles()
		u=User(email='john@example.com',password='cats')
		self.assertTrue(u.can(Permission.WRITE_ARTICLES))
		self.assertFalse(u.can(Permission.MODERATE_COMMENTS))
		
	def test_anonymous_user(self):
		u=AnonymousUser()
		self.assertFalse(u.can(Permission.FOLLOW))
		
	def test_follows(self):
		u1 = User(email='john@example.com', password='cat')
		u2 = User(email='susan@example.org', password='dog')
		db.session.add(u1)
		db.session.add(u2)
		db.session.commit()
		self.assertFalse(u1.is_following(u2))
		self.assertFalse(u1.is_followed_by(u2))
		timestamp_before = datetime.utcnow()
		u1.follow(u2)
		db.session.add(u1)
		db.session.commit()
		timestamp_after = datetime.utcnow()
		self.assertTrue(u1.is_following(u2))
		self.assertFalse(u1.is_followed_by(u2))
		self.assertTrue(u2.is_followed_by(u1))
		self.assertTrue(u1.followed.count() == 1)
		self.assertTrue(u2.followers.count() == 1)
		f = u1.followed.all()[-1]
		self.assertTrue(f.followed == u2)
		self.assertTrue(timestamp_before <= f.timestamp <= timestamp_after)
		f = u2.followers.all()[-1]
		self.assertTrue(f.follower == u1)
		u1.unfollow(u2)
		db.session.add(u1)
		db.session.commit()
		self.assertTrue(u1.followed.count() == 0)
		self.assertTrue(u2.followers.count() == 0)
		self.assertTrue(Follow.query.count() == 0)
		u2.follow(u1)
		db.session.add(u1)
		db.session.add(u2)
		db.session.commit()
		db.session.delete(u2)
		db.session.commit()
		self.assertTrue(Follow.query.count() == 0)		
		
		