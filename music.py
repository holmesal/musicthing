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
		Creates a playlist from the station meta variables in the session
		
		Response:
		artists : an array of the artist entities, as they come out of the datastore
		
		'''
#		self.set_plaintext()
		timer = utils.Timer()
		time = timer.time
		
		t0 = dt.now()
		station_tags,serendipity,city = self.get_station_meta_from_session()
		time('b_get_station_meta')
		
		# format the tags for the client
		tags = [{'name':t,'count':c} for t,c in station_tags.iteritems()]
		tags = sorted(tags,key=lambda x: x['count'],reverse=True)
		time('c_format_tags')
		# create the station!!
		station = utils.StationPlayer(station_tags,serendipity,city)
		algo_times = station.create_station()
		time('d_create_station')
		# pull the first 10 tracks
		count = 10
		tracks = station.sorted_tracks_list[:count]
		artists = [t['artist'] for t in tracks]
		
		# find available cities with a minimum number of artists
		available_cities = self.calc_major_cities(station.artists())
		
		# update session
		session = get_current_session()
		session['idx'] = count
		
		# store the tracks that have been listened to
		listened_to = [t['key'] for t in tracks]
		session['listened_to'] = listened_to
		
#		self.say(json.dumps([[t['rank'], t['old_rank']] for t in tracks]))
#		return
		template_values = {
			'artists' : artists,
			'city' : city,
			'tags' : tags,
			'serendipity' : serendipity,
			'cities' : available_cities
		}
		logging.info(dt.now()-t0)
		global_times = timer.get_times()
		self.say(json.dumps({'global':global_times,'algo':algo_times}))
		return
#		self.say(template_values['cities'])
#		self.say(json.dumps([a['artist'].username for a in tracks]))
#		return
		jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
		template = jinja_environment.get_template('templates/music.html')
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
		new_idx = idx+10
		
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
class UpdateStationHandler(handlers.UserHandler):
	def post(self):
		'''
		Updates the station playlist with new variables
		'''
		max_serendipity = 5.
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
		self.redirect('/music')
	
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
							('/music/updateCity',UpdateCityHandler)
							])





	