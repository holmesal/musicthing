from collections import defaultdict
from datetime import datetime
from gaesessions import get_current_session
from geo import geohash
from google.appengine.ext import ndb
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
	_city_mode = 'city'
	_location_mode = 'location'
	_favorites_mode = 'favorites'
	_all_mode = 'all'
	available_modes = [_city_mode,_location_mode,_favorites_mode,_all_mode]
	
	def __init__(self,station_tags,serendipity,mode,mode_data=None):
		
		assert serendipity or serendipity < 0.01, 'serendipity is empty'
		assert serendipity <= 1., 'serendipity is too large, (0 < serendipity < 1), {}'.format(serendipity)
		if serendipity < 0.1:
			serendipity = 0.1
		self.serendipity = serendipity
		
		# set the station tags
		self.station_tags = station_tags
		logging.info(self.station_tags)
		if station_tags:
			keyfunc = lambda x: x[1]
			# calc the max count for the station tags
			self.station_max_count = keyfunc(max(station_tags.iteritems(),key=keyfunc))
			# calc the total count for the station tags
			self.station_total_count = sum(station_tags.values())
		
		# assign the station mode
		self.set_mode(mode,mode_data)
		
		# init the station track list index variable
		self.idx = 0
		# limit the number of tracks that can be played in one station
		self.max_tracks = 10#150
		
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
	def artists(self):
		# fetch all the artist ENTITIES from the tracks list
		return [t['artist'] for t in self.playlist]
	def playlist_json_friendly(self):
		to_return = []
		for track in self.playlist:
			to_return.append({
				'key' : track['key'],
				'rank' : track['rank']
				})
	def set_mode(self,mode,mode_data):
		'''
		Use to set the station mode
		@param mode: station mode
		@type mode: str
		'''
		assert mode in self.available_modes, 'Station mode not supported, {}'.format(mode)
		logging.info(mode)
		logging.info(mode_data)
		self._mode = mode
		self.mode_data = mode_data
		
	@property
	def mode(self):
		return self._mode
	def fetch_artist_keys(self):
		modes = {
				self._city_mode : {
								'func' : fetch_artist_keys_from_city,
								'params' : ('city','radius')#(self.mode_data['city'],self.mode_data['radius'])
								},
				self._favorites_mode : {
								'func' : fetch_favorite_artist_keys,
								'params' : ('user_key')#(self.mode_data['user_key'])
								},
				self._location_mode : {
								'func' : fetch_artist_keys_from_ghash,
								'params' : ('city','radius')#(self.mode_data['city'],self.mode_data['radius'])
								},
				self._all_mode : {
								'func' : fetch_all_artist_keys,
								'params' : None,
								}
				}
		# fetch the function and its params from the dict
		action = modes[self.mode]
		func = action['func']
		param_keys = action['params']
		try:
			params = (self.mode_data[p] for p in param_keys)
		except TypeError,e:
			raise TypeError(e)
		# get the attribute from self specified in the modes dict
#		params = getattr(self,param_attr) if param_attr is not None else None
		
		# fetch the artist keys using the func and params in the modes dict
		artist_keys = func(*params) if params is not None else func()
		
		return artist_keys
	@staticmethod
	def convert_artist_to_track(artist):
		return {
				'key' : artist.key,
				'artist':artist,
				'tags_to_counts' : artist.tags_dict,
				'tags_to_ranks' : {},
				'rank' : 0
				}
	def create_station(self):
		'''
		Creates a station using the station meta properties.
		Does not return anything.
		Saves a list of track objects to self
		Adds self to the current session
		
		@todo: need to handle a case where there are no artist keys returned. this is not a trivial case
		'''
		# query each of the tags from the station meta
		# create a list of iterators to fetch all of the keys
		timer = Timer()
		time = timer.time
		# fetch the applicable artist keys
		artist_keys = self.fetch_artist_keys()
		# TODO: filter out tacks that should not be played
		
		time('b_fetch_keys')
		if not self.station_tags:
			logging.info('empty station')
			artist_keys = [k for k in artist_keys]
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
			time('n_clip_track_length')
		else:
			logging.info('not empty station')
			# create artist future objects
			artist_futures = ndb.get_multi_async(artist_keys)
			time('c_get_futures')
			# create generator for getting artist results
			tracks = (f.get_result() for f in artist_futures)
			time('d_get_results')
			# convert tracks to station form
			tracks_list = (self.convert_artist_to_track(t) for t in tracks)
			time('e_parse_artist to track')
			# Rank the tracks based on their tags
			tracks_list = [self.rank_track(track) for track in tracks_list]
			time('m_rank_tracks')
			# add entropy
			
			
			
			### DEV
			warnings.warn('Playlist is not affected by serendipity')
			self.playlist = sorted(tracks_list,key=lambda x: x['rank'],reverse=True)
#			self.playlist = self.add_entropy(tracks_list, time)
			###
