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


class MusicHandler(handlers.BaseHandler):
	'''
	The big main music player. Awwww yeah.
	'''
	def get(self):
		'''
		This handler does most of the heavy lifting. The process is:
		1. Grab user info
		2. Decide which tracks to play
		3. Write out those tracks
		'''
		
		'''
		You should check if they're already logged in, and redirect appropriately if not (back to the user signup page)
		'''
		
		
		'''
		OUTPUTS:
		
		artists		:	an array of the artist entities, as they come out of the datastore
		
		Here's some test values:
		'''
		
		artist_keys = models.Artist.query().fetch(30,keys_only=True)
		artists = ndb.get_multi(artist_keys)
		logging.info(artists)
		
		
		template_values = {
			"artists"		:	artists
		}
		
		jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
		template = jinja_environment.get_template('templates/player.html')
		self.response.out.write(template.render(template_values))
		
	def post(self):
		'''
		This handler takes care of updating user preferences that are available on the player page
		There's nothing here yet
		'''
		
		pass
		


app = webapp2.WSGIApplication([('/music', MusicHandler)])





	