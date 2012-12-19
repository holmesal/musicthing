from google.appengine.ext import blobstore
from sc_creds import sc_creds
import jinja2
import logging
import models
import os
import soundcloud
import handlers
import webapp2

jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class ArtistImageHandler(handlers.BaseHandler):
	def get(self,artist_id):
		'''For serving up the artists image
		'''
		try:
			artist = self.get_artist(artist_id)
		except AssertionError:
			raise Exception('Artist does not exist')
		self.say('image view {}'.format(artist_id))
app = webapp2.WSGIApplication([
							('/image/(.*)',ArtistImageHandler),
							])