#		logging.info(', '.join([str(t['rank']) for t in self.playlist]))
		#=======================================================================
		# add station to current session
		#=======================================================================
		session = get_current_session()
		session['station'] = self
		session['idx'] = self.idx
		return session,timer.get_times()
	def rank_track(self,track):
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
def fetch_favorite_artist_keys(user_key):
	'''
	Fetches the keys of all artists that the user has favorited
	@param user_key:
	@type user_key:
	'''
	assert False, user_key
	# fetch all the keys for the Favorite entities that relate user --> artist
	favorite_keys = models.Favorite.query(ancestor = user_key).iter(batch_size = 50,keys_only = True)
	# favorite ids are the same as the artist ids - collect the ids from the favorite keys
	artist_ids = (key.id() for key in favorite_keys)
	# create artist keys from the ids collected from favorites
	artist_keys = (ndb.Key(models.Artist, i) for i in artist_ids)
	return artist_keys
def fetch_all_artist_keys():
	'''
	Fetches all artist keys asyncronously
	@return: An iterable that returns all artist keys
	@rtype: ndb.QueryIterator
	'''
	artist_keys = models.Artist.query().iter(batch_size=50,keys_only=True)
	return artist_keys
def fetch_artist_keys_from_city(city,radius):
	precision = 4
	ghash = city.ghash[:4]
	ghash_list = expand_ghash_list(ghash, n=3)
	artist_keys = fetch_artist_keys_from_ghash_list(ghash_list)
	return artist_keys
def fetch_artist_keys_from_ghash_list(ghash_list):
	ghash_list = set(ghash_list)
	artist_keys = set([])
	for ghash in ghash_list:
		keys = models.Artist.query(
						models.Artist.ghash >= ghash,
						models.Artist.ghash <= ghash+"{"
						).iter(
							batch_size = 50,
							keys_only = True)
		artist_keys.update(keys)
	return artist_keys
def fetch_artist_keys_from_city_key(city_key):
	'''
	Fetches all artist keys from a city with key: city_key
	@param city_key: the key of the city entity in question
	@type city_key: ndb.Key
	@return: An iterable that returns all artist keys
	@rtype: ndb.QueryIterator 
	'''
	artists = models.Artist.query(
								models.Artist.city_keys == city_key
								).iter(
									batch_size = 50,
									keys_only = True)
	return artists
def fetch_city_keys_from_ghash_list(ghash_list):
	'''
	'''
	
	
def fetch_artist_keys_from_ghash(ghash,n):
	'''
	Fetches all artists in a given ghash. The ghash can be of any length
	@param ghash: unicode ghash string of any length
	@type ghash: str
	@return: An iterable that returns all artist keys
	@rtype: ndb.QueryIterator
	'''
	assert False, ghash
	artist_keys = models.Artist.query(
					models.Artist.ghash >= ghash,
					models.Artist.ghash <= ghash+"{"
					).iter(
						batch_size = 50,
						keys_only = True)
	return artist_keys

def expand_ghash_list(ghash_list,n):
	'''
	Expands self.ghash n times
	@param n: number of expansions
	@type n: int
	'''
	if isinstance(ghash_list,basestring):
		ghash_list = [ghash_list,]
	ghash_list = set(ghash_list)
	for _ in range(0,n):
		# expand each ghash, and remove duplicates to expand a ring
		new_ghashes = set([])
		for ghash in ghash_list:
			new_ghashes.update(geohash.expand(ghash))
		# add new hashes to master list
		ghash_list.update(new_ghashes)
	return ghash_list
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
	ghash_list = [ghash]
	
	# determine number of iterations based on the precision
	ghash_list = expand_ghash_list(ghash_list, n)
	return ghash_list

def calc_bounding_box(ghash_list):
	'''
	Calculates a bounding box from a list of geohashes
	@param ghash_list: a list of geo_hashes
	@type ghash_list: list
	
	@return: {'bottom_left':<float>,'top_right':<float>}
	@rtype: dict
	'''
	points = [geohash.decode(ghash) for ghash in ghash_list]
	
	# calc precision from one the ghashes
	precision = max([ghash.__len__() for ghash in ghash_list])
	
	#unzip lat,lons into two separate lists
	lat,lon = zip(*points)
	
	#find max lat, long
	max_lat = max(lat)
	max_lon = max(lon)
	#find min lat, long
	min_lat = min(lat)
	min_lon = min(lon)
	
	# encode the corner points
	bottom_left_hash = geohash.encode(min_lat,min_lon,precision)
	top_right_hash = geohash.encode(max_lat, max_lon, precision)
	
	# get bounding boxes for the corner hashes
	tr = geohash.bbox(top_right_hash)
	bl = geohash.bbox(bottom_left_hash)
	# get the corner coordinates for the two corner hashes
	top_right = (tr['n'],tr['e'])
	bottom_left = (bl['s'],bl['w'])
	# compile into dict
	bounding_box = {
				'bottom_left'	: bottom_left,
				'top_right'		: top_right
				}
	return bounding_box



