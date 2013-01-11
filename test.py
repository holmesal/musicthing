from datetime import datetime as dt
from gaesessions import get_current_session
from geo import geohash, geohash
from google.appengine.api import taskqueue
from google.appengine.ext import blobstore, ndb
from sc_creds import sc_creds, sc_creds_test
import handlers
import jinja2
import json
import logging
import mixpanel_track as mixpanel
import models
import os
import random
import random
import soundcloud
import urllib2
import utils
import webapp2
import random

class EndSessionHandler(handlers.BaseHandler):
	def get(self):
		session = get_current_session()
		self.say(session)
		session.terminate()
		self.say(session)
class CreateSessionHandler(handlers.UserHandler):
	def get(self):
		'''
		Creates a custom session
		'''
		session = get_current_session()
		user = models.User.get_by_id('dev')
		assert user,user
		self.log_in(user.key.id())
#		session.terminate()
#		session['tags'] = {'rock':100,'indie':50}
#		session['serendipity'] = .2
#		session['city'] = 'Boston'
		self.say(session)
class UpdateHandler(handlers.ArtistHandler):
	def get(self):
		'''
		updates all artists so their soundcloud genre is used as a tag
		'''
		artists = models.Artist.query().iter(batch_size=50)
		to_put = []
		for artist in artists:
			if artist.genre:
				if not artist.tags_:
					self.say(artist.genre)
					tag_to_count_mapping = {artist.genre:100}
					prepped_tags = self.prep_tags_for_datastore(tag_to_count_mapping)
					artist.tags_.extend(prepped_tags)
					to_put.append(artist)
				else:
					logging.info('Already has tags:')
					logging.info(artist)
		
		ndb.put_multi(to_put)
		#=======================================================================
		# '''
		# get all emails from the landing page signup
		# '''
		# users = models.User.query().iter(batch_size=50)
		# emails = [u.email for u in users]
		# self.response.out.write(json.dumps(emails))
		#=======================================================================
		
#===============================================================================
#		artists = models.Artist.query().iter(batch_size=50)
#		bad_artists = []
#		good_artists = []
#		backups = []
#		for a in artists:
# #			logging.info(a._properties)
#			if not a.access_token:
#				bad_artists.append(a)
#			else:
#				good_artists.append(a)
# #				
# #				b = models.ArtistBackup(id=a.strkey)
# #				for p in a._properties:
# ##					logging.info(p)
# #					val = getattr(a, p)
# #					setattr(b, p, val)
# #				backups.append(b)
# #		ndb.put_multi(backups)
#		self.say(good_artists.__len__())
#		self.say(bad_artists.__len__())
#		good_keys = sorted([x.username for x in good_artists])
#		bad_keys = sorted([x.username for x in bad_artists])
# #		z = zip(good_keys,bad_keys)
# #		self.say('\n'.join([a+b for a,b in z]))
#		
#		self.say(filter(lambda x: x not in bad_keys,good_keys))
#		ndb.delete_multi([a.key for a in bad_artists])
#===============================================================================
		# create backups

#		
#===============================================================================
# #		artists = models.Artist.query().iter(batch_size=50)
# ##		i = 0
# #		boston_cities = [
# #						'boston, ma',
# #						'cambridge',
# #						'somerville',
# #						'marlborough',
# #						'lincoln',
# #						'framingham',
# #						'newburyport',
# #						'greater boston',
# #						'lawrence, ma',
# #						'danvers, ma',
# #						'bedford'
# #						]
# #		to_put = []
# #		for artist in artists:
# #			if artist.city:
# #				self.say(artist.city)
# #				if artist.city.lower() in boston_cities:
# #					self.say('!!!')
# #					artist.city = 'Boston'
# #					to_put.append(artist)
# #		self.say(to_put)
# #		self.say([a.city for a in to_put])
# #		ndb.put_multi(to_put)
#		
# #			if not artist.city:
# #				i += 1
# #				try:
# #					access_token = artist.access_token
# #					client = soundcloud.Client(access_token = access_token)
# #					user = client.get('/me')
# #					self.say(user.city)
# #					artist.city = user.city
# #					to_put.append(artist)
# #				except:
# #					pass
# #			
# #			if i > 100:
# #				break
# #		else:
# #			self.say('really done!')
# #		self.say([a.city for a in to_put])
# #		self.say(to_put)
# #		ndb.put_multi(to_put)
# #		self.say('Done!')
#		
# #			data = json.loads(user.raw_data)
# #			a = artist.to_dict(exclude=('created',))
# #			to_send.append({'data':data,'artist':a})
# #		self.response.out.write(json.dumps(to_send))
#===============================================================================
class TestHandler(handlers.UserHandler):
	def get_new_user(self):
		'''
		Create a dev user
		'''
		pw,salt = self.hash_password('pat')
		email = 'patrick@levr.com'
		models.User.get_or_insert('dev',email=email,pw=pw,salt=salt)
		self.say('done!')
	def get_city(self):
		artist = ndb.Key(models.Artist,'31035942').get()
		country = 'United States'
		admin1 = 'MA'
		city_name = 'Boston'
		geo_point = ndb.GeoPt('42.3584308, -71.0597732')
		city = utils.fetch_city_from_path(country, admin1, city_name, geo_point)
		artist.city_keys.append(city.key)
		artist.put()
		self.say(city)
	def add_cities_to_artists(self):
