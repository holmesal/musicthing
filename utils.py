from gaesessions import get_current_session
import random
import logging
from datetime import datetime

import models
from collections import defaultdict
from google.appengine.ext import ndb
from math import radians, asin, cos, sin, sqrt
from geo import geohash
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
	max_serendipity = 255.
	def __init__(self,station_tags,serendipity,city=None):
		self.station_tags = station_tags
		logging.info(self.station_tags)
		assert serendipity or serendipity < 0.01, 'serendipity is empty'
		if serendipity < 0.1:
			serendipity = 0.1
		self.serendipity = serendipity
		self.city = city
		# calculated values
		if station_tags:
			keyfunc = lambda x: x[1]
			self.station_max_count = keyfunc(max(station_tags.iteritems(),key=keyfunc))
			self.station_total_count = sum(station_tags.values())
		
		# init the iterator index variable
		self.idx = 0
		# set the limit to the number of tracks that can be played
		self.max_tracks = 150
		
	def _rank_track_tags(self,track_count,station_count):
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
		return inverted_diff * station_tag_weight
	def _rank_track(self,tags_to_rank):
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
		return [t['artist'] for t in self.sorted_tracks_list]
	def create_station(self):
		'''
		Creates a station using the station meta properties.
		Does not return anything.
		Saves a list of track objects to self
		Adds self to the current session
		'''
		# query each of the tags from the station meta
		# create a list of iterators to fetch all of the keys
		timer = Timer()
		time = timer.time
		if self.city:
			artist_keys = models.Artist.query(models.Artist.city == self.city).iter(batch_size=50,keys_only=True)
		else:
			artist_keys = models.Artist.query().iter(batch_size=50,keys_only=True)
		time('b_fetch_keys')
		f = lambda x: {'key':x.key,'artist':x,'tags_to_counts':x.tags_dict,'tags_to_ranks':{},'rank':0}
		if not self.station_tags:
			logging.info('empty station')
#			if self.city:
#				artists = models.Artist.query(models.Artist.city == self.city).iter(batch_size=50)
#			else:
#				artists = models.Artist.query().iter(batch_size=50)
#			tracks = [f(a) for a in tracks]
#			tracks = [track for track in tracks]
#			random.shuffle(tracks_list)
			# this line necessary b/c artist_keys is a generator
			artist_keys = [k for k in artist_keys]
			try:
				artist_keys = random.sample(artist_keys,self.max_tracks)
			except ValueError:
				pass
			
			random.shuffle(artist_keys)
			time('select_random_artists')
			artists = ndb.get_multi(artist_keys)
			tracks_list = [f(a) for a in artists]
			self.sorted_tracks_list = tracks_list
			time('n_clip_track_length')
		else:
			logging.info('not empty station')
			artist_futures = ndb.get_multi_async(artist_keys)#[a.get_async() for a in artist_keys]
			time('c_get_futures')
			tracks = (f.get_result() for f in artist_futures)
			time('d_get_results')
			
			tracks_list = [f(t) for t in tracks]
			time('e_parse_artist to track')
			#=======================================================================
			# Rank the tracks based on their tags
			#=======================================================================
			for track in tracks_list:
				for tag,station_count in self.station_tags.iteritems(): # for each tag in the station
					try:
						# pull the track affinity for the station tag
						track_count = track['tags_to_counts'][tag]
						# rank the track tag based on the station tag
						track['tags_to_ranks'][tag] = self._rank_track_tags(track_count,station_count)
						logging.info(track['tags_to_ranks'][tag])
					except KeyError:
						# the track did not have that tag in its list of tags
						pass
				# set the total rank of the track
				track['rank'] = self._rank_track(track['tags_to_ranks'])
			time('m_rank_{}_tracks'.format(tracks_list.__len__()))
			#=======================================================================
			# # add some entropy
			#=======================================================================
			keyfunc = lambda x: x['rank']
			max_rank = keyfunc(max(tracks_list,key=keyfunc))
			time('n_calc_max_rank')
			if max_rank < 0.0001:
				max_rank = 0.1
			logging.info('max rank: '+str(max_rank))
			min_rank = 0
			for track in tracks_list:
				rank = track['rank']
				random_factor = max_rank*self.serendipity
				rank_plus = rank + random_factor
				if rank_plus > max_rank:
					rank_plus = max_rank
				rank_minus = rank - random_factor
				if rank_minus < min_rank:
					rank_minus = min_rank
#				range_factor = 100.
#				rank_plus = int(rank_plus*range_factor)
#				rank_minus = int(rank_minus*range_factor)
				if rank_plus == rank_minus:
					logging.info('! same ranks')
					new_rank = rank
				else:
					new_rank = random.uniform(rank_minus,rank_plus)
#					r = [x/range_factor for x in range(rank_minus,rank_plus)]
#					new_rank = random.choice(r)
				track['rank'] = new_rank
				track['old_rank'] = rank
#				logging.info('-->')
#				logging.info('rank: '+str(rank))
#				logging.info('new_rank: '+str(new_rank))
#				logging.info('serendipity: '+str(self.serendipity))
#				logging.info('random_factor: '+str(random_factor))
#				logging.info('rank_plus: '+str(rank_plus/range_factor))
#				logging.info('rank_minus: '+str(rank_minus/range_factor))
			time('o_entropy_gen')
			# sort the tracks list based on their new ranks
			sorted_tracks_list = sorted(tracks_list,key=lambda x: x['rank'],reverse=True)
			time('p_sort_tracks')
			self.sorted_tracks_list = sorted_tracks_list[:self.max_tracks]
#		logging.info(', '.join([str(t['rank']) for t in self.sorted_tracks_list]))
		#=======================================================================
		# add station to current session
		#=======================================================================
		session = get_current_session()
		session['station'] = self
		session['idx'] = self.idx
		return session,timer.get_times()
#		return timer.get_times()
	
#			if self.city:
#				# also filter by city
#				tags_to_keys = {tag:models.Artist.query(
#										models.Artist.tags_.genre == tag,
#										models.Artist.city == self.city
#										).iter(batch_size=50,keys_only=True) \
#							for tag in self.station_tags}
#			else:
#				# do not filter by city
#				tags_to_keys = {tag:models.Artist.query(models.Artist.tags_.genre == tag
#										).iter(batch_size=50,keys_only=True) \
#							for tag in self.station_tags}
#			# reverse key:val mappings, so tracks become unique and are mapped to lists of their tags
#			# reduces number of gets required from the datastore
#			keys_to_tags = defaultdict(list)
#			for tag,tag_qit in tags_to_keys.iteritems():
#				# each of the tags is mapped to an iterator for getting artist keys
#				for key_result in tag_qit:
#	#				# result: {ndb.Key:['tag','tag','tag']}
#					keys_to_tags[key_result].append(tag)
#			# make keys_to_tags static
#			keys_to_tags.default_factory = None
#			# fetch datastore entites asynchronously
#			keys_to_be_fetched = [key for key in keys_to_tags]
#			track_futures = ndb.get_multi_async(keys_to_be_fetched)
#			tracks = (t.get_result() for t in track_futures)
	#		f = lambda x: {'key':x.key,'artist':x,'tags_to_counts':x.tags_dict,'tags_to_ranks':{},'rank':0}
#			assert False, tracks
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
