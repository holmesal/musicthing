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
from datetime import datetime as dt
import utils
from gaesessions import get_current_session


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
#		self.set_plaintext()
		t0 = dt.now()
		station_tags,serendipity = self.get_station_meta_from_session()
		#=======================================================================
		# # TODO: handle case where station doesnt exist
		#=======================================================================
		station = utils.StationPlayer(station_tags,serendipity)
		station.create_station()
		
		count = 20
		tracks = station.sorted_tracks_list[:count]
		artists = [t['artist'] for t in tracks]
		# update session
		session = get_current_session()
		session['idx'] = count
		
		template_values = {
			"artists"		:	artists
		}
		logging.info(dt.now()-t0)
		jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
		template = jinja_environment.get_template('templates/player.html')
		self.response.out.write(template.render(template_values))
		
	def get_spoof(self):
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
class GetTracksHandler(handlers.UserHandler):
	def get(self):
		'''
		For an ajax call to get the next 20 tracks
		'''
		session = get_current_session()
		station = session['station']
		idx = session['idx']
		new_idx = idx+20
		
		tracks = station.sorted_tracks_list[idx:new_idx]
		artists = []
		for track in tracks:
			artist = track['artist']
			artist_dict = artist.to_dict(exclude=('created',))
			artist_dict.update({'id':artist.strkey})
			artists.append(artist_dict)
		
		# update session
		session['idx'] = new_idx
		self.response.out.write(json.dumps(artists))
		

app = webapp2.WSGIApplication([
							('/music', MusicHandler),
							('/music/gettracks',GetTracksHandler)
							])





	