#	def get(self):
		cities = ['c'*i for i in range(1,10)]
		states = ['s'*i for i in range(1,10)]
		countries = ['y'*i for i in range(1,10)]
		
		city_keys = []
		for y in countries:
			for s in states:
				for c in cities:
					lat = random.uniform(41.9,42.9)
					lon = random.uniform(-70.9,-71.9)
#					gstring = '{},{}'.format(lat,lon)
					geo_point = ndb.GeoPt(lat,lon)
					city = utils.fetch_city_from_path(y,s,c,geo_point)
					city_keys.append(city)
					
#		allston = utils.fetch_city_from_path('United States', 'MA', 'Allston', ndb.GeoPt('42.3539038, -71.1337112'))
#		boston = utils.fetch_city_from_path('United States', 'MA', 'Boston', ndb.GeoPt('42.353, -71.133'))
#		somerville = utils.fetch_city_from_path('United States', 'MA', 'Somerville', ndb.GeoPt('42.3875968, -71.0994968'))
#		
#		city_keys = [allston,boston,somerville]
		artists = models.Artist.query().iter(batch_size = 50)
		for a in artists:
#			del a._properties['city_keys']
#			del a._properties['ghash']
			city = random.choice(city_keys)
			a.cities.append(models.CityProperty(city_key = city.key, ghash = city.ghash))
#			a.ghash = city.ghash
#			a.city_keys.append(city.key)
			a.put()
#			self.say(a.key)
		self.say('Done!')
#	def get(self):
	def add_favorite(self):
		'''
		Adds a random favorite to the user
		'''
		pw,salt = self.hash_password('pat')
		email = 'patrick@levr.com'
		user = models.User.get_or_insert('dev',email=email,pw=pw,salt=salt)
		
		
		artists = models.Artist.query().fetch(None)
		a = random.sample(artists,20)
		for art in a:
			user.add_favorite(art.key)
#	def get(self):
	def remove_favorite(self):
		pw,salt = self.hash_password('pat')
		email = 'patrick@levr.com'
		user = models.User.get_or_insert('dev',email=email,pw=pw,salt=salt)
		
		artist = models.Artist.query().get()
		
		user.remove_favorite(artist.key)
#	def get(self):
	def test(self):
		'''
		Test out the station
		'''
		station_tags = {}#{'Instrumental':100}
		serendipity = 0.4
		radius = 10.
		pw,salt = self.hash_password('pat')
		email = 'patrick@levr.com'
		user = models.User.get_or_insert('dev',email=email,pw=pw,salt=salt)
		
		#=======================================================================
		# City
		#=======================================================================
		mode = utils.StationPlayer._city_mode
		city = utils.fetch_city_from_path('United States', 'MA', 'Boston', ndb.GeoPt('42.353, -71.133'))
		mode_data = {'city':city,'radius':radius}
		s = utils.StationPlayer(mode,mode_data,station_tags)
		s.create_station()
		
		#=======================================================================
		# All
		#=======================================================================
		mode = utils.StationPlayer._all_mode
		mode_data = 'all!'
		s = utils.StationPlayer(mode,mode_data,station_tags)
		s.create_station()
		
		#=======================================================================
		# Favorites
		#=======================================================================
		mode = utils.StationPlayer._favorites_mode
		mode_data = {'user_key' : user.key}
		s = utils.StationPlayer(mode,mode_data,station_tags)
		s.create_station()
		#=======================================================================
		# Location
		#=======================================================================
		mode = utils.StationPlayer._location_mode
		geo_point = ndb.GeoPt('42.353, -71.133')
		ghash = geohash.encode(geo_point.lat,geo_point.lon)
		mode_data = {'ghash':ghash,'radius':radius}
		s = utils.StationPlayer(mode,mode_data,station_tags)
		s.create_station()
		
		
		
		for track in s.playlist:
			track['key'] = track['key'].id()
			track['name'] = track['artist'].username
			track['city'] = track['artist'].cities[0].city_key.get().to_dict()['city']
			del track['tags_to_counts']
			del track['artist']
		
		cities = [t['city'] for t in s.playlist]
#		self.say(json.dumps(s.playlist))
		self.say(json.dumps(sorted(cities)))
#		self.say('Done!')
		session = get_current_session()
		session.terminate()
class EthanArtistHandler(handlers.UserHandler):
	def get(self):
		'''Handler to send some artist data back to ethan for testing
		'''
		mode = utils.StationPlayer._all_mode
		mode_data = None
		tracks = self.change_station_mode(mode, mode_data)
		packaged_artists = utils.StationPlayer.api_package_track_multi(tracks)
		
		# return with the packaged artist list
		self.send_success(packaged_artists)
app = webapp2.WSGIApplication([
							('/test/kill',EndSessionHandler),
							('/test/session',CreateSessionHandler),
							('/test/ethan',EthanArtistHandler),
#							('/test/get_artists',)
#							('/test',UpdateHandler),
							('/test',TestHandler)
#							('/test/viewsession',ViewSessionHandler)
							])
