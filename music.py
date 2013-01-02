from collections import defaultdict
from datetime import datetime as dt
from gaesessions import get_current_session
from google.appengine.ext import ndb
import handlers
import jinja2
import json
import logging
import models
import os
import random
import utils
import webapp2


class MusicHandler(handlers.UserHandler):
	'''
	The big main music player. Awwww yeah.
	'''
	def get(self):
		'''
		The page for playing music on. Tracks are fetched with an ajax call to another handler
		'''
#		self.set_plaintext()
		station_tags,serendipity,city = self.get_station_meta_from_session()
		
		# format the tags for the client
		tags = [{'name':t,'count':c} for t,c in station_tags.iteritems()]
		tags = sorted(tags,key=lambda x: x['count'],reverse=True)
		
		template_values = {
			'city' : city,
			'tags' : tags,
			'serendipity' : int(serendipity*utils.StationPlayer.max_serendipity),
			'cities' : ['Boston']
		}
#		self.say(template_values['serendipity'])
		jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
		template = jinja_environment.get_template('templates/music.html')
		self.response.out.write(template.render(template_values))
		
	def post(self):
		'''
		This handler takes care of updating user preferences that are available on the player page
		There's nothing here yet
		'''
		
		pass
class InitializeStationHandler(handlers.UserHandler):
	def get(self):
		'''
		For an ajax call to create a playlist
		Also serves the first n tracks in the playlist
		'''
		timer = utils.Timer()
		time = timer.time
		
		station_tags,serendipity,city = self.get_station_meta_from_session()
		time('b_get_station_meta')
		
		# create the station!!
		station = utils.StationPlayer(station_tags,serendipity,city)
		session,algo_times = station.create_station()
		
		time('d_create_station')
		# pull the first 10 tracks
		artists = self.fetch_next_n_artists(10,session)
		packaged_artists = self.package_artist_multi(artists)
		
		time('e_package_artists')
		global_times = timer.get_times()
		
		logging.info(json.dumps({'global':global_times,'algo':algo_times}))
		self.response.out.write(json.dumps(packaged_artists))
class GetTracksHandler(handlers.UserHandler):
	def get(self):
		'''
		For an ajax call to get the next n tracks
		'''
		artists = self.fetch_next_n_artists(10)
		packaged_artists = self.package_artist_multi(artists)
		self.response.out.write(json.dumps(packaged_artists))
class UpdateStationHandler(handlers.UserHandler):
	def post(self):
		'''
		Updates the station playlist with new variables
		'''
		max_serendipity = utils.StationPlayer.max_serendipity
		serendipity = self.request.get("serendipity",2)
		serendipity = float(serendipity)/max_serendipity
		try:
			raw_tags = json.loads(self.request.get("tags","{}")) #NOTE - this currently crashes if tags is empty
			tags = self.parse_tags(raw_tags)
		except:
			tags = {}
			logging.info('empty tags')
#			logging.error('tags are not being handled correctly when not passed in post')
		# Clean tags
		# preferences are only stored in the session
		self.add_station_meta_to_session(tags,serendipity)
		return self.redirect('/music')
	
class UpdateCityHandler(handlers.UserHandler):
	def get(self):
		'''
		Updates the station playlist with a new city
		'''
		city = self.request.get('city',None)
		session = get_current_session()
		if city.lower() == 'none' or city.lower() == 'all':
			city = None
		session['city'] = city
		return self.redirect('/music')

app = webapp2.WSGIApplication([
							('/music', MusicHandler),
							('/music/gettracks',GetTracksHandler),
							('/music/updateStation',UpdateStationHandler),
							('/music/updateCity',UpdateCityHandler),
							('/music/initialize',InitializeStationHandler)
							])





	