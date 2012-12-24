from google.appengine.ext import blobstore
from google.appengine.api import taskqueue
from sc_creds import sc_creds, sc_creds_test
import handlers
import jinja2
import logging
import mixpanel_track as mixpanel
import models
import os
import soundcloud
import webapp2
import json
from datetime import datetime as dt

jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


class ArtistFaqHandler(handlers.BaseHandler):
	def get(self):
		'''FAQ for artists'''
		template = jinja_environment.get_template('templates/artistfaq.html')
		self.response.out.write(template.render())


class ConnectSCHandler(handlers.ArtistHandler):
	def get(self):
		'''Login page for artists
		'''
		try:
			# check for an existing artist session
			artist = self.get_artist_from_session()
		except self.SessionError:
			# artist is not already logged in
			template_values = {
			}
			template = jinja_environment.get_template('templates/signup.html')
			self.response.out.write(template.render(template_values))
		else:
			# artist is already logged in, redirect to manage page
			return self.redirect(ARTIST_MANAGE)
		
class SCAuthHandler(handlers.ArtistHandler):
	def get(self):
		# init soundcloud client
		client = soundcloud.Client(**sc_creds)
		# redirect to soundcloud page to perform oauth handshake
		return self.redirect(client.authorize_url())	
	

class ConnectAccountHandler(handlers.ArtistHandler):
	def get(self):
		'''Complete oauth handshake with soundcloud
		'''
		
		logging.debug(self.request.url)
# 		get the oauth code
		code = self.request.get('code',None)
		if code is None:
			return self.redirect(ARTIST_LOGIN)
		# init the cloudsound client
		client = soundcloud.Client(**sc_creds)
		# exchange the code for an access token
		response = client.exchange_token(code)
		# pull the access token from the response
		access_token = response.access_token

		# get the access token
# 		access_token = self.request.get("access_token",None)
		
		logging.debug(access_token)
		
		
# 		if access_token is None:
# 			return self.redirect(ARTIST_LOGIN)

		# create a new client with the access token
		del client
		client = soundcloud.Client(access_token = access_token)
		current_user = client.get('/me')
		
		# pull the artist_id from the response
		artist_id = str(current_user.id)
		logging.debug(artist_id)
		logging.debug(current_user)
		
		# check for an existing user 
		try:
			# will raise SessionError if artist doesnt exist in db
			artist = self.get_artist(artist_id)
		except self.SessionError:
			# artist does not exist yet. Create one
			# log some mixpanel shiiiiit!
			try:
				properties = {
								'$username' : current_user.username,
								'city' : current_user.city,
								'country' : current_user.country,
								'signed_up' : self.request.get('signed_up',0),
								'tracks_added' : 0,
								'$created' : str(dt.now())
								}
				# set the first name for display purposes
				properties['$first_name'] = \
					current_user.full_name or current_user.username
				rpc = mixpanel.track_person(str(current_user.id), properties)
				
			except Exception,e:
				logging.error(e)
			logging.info('artist does not exist')
			artist = models.Artist(
							id = artist_id,
							access_token = access_token,
							username = current_user.username,
							)
			artist.put()
			# log in
			self.log_in(artist_id)
			
			# finish mixpanel rpc call
			self.complete_rpc(rpc)
			
			try:
				#send a text notification
				task_params = {
					'artist_name'	:	artist.username
				}
				logging.debug(artist.username)
				taskqueue.add(url='/tasks/textTask',payload=json.dumps(task_params))
			except Exception,e:
				logging.error(e)
			
			# redirect to image upload page
			return self.redirect(CHOOSE_TRACK)
		else:
			# artist already exists. Login and redirect to manage
			logging.info('artist exists')
			
			# track login on mixpanel
			try:
				properties = {
							'$username' : current_user.username,
							'city' : current_user.city,
							'country' : current_user.country,
							'$last_login' : str(dt.now())
							}
				# set the first name for display purposes
				properties['$first_name'] = \
					current_user.full_name or current_user.username
				logging.info(properties)
				rpc = mixpanel.track_person(str(current_user.id), properties)
				
			except Exception,e:
				logging.error(e)
			else:
				logging.info('Mixpanel rpc creation succeeded')
			
			# create a session for the artist
			self.log_in(artist_id)
			
			# complete mixpanel rpc
			self.complete_rpc(rpc)
			
			
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
		except self.SessionError:
			return self.redirect(ARTIST_LOGIN)
		
		
