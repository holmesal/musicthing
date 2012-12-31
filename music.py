from collections import defaultdict
from google.appengine.ext import ndb
import handlers
import jinja2
import json
import logging
import models
import os
import random
import webapp2


class MusicHandler(handlers.UserHandler):
	'''
	The big main music player. Awwww yeah.
	'''
	def get(self):
		'''
		1. Grab user info
		2. Decide which tracks to play
		3. Write out those tracks
		
		OUTPUTS:
		artists		:	an array of the artist entities, as they come out of the datastore
		
		'''
		self.set_plaintext()
		tags_to_counts,serendipity = self.get_station_from_session()
		# calc max count in the station
		keyfunc = lambda x: x[1]
		station_max_count = keyfunc(max(tags_to_counts.iteritems(),key=keyfunc))
		station_total_count = sum(tags_to_counts.values())
		# query each of the tags
		# create a list of iterators to fetch all of the keys 
		tags_to_keys = {tag:models.Artist.query(models.Artist.tags_.genre == tag
								).iter(batch_size=50,keys_only=True) \
					for tag in tags_to_counts}
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
#		# create list of [{key:<key>,tags:{},rank:<int>,]
		f = lambda x: {'key':x.key,'tags_to_counts':x.tags_dict,'tags_to_ranks':{},'rank':0}
		tracks_list = [f(t) for t in tracks]
		def rank_track_tags(track_count,station_count):
			inverted_diff = station_max_count - abs(station_count - track_count)
			station_tag_weight = float(station_count)/float(station_max_count)
			return inverted_diff * station_tag_weight
		def rank_track(tags_to_rank,station_total_count):
			'''
			Sum the weighted counts in each of the tags, and normalize by the max score
			@param tags_to_rank: mapping of {'tag':rank}
			@type tags_to_rank: dict
			@param station_total_count: the sum of all the tag counts in the station
			@type station_total_count: int
			@return: the total rank of the track w/ respect to the station
			'''
			track_total_rank = sum(tags_to_rank.values())
			return float(track_total_rank)/float(station_total_count)
		
		for track in tracks_list:
			for tag,station_count in tags_to_counts.iteritems(): # for each tag in the station
				try:
					track_count = track['tags_to_counts'][tag]
					track['tags_to_ranks'][tag] = rank_track_tags(track_count,station_count)
				except KeyError:
					pass
			# set the total rank of the track
			track['rank'] = rank_track(track['tags_to_ranks'], station_total_count)
		
		tracks_list = sorted(tracks_list,key=lambda x: x['rank'],reverse=True)
		self.say(tracks_list)
		#=======================================================================
		# Sum the individual tag ranks and divide by the station sum to get net rank
		#=======================================================================
		
		
	def get_(self):
		'''
		This handler does most of the heavy lifting. The process is:
		
		'''
		
		'''
		You should check if they're already logged in, and redirect appropriately if not (back to the user signup page)
		'''
		
		
		# fetch keys
		artist_keys = models.Artist.query().fetch(None,keys_only=True)
		try:
			# get a random sample
			random_artists = random.sample(artist_keys,50)
		except ValueError:
			# list is not big enough, return all of them
			random_artists = artist_keys
		# shuffle list
		random.shuffle(random_artists)
		artists = ndb.get_multi(random_artists)
		
		template_values = {
			"artists"		:	artists
		}
		
		jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
		template = jinja_environment.get_template('templates/player.html')
		self.response.out.write(template.render(template_values))
		
	def post(self):
		'''
		This handler takes care of updating user preferences that are available on the player page
		There's nothing here yet
		'''
		
		pass
		


app = webapp2.WSGIApplication([('/music', MusicHandler)])





	