#	def create_station_(self):
#		'''
#		Creates a station using the station meta properties.
#		Does not return anything.
#		Saves a list of track objects to self
#		Adds self to the current session
#		'''
#		# query each of the tags from the station meta
#		# create a list of iterators to fetch all of the keys
#		timer = Timer()
#		time = timer.time
#		if self.city:
#			artist_keys = models.Artist.query(models.Artist.city == self.city).iter(batch_size=50,keys_only=True)
#		else:
#			artist_keys = fetch_all_artist_keys()
#		time('b_fetch_keys')
#		f = lambda x: {'key':x.key,'artist':x,'tags_to_counts':x.tags_dict,'tags_to_ranks':{},'rank':0}
#		if not self.station_tags:
#			logging.info('empty station')
##			if self.city:
##				artists = models.Artist.query(models.Artist.city == self.city).iter(batch_size=50)
##			else:
##				artists = models.Artist.query().iter(batch_size=50)
##			tracks = [f(a) for a in tracks]
##			tracks = [track for track in tracks]
##			random.shuffle(tracks_list)
#			# this line necessary b/c artist_keys is a generator
#			artist_keys = [k for k in artist_keys]
#			try:
#				artist_keys = random.sample(artist_keys,self.max_tracks)
#			except ValueError:
#				pass
#			
#			random.shuffle(artist_keys)
#			time('select_random_artists')
#			artists = ndb.get_multi(artist_keys)
#			tracks_list = [f(a) for a in artists]
#			self.playlist = tracks_list
#			time('n_clip_track_length')
#		else:
#			logging.info('not empty station')
#			artist_futures = ndb.get_multi_async(artist_keys)#[a.get_async() for a in artist_keys]
#			time('c_get_futures')
#			tracks = (f.get_result() for f in artist_futures)
#			time('d_get_results')
#			
#			tracks_list = [f(t) for t in tracks]
#			time('e_parse_artist to track')
#			#=======================================================================
#			# Rank the tracks based on their tags
#			#=======================================================================
#			for track in tracks_list:
#				for tag,station_count in self.station_tags.iteritems(): # for each tag in the station
#					try:
#						# pull the track affinity for the station tag
#						track_count = track['tags_to_counts'][tag]
#						# rank the track tag based on the station tag
#						track['tags_to_ranks'][tag] = self._rank_track_tags(track_count,station_count)
#						logging.info(track['tags_to_ranks'][tag])
#					except KeyError:
#						# the track did not have that tag in its list of tags
#						pass
#				# set the total rank of the track
#				track['rank'] = self._rank_track(track['tags_to_ranks'])
#			time('m_rank_{}_tracks'.format(tracks_list.__len__()))
#			#=======================================================================
#			# # add some entropy
#			#=======================================================================
#			keyfunc = lambda x: x['rank']
#			max_rank = keyfunc(max(tracks_list,key=keyfunc))
#			time('n_calc_max_rank')
#			if max_rank < 0.0001:
#				max_rank = 0.1
#			logging.info('max rank: '+str(max_rank))
#			min_rank = 0
#			for track in tracks_list:
#				rank = track['rank']
#				random_factor = max_rank*self.serendipity
#				rank_plus = rank + random_factor
#				if rank_plus > max_rank:
#					rank_plus = max_rank
#				rank_minus = rank - random_factor
#				if rank_minus < min_rank:
#					rank_minus = min_rank
##				range_factor = 100.
##				rank_plus = int(rank_plus*range_factor)
##				rank_minus = int(rank_minus*range_factor)
#				if rank_plus == rank_minus:
#					logging.info('! same ranks')
#					new_rank = rank
#				else:
#					new_rank = random.uniform(rank_minus,rank_plus)
##					r = [x/range_factor for x in range(rank_minus,rank_plus)]
##					new_rank = random.choice(r)
#				track['rank'] = new_rank
#				track['old_rank'] = rank
##				logging.info('-->')
##				logging.info('rank: '+str(rank))
##				logging.info('new_rank: '+str(new_rank))
##				logging.info('serendipity: '+str(self.serendipity))
##				logging.info('random_factor: '+str(random_factor))
##				logging.info('rank_plus: '+str(rank_plus/range_factor))
##				logging.info('rank_minus: '+str(rank_minus/range_factor))
#			time('o_entropy_gen')
#			# sort the tracks list based on their new ranks
#			playlist = sorted(tracks_list,key=lambda x: x['rank'],reverse=True)
#			time('p_sort_tracks')
#			self.playlist = playlist[:self.max_tracks]
##		logging.info(', '.join([str(t['rank']) for t in self.playlist]))
#		#=======================================================================
#		# add station to current session
#		#=======================================================================
#		session = get_current_session()
#		session['station'] = self
#		session['idx'] = self.idx
#		return session,timer.get_times()