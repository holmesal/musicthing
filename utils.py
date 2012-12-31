from gaesessions import get_current_session

class Test(object):
	def next(self):
		for i in range(0,10):
			yield i
import models
from collections import defaultdict
from google.appengine.ext import ndb

class StationPlayer(object):
	def __init__(self,station_tags,serendipity):
		assert station_tags, 'station tags is empty'
		assert serendipity or serendipity==0, 'serendipity is empty'
		self.station_tags = station_tags
		self.serendipity = serendipity
		# calculated values
		keyfunc = lambda x: x[1]
		self.station_max_count = keyfunc(max(station_tags.iteritems(),key=keyfunc))
		self.station_total_count = sum(station_tags.values())
		
		# init the iterator count variable
		self.idx = 0
#	def __iter__(self):
#		return self
#	def next(self):
#		'''
#		Iterator method for returning tracks. Yields one track (aka artist) at a time
#		'''
#		while self.idx < self.sorted_tracks_list.__len__():
#			yield self.sorted_tracks_list[self.idx]
#			self.idx += 1
		
	def _rank_track_tags(self,track_count,station_count):
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
		return float(track_total_rank)/float(self.station_total_count)
	def create_station(self):
		# query each of the tags
		# create a list of iterators to fetch all of the keys 
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
		tracks = [t.get_result() for t in track_futures]
		#=======================================================================
		# Have a unique set of tags
		#=======================================================================
		f = lambda x: {'key':x.key,'artist':x,'tags_to_counts':x.tags_dict,'tags_to_ranks':{},'rank':0}
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
		
		self.sorted_tracks_list = sorted(tracks_list,key=lambda x: x['rank'],reverse=True)
		
		#=======================================================================
		# add station to current session
		#=======================================================================
		session = get_current_session()
		session['station'] = self