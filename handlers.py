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
import utils
import json
from google.appengine.ext import ndb
from geo import geohash

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
#			artist_id = str(artist_id)
			artist_id = int(artist_id)
			logging.info(artist_id)
			artist = models.Artist.get_by_id(artist_id)
			assert artist, 'Artist does not exist'
		except AssertionError,e:
			raise self.SessionError(e)
		else:
			return artist
			
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
	def convert_client_tags_to_tags_dict_OLD(self, raw_tags):
		'''
		This method is used on the artist addtags page where we are using the old form
		
		@param raw_tags: list of tag objects [{'name':'radiohead','count':100},]
		@type raw_tags: list
		@return: tag:count mapping
		@rtype: dict
		'''
		tags = defaultdict(int)
		for t in raw_tags:
			name = t['name']
			count = int(t['count'])
			tags[name] += count
		max_count = max(tags.values())
		# normalize the counts by dividing by the max value and *100
		tags = {key:int(float(count)/float(max_count)*100) for key,count in tags.iteritems()}
		return tags
		
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
		max_count = max(tags.values())
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
		'''Pulls the station from the session.
		@raise self.SessionError: if station doesn't exist
		@return: a music station
		@rtype: utils.StationPlayer
		'''
		session = get_current_session()
		try:
			station = session['station']
		except KeyError,e:
			raise self.SessionError(e)
		else:
			return station
	def get_or_create_station_from_session(self):
		'''Pulls the station from the session.
		If a station does not exist in the session,
		an empty station is created
		@return: a music station
		@rtype: utils.StationPlayer
		'''
		try:
			station = self.get_station_from_session()
		except self.SessionError:
			station = utils.StationPlayer()
		
		return station
	def change_station_mode(self,mode,mode_data):
		'''
		Changes the mode of a station. If the station doesn't exist,
		a new one is created using the mode and mode_data provided
		@param mode: station player mode
		@type mode: str
		@param mode_data: info needed for the specified mode
		@type mode_data: dict
		@return: a list of packaged artists for the client
		@rtype: list
		'''
		timer = utils.Timer()
		time = timer.time
		
		# grab the station
		station = self.get_or_create_station_from_session()
		time('get or create station')
		# set the station mode
		station.set_mode(mode,mode_data)
		time('set mode')
		
		# create the station!!
		algo_times = station.create_station()
		time('create_station()')
		
		# pull the first 10 tracks
		tracks = station.fetch_next_n_tracks()
		time('fetch tracks')
		
		# package the fuckers!
		
		global_times = timer.get_times()
		logging.info('{} tracks in the playlist'.format(station.playlist.__len__()))
		logging.info(json.dumps({'global':global_times,'algo':algo_times}))
		
		# add the station to the session
		station.add_to_session()
		time('add to session')
		
		return tracks
	def send_success(self,response):
		'''
		Simple method to send a list of packaged artists
		@param packaged_artists: list of packaged artists dicts
		@type packaged_artists: list
		'''
		to_send = {
				'success' : 1,
				'response' : response
				}
		self.response.out.write(json.dumps(to_send))
		
	def fetch_radial_cities(self,ghash,precision=4,n=3):
		'''
		Fetches cities around the specified ghash
		Sorts the cities by distance from the center ghash
		@param ghash: the ghash of the center point
		@type ghash: str
		'''
		# calc the center geo_point
		center_geo_point = geohash.decode(ghash)
		# create a list of ghashes around the 
		ghash = utils.chop_ghash(ghash, precision)
		ghash_list = utils.create_ghash_list(ghash, n)
		# get a list of all the city keys in the range of ghashes
		city_keys_set = set([])
		for ghash in ghash_list:
			city_keys = models.City.query(
						models.City.ghash >= ghash,
						models.City.ghash <= ghash+"{"
						).iter(
							batch_size = 50,
							keys_only = True)
			city_keys_set.update(city_keys)
		
		city_futures = ndb.get_multi_async(city_keys_set)
		cities = (c.get_result() for c in city_futures)
		
		cities_list = []
		# calculate the distance from the center ghash
		for city in cities:
			# package the city for the radius list
			city_dict = city.package_for_radius_list()
			# calc distance from center point
			distance = utils.distance_between_points(center_geo_point, city.geo_point)
			# add the distance 
			city_dict['distance'] = distance
			cities_list.append(city_dict)
		
		# sort the list of cities by distance
		cities_list = sorted(cities_list,key=lambda c: c['distance'])
		return cities_list
		
	def calc_major_cities(self):
		'''
		Tries to calc major cities with the most artists
		@param artists:
		@type artists:
		'''
		
		min_artists = 20
		popular_city_keys = []
		for key in models.City.query().iter(keys_only=True):
			artist_count = models.Artist.query(models.Artist.cities.city_key == key).count()
			if artist_count > min_artists:
				popular_city_keys.append((key,artist_count))
		# sort the keys
		popular_city_keys = sorted(popular_city_keys,key=lambda x: x[1])
		# grab only the city keys
		city_keys = (x[0] for x in popular_city_keys)
		# fetch them!
		city_futures = ndb.get_multi_async(city_keys)
		cities = (f.get_result() for f in city_futures)
		
		to_send = (c.to_dict() for c in cities)
		return to_send
class UploadHandler(ArtistHandler,blobstore_handlers.BlobstoreUploadHandler):
	pass

