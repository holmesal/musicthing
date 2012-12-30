from google.appengine.ext import ndb
from google.appengine.api import taskqueue
import handlers
import jinja2
import logging
import models
import os
import random
import webapp2
import json


class NewUserHandler(handlers.UserHandler):
	'''
	Handle new user signups
	'''
	def get(self):
		'''
		This handler primarily writes out the new user page
		'''
		
		'''
		You should check if they're already logged in, and redirect appropriately if so
		'''
		
		template_values = {
		}
		
		jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
		template = jinja_environment.get_template('templates/build_user.html')
		self.response.out.write(template.render(template_values))
		
	def post(self):
		'''
		This handler grabs the inputs from the new user page, and either writes out an error
			(if some of the information is incorrect)
			or creates the user and redirects to the music page
		'''
		serendipity	=	self.request.get("serendipity",-1)
		email 		=	self.request.get("email",'')
		pw			=	self.request.get("pw",'')
		submit_type =	self.request.get("submit")
		tags		=	json.loads(self.request.get("tags","{}")) #NOTE - this currently crashes if tags is empty
		try:
			'''
			You should check the following statements:
			1. tags is not empty
			2. serendipity is an integer between 0 and 255
			3. email is not already in the database
			4. email is valid (grab the regex from the wayfare or levr pages)
			5. pw is valid (see above)
			'''
			# assure that all fields are passed
			assert tags, 'You did not select any tags!'
			assert serendipity, 'You did not choose a serendipity level!'
			
			# validate serendipity
			try:
				serendipity = int(serendipity)
				assert serendipity >-1 and serendipity < 256, \
					'Serendipity must be an integer in range 0-255'
			except ValueError:
				assert False, 'serendipity must be an integer in range 0-255'
			
			if submit_type != 'Sign Up':
				# user did not create an account
				# preferences are only stored in the session
				self.update_session()
			else:
				# the signup button was pressed
				# Create a new user account to store preferences
				assert email, 'email is empty'
				assert pw, 'pw is empty'
				# validate email
				existing_user = models.User.query(
												models.User.email == email
												).fetch(keys_only=True)
				assert not existing_user, 'email already exists'
				
				# create a new user in the ndb
				pw,salt = self.hash_password(pw)
				logging.info('pw: {}'.format(pw))
				logging.info('salt: {}'.format(salt))
				user = models.User(
						email = email,
						pw = pw,
						salt = salt,
						serendipity = serendipity,
						tags = tags
						)
				logging.info()
				user.put()
				logging.info(user)
				uid = user.id()
				logging.info(uid)
				assert False, uid
				self.create_session(uid)
			
			
		except AssertionError,error:
			#write out all of the inputted values and tags
			template_values = {
				"error"			:	error,
				"tags"			:	json.dumps(tags),
				"serendipity"	:	serendipity,
				"email"			:	email,
				"pw"			:	pw
			}
			
			jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
			template = jinja_environment.get_template('templates/build_user.html')
			self.response.out.write(template.render(template_values))
		else:
			# send me to some sweet sweet music!
			return self.redirect('/music')
			
			
		
		
		'''
		If there is no error, create the user (if they passed signup info), 
		create the session variable, and redirect them to /music
		'''
app = webapp2.WSGIApplication([('/new',NewUserHandler)])




	