from collections import defaultdict
from datetime import datetime
from gaesessions import get_current_session
from geo import geohash
from google.appengine.ext import ndb
from math import radians, asin, cos, sin, sqrt
import logging
import models
import random
import warnings

class Timer(object):
	def __init__(self):
		self.times_dict = {}
		self.init_time = datetime.now()
		self.last_time = datetime.now()
	def time(self,name):
		now = datetime.now()
		dt = now - self.last_time
		self.last_time = now
		self.times_dict.update({name:dt})
	def get_times(self):
		times_dict = {key:str(val) for key,val in self.times_dict.iteritems()}
		times_dict.update({'_total':str(datetime.now()-self.init_time)})
		return times_dict
class StationPlayer(object):
	_city_mode = 'city_mode'
	_location_mode = 'location_mode'
	_favorites_mode = 'favorites_mode'
	_all_mode = 'all_mode'
	available_modes = [_city_mode,_location_mode,_favorites_mode,_all_mode]
	
	def __init__(self):
		# init station data variables.
		self._mode = None
		self.city_entity = None
		self.radial_city_keys = None
		self.user_key = None
		self.ghash = None
		
		# init the station track list index variable
		self.idx = 0
		self.previous_idx = 0
		
		# limit the number of tracks that can be played in one station
#		warnings.warn('Max tracks is not set to the production value')
		self.max_tracks = 150
		
		self.skipped_artist_keys = []
		
	@property
	def city_dict(self):
		return self.city_entity.to_dict()
	@property
	def geo_point(self):
		geo_point = geohash.decode(self.ghash)
		return {
			'lat' : geo_point[0],
			'lon' : geo_point[1]
			}
	@property
	def mode(self):
		return self._mode
	def set_mode(self,mode,**mode_data):
		'''
		Use to set the station mode
		All params that are not sent in mode_data are set to None by default
		
		If mode is set to none, create_station will raise an error
		
		@param mode: station mode
		@type mode: str
		@param mode_data: all the information needed to play a station in the specified mode
		@type mode_data: dict
		'''
		# assure mode is supported
		assert mode is None or mode in self.available_modes, 'Station mode not supported, {}'.format(mode)
		
		# set mode
		self._mode = mode
		
		# set the mode data
		for key,val in mode_data.iteritems():
			setattr(self, key, val)
		
		# if have a city but not ghash, convert city to ghash
		if self.city_entity is not None:
			self.ghash = self.city_entity.ghash
		
		
	def set_station_tags(self,station_tags = None,client_tags = None):
		'''
		Updates the stations tags
		@param station_tags: dict of tag:count that is used in the station calc
		@type station_tags: dict
		@param client_tags: the original list of artist dicts that the client uses
		@type client_tags: list
		'''
		# this is necessary in the even that an empty dict is passed as station tags
		if not station_tags:
			station_tags = None
		
		# make sure that if tags are passed, the original form is preserved
		if station_tags is not None:
			assert client_tags is not None, 'If passing tags, must also pass in client form.'
		
		# set the station tags to the station
		self.station_tags = station_tags
		self.client_tags = client_tags
		
		# if tags exist, calculate some necessary values for the station calculations
		if station_tags is not None:
			# calc the max count for the station tags
			keyfunc = lambda x: x[1]
			self.station_max_count = keyfunc(max(station_tags.iteritems(),key=keyfunc))
			# calc the total count for the station tags
			self.station_total_count = sum(station_tags.values())
	def record_skipped_tracks(self):
		pass
	def fetch_artist_keys(self):
		'''
		Fetches all of the artist keys that apply to the stations current mode
		@return: a list of artist keys
		@rtype: list
		'''
		modes = {
				self._city_mode : {
								'func' : fetch_artist_keys_from_city_key_list,
								'params' : self.radial_city_keys
								},
				self._favorites_mode : {
								'func' : fetch_artist_keys_from_favorites,
								'params' : self.user_key
								},
				self._location_mode : {
								'func' : fetch_artist_keys_from_ghash,
								'params' : self.radial_city_keys
								},
				self._all_mode : {
								'func' : fetch_all_artist_keys,
								'params' : None,
								}
				}
		# fetch the function and its params from the dict
		action = modes[self.mode]
		func = action['func']
		params = action['params']
		
		# fetch the artist keys using the func and params in the modes dict
		artist_keys = func(*params) if params is not None else func()
		
		# filter out the hard blacklisted keys
		blacklisted_keys = self.fetch_hard_blacklist()
		if blacklisted_keys:
			artist_keys = (a for a in artist_keys if a not in blacklisted_keys)
		
		# filter out artists that do not have a track
		artist_keys = filter(lambda a: a.track_id is not None,artist_keys)
		return artist_keys
	def fetch_hard_blacklist(self):
		'''
		Some tracks should not be played. EVER.
		@return: a set of keys that the user has requested 
		@rtype: set
		'''
		user_key = self.user_key
		if user_key is None:
			# if there is no user tied to the station, return None
			return None
		# fetch all the NeverPlay artists
		never_plays = models.NeverPlay.query(ancestor = user_key).iter(batch_size=50,keys_only=True)
		# convert NeverPlay entities to artist entities with the same ids
		blacklisted_keys = set([ndb.Key(models.Artist,n.id()) for n in never_plays])
		
		return blacklisted_keys
		
	def calc_tag_rank(self,track_count,station_count):
		'''
		Compares the tag counts for station tags and track tags.
		@param track_count:
		@type track_count:
		@param station_count:
		@type station_count:
		@return: a rank for the track tag
		@rtype: float
		'''
		inverted_diff = self.station_max_count - abs(station_count - track_count)
		station_tag_weight = float(station_count)/float(self.station_max_count)
		rank = inverted_diff * station_tag_weight
		return rank
	def calc_total_rank(self,tags_to_rank):
		'''
		Sum the weighted counts in each of the tags, and normalize by the max score
		@param tags_to_rank: mapping of {'tag':rank}
		@type tags_to_rank: dict
		@param station_total_count: the sum of all the tag counts in the station
		@type station_total_count: int
		@return: the total rank of the track w/ respect to the station
		'''
		track_total_rank = sum(tags_to_rank.values())
		return float(track_total_rank)/float(self.station_total_count)*100
	@staticmethod
	def convert_artist_to_track(artist):
		return {
				'key' : artist.key,
				'artist':artist,
				'tags_to_counts' : artist.tags_dict,
				'tags_to_ranks' : {},
				'rank' : 0
				}
	def fetch_next_n_tracks(self,n=10):
		'''
		Fetches next n tracks from the playlist
		Updates the station self.idx value so the next time this method
		is called, the first track fetched is the next track after the
		last track returned by the previous call
		@param n: the number of tracks to be fetched
		@type n: int
		@return: a list of n tracks
		@rtype: list
		'''
		idx = self.idx
		logging.info('playlist length:'+str(self.playlist.__len__()))
		logging.info('beginning idx: '+str(idx))
		# calc maximum possible index
		max_idx = self.playlist.__len__() -1
		# reset the playlist if all tracks have been played
		if idx == max_idx:
			idx = 0
		
		# calc the posterior index
		new_idx = idx+n
		# limit the posterior index to the length of the playlist
		if new_idx > max_idx:
			new_idx = max_idx
		logging.info('new_index: '+str(new_idx))
		# store the previous index
		self.previous_idx = idx
		# set the posterior index to the next iterations anterior index
		self.idx = new_idx
		
		# normal case, where playlist is at least two elements long
		if new_idx > 0:
			tracks = self.playlist[idx:new_idx]
		# special cases
		# playlist is one element long
		elif new_idx == 0:
			tracks = self.playlist
		# playlist is empty
		elif new_idx == -1:
			tracks = []
		
		return tracks
		
	def create_station(self):
		'''
		Creates a station using the station meta properties.
		Saves a list of track objects to self
		@todo: need to handle a case where there are no artist keys returned. this is not a trivial case
		'''
		# assure mode is set
		assert self.mode is not None, 'Station mode not set.'
		
		# query each of the tags from the station meta
		# create a list of iterators to fetch all of the keys
		timer = Timer()
		time = timer.time
		# fetch the applicable artist keys
		artist_keys = self.fetch_artist_keys()
		time('b fetch_keys')
		
		if self.station_tags is None or self.mode == self._favorites_mode:
			logging.info('Station does not have tags or is favorites')
			# artist keys cannot be a generator object
			artist_keys = list(artist_keys)
			# Try to fetch a sample of artists from the list of available artists
			try:
				artist_keys = random.sample(artist_keys,self.max_tracks)
			except ValueError:
				# if self.max_tracks > artist_keys.__len__(), just use all tracks
				pass
			
			# shuffle the selected tracks
			random.shuffle(artist_keys)
			time('select_random_artists')
			# fetch the entities synchronously
			artists = ndb.get_multi(artist_keys)
			# convert to station form
			tracks_list = [self.convert_artist_to_track(a) for a in artists]
			# set tracks to station
			self.playlist = tracks_list
			time('n clip_track_length')
		else:
			logging.info('Station has tags')
			# create artist future objects
			artist_futures = ndb.get_multi_async(artist_keys)
			time('c get futures')
			# create generator for getting artist results
			tracks = (f.get_result() for f in artist_futures)
			time('d get results')
			# convert tracks to station form
			tracks_list = (self.convert_artist_to_track(t) for t in tracks)
			time('e parse artist to track')
			# Rank the tracks based on their tags
			tracks_list = [self.rank_track(track) for track in tracks_list]
			time('m rank tracks')
			
			success_tracks,fail_tracks = self.clip_low_ranked_tracks(tracks_list)
