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
						'radius' : station.radius,
						'geo_point' : station.geo_point
						# cities list with name, key, and radius
						# suggested cities with google places fields
						
						}
		template = jinja_environment.get_template('templates/music.html')
		self.response.out.write(template.render(template_values))
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
# TODO: get cities for the radius selection
class FavoritesStationHandler(handlers.UserHandler):
	def get(self):
		'''A station to play a users favorites
		'''
		try:
			# grab the current user
			user = self.get_user_from_session()
		except self.SessionError:
			# how can we play a user playlist if the user doesnt exist?
			return self.response.out.write(json.dumps({'success':0,'message':'User not found.'}))
		else:
			# we only need the users key
			user_key = user.key
		
		mode = utils.StationPlayer._favorites_mode
		mode_data = {'user_key':user_key}
		packaged_artists = self.change_station_mode(mode, mode_data)
		
		self.send_artists(packaged_artists)
		
class EverywhereStationHandler(handlers.UserHandler):
	def get(self):
		'''A station to play music everywhere
		'''
		
		mode = utils.StationPlayer._all_mode
		mode_data = None
		packaged_artists = self.change_station_mode(mode, mode_data)
		
		# return with the packaged artist list
		self.send_artists(packaged_artists)
class MyLocationStationHandler(handlers.UserHandler):
	def get(self):
		'''A station to play music near the user
		'''
		# get the users location
		lat = self.request.get('lat')
		lon = self.request.get('lon')
		ghash = geohash.encode(lat,lon)
		
		# get the list of included cities
		cities = self.request.get('cities')
		
		
		# set the mode
		mode = utils.StationPlayer._location_mode
		mode_data = {'ghash':ghash,'radial_cities':cities}
		packaged_artists = self.change_station_mode(mode, mode_data)
		
		# respond with the artists
		self.send_artists(packaged_artists)
class CityStationHandler(handlers.UserHandler):
	def get(self):
		'''A station to play music around a city
		'''
		# city path
		city_name = self.request.get('locality') or ' '
		admin1 = self.request.get('administrative_area_level_1','') or ' '
		country = self.request.get('country','') or ' '
		
		# geo point
		lat = self.request.get('lat')
		lon = self.request.get('lon')
		geo_point = ndb.GeoPt('{},{}'.format(lat,lon))
		
		
		# get the list of included cities
		cities = self.request.get('cities')
		
		# fetch the city from path
		city = utils.fetch_city_from_path(country, admin1, city_name, geo_point)
		
		# set the mode
		mode = utils.StationPlayer._city_mode
		mode_data = {'city':city,'radial_cities':cities}
		packaged_artists = self.change_station_mode(mode, mode_data)
		
		self.send_artists(packaged_artists)
class SetTagsHandler(handlers.UserHandler):
	def get(self):
		'''Handler to change the stations tags.
		'''
		# grab the tags from the request
		try:
			client_tags = json.loads(self.request.get('tags','{}'))
		except ValueError:
			# json throws error if tags is empty
			client_tags = []
		
		# parse the tags into a usable format
		if client_tags:
			station_tags = self.convert_client_tags_to_tags_dict(client_tags)
		else:
			# empty list if raw_tags is empty
			station_tags = []
		
		# grab session
		station = self.get_or_create_station_from_session()
		# update the station
		station.set_station_tags(station_tags, client_tags)
		# recalculate the station
		algo_times = station.create_station()
		logging.info(json.dumps(algo_times))
		# grab the first few tracks and package them
		tracks = station.fetch_next_n_tracks()
		packaged_artists = station.package_track_multi(tracks)
		
		# dont forget to add the station to the session
		station.add_to_session()
		self.send_artists(packaged_artists)
class GetTracksHandler(handlers.UserHandler):
	def get(self):
		'''
		For an ajax call to get the next n tracks
		'''
		try:
			station = self.get_station_from_session()
		except self.SessionError:
			return self.response.out.write(json.dumps({'success':0}))
		# get more tracks and package them!
		tracks = station.fetch_next_n_tracks()
		packaged_artists = station.package_track_multi(tracks)
		# send the tracks!
		self.send_artists(packaged_artists)
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
													'success' : 0,
													'message' :'Could not find station'}))
		else:
			return self.response.out.write(json.dumps({'success' : 1,
													'message' : 'OK'
													}))
app = webapp2.WSGIApplication([
							# music player page
							('/music', MusicHandler),
							# set mode
							('/music/everywhere',EverywhereStationHandler),
							('/music/city',CityStationHandler),
							('/music/favorites',FavoritesStationHandler),
							('/music/location',MyLocationStationHandler),
							# playlist stuff
							('/music/change_tags',SetTagsHandler),
							('/music/gettracks',GetTracksHandler),
							('/music/chirp',ChirpHandler)
							])





	