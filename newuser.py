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
from collections import defaultdict
import re


class NewUserHandler(handlers.UserHandler):
	'''
	Handle new user signups
	'''
	def get(self):
		'''
		This handler primarily writes out the new user page
		Check login state. If a user already exists, redirect to the music page
		'''
#		try:
#			self.get_user_from_session()
#		except self.SessionError:
#			pass
#		else:
#			# user exists, so redirect to some music!
#			return self.redirect('/music')
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
		try:
			raw_tags		=	json.loads(self.request.get("tags","{}")) #NOTE - this currently crashes if tags is empty
		except:
			raw_tags = {}
			logging.error('tags are not being handled correctly when not passed in post')
		try:
			'''
			You should check the following statements:
			1. tags is not empty
			2. serendipity is an integer between 0 and 255
			3. email is not already in the database
			4. email is valid (grab the regex from the wayfare or levr pages)
			5. pw is valid (see above)
			'''
			#===================================================================
			# Validate required fields
			#===================================================================
			# assure that all fields are passed
			assert raw_tags, 'You did not select any tags!'
			assert serendipity, 'You did not choose a serendipity level!'
			
			# validate serendipity
			try:
				serendipity = int(serendipity)
				assert serendipity >-1 and serendipity < 256, \
					'Serendipity must be an integer in range 0-255'
			except ValueError:
				assert False, 'serendipity must be an integer in range 0-255'
			#===================================================================
			# Clean tags
			#===================================================================
			tags = self.parse_tags(raw_tags)
			#===================================================================
			# Perform actions
			#===================================================================
			if submit_type != 'Sign Up':
				# user did not create an account
				# preferences are only stored in the session
				self.add_station_to_session(tags,serendipity)
			else:
				# the signup button was pressed
				# Create a new user account to store preferences
				assert email, 'Email is empty.'
				assert pw, 'Password is empty.'
				# validate email
				email_pattern = re.compile("[-a-zA-Z0-9._]+@[-a-zA-Z0-9_]+.[a-zA-Z0-9_.]+", re.IGNORECASE)
				assert email_pattern.match(email),'Invalid email.'
				existing_user = models.User.query(models.User.email == email).get()
				assert not existing_user, 'Email is already in use.'
				
				# create a new user in the ndb
				pw,salt = self.hash_password(pw)
				id_ = models.User.allocate_ids(1)[0]
				user = models.User(id=id_,
						email = email,
						pw = pw,
						salt = salt,
						)
				self.log_in(user.intkey, tags, serendipity)
				self.create_new_playlist(user.key, tags, serendipity)
				user.put()
			
		except AssertionError,error:
			#write out all of the inputted values and tags
			template_values = {
				"error"			:	error,
				"serendipity"	:	serendipity,
				"email"			:	email,
				"pw"			:	pw
			}
			if raw_tags:
				template_values['tags'] = json.dumps(raw_tags)
			
			jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
			template = jinja_environment.get_template('templates/build_user.html')
			self.response.out.write(template.render(template_values))
		else:
			# send me to some sweet sweet music!
			return self.redirect('/music')
			
			
app = webapp2.WSGIApplication([('/new',NewUserHandler)])




	