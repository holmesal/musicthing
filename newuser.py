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


class NewUserHandler(handlers.BaseHandler):
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
		This handler grabs the inputs from the new user page, and either writes out an error (if some of the information is incorrect) or creates the user and redirects to the music page
		'''
		
		logging.info(self.request.get("serendipity"))
		
		tags		=	json.loads(self.request.get("tags"),None) #NOTE - this currently crashes if tags is empty
		serendipity	=	self.request.get("serendipity",None)
		email 		=	self.request.get("email",None)
		pw			=	self.request.get("pw",None)
		
		logging.info(tags)
		logging.info(serendipity)
		logging.info(email)
		logging.info(pw)
		
		'''
		You should check the following statements:
		1. tags is not empty
		2. serendipity is an integer between 0 and 255
		3. email is not already in the database
		4. email is valid (grab the regex from the wayfare or levr pages)
		5. pw is valid (see above)
		'''
		
		'''
		If there is an error, do this:
		'''
		
		error = "This is some error text, featherplucka"
		
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
		
		
		'''
		If there is no error, create the user (if they passed signup info), create the session variable, and redirect them to /music
		'''


app = webapp2.WSGIApplication([('/new',NewUserHandler)])





	