# 		self.say('manage page {}   '.format(artist.strkey))

		logging.info(artist.bandcamp_url)
		
		template_values = {
						'artist' : artist
		}
		
		template = jinja_environment.get_template('templates/artist/manage.html')
		self.response.out.write(template.render(template_values))
		
		
class UploadImageHandler(handlers.UploadHandler):
	def get(self):
		'''View page to upload an image
		'''
		try:
			artist = self.get_artist_from_session()
		except self.SessionError:
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
		except self.SessionError:
			return self.redirect(ARTIST_LOGIN)
		
		upload = self.get_uploads('image')[0]
		img_key = upload.key()
		artist.image_key = img_key
		artist.put()
		
		# determine where to redirect the user
		signup = self.request.get('signup',0)
		if signup == 1:
			# the user is creating an account. 
			# redirect to the audio upload page instead of manage
			return self.redirect(CHOOSE_TRACK)
		else:
			return self.redirect(ARTIST_MANAGE)
# class UploadAudioHandler(handlers.ArtistHandler):
# 	def get(self):
# 		'''View the page to upload an audio track url
# 		'''
# 		
# 		try:
# 			artist = self.get_artist_from_session()
# 		except self.SessionError:
# 			return self.redirect(ARTIST_LOGIN)
# 		# fetch a list of all of the artists tracks from soundcloud
# 		client = soundcloud.Client(access_token = artist.access_token)
# 		response = client.get('/users/{}/tracks'.format(artist.strkey))
# 		
# 		
# 		signup = self.request.get('signup',0)
# 		template_values = {
# 						'signup' : signup,
# 						'artist' : artist,
# 						'artist_key' : artist.strkey,
# 						'tracks' : response
# 		}
# 		
# 		template = jinja_environment.get_template('templates/artist/upload_audio.html')
# 		self.response.out.write(template.render(template_values))
# 		

# 		self.say('audio upload post {}'.format(artist.track_url))

class ChooseTrackHandler(handlers.ArtistHandler):
	def get(self):
		'''View the page to choose tracks from soundcloud
		'''
		
		try:
			artist = self.get_artist_from_session()
		except self.SessionError:
			return self.redirect(ARTIST_LOGIN)
			
		template_values = {
			"artist"	:	artist
		}
		
		logging.info(artist.artist_id)
		
		#write out the choosetrack page
		template = jinja_environment.get_template('templates/artist/choosetrack.html')
		self.response.out.write(template.render(template_values))
		
class StoreTrackHandler(handlers.ArtistHandler):
	def get(self):
		'''Store the soundcloud url to the artists audio track, also track_id
		'''
		try:
			artist = self.get_artist_from_session()
		except self.SessionError:
			return self.redirect(ARTIST_LOGIN)
		# track login on mixpanel
		try:
			properties = {
						'tracks_added' : 1
						}
			logging.info(properties)
			rpc = mixpanel.track_person(artist.strkey, properties)
			
		except Exception,e:
			logging.error(e)
		else:
			logging.info('Mixpanel rpc creation succeeded')
		
		
		# do stuff
		
		track_url = self.request.get('track_url')
		track_id = self.request.get('track_id')
		genre = self.request.get('genre')
		artist.tack_url = track_url
		artist.track_id = str(track_id)
		artist.genre = genre
		artist.put()
		
		
		
		
		
		# complete mixpanel rpc
		self.complete_rpc(rpc)
		
		self.redirect(ARTIST_MANAGE)
