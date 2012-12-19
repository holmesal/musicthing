import webapp2
import utils
from sc_creds import sc_creds
import logging
import jinja2
import os
import utils
import soundcloud
import models

jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


class ConnectSCHandler(utils.BaseHandler):
	def get(self):
		
		template_values = {
		}
		
		template = jinja_environment.get_template('templates/artist/login.html')
		self.response.out.write(template.render(template_values))
	def post(self):
		client = soundcloud.Client(**sc_creds)
		self.set_plaintext()
		self.redirect(client.authorize_url())
class ConnectAccountHandler(utils.BaseHandler):
	def get(self):
		# get the oauth code
		code = self.request.get('code')
		# init the cloudsound client
		client = soundcloud.Client(**sc_creds)
		# exchange the code for an access token
		response = client.exchange_token(code)
		access_token = response.access_token
		logging.info('access token: {}'.format(access_token))
		# create a new client with the access token
		del client
		client = soundcloud.Client(access_token = access_token)
		current_user = client.get('/me')
		logging.info(current_user)
		# check for an existing user 
		existing_artist = models.Artist.get_by_id(current_user.id)
		logging.info(existing_artist)
		if existing_artist:
			logging.info('artist exist. redirecting')
			# redirect to their manage page. They already have an account
			self.redirect('/artist/{}/manage'.format(existing_artist.strkey))
			return
		else:
			logging.info('artist does not exist. creating.')
			del existing_artist
		# still here? An artist is creating an account with us
		artist = models.Artist(
							id = str(current_user.id),
							access_token = access_token,
							username = current_user.username,
							)
		artist.put()
		logging.info(artist)
		self.redirect('/artist/{}/upload/image'.format(artist.strkey))
		return
#		template_values = {
#						'uid' : artist.key
#		}
#		template = jinja_environment.get_template('templates/artist/new_signup.html')
#		self.response.out.write(template.render(template_values))

class GetDataHandler(utils.BaseHandler):
	# test handler
	def get(self):
		access_token = '1-29375-30759062-700d24381a1af75'#artist.access_token
		
		client = soundcloud.Client(access_token=access_token)
#		client.access_token = access_token
		current_user = client.get('/me')
		self.set_plaintext()
		self.say(current_user.fields())
class ManageArtistHandler(utils.BaseHandler):
	def get(self,uid):
		logging.info(uid)
		artist = models.Artist.get_by_id(uid)
		logging.info(artist)
		if not self.validate_artist(artist):
			return
		# TODO: check gaesessions to make sure the artist is logged in. If not, redirect
		self.say('manage page {}'.format(uid))
		
class UploadImageHandler(utils.UploadHandler):
	def get(self,uid):
		# make sure artist exists
		artist = models.Artist.get_by_id(uid)
		logging.info(uid)
		logging.info(artist)
		if not self.validate_artist(artist):
			return
		
		signup = self.request.get('signup',0)
		template_values = {
						'signup' : signup,
						'artist_key' : artist.strkey
		}
		
		template = jinja_environment.get_template('templates/artist/upload_image.html')
		self.response.out.write(template.render(template_values))
	def post(self,uid):
		artist = models.Artist.get_by_id(uid)
		if not self.validate_artist(artist):
			return
		upload = self.get_uploads('image')
		img_key = upload.key()
		artist.image = img_key
		
		artist.put()
		
		# check that the artist exists
		
		
		self.say(artist.properties())
		
class UploadAudioHandler(utils.UploadHandler):
	def get(self,uid):
		artist = models.Artist.get_by_id(uid)
		if not self.validate_artist(artist):
			return
		
		self.say('audio upload {}'.format(uid))
	def post(self,uid):
		artist = models.Artist.get_by_id(uid)
		if not self.validate_artist(artist):
			return
		self.say('audio upload post'.format(uid))
	
class SpoofArtistHandler(utils.BaseHandler):
	def get(self):
		artist = models.Artist.get_or_insert('111',
											username = 'pat'
											)
		artist.put()
		self.say('Done!')
app = webapp2.WSGIApplication([
							('/artist/spoof',SpoofArtistHandler),
							('/artist/login',ConnectSCHandler),
							('/artist/login/complete',ConnectAccountHandler),
							('/artist/signup/get_data',GetDataHandler),
							('/artist/(.*)/manage',ManageArtistHandler),
							('/artist/(.*)/upload/image',UploadImageHandler),
							('/artist/(.*)/upload/audio',UploadAudioHandler)
							])