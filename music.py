from geo import geohash
import handlers
import jinja2
import json
import logging
import os
import utils
import webapp2
from google.appengine.ext import ndb
import models

jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
class MusicHandler(handlers.UserHandler):
	'''
	The big main music player.
	'''
	def get(self):
		'''
		The music page. Station is created in ajax.
		'''
		# fetch the user from the session
		user_key = self.get_user_key_from_session()
		
		# fetch the station from the session
		try:
			station = self.get_station_from_session()
		except self.SessionError:
			# if there is no station in the session, create a new one with defaults.
			station = utils.StationPlayer(utils.StationPlayer._all_mode,{'user_key':user_key},None,None)
		
		# add the station to the session
		station.add_to_session()
		
		# grab the city if there is one
		template_values = {
						'mode' : station.mode,
						'city' : station.city_dict,
						'tags' : station.client_tags,
						'geo_point' : station.geo_point
						}
		template = jinja_environment.get_template('templates/music.html')
		self.response.out.write(template.render(template_values))
class InitializeStationHandler(handlers.UserHandler):
	def get(self):
		'''
		For an ajax call to create a playlist
		Also serves the first n tracks in the playlist
		'''
		timer = utils.Timer()
		time = timer.time
		try:
			# grab the existing station
			station = self.get_station_from_session()
		except:
			# default station
			user_key = self.get_user_key_from_session()
			station = utils.StationPlayer(utils.StationPlayer._all_mode,{'user_key':user_key},None,None)
		time('get or create station')
		
		# create the station!!
		algo_times = station.create_station()
		# add the station to the session
		time('create_station')
		
		# pull the first 10 tracks
		tracks = station.fetch_next_n_tracks(10)
		time('fetch tracks')
		artists = [t['artist'] for t in tracks]
		packaged_artists = self.package_artist_multi(artists)
		
		time('package_artists')
		global_times = timer.get_times()
		
		logging.info('{} tracks in the playlist'.format(station.playlist.__len__()))
		logging.info(json.dumps({'global':global_times,'algo':algo_times}))
		
		# return with the packaged artist list
		self.response.out.write(json.dumps(packaged_artists))
class GetTracksHandler(handlers.UserHandler):
	def get(self):
		'''
		For an ajax call to get the next n tracks
		'''
		try:
			station = self.get_station_from_session()
		except self.SessionError:
			return self.response.out.write(json.dumps({'status':204}))
		tracks = station.fetch_next_n_tracks(10)
		artists = [t['artist'] for t in tracks]
		packaged_artists = self.package_artist_multi(artists)
		self.response.out.write(json.dumps(packaged_artists))
class UpdateStationHandler(handlers.UserHandler):
	def post(self):
		'''
		Updates the station playlist with new variables
		'''
		# grab station variables from the client
		mode = self.request.get('mode')
		city = self.request.get('city')
		lat = self.request.get('lat')
		lon = self.request.get('lon')
		try:
			ghash = geohash.encode(lat,lon)
		except Exception:
			ghash = None
		user_key = self.get_user_key_from_session()
		# create mode_data from station variables
		mode_data = {
					'user_key' : user_key,
					'city' : city,
					'ghash' : ghash,
					}
		
		# convert the client_tags to station_tags
		try:
			client_tags = json.loads(self.request.get("tags","{}")) #NOTE - this currently crashes if tags is empty
			station_tags = self.convert_client_tags_to_tags_dict(client_tags)
		except:
			client_tags = None
			station_tags = None
			logging.info('empty tags')
		
		# create the station
		station = utils.StationPlayer(mode,mode_data,station_tags,client_tags)
		algo_times = station.create_station()
		logging.info(algo_times)
		# set the station to session to be passed on to /music
		session = station.add_to_session()
		return self.redirect('/music')

class ChirpHandler(handlers.UserHandler):
	def get(self):
		'''
		Called before fetching next set of tracks, s
		'''
		skipped_track_ids = self.request.get_all('skipped_track_ids')
		played_track_ids = self.request.get_all('played_track_ids')
		try:
			skipped_track_keys = (ndb.Key(models.Artist,i) for i in skipped_track_ids)
			skipped_artists = ndb.get_multi(skipped_track_keys)
			
			station = self.get_station_from_session()
			station.skipped_artist_keys.append(skipped_artists)
			station.add_to_session()
			
		except self.SessionError,e:
			logging.error(e)
			logging.error('Could not find station')
			return self.response.out.write(json.dumps({
													'status' : 404,
													'message' :'Could not find station'}))
		else:
			return self.response.out.write(json.dumps({'status' : 200,
													'message' : 'OK'
													}))
app = webapp2.WSGIApplication([
							('/music', MusicHandler),
							('/music/gettracks',GetTracksHandler),
							('/music/updateStation',UpdateStationHandler),
							('/music/initialize',InitializeStationHandler),
							('/music/chirp',ChirpHandler)
							])





	