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
#		lat = self.request.get('lat') or 42.3584308 
#		lon = self.request.get('lon') or -71.0597732
#		ghash = geohash.encode(lat,lon)
		ghash = 'drt3nh6v'
		# fetch the user from the session
		user_key = self.get_user_key_from_session()
		
		station = self.get_or_create_station_from_session()
		mode = utils.StationPlayer._all_mode
		mode_data = {'user_key':user_key}
		station.set_mode(mode, mode_data)
		
		# add the station to the session
		station.add_to_session()
		
		timer = utils.Timer()
		time = timer.time
		
		# suggested cities with google places fields
#		popular_cities = list(self.calc_major_cities())
		popular_cities = [
						{
						'city_string' : 'Boston, MA',
						'country' : 'United States',
						'administrative_area_level_1' : 'Massachusetts',
						'locality' : 'Boston',
						'lat' : 42.3584308,
						'lon' : -71.0597732
						}
						]
#		time('calc popular')
		# cities list with name, key, and distance
#		radial_cities = list(self.fetch_radial_cities(ghash))
		time('calc radial')
		template_values = {
						'mode' : station.mode,
						'mode_data' : station.mode_data,
						# TODO: what to template out here?
#						'city' : station.city_dict(),
#						'tags' : station.client_tags,
#						'radius' : station.radius,
#						'geo_point' : station.geo_point,
						'popular_cities' : popular_cities,
#						'radial_cities' : list(radial_cities),
#						'times' : timer.get_times()
						}
		return self.response.out.write(json.dumps(template_values))
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
		tracks = self.change_station_mode(mode, mode_data)
		packaged_artists = utils.StationPlayer.package_track_multi(tracks)
		self.send_success(packaged_artists)
		
class EverywhereStationHandler(handlers.UserHandler):
	def get(self):
		'''A station to play music everywhere
		'''
		
		mode = utils.StationPlayer._all_mode
		mode_data = None
		tracks = self.change_station_mode(mode, mode_data)
		packaged_artists = utils.StationPlayer.package_track_multi(tracks)
		# return with the packaged artist list
		self.send_success(packaged_artists)
class MyLocationStationHandler(handlers.UserHandler):
	def get(self):
		'''A station to play music near the user
		'''
		# get the users location
		lat = float(self.request.get('lat'))
		lon = float(self.request.get('lon'))
		ghash = geohash.encode(lat,lon)
		
		# get the list of included cities
		cities = self.request.get('cities')
		
		
		# set the mode
		mode = utils.StationPlayer._location_mode
		mode_data = {'ghash':ghash,'radial_cities':cities}
		tracks = self.change_station_mode(mode, mode_data)
		packaged_artists = utils.StationPlayer.package_track_multi(tracks)
		# respond with the artists
		self.send_success(packaged_artists)
class CityStationHandler(handlers.UserHandler):
	def get(self):
		'''A station to play music around a city
		'''
		# city path
		city_name = self.request.get('locality') or ' '
		admin1 = self.request.get('administrative_area_level_1','') or ' '
		country = self.request.get('country','') or ' '
		
		# geo point
		lat = float(self.request.get('lat'))
		lon = float(self.request.get('lon'))
		geo_point = ndb.GeoPt('{},{}'.format(lat,lon))
		
		
		# get the list of included cities
		cities = self.request.get('cities')
		
		# fetch the city from path
		city = utils.fetch_city_from_path(country, admin1, city_name, geo_point)
		
		# set the mode
		mode = utils.StationPlayer._city_mode
		mode_data = {'city':city,'radial_cities':cities}
		tracks = self.change_station_mode(mode, mode_data)
		packaged_artists = utils.StationPlayer.package_track_multi(tracks)
		self.send_success(packaged_artists)
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
		self.send_success(packaged_artists)
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
		self.send_success(packaged_artists)
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
class GetRadialCitiesHandler(handlers.UserHandler):
	def get(self):
		'''Method to return the list of cities around a point
		'''
		lat = float(self.request.get('lat'))
		lon = float(self.request.get('lon'))
		ghash = geohash.encode(lat,lon)
		
		radial_cities = self.fetch_radial_cities(ghash)
		
		self.send_success(radial_cities)

		
app = webapp2.WSGIApplication([
							# music player page
							('/music', MusicHandler),
							# set mode
							('/music/everywhere',EverywhereStationHandler),
							('/music/city',CityStationHandler),
							('/music/favorites',FavoritesStationHandler),
							('/music/location',MyLocationStationHandler),
							# playlist stuff
							('/music/get_radial_cities',GetRadialCitiesHandler),
							('/music/change_tags',SetTagsHandler),
							('/music/gettracks',GetTracksHandler),
							('/music/chirp',ChirpHandler)
							])





	