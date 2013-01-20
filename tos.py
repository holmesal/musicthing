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

class Tos(handlers.BaseHandler):
	def get(self):
		
		
		jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
		template = jinja_environment.get_template('templates/tos.html')
		self.response.out.write(template.render())

app = webapp2.WSGIApplication([('/terms',Tos)])