class UploadUrlsHandler(handlers.ArtistHandler):
	def get(self):
		'''Dev handler for testing the post.
		'''
		template_values = {}
		template = jinja_environment.get_template('templates/artist/upload_urls.html')
		self.response.out.write(template.render(template_values))
	def post(self):
		'''For uploading urls to the bands other websites
		'''
		try:
			artist = self.get_artist_from_session()
		except self.SessionError:
			return self.redirect(ARTIST_LOGIN)
		# fuck bitches, accumulate urls
		defined_urls = {
			'bandcamp_url' : self.request.get('bandcamp_url',None),
			'facebook_url' : self.request.get('facebook_url',None),
			'myspace_url' : self.request.get('myspace_url',None),
			'tumblr_url' : self.request.get('tumblr_url',None),
			'twitter_url' : self.request.get('twitter_url',None),
			'youtube_url' : self.request.get('youtube_url',None),
			'website_url' : self.request.get('website_url',None)
		}
		# store urls
		for url_id,url in defined_urls.iteritems():
			setattr(artist, url_id, url)
		
		# store extraneous urls
		other_urls = self.request.get_all('other_urls')
		artist.other_urls = other_urls
		
		# store the artists email
		email = self.request.get('email',None)
		if email is not None:
			artist.email = email
		
		# store changes
		artist.put()
		
		# return to the manage page
		return self.redirect(ARTIST_MANAGE)
class ViewArtistHandler(handlers.BaseHandler):
	def get(self,artist_id):
		'''For viewing an artists page as a user
		'''
		try:
			artist = self.get_artist(artist_id)
		except:
			self.say('Artist {} does not exist'.format(artist_id))
		template_values = {
						'artist' : artist,
		}
		
		template = jinja_environment.get_template('templates/artist/view.html')
		self.response.out.write(template.render(template_values))
#===============================================================================
# Development handlers
#===============================================================================
class SpoofArtistHandler(handlers.ArtistHandler):
	def get(self):
		'''
		For creating an artist account without soundcloud handshake
		'''
		artist = models.Artist.get_or_insert('31035942',
											username = 'pat',
											access_token = '1-29375-31035942-4e37f11f60c2f90'
											)
		artist.put()
		self.log_in(artist.strkey)
		
		self.say('Done!')
		
class TestHandler(handlers.ArtistHandler):
	def get(self):
		self.set_plaintext()
		artist = self.get_artist_from_session()
		artist_id = artist.strkey
		
		client = soundcloud.Client(access_token = artist.access_token)
		current_user = client.get('/me')
		
		self.say(current_user.fields())
		logging.info('artist exists')
			
		# track login on mixpanel
		properties = {
					'$username' : current_user.username,
					'city' : current_user.city,
					'country' : current_user.country,
					'$last_login' : str(dt.now())
					}
		# set the first name for display purposes
		properties['$first_name'] = \
			current_user.full_name or current_user.username
		logging.info(properties)
		rpc = mixpanel.track_person(str(current_user.id), properties)
			
		
		# create a session for the artist
		self.log_in(artist_id)
		
		# complete mixpanel rpc
		mp_result = rpc.get_result()
		self.say(mp_result.content)
		self.say(type(mp_result.content))
		assert int(mp_result.content) == 1, \
			'mixpanel "login" rpc for user {} failed'.format(str(current_user.id))

ARTIST_LOGIN = '/artist/login'
SC_AUTH = '/artist/scauth'
ARTIST_LOGIN_COMPLETE = '/artist/login/complete'
ARTIST_LOGOUT = '/artist/logout'
ARTIST_MANAGE = '/artist/manage'
UPLOAD_IMAGE = '/artist/upload/image'
# UPLOAD_AUDIO = '/artist/upload/audio'
CHOOSE_TRACK = '/artist/choosetrack'
STORE_TRACK = '/artist/storetrack'
UPLOAD_URLS = '/artist/upload/urls'
app = webapp2.WSGIApplication([
							('/artist/spoof',SpoofArtistHandler),
							('/artist/faq',ArtistFaqHandler),
							(ARTIST_LOGIN,ConnectSCHandler),
							(SC_AUTH,SCAuthHandler),
							(ARTIST_LOGIN_COMPLETE,ConnectAccountHandler),
							(ARTIST_LOGOUT,LogOutHandler),
							(ARTIST_MANAGE,ManageArtistHandler),
							(UPLOAD_IMAGE,UploadImageHandler),
							(UPLOAD_URLS,UploadUrlsHandler),
							(CHOOSE_TRACK,ChooseTrackHandler),
							(STORE_TRACK,StoreTrackHandler),
							('/artist/(.*)/',ViewArtistHandler),
							('/artist/test',TestHandler)
							])