#			if success_tracks.__len__() != self.max_tracks:
#				fail_tracks = random.shuffle(fail_tracks)
			
			
			### DEV
#			warnings.warn('Playlist is not affected by entropy')
			success_tracks = self.add_entropy(success_tracks, time)
			self.playlist = sorted(success_tracks,key=lambda x: x['rank'],reverse=True)[:self.max_tracks]
			# add entropy
#			self.playlist = self.add_entropy(success_tracks, time)
			###
		return timer.get_times()
#		logging.info(', '.join([str(t['rank']) for t in self.playlist]))
	def add_to_session(self,session = None):
		if session is None:
			session = get_current_session()
		session['station'] = self
		return session
	def clip_low_ranked_tracks(self,tracks):
		'''
		Splits a list into two lists: success and fail
		Success is all tracks that have a rank greater than the minimum rank
		Fail is all tracks that have a rank less than the minimum rank
		min_rank is taken as a certain percentage of the max_rank
		@param tracks: the list of track dicts
		@type tracks: list
		@return: success_list,fail_list
		@rtype: tuple
		'''
		keyfunc = lambda x: x['rank']
		max_rank = keyfunc(max(tracks,key=keyfunc))
		# only take the top 70% of the tracks
		min_rank = 0.3*float(max_rank)
		
		success_list = []
		fail_list = []
		for t in tracks:
			if t['rank'] >= min_rank:
				success_list.append(t)
			else:
				fail_list.append(t)
		
		return success_list,fail_list
		
	def rank_track(self,track):
		'''
		Calculates an overall rank for a track by ranking each of its constituent tags
		@param track: track dict, not an artist
		@type track: dict
		@return: the same track that was passed, updated with rank info
		@rtype: dict
		'''
		for station_tag,station_count in self.station_tags.iteritems(): # for each tag in the station
			try:
				# pull the track affinity for the station tag
				# this will raise KeyError if the station tag doesnt exist in the track
				track_count = track['tags_to_counts'][station_tag]
				# rank the track tag based on the station tag
				track['tags_to_ranks'][station_tag] = self.calc_tag_rank(track_count,station_count)
