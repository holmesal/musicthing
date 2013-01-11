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


class TestHandler(handlers.BaseHandler):
	def get(self):
		# fetch keys
		# artist_keys = models.Artist.query().fetch(None,keys_only=True)
# 		try:
# 			# get a random sample
# 			random_artists = random.sample(artist_keys,50)
# 		except ValueError:
# 			# list is not big enough, return all of them
# 			random_artists = artist_keys
# 		# shuffle list
# 		random.shuffle(random_artists)
# 		artists = ndb.get_multi(random_artists)
# 		
# 		# package the suckers
# 		template_values = {
# 						'artists' : artists
# 		}
		
		jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
		template = jinja_environment.get_template('templates/landingv3.html')
		self.response.out.write(template.render())
		
class BuildHandler(handlers.BaseHandler):
	def get(self):
		
		jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
		template = jinja_environment.get_template('templates/build_user.html')
		self.response.out.write(template.render())
		
class RadiusHandler(handlers.BaseHandler):
	def get(self):
		
		template_values = {
			"city" : "heythere"
		}
		
		jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
		template = jinja_environment.get_template('templates/station-radius.html')
		self.response.out.write(template.render(template_values))


app = webapp2.WSGIApplication([('/test',TestHandler),
								('/test/build',BuildHandler),
								('/test/radius',RadiusHandler)])





	