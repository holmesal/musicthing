import webapp2
from google.appengine.ext.webapp import blobstore_handlers
import jinja2
import os
import models
import logging
from gaesessions import get_current_session
import hashlib, uuid
from collections import defaultdict
from collections import Counter

#from excepts import *
jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class BaseHandler(webapp2.RequestHandler):
	class SessionError(Exception):
		'''Session is invalid'''
	def say(self,stuff=''):
		'''For debugging when I am too lazy to type
		'''
		self.response.headers['Content-Type'] = 'text/plain'
		self.response.out.write('\n')
		self.response.out.write(stuff)
	def log_out(self):
		'''Terminates the session
		'''
		session = get_current_session()
		session.terminate()
	def get_artist_by_id(self,artist_id):
		'''
		Fetches an artist from the ndb.
		@raise SessionError: 
			if artist_id does not yield an artist entity from the db
		
		@param artist_id: The soundcloud id of an artist
		@type artist_id: str
		
		@return: The artist that corresponds to the provided artist_id
		@rtype: models.Artist
		'''
		try:
			artist_id = str(artist_id)
			logging.info(artist_id)
			artist = models.Artist.get_by_id(artist_id)
			assert artist, 'Artist does not exist'
			return artist
		except AssertionError,e:
			raise self.SessionError(e)
	def get_user_by_id(self,user_id):
		'''
		Fetches a user by their id, not to be confused with key.
		@param user_id: the users id
		@type user_id: int
		@return: the user referenced by the id
		@rtype: models.User
		'''
		try:
			user_id = long(user_id)
			user = models.User.get_by_id(user_id)
			assert user, 'User does not exist'
		except AssertionError,e:
			raise self.SessionError(e)
		else:
			return user
			
	def complete_rpc(self,rpc):
		'''
		Completes an rpc call for an asynchronous mixpanel event log.
		@param rpc: the mixpanel url fetch rpc
		@type rpc: ??rpc??
		'''
		try:
			mp_result = rpc.get_result()
			assert mp_result.content == '1', \
				'mixpanel rpc failed'
		except Exception,e:
			logging.error(e)
	def convert_client_tags_to_tags_dict(self,raw_tags):
		'''
		Converts a list of objects in form 
			[{
				'artist':'Radiohead',
				'tags':[
					{'name':'rock','count':100},
					]
			},]
		@param raw_tags: list of lastfm tag objects
		@type raw_tags: list
		@return: dict mapping of {tag:count,}
		@rtype: dict
		'''
		# combine duplicates
		tags = defaultdict(int)
		for group in raw_tags:
			for item in group['tags']:
				tag = item['name']
				count = int(item['count'])
				tags[tag] += count
		# make tags static
		tags.default_factory = None
		# calc max count for all the tags
		max_count = max([tags[tag] for tag in tags])
		# update the tags dict
		tags = {key:int(float(count)/float(max_count)*100) for key,count in tags.iteritems()}
		return tags
	def prep_tags_for_datastore(self,tag_to_count_mapping):
		'''
		Converts a dict of tags:count to a list of TagProperties
		@param parsed_tags: dict mapping {tag:count,}
		@type parsed_tags: dict
		@return: a list of models.TagProperty objects
		@rtype: list
		'''
		return [models.TagProperty(
									genre = tag,
									count = count
									)
					for tag,count in tag_to_count_mapping.iteritems() if count > 0
					]
	
class ArtistHandler(BaseHandler):
	def log_in(self,artist_id):
		'''
		Creates a session, setting logged_in to true, 
			and assigning any other session variables
		@param artist_id: the artists ndb key
		@type artist_id: str
		'''
		session = get_current_session()
		session['logged_in'] = True
		session['artist_id'] = str(artist_id)
	def get_artist_from_session(self):
		'''
		Assures that the artist is logged in
		@raise SessionError: 
			if logged_in is False
			if either logged_in or artist_id do not exist as session keys
			if artist_id is invalid, i.e. no artist by that id exists in the db
		@return: the artist entity
		@rtype: models.Artist
		'''
		try:
			session = get_current_session()
			# make sure they are logged in
			assert session['logged_in'] == True, 'Not logged in.'
			
			# grab the artist by the session artist_id and make sure it exists in the db
			artist_id =  session['artist_id']
			logging.debug(artist_id)
			artist = models.Artist.get_by_id(artist_id)
			assert artist, 'Artist does not exist'
			artist.artist_id = artist_id
			return artist
		except AssertionError,e:
			raise self.SessionError(e)
		except KeyError,e:
			raise self.SessionError(e)