#				logging.info(track['tags_to_ranks'][station_tag])
			except KeyError:
				# the track did not have that tag in its list of tags
				pass
		# set the total rank of the track based on all tag ranks
		track['rank'] = self.calc_total_rank(track['tags_to_ranks'])
		return track
	def add_entropy(self,tracks_list,time):
		self.serendipity = 0.2
		warnings.warn('serendipity is hardcoded to 0.2')
		keyfunc = lambda x: x['rank']
		max_rank = keyfunc(max(tracks_list,key=keyfunc))
		time('n_calc_max_rank')
		if max_rank < 0.0001:
			max_rank = 0.1
		logging.info('max rank: '+str(max_rank))
		min_rank = 0
		for track in tracks_list:
			rank = track['rank']
			# set the range on how far each track is allowed to propagate
			random_factor = max_rank*self.serendipity
			# create an upper limit on track propagation
			rank_plus = rank + random_factor
			if rank_plus > max_rank:
				rank_plus = max_rank
			# create a lower limit on track propagation
			rank_minus = rank - random_factor
			if rank_minus < min_rank:
				rank_minus = min_rank
			# if the ranks are the same, use the original rank
			if rank_plus == rank_minus:
				logging.info('! same ranks')
				new_rank = rank
			else:
				# randomly select a new range given the upper and lower bounds
				new_rank = random.uniform(rank_minus,rank_plus)
			# set the new rank and old rank to the track
			track['rank'] = new_rank
			track['old_rank'] = rank
