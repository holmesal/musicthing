from gaesessions import get_current_session
import random
import logging

class Test(object):
	def next(self):
		for i in range(0,10):
			yield i
import models
from collections import defaultdict
from google.appengine.ext import ndb

class StationPlayer(object):
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
		
	def _rank_track_tags(self,track_count,station_count):
		'''
		Compares the tag counts for station tags and track tags.
		@param track_count:
		@type track_count:
		@param station_count:
		@type station_count:
		@return: a rankfor the track tag
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
		f = lambda x: {'key':x.key,'artist':x,'tags_to_counts':x.tags_dict,'tags_to_ranks':{},'rank':0}
		logging.info(not self.station_tags)
		if not self.station_tags:
			logging.info('empty station')
			if self.city:
				artists = models.Artist.query(models.Artist.city == self.city).iter(batch_size=50)
			else:
				artists = models.Artist.query().iter(batch_size=50)
			tracks = [f(a) for a in artists]
			random.shuffle(tracks)
			self.sorted_tracks_list = tracks
		else:
			if self.city:
				# also filter by city
				tags_to_keys = {tag:models.Artist.query(
										models.Artist.tags_.genre == tag,
										models.Artist.city == self.city
										).iter(batch_size=50,keys_only=True) \
							for tag in self.station_tags}
			else:
				# do not filter by city
				tags_to_keys = {tag:models.Artist.query(models.Artist.tags_.genre == tag
										).iter(batch_size=50,keys_only=True) \
							for tag in self.station_tags}
			# reverse key:val mappings, so tracks become unique and are mapped to lists of their tags
			# reduces number of gets required from the datastore
			keys_to_tags = defaultdict(list)
			for tag,tag_qit in tags_to_keys.iteritems():
				# each of the tags is mapped to an iterator for getting artist keys
				for key_result in tag_qit:
	#				# result: {ndb.Key:['tag','tag','tag']}
					keys_to_tags[key_result].append(tag)
			# make keys_to_tags static
			keys_to_tags.default_factory = None
			# fetch datastore entites asynchronously
			keys_to_be_fetched = [key for key in keys_to_tags]
			track_futures = ndb.get_multi_async(keys_to_be_fetched)
			tracks = (t.get_result() for t in track_futures)
	#		f = lambda x: {'key':x.key,'artist':x,'tags_to_counts':x.tags_dict,'tags_to_ranks':{},'rank':0}
			tracks_list = [f(t) for t in tracks]
			
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
					except KeyError:
						# the track did not have that tag in its list of tags
						pass
				# set the total rank of the track
				track['rank'] = self._rank_track(track['tags_to_ranks'])
			#=======================================================================
			# # add some entropy
			#=======================================================================
			keyfunc = lambda x: x['rank']
			max_rank = keyfunc(max(tracks_list,key=keyfunc))
			logging.info('max rank: '+str(max_rank))
			min_rank = 0
			for track in tracks_list:
				rank = track['rank']
				random_factor = max_rank*self.serendipity
				rank_plus = rank + random_factor
				if rank_plus > max_rank: rank_plus = max_rank
				rank_minus = rank - random_factor
				if rank_minus < min_rank: rank_minus = min_rank
				range_factor = 100.
				rank_plus = int(rank_plus*range_factor)
				rank_minus = int(rank_minus*range_factor)
				if rank_plus == rank_minus:
					logging.info('! same ranks')
					new_rank = rank
				else:
					r = [x/range_factor for x in range(rank_minus,rank_plus)]
					new_rank = random.choice(r)
				track['rank'] = new_rank
				track['old_rank'] = rank
				logging.info('rank: '+str(rank))
	#			logging.info('serendipity: '+str(self.serendipity))
	#			logging.info('random_factor: '+str(random_factor))
	#			logging.info('rank_plus: '+str(rank_plus/range_factor))
	#			logging.info('rank_minus: '+str(rank_minus/range_factor))
				logging.info('new_rank: '+str(new_rank))
			
			# sort the tracks list based on their new ranks
			self.sorted_tracks_list = sorted(tracks_list,key=lambda x: x['rank'],reverse=True)
#		logging.info(', '.join([str(t['rank']) for t in self.sorted_tracks_list]))
		#=======================================================================
		# add station to current session
		#=======================================================================
		session = get_current_session()
		session['station'] = self