class UserHandler(BaseHandler):
	def get_user_from_session(self):
		try:
			session = get_current_session()
			assert session['logged_in'] == True, 'Not logged in'
			# grab the users id
			user_id = session['id']
			user = models.User.get_by_id(user_id)
			assert user, 'User does not exist'
		except AssertionError,e:
			raise self.SessionError(e)
		except KeyError,e:
			raise self.SessionError(e)
		else:
			return user
	def hash_password(self,pw,salt=None):
		'''
		Hashes a password using a salt and hashlib
		http://stackoverflow.com/questions/9594125/salt-and-hash-a-password-in-python
		@param pw: the users password
		@type pw: str
		@return: hashed_password (str), salt (str)
		@rtype: tuple
		'''
		if salt is None:
			salt = uuid.uuid4().hex
		hashed_password = hashlib.sha512(pw + salt).hexdigest()
		return hashed_password,salt
	def log_in(self,uid):
		session = get_current_session()
		session['logged_in'] = True
		session['id'] = uid
#	def set_station_meta_to_station(self,mode,mode_data,station_tags=None,client_tags=None):
#		# assure the original artist --> tags:counts mappings are preserved
#		if station_tags is not None:
#			assert client_tags is not None, 'If passing tags, must preserve client tags.'
#		session = get_current_session()
#		session['mode'] = mode
#		session['mode_data'] = mode_data
#		session['station_tags'] = station_tags
#		session['client_tags'] = client_tags
#		
#	def get_station_meta_from_session(self):
#		session = get_current_session()
#		try:
#			mode = session['mode']
#			mode_data = session['mode_data']
#			station_tags = session['station_tags']
#			client_tags = session['client_tags']
#		except KeyError,e:
#			raise self.SessionError(e)
#		else:
#			return mode,mode_data,station_tags,client_tags
	def get_user_key_from_session(self):
		'''
		Fetches the users key from the session.
		If the user does not exist, or if there is no user in the session,
		user key is returned as None
		@return: user_key
		@rtype: ndb.Key or None
		'''
		try:
			user = self.get_user_from_session()
			user_key = user.key
		except self.SessionError:
			user_key = None
		return user_key
		
	def get_station_from_session(self):
		session = get_current_session()
		try:
			station = session['station']
		except KeyError,e:
			raise self.SessionError(e)
		else:
			return station
	def calc_major_cities(self,artists):
		# TODO: redo this?
		'''
		@param artists: a list of artist entities
		@type artists: list
		@return: a list of cities with a minimum number of artists
		@rtype: list
		'''
		# minumum artists in a city to qualify to be a major city
		min_artists = 10
		cities = [a.city.lower() for a in artists if a.city]
		city_counts = Counter(cities).most_common()
#		logging.info(cities)
		cities = filter(lambda x: x[1] > min_artists,city_counts)
		cities = [c[0].title() for c in cities]
		logging.info(cities)
		return cities
	def package_artist_multi(self,artists):
		'''
		Packages a list of artists into dictionary form
		@param artists: a list of artist entities
		@type artists: list
		@return: a list of artists in dictionary form
		@rtype: list
		'''
		to_send = []
		for artist in artists:
			artist_dict = artist.to_dict(exclude=('created',))
			artist_dict.update({'id':artist.strkey})
			to_send.append(artist_dict)
		return to_send
class UploadHandler(ArtistHandler,blobstore_handlers.BlobstoreUploadHandler):
	pass

