import webapp2
from google.appengine.ext.webapp import blobstore_handlers
import jinja2
import os
import models
import logging
jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class BaseHandler(webapp2.RequestHandler):
	def set_plaintext(self):
		self.response.headers['Content-Type'] = 'text/plain'
	def say(self,stuff=''):
		'''For debugging when I am too lazy to type
		'''
		self.response.out.write('\n')
		self.response.out.write(stuff)
	def validate_artist(self,artist):
		logging.info('artist:')
		logging.info(artist)
		if not artist:
			# if the artist is not found, then show not found page
			template_values = {
						}
			template = jinja_environment.get_template('templates/artist/not_found.html')
			self.response.out.write(template.render(template_values))
			return False
		else:
			return True
class UploadHandler(BaseHandler,blobstore_handlers.BlobstoreUploadHandler):
	pass