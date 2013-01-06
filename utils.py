from gaesessions import get_current_session
import random
import logging
from datetime import datetime

import models
from collections import defaultdict
from google.appengine.ext import ndb
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

def fetch_city_from_path(country,admin1,city,geo_point):
	'''
	Fetches a city from the ndb.
	Properly creates any missing elements along the key path
	@param country: e.g. United States
	@type country: str
	@param admin1: e.g. MA
	@type admin1: str
	@param city: e.g. Boston
	@type city: str
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
					city.lower(),
					parent = admin1_entity.key,
					name = city,
					ghash = ghash)
	return city_entity

def fetch_artist_keys_from_city_key(city_key):
	'''
	Fetches all artist keys from a city with key: city_key
	@param city_key: the key of the city entity in question
	@type city_key: ndb.Key
	@return: 
	'''
	artists = models.Artist.query(
								models.Artist.city_keys == city_key
								).iter(
									batch_size = 50,
									keys_only = True)
	return artists
def fetch_artist_keys_from_ghash(ghash):
	artists = models.Artist.query(
					models.Artist.ghash >= ghash,
					models.Artist.ghash <= ghash+"{"
					).iter(
						batch_size = 50,
						keys_only = True)
	return artists

