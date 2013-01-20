from datetime import datetime as dt
from gaesessions import get_current_session
from google.appengine.api import taskqueue
from google.appengine.ext import blobstore, ndb
from sc_creds import sc_creds, sc_creds_test
import handlers
import jinja2
import json
import logging
import mixpanel_track as mixpanel
import models
import os
import random
import soundcloud
import urllib2
import utils
import webapp2

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
		logging.info('city: '+str(current_user.city))
		# pull the artist_id from the response
		artist_id = str(current_user.id)
		logging.debug(artist_id)
		logging.debug(current_user)
		
		# check for an existing user 
		try:
			# will raise SessionError if artist doesnt exist in db
			artist = self.get_artist_by_id(artist_id)
		except self.SessionError,e:
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
							city = current_user.city,
#							genre = current_user.genre
							)
			try:
				artist.genre = current_user.genre
			except AttributeError:
				pass
			except Exception,e:
				logging.error(e)
			artist.put()
			
			# finish mixpanel rpc call
			self.complete_rpc(rpc)
			
#			try:
#				# send a text notification
#				task_params = {
#					'artist_name'	:	artist.username
#				}
#				logging.debug(artist.username)
#				taskqueue.add(url='/tasks/textTask',payload=json.dumps(task_params))
#			except Exception,e:
#				logging.error(e)
			
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
				# complete mixpanel rpc
				self.complete_rpc(rpc)
			
		# create a session for the artist
		session = self.log_in(artist_id)
		
		
		#===================================================================
		# Determine redirect destination
		#===================================================================
		if artist.track_id is None:
			redirection = CHOOSE_TRACK
		elif session.get('login_redirect'):
			redirection = session['login_redirect']
		else:
			redirection = ARTIST_MANAGE
		# redirect
		return self.redirect(redirection)
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
		
		# for right now, we only handle one city at a time. 
		template_values = {
						'artist' : artist,
						'city' : artist.city_dict()
		}
		logging.info(template_values)
		template = jinja_environment.get_template('templates/artist/manage.html')
		self.response.out.write(template.render(template_values))
		
class AddTagsHandler(handlers.ArtistHandler):
	'''
	This handles the tagging process for artists
	'''
	def get(self):
		'''
		Write out the form and any existing tags in form [{name:name,count:count}]
		ordered by count, descending
		'''
		try:
			artist = self.get_artist_from_session()
		except:
			return self.redirect(ARTIST_LOGIN)
		tags = artist.tags
		tags = sorted(tags,key=lambda x: x['count'],reverse=True)
		template_values = {
			"tags"		:	json.dumps(tags)
		}
		
		jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
		template = jinja_environment.get_template('templates/addtags.html')
		self.response.out.write(template.render(template_values))
	
		
		
		
	def post(self):
		'''
		Update the artist's tags
		Then redirect to /manage
		'''
		# grab the submitted tags
		try:
			raw_tags = json.loads(self.request.get('tags','{}'))
		except ValueError:
			# json throws error if tags is empty
			raw_tags = []
		
		# grab the artist in question
		try:
			artist = self.get_artist_from_session()
		except self.SessionError:
			return self.redirect(ARTIST_MANAGE)
		
		
		if raw_tags:
			parsed_tags = self.convert_client_tags_to_tags_dict_OLD(raw_tags)
			prepped_tags = self.prep_tags_for_datastore(parsed_tags)
		else:
			# empty list if raw_tags is empty
			prepped_tags = []
		
		artist.tags_ = prepped_tags
		artist.put()
		
		return self.redirect(ARTIST_MANAGE)
		
		
		
		
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
		template = jinja_environment.get_template('templates/artist/choosetrackv2.html')
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
		
		#=======================================================================
		# Determine redirect location
		#=======================================================================
		session = get_current_session()
		logging.info('login_redirect: {}'.format(session.get('login_redirect')))
		logging.info(session)
		if session.get('login_redirect'):
			redirection = session.get('login_redirect')
		else:
			redirection = ARTIST_MANAGE
		self.redirect(redirection)
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
		
		#=======================================================================
		# Update city information
		#=======================================================================
		
		
		city_name = self.request.get('locality') or ' '
		if city_name is not ' ':
			admin1 = self.request.get('administrative_area_level_1','') or ' '
			country = self.request.get('country','') or ' '
			lat = self.request.get('lat')
			lon = self.request.get('lon')
			geo_point = ndb.GeoPt('{},{}'.format(lat,lon))
			
			# create the global city entity in the db
			city = utils.fetch_city_from_path(country, admin1, city_name, geo_point)
			# create a version of the city to be stored on the artist
			city_property = city.to_city_property()
			# artist.cities is a list, pass city_property as a singleton
			artist.cities = [city_property,]
			# store the city name because, shit will break if we dont
			artist.city = city_name
		# store changes
		artist.put()
		
		# return to the manage page
		return self.redirect(ARTIST_MANAGE)
class ViewArtistHandler(handlers.BaseHandler):
	def get(self,artist_id):
		'''For viewing an artists page as a user
		'''
		try:
			artist = self.get_artist_by_id(artist_id)
		except:
			self.say('Artist {} does not exist'.format(artist_id))
			artist = None
		template_values = {
						'artist' : artist,
		}
		
		template = jinja_environment.get_template('templates/artist/view.html')
		self.response.out.write(template.render(template_values))
