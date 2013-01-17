import handlers
import jinja2
import logging
import models
import webapp2
import json
import os

class DemoHandler(handlers.BaseHandler):
	def get(self):
		
		jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
		template = jinja_environment.get_template('templates/bandpage-demo.html')
		self.response.out.write(template.render())

app = webapp2.WSGIApplication([('/demo',DemoHandler)])


