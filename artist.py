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


class ConnectSCHandler(handlers.ArtistHandler):
	def get(self):
		'''Login page for artists
		'''
		try:
			# check for an existing artist session
			artist = self.get_artist_from_session()
		except AssertionError:
			# artist is not already logged in
			template_values = {
			}
			template = jinja_environment.get_template('templates/artist/login.html')
			self.response.out.write(template.render(template_values))
		else:
			# artist is already logged in, redirect to manage page
			return self.redirect(ARTIST_MANAGE)
		
	def post(self):
		# init soundcloud client
		client = soundcloud.Client(**sc_creds)
		# redirect to soundcloud page to perform oauth handshake
		return self.redirect(client.authorize_url())
class ConnectAccountHandler(handlers.ArtistHandler):
	def get(self):
		# get the oauth code
		code = self.request.get('code')
		# init the cloudsound client
		client = soundcloud.Client(**sc_creds)
		# exchange the code for an access token
		response = client.exchange_token(code)
		# pull the access token from the response
		access_token = response.access_token
		
		# create a new client with the access token
		del client
		client = soundcloud.Client(access_token = access_token)
		current_user = client.get('/me')
		# pull the artist_id from the response
		artist_id = str(current_user.id)
		
		# check for an existing user 
		try:
			# will raise AssertionError if artist doesnt exist in db
			artist = self.get_artist(artist_id)
		except AssertionError:
			# artist does not exist yet. Create one
			logging.info('artist does not exist')
			artist = models.Artist(
							id = artist_id,
							access_token = access_token,
							username = current_user.username,
							)
			artist.put()
			# log in
			self.log_in(artist_id)
			# redirect to image upload page
			return self.redirect(UPLOAD_IMAGE)
		else:
			# artist already exists. Login and redirect to manage
			logging.info('artist exists')
			self.log_in(artist_id)
			return self.redirect(ARTIST_MANAGE)
class LogOutHandler(handlers.ArtistHandler):
	def get(self):
		'''Logs out an artist
		'''
		# log out of session
		self.log_out()
		# redirect to landing page
		return self.redirect('/')

class ManageArtistHandler(handlers.ArtistHandler):
	def get(self):
		try:
			artist = self.get_artist_from_session()
		except AssertionError:
			return self.redirect()
		
		# TODO: check gaesessions to make sure the artist is logged in. If not, redirect
		self.say('manage page {}'.format(artist.strkey))
		
class UploadImageHandler(handlers.ArtistHandler):
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
class UploadExistingAudioHandler(handlers.ArtistHandler):
	def get(self):
		'''For selecting an existing soundcloud track
		'''
		try:
			artist = self.get_artist_from_session()
		except AssertionError:
			return self.redirect(ARTIST_LOGIN)
		# fetch a list of all of the artists tracks from soundcloud
		client = soundcloud.Client(access_token = artist.access_token)
		client.get('/tracks')
		
		signup = self.request.get('signup',0)
		template_values = {
						'signup' : signup,
						'artist_key' : artist.strkey,
						'upload_url' : blobstore.create_upload_url('/artist/{}/upload/audio'.format(artist.strkey))
		}
		
		template = jinja_environment.get_template('templates/artist/upload_image.html')
		self.response.out.write(template.render(template_values))
		
class UploadNewAudioHandler(handlers.ArtistHandler):
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

#===============================================================================
# Development handlers
#===============================================================================
class SpoofArtistHandler(handlers.ArtistHandler):
	def get(self):
		'''
		For creating an artist account without soundcloud handshake
		'''
		artist = models.Artist.get_or_insert('111',
											username = 'pat',
											access_token = '1-29375-30759062-700d24381a1af75'
											)
		artist.put()
		self.log_in(artist.strkey)
		
		self.say('Done!')

ARTIST_LOGIN = '/artist/login'
ARTIST_LOGIN_COMPLETE = '/artist/login/complete'
ARTIST_LOGOUT = '/artist/logout'
ARTIST_MANAGE = '/artist/manage'
UPLOAD_IMAGE = '/artist/upload/image'
UPLOAD_AUDIO = '/artist/upload/audio'
app = webapp2.WSGIApplication([
							('/artist/spoof',SpoofArtistHandler),
							(ARTIST_LOGIN,ConnectSCHandler),
							(ARTIST_LOGIN_COMPLETE,ConnectAccountHandler),
							(ARTIST_LOGOUT,LogOutHandler),
							(ARTIST_MANAGE,ManageArtistHandler),
							(UPLOAD_IMAGE,UploadImageHandler),
							(UPLOAD_AUDIO,UploadNewAudioHandler)
							])