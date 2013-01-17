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
		
		going = ["going person 1","going person 2","going person 3"]
		
		artist = {
			"track_id"		:	53097530,
			"artist_name"	:	"The Band"
		}
		
		template_values = {
			"tickets_total"	:	40,
			"tickets_remaining"	:	40,
			"tickets_sold"		:	0,
			"place_string"		:	"2nd",
			"going"			:	going,
			"artist"		:	artist,
			"contestant_id"	:	"1x3rp",
			"status"		:	"won",
			"tickets_available"	:	False
		}
		
		jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
		template = jinja_environment.get_template('templates/bandpage.html')
		self.response.out.write(template.render(template_values))


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


