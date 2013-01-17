import handlers
import jinja2
import logging
import models
import webapp2
import json
import os
import json


class ShowHandler(handlers.BaseHandler):
	def get(self):
	
		jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
		template = jinja_environment.get_template('templates/bandshowsignup.html')
		self.response.out.write(template.render())
		
class TestHandler(handlers.BaseHandler):
	def get(self):
	
		jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
		template = jinja_environment.get_template('templates/bandpage.html')
		self.response.out.write(template.render())


class PlayCheckHandler(handlers.BaseHandler):
	def get(self):
		
		#respond with true if logged in, false if not
		
		response = {
			"loggedin"	:	False
		}
		self.response.out.write(json.dumps(response))

app = webapp2.WSGIApplication([	('/shows',ShowHandler),
								('/shows/test',TestHandler),
								('/shows/playcheck',PlayCheckHandler)])


