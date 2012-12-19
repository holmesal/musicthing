import webapp2
import utils
from sc_creds import sc_creds
import logging
import jinja2
import os
import utils
import soundcloud
import models
from google.appengine.ext import blobstore
from gaesessions import get_current_session

jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


class ConnectSCHandler(utils.ArtistHandler):
	def get(self):
		
		template_values = {
		}
		
		template = jinja_environment.get_template('templates/artist/login.html')
		self.response.out.write(template.render(template_values))
	def post(self):
		client = soundcloud.Client(**sc_creds)
		self.set_plaintext()
		self.redirect(client.authorize_url())
class ConnectAccountHandler(utils.ArtistHandler):
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
			self.redirect('/artist/manage'.format(existing_artist.strkey))
			return
		else:
			logging.info('artist does not exist. creating.')
			del existing_artist
		# still here? An artist is creating an account with us
		artist_key = str(current_user.id)
		artist = models.Artist(
							id = artist_key,
							access_token = access_token,
							username = current_user.username,
							)
		
		artist.put()
		
		# create session 
		self.log_in(artist.strkey)
		
		logging.info(artist)
		self.redirect('/artist/upload/image'.format(artist_key))
		return
#		template_values = {
#						'uid' : artist.key
#		}
#		template = jinja_environment.get_template('templates/artist/new_signup.html')
#		self.response.out.write(template.render(template_values))


class ManageArtistHandler(utils.ArtistHandler):
	def get(self):
		try:
			artist = self.get_artist_from_session()
		except AssertionError:
			return self.redirect()
		
		# TODO: check gaesessions to make sure the artist is logged in. If not, redirect
		self.say('manage page {}'.format(artist.strkey))
		
class UploadImageHandler(utils.ArtistHandler):
	def get(self):
		'''View page to upload an image
		'''
		try:
			artist = self.get_artist_from_session()
		except AssertionError:
			return self.redirect(ARTIST_LOGIN)
		
		signup = self.request.get('signup',0)
		template_values = {
						'signup' : signup,
						'artist_key' : artist.strkey,
						'upload_url' : blobstore.create_upload_url('/artist/upload/image'.format(artist.strkey))
		}
		
		template = jinja_environment.get_template('templates/artist/upload_image.html')
		self.response.out.write(template.render(template_values))
	def post(self):
		'''Store the image in blobstore and 
		'''
		try:
			artist = self.get_artist_from_session()
		except AssertionError:
			return self.redirect(ARTIST_LOGIN)
		
		upload = self.get_uploads('image')[0]
		img_key = upload.key()
		artist.image = img_key
		artist.put()
		return self.redirect(ARTIST_MANAGE)
class UploadExistingAudioHandler(utils.ArtistHandler):
	def get(self):
		'''For selecting an existing soundcloud track
		'''
		try:
			artist = self.get_artist_from_session()
		except AssertionError:
			return self.redirect(ARTIST_LOGIN)
		# fetch a list of all of the artists tracks from soundcloud
		client = soundcloud.Client(**sc_creds)
		
		
		signup = self.request.get('signup',0)
		template_values = {
						'signup' : signup,
						'artist_key' : artist.strkey,
						'upload_url' : blobstore.create_upload_url('/artist/{}/upload/audio'.format(artist.strkey))
		}
		
		template = jinja_environment.get_template('templates/artist/upload_image.html')
		self.response.out.write(template.render(template_values))
		
class UploadNewAudioHandler(utils.ArtistHandler):
	def get(self):
		'''View the page to upload an audio track url
		'''
		try:
			artist = self.get_artist_from_session()
		except AssertionError:
			return self.redirect(ARTIST_LOGIN)
		
		signup = self.request.get('signup',0)
		
		template_values = {
						'signup' : signup,
						'artist_key' : artist.strkey,
						'upload_url' : blobstore.create_upload_url('/artist/{}/upload/audio'.format(artist.strkey))
		}
		
		template = jinja_environment.get_template('templates/artist/upload_image.html')
		self.response.out.write(template.render(template_values))
		
	def post(self):
		'''Store the soundcloud url to the artists audio track
		'''
		try:
			artist = self.get_artist_from_session()
		except AssertionError:
			self.redirect(ARTIST_LOGIN)
		self.say('audio upload post'.format(artist.strkey))
class ArtistImageHandler(utils.BaseHandler):
	def get(self,artist_id):
		'''For serving up the artists image
		'''
		try:
			artist = self.get_artist(artist_id)
		except AssertionError:
			raise Exception('Artist does not exist')
		self.say('image view {}'.format(artist_id))
class ArtistAudioHandler(utils.BaseHandler):
	def get(self,artist_id):
		'''For serving up the artists audio
		'''
		try:
			artist = self.get_artist(artist_id)
		except AssertionError:
			raise Exception('Artist does not exist')
		self.say('audio listen {}'.format(artist_id))
#===============================================================================
# Development handlers
#===============================================================================
class SpoofArtistHandler(utils.ArtistHandler):
	def get(self):
		'''
		For creating an artist account without soundcloud handshake
		'''
		artist = models.Artist.get_or_insert('111',
											username = 'pat'
											)
		artist.put()
		self.say('Done!')
class GetDataHandler(utils.ArtistHandler):
	# test handler
	def get(self):
		access_token = '1-29375-30759062-700d24381a1af75'#artist.access_token
		
		client = soundcloud.Client(access_token=access_token)
#		client.access_token = access_token
		current_user = client.get('/me')
		self.set_plaintext()
		self.say(current_user.fields())

ARTIST_LOGIN = '/artist/login'
ARTIST_LOGIN_COMPLETE = '/artist/login/complete'
ARTIST_MANAGE = '/artist/manage'
UPLOAD_IMAGE = '/artist/upload/image'
UPLOAD_AUDIO = '/artist/upload/audio'
app = webapp2.WSGIApplication([
							('/artist/spoof',SpoofArtistHandler),
							(ARTIST_LOGIN,ConnectSCHandler),
							(ARTIST_LOGIN_COMPLETE,ConnectAccountHandler),
							(ARTIST_MANAGE,ManageArtistHandler),
							(UPLOAD_IMAGE,UploadImageHandler),
							(UPLOAD_AUDIO,UploadNewAudioHandler),
							('/artist/(.*)/image',ArtistImageHandler),
							('/artist/(.*)/audio',ArtistAudioHandler)
							])