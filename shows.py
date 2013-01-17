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


class PlayCheckHandler(handlers.BaseHandler):
	def get(self):
		
		response = {
			"loggedin"	:	True
		}
		self.response.out.write(json.dumps(response))

app = webapp2.WSGIApplication([	('/shows',ShowHandler),
								('/shows/playcheck',PlayCheckHandler)])


