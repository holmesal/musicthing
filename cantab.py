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

class CantabHandler(handlers.BaseHandler):
	def get(self):
		
		
		jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
		template = jinja_environment.get_template('templates/cantablanding.html')
		self.response.out.write(template.render())

	def post(self):
		email = self.request.get('email')
		
		existing = models.Cantab.query().filter(models.Cantab.email == email).get()
		if not existing:
			models.Cantab(email=email).put()
		
		template_values = {
			"state"	:	"signedup"
		}
		
		try:
			#send a text notification
			task_params = {
				'email'	:	email
			}
			logging.debug(email)
			taskqueue.add(url='/tasks/cantabTask',payload=json.dumps(task_params))
		except Exception,e:
			logging.error(e)
		
		jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
		template = jinja_environment.get_template('templates/cantablanding.html')
		self.response.out.write(template.render(template_values))

app = webapp2.WSGIApplication([('/boston',CantabHandler)])