#				logging.info('-->')
			logging.info('rank: '+str(rank))
#				logging.info('new_rank: '+str(new_rank))
#				logging.info('serendipity: '+str(self.serendipity))
#				logging.info('random_factor: '+str(random_factor))
#				logging.info('rank_plus: '+str(rank_plus/range_factor))
#				logging.info('rank_minus: '+str(rank_minus/range_factor))
		time('o_entropy_gen')
		# sort the tracks list based on their new ranks
		playlist = sorted(tracks_list,key=lambda x: x['rank'],reverse=True)
		time('p_sort_tracks')
		return playlist[:self.max_tracks]
	@staticmethod
	def api_package_track_multi(tracks):
		'''
		Packages playlist into api form
		@param tracks: self.playlist tracks
		@type tracks: list
		@return: a list of artist dicts
		@rtype: list
		'''
		# grab the artists from the tracks
		artists = [t['artist'] for t in tracks]
		# package all the artists for the client
		to_send = []
		for artist in artists:
			# remove the fields that are not json serializable
			exclude = ('created','access_token','email','description','image_key',
					'track_url','tags_','genre','external_image_url','cities','city')
			artist_dict = artist.to_dict(exclude=exclude)
			# add the artists id to the dict, for reference upon return to server
			artist_dict.update({
							'id' : artist.strkey,
							'soundcloud_id' : artist.strkey,
							'vicinity' : artist.city
							})
			# add the artist dict to the to_send array
			to_send.append(artist_dict)
		return to_send
	@staticmethod
	def package_track_multi(tracks):
		'''
		Packages playlist tracks into a form that is relevant to the client
		Assumes that the tracks are already in a relevant order
		@param tracks: self.playlist tracks
		@type tracks: list
		@return: a list of artist dicts
		@rtype: list
		'''
		# grab the artists from the tracks
		artists = [t['artist'] for t in tracks]
		# package all the artists for the client
		to_send = []
		for artist in artists:
			# remove the fields that are not json serializable
			exclude = ('created','access_token','email','description','image_key',
					'track_url','tags_','genre','external_image_url','cities')
			artist_dict = artist.to_dict(exclude=exclude)
			# add the artists id to the dict, for reference upon return to server
			artist_dict.update({
							'id' : artist.strkey,
							'soundcloud_id' : artist.strkey,
							'tags' : artist.tags_dict,
							'city	' : artist.city_dict()
							})
			# add the artist dict to the to_send array
			to_send.append(artist_dict)
		return to_send

	
def fetch_city_from_path(country,admin1,city_name,geo_point):
	'''
	Fetches a city from the ndb.
	Properly creates any missing elements along the key path
	@param country: e.g. United States
	@type country: str
	@param admin1: e.g. MA
	@type admin1: str
	@param city_name: e.g. Boston
	@type city_name: str
	@param geo_point: The cities geopoint as an ndb geopoint property
	@type geo_point: ndb.GeoPt
	
	@return: the city entity specified by the path provided
	@rtype: models.City
	'''
	ghash = geohash.encode(geo_point.lat, geo_point.lon, precision=8)
	country_entity = models.Country().get_or_insert(country.lower(),
												name = country)
	admin1_entity = models.Admin1().get_or_insert(
						admin1.lower(),
						parent = country_entity.key,
						name = admin1)
	city_entity = models.City().get_or_insert(
					city_name.lower(),
					parent = admin1_entity.key,
					name = city_name,
					ghash = ghash)
	return city_entity