#===============================================================================
# Development handlers
#===============================================================================
class GetArtistInfoHandler(handlers.UserHandler):
	def get(self):
		'''
		Fetch artist names and emails for filtering on the email list
		'''
		artist_keys = models.Artist.query(keys_only = True)
		artist_futures = ndb.get_multi_async(artist_keys)
		artists = (a.get_result() for a in artist_futures)
		artist_data = ({a.username:a.email} for a in artists)
		
		self.response.out.write(json.dumps(artist_data))
		
		
class SpoofArtistHandler(handlers.ArtistHandler):
	def get_all(self):
		'''
		Spoof a lot of the data on the server
		'''
		if os.environ['SERVER_SOFTWARE'].startswith('Development') == False:
			self.say('This handler can not be accessed')
			return
		remote_url = 'http://pattest.radius-levr.appspot.com/artist/test'
		data = json.loads(urllib2.urlopen(remote_url).read())
		
		# extract all the genres
		tags = list(set([d['genre'] for d in data]))
		counts = range(1,101) + [0 for i in range(1,601)] #@UnusedVariable
		
		
		
#		logging.info(data)
		self.say(json.dumps(data))
		return
		artist_futures = []
		for d in data:
			# create random tag counts
			parsed_tags = {tag:random.choice(counts) for tag in tags}
			prepped_tags = self.prep_tags_for_datastore(parsed_tags)
			artist_futures.append(models.Artist(username = d['username'],
								genre = d['genre'],
								track_id = d['track_id'],
								tags_ = prepped_tags,
								city = d['city']
								).put_async())
		for f in artist_futures:
			self.say(f.get_result())
		self.say('Done!')
		
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
		'''
		A spoof api call to exist on the server to retrieve artist information
		for use on the dev server
		'''
		artists = models.Artist.query().fetch(None)
#		artist_list = []
#		for a in artists:
#			exclude = ('created','cities')
#			a_dict = a.to_dict(exclude=exclude)
#			a_dict['city'] = a.city_dict()
		self.response.out.write(json.dumps([a.to_dict(exclude=('created','cities')) for a in artists]))
	def get_2(self):
		'''
		Gets all the access tokens of the artists on the server.
		'''
		artists = models.Artist.query().fetch(None)
#		tokens = [artist.access_token for artist in artists]
		for a in artists:
			self.say('"'+a.username.encode('ascii','ignore')+'" : "'+a.access_token+'",')
	def get_1(self):
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

class AddSpoofCititesHandler(handlers.UserHandler):
	def get(self):
		'''
		Adds cities to all the spoofed artists
		'''
		if os.environ['SERVER_SOFTWARE'].startswith('Development') == False:
			self.say('This handler can not be accessed')
			return
		cities = ['c'*i for i in range(1,10)]
		states = ['s'*i for i in range(1,10)]
		countries = ['y'*i for i in range(1,10)]
		
		city_keys = []
		for y in countries:
			for s in states:
				for c in cities:
					lat = random.uniform(41.9,42.9)
					lon = random.uniform(-70.9,-71.9)
#					gstring = '{},{}'.format(lat,lon)
					geo_point = ndb.GeoPt(lat,lon)
					city = utils.fetch_city_from_path(y,s,c,geo_point)
					city_keys.append(city)
					
#		allston = utils.fetch_city_from_path('United States', 'MA', 'Allston', ndb.GeoPt('42.3539038, -71.1337112'))
#		boston = utils.fetch_city_from_path('United States', 'MA', 'Boston', ndb.GeoPt('42.353, -71.133'))
#		somerville = utils.fetch_city_from_path('United States', 'MA', 'Somerville', ndb.GeoPt('42.3875968, -71.0994968'))
#		
#		city_keys = [allston,boston,somerville]
		artists = models.Artist.query().iter(batch_size = 50)
		for a in artists:
#			del a._properties['city_keys']
#			del a._properties['ghash']
			city = random.choice(city_keys)
			a.cities.append(models.CityProperty(city_key = city.key, ghash = city.ghash))
#			a.ghash = city.ghash
#			a.city_keys.append(city.key)
			a.put()
#			self.say(a.key)
		self.say('Done!')
class ChangeNameHandler(handlers.ArtistHandler):
	def post(self):
		'''
		An artist changes their name on a contest page
		'''
		try:
			artist = self.get_artist_from_session()
		except self.SessionError:
			self.redirect('/')
		new_name = self.request.get('artist_name')
		artist.proper_name = new_name
		artist.put()
		
		return self.redirect(self.request.referrer)
		
ARTIST_LOGIN = '/artist/login'
SC_AUTH = '/artist/scauth'
ARTIST_LOGIN_COMPLETE = '/artist/login/complete'
ARTIST_LOGOUT = '/artist/logout'
ARTIST_MANAGE = '/artist/manage'
ARTIST_ADDTAGS = '/artist/addtags'
ARTIST_CHANGE_NAME = '/artist/changename'
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
							(ARTIST_ADDTAGS,AddTagsHandler),
							(ARTIST_CHANGE_NAME,ChangeNameHandler),
							(UPLOAD_IMAGE,UploadImageHandler),
							(UPLOAD_URLS,UploadUrlsHandler),
							(CHOOSE_TRACK,ChooseTrackHandler),
							(STORE_TRACK,StoreTrackHandler),
							('/artist/(.*)/',ViewArtistHandler),
							('/artist/test',TestHandler),
							('/artist/data',''),
							('/artist/test/add_cities',AddSpoofCititesHandler)
							])