def fetch_artist_keys_from_favorites(user_key):
	'''
	Fetches the keys of all artists that the user has favorited
	@param user_key:
	@type user_key:
	'''
	# fetch all the keys for the Favorite entities that relate user --> artist
	favorite_keys = models.Favorite.query(ancestor = user_key).iter(batch_size = 50,keys_only = True)
	# favorite ids are the same as the artist ids - collect the ids from the favorite keys
	artist_keys = (ndb.Key(models.Artist, k.id()) for k in favorite_keys)
	return artist_keys
def fetch_all_artist_keys():
	'''
	Fetches all artist keys asyncronously
	@return: An iterable that returns all artist keys
	@rtype: ndb.QueryIterator
	'''
	artist_keys = models.Artist.query().iter(batch_size=50,keys_only=True)
	return artist_keys
def fetch_artist_keys_from_city_key_list(city_key_list):
	'''Fetches artist keys from a list of city keys
	'''
	artist_keys = models.Artist.query(
						models.Artist.cities.city_key.IN(city_key_list)).iter(
						keys_only=True)
	return artist_keys
def fetch_artist_keys_from_ghash(ghash):
	'''
	@param ghash: unicode ghash string of any length
	@type ghash: str
	@return: An iterable that returns all artist keys
	@rtype: ndb.QueryIterator
	'''
	ghash = chop_ghash(ghash)
	ghash_list = create_ghash_list(ghash)
	artist_keys = fetch_artist_keys_from_ghash_list(ghash_list)
	return artist_keys
def fetch_artist_keys_from_ghash_list(ghash_list):
	'''
	Fetches artist keys from a list of ghashes
	@param ghash_list: a list of ghashes
	@type ghash_list: list
	@return: a list of artist keys
	@rtype: list
	'''
	ghash_list = set(ghash_list)
	artist_keys = set([])
	for ghash in ghash_list:
		keys = models.Artist.query(
						models.Artist.cities.ghash >= ghash,
						models.Artist.cities.ghash <= ghash+"{"
						).iter(
							batch_size = 50,
							keys_only = True)
		artist_keys.update(keys)
	return artist_keys
def chop_ghash(ghash,precision=4):
	'''
	Returns only the number of chars specified by precision
	@return: a ghash with precision up to the precision specified
	@rtype: str
	'''
	return ghash[:precision]
def create_ghash_list(ghash,n=3):
	'''
	Creates a list of ghashes from the provided geo_point
	Expands the ghash list a number of times depending on the precision
	
	@param geo_point: The center of the requested ghash list box
	@type geo_point: db.GeoPt
	@param precision: The desired precision of the ghashes
	@type precision: int
	
	@return: A unique list of ghashes
	@rtype: list
	'''
	ghash_list = set([ghash])
	
	# determine number of iterations based on the precision
	for _ in range(0,n):
		# expand each ghash, and remove duplicates to expand a ring
		new_ghashes = set([])
		for ghash in ghash_list:
			new_ghashes.update(geohash.expand(ghash))
		# add new hashes to master list
		ghash_list.update(new_ghashes)
	return ghash_list


def distance_between_points((lat1, lon1), (lat2, lon2)):
	# all args are in degrees
	# WARNING: loss of absolute precision when points are near-antipodal
	Earth_radius_km = 6371.0
	Earth_radius_mi = 3958.76
	RADIUS = Earth_radius_mi
	def haversine(angle_radians):
		return sin(angle_radians / 2.0) ** 2
	
	def inverse_haversine(h):
		return 2 * asin(sqrt(h)) # radians
	lat1 = radians(lat1)
	lat2 = radians(lat2)
	dlat = lat2 - lat1
	dlon = radians(lon2 - lon1)
	h = haversine(dlat) + cos(lat1) * cos(lat2) * haversine(dlon)
	return RADIUS * inverse_haversine(h)
