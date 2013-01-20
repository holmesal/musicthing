from google.appengine.ext import ndb
from google.appengine.api import images
from geo import geohash
import os
import heapq
BASEURL = 'http://local-music.appspot.com'
DEFAULT_IMAGE_URL = '{}/img/default_artwork.jpeg'.format(BASEURL)

if os.environ['SERVER_SOFTWARE'].startswith('Development') == False:
	# not on dev server
	BASE_URL = 'http://getradi.us'
else:
	# on dev server
	BASE_URL = 'http://0.0.0.0:8080'
#===============================================================================
# Location Stuff
#===============================================================================

class Country(ndb.Model):
	# need to make sure it is created with a country identifier
	name = ndb.StringProperty(required = True)
	name_lower = ndb.ComputedProperty(lambda self: self.name.lower())
class Admin1(ndb.Model):
	# this is the state or province
	name = ndb.StringProperty(required = True)
	name_lower = ndb.ComputedProperty(lambda self: self.name.lower())
class City(ndb.Model):
	ghash = ndb.StringProperty(required = True)
	name = ndb.StringProperty(required = True)
	name_lower = ndb.ComputedProperty(lambda self: self.name.lower())
	@property
	def geo_point(self):
		return geohash.decode(self.ghash)
	def to_dict(self):
		'''
		Reverse engineers the city's key to model the form that the server
		receives a city from google maps
		'''
		flat_key = self.key.flat()
		country = flat_key[1]
		admin1 = flat_key[3]
		locality = flat_key[5]
		city_string = '{}, {}'.format(locality,admin1) if admin1 != ' ' else locality
		lat,lon =  geohash.decode(self.ghash)
		return {
			'city_string' : city_string,
			'country' : country,
			'administrative_area_level_1' : admin1,
			'locality' : locality,
			'lat' : lat,
			'lon' : lon
			}
	def package_for_radius_list(self):
		'''
		Package for radius list
		'''
		return {
			'name' : self.key.id(),
			'key' : self.key.urlsafe()
			}
	def to_city_property(self):
		'''
		Method to convert a City entity to a CityProperty entity
		to be stored on an artist
		@return: a CityProperty version of self
		@rtype: CityProperty
		'''
		return CityProperty(
						city_key=self.key,
						ghash=self.ghash,
						name=self.name
						)


class TagProperty(ndb.Model):
	'''
	Model definition of the structured property on users
	'''
	genre = ndb.StringProperty()
	count = ndb.FloatProperty()
class CityProperty(ndb.Model):
	'''
	Model definition of the structured city property for artists
	'''
	city_key = ndb.KeyProperty(City)
	ghash = ndb.StringProperty()
	name = ndb.StringProperty()
	
	
class Artist(ndb.Model):
	created = ndb.DateProperty(auto_now_add=True)
	proper_name = ndb.StringProperty()
	access_token = ndb.StringProperty()
	username = ndb.StringProperty()
	description = ndb.StringProperty()
	email = ndb.StringProperty()
	phone = ndb.StringProperty()
	city = ndb.StringProperty()
	
	cities = ndb.StructuredProperty(CityProperty,repeated = True)
#	city_keys = ndb.KeyProperty(repeated=True)
#	ghash = ndb.StringProperty()
	
	# music data/metadata
	track_url = ndb.StringProperty()
	track_id = ndb.StringProperty() # soundcloud track id
	tags_ = ndb.StructuredProperty(TagProperty,repeated=True)
	
	# external urls
	bandcamp_url = ndb.StringProperty()
	facebook_url = ndb.StringProperty()
	myspace_url = ndb.StringProperty()
	tumblr_url = ndb.StringProperty()
	twitter_url = ndb.StringProperty()
	youtube_url = ndb.StringProperty()
	website_url = ndb.StringProperty()
	other_urls = ndb.StringProperty(repeated=True)
	soundcloud_url = ndb.StringProperty()
	
	# deprecated
	external_image_url = ndb.StringProperty()
	image_key = ndb.BlobKeyProperty()
	genre = ndb.StringProperty() # deprecated
	@property
	def artist_name(self):
		'''
		The name to display for an artist
		@return: either the bands proper name or their username
		'''
		return self.proper_name or self.username
		
	def city_dict(self):
		'''
		Creates a dict form of the artists city for manage page, etc...
		@warning: This method assumes that each artist has a max of one city
		@return: All the fields that the manage page posts when the server receives a manage post
		@rtype: dict
		'''
		try:
			city = self.cities[0]
		except IndexError:
			# the artist does not have any cities
			# return an empty dict
			return {}
		else:
			# get the full city path
			city_key = city.city_key
			# flatten the key to get the whole path
			flat_key = city_key.flat()
			country = flat_key[1].title()
			admin1 = flat_key[3].title()
			locality = flat_key[5].title()
			
			# get the lat,lon from the ghash
			lat,lon = geohash.decode(city.ghash)
			
			# create a string version for display purposes
			city_string = '{}, {}'.format(locality,admin1) if admin1 != ' ' else locality
			
			city_dict = {
						'country' : country,
						'administrative_area_level_1' : admin1,
						'locality' : locality,
						'lat' : lat,
						'lon' : lon,
						'city_string' : city_string
						}
		return city_dict
	@property
	def tags_dict(self):
		return {tag.genre:tag.count for tag in self.tags_}
	@property
	def tags(self):
		return [{'name':tag.genre,'count':tag.count} for tag in self.tags_]
	@property
	def image_url(self):
		'''Returns a url for serving the artists artwork
		If the artist uploaded an image, and therefore has an image_key,
		a serving url is created to serve that image.
		Otherwise, an external url is provided
		If an external url does not exist, then a default image is used
		
		@return: image_url
		@rtype: str
		'''
		try:
			return images.get_serving_url(self.image_key, size=1000, crop=True)
		except:
			return self.external_image_url or DEFAULT_IMAGE_URL
	
	@property
	def strkey(self):
		'''Returns a urlsafe version of the artists key
		@return: the artists numeric id as a string
		@rtype: str
		'''
		return str(self.key.id())

class ArtistBackup(Artist):
	pass
class User(ndb.Model):
	created = ndb.DateProperty(auto_now_add=True)
	email = ndb.StringProperty()
	pw = ndb.StringProperty()
	salt = ndb.StringProperty() # salt for the pw hash
	@ndb.transactional
	def add_interaction(self,model,artist_key):
		'''
		Creates a link between the user (self) and an artist.
		Does nothing if the interaction already exists
		@param model: The type of interaction being created
		@type model: Favorite or Follow or NeverPlay
		@param artist_key: The key of the artist to be interacted with
		@type artist_key: ndb.Key
		'''
		assert model in [Favorite,Follow,NeverPlay], \
			'Unsupported interaction: {}'.format(model)
		existing_enitity = model.get_by_id(artist_key.id(),parent=self.key)
		if existing_enitity is None:
			model(id=artist_key.id(),parent=self.key,artist_key=artist_key).put()
	@ndb.transactional
	def remove_interaction(self,model,artist_key):
		'''
		Removes an interaction created by self.add_interaction
		Does nothing if the interaction doesn't exist
		@param model: The model of the interaction being deleted
		@type model: Favorite or Follow or NeverPlay
		@param artist_key: The key of the artist in question
		@type artist_key: ndb.Key
		'''
		assert model in [Favorite,Follow,NeverPlay], \
			'Unsupported interaction: {}'.format(model)
		key = ndb.Key(model,artist_key.id(),parent=self.key)
		key.delete()

class Favorite(ndb.Model):
	# interaction
	artist_key = ndb.KeyProperty(required=True)
	created = ndb.DateTimeProperty(auto_now_add=True)
class Follow(ndb.Model):
	# interaction
	artist_key = ndb.KeyProperty(required=True)
	created = ndb.DateTimeProperty(auto_now_add=True)
class NeverPlay(ndb.Model):
	# interaction
	artist_key = ndb.KeyProperty(required=True)
	create = ndb.DateTimeProperty(auto_now_add=True)

class Station(ndb.Model):
	serendipity = ndb.IntegerProperty()
	tags_ = ndb.StructuredProperty(TagProperty,repeated=True)
	
	@property
	def tags(self):
		return [{'name':tag.genre,'count':tag.count} for tag in self.tags_]
	@property
	def tags_dict(self):
		return {tag.genre:tag.count for tag in self.tags_}
		
#===============================================================================
# Crowdfunding Contest stuff
#===============================================================================
class Event(ndb.Model):
	# venue details
	venue_name = ndb.StringProperty()
	venue_location = ndb.StringProperty()
	min_age = ndb.IntegerProperty()
	
	event_date_str = ndb.StringProperty()
	event_date_time = ndb.DateTimeProperty()
	tickets_start = ndb.DateTimeProperty()
	tickets_end = ndb.DateTimeProperty()
	
	capacity = ndb.IntegerProperty()
	num_available_positions = ndb.IntegerProperty()
	nominal_tpb = ndb.IntegerProperty()
	
	base_ticket_price = ndb.FloatProperty()
#	ticket_provider = ndb.StringProperty()
#	ticket_provider_url = ndb.StringProperty()
#	ticket_provider_fee = ndb.FloatProperty()
	radius_fee = ndb.FloatProperty()
	
	@property
	def extra_tickets(self):
		'''
		Calculates the number of surplus tickets available beyond the minimum tbp*num bands
		'''
		return self.capacity - self.nominal_tpb * self.num_available_positions
		
	def get_number_of_contestants(self):
		'''Counts the number of artists competing to perform
		'''
		return Contestant.query(ancestor = self.key).count()
	def get_ticket_sales_per_band(self):
		'''
		Fetches the ticket sales of the highest-selling n bands
		n == num_available_positions
		@return: a list of ticket sales in ints and list of corresponding band keys
		@rtype: list,list
		'''
		# grab all the contestants
		contestant_keys = Contestant.query(ancestor=self.key).fetch(None,keys_only=True)
		
		# count the tickets sold per band, and put in form that can be sorted
		sales_count_list = ((key,Contestant.get_ticket_count(key)) for key in contestant_keys)
		sorted_ticket_sales = sorted(sales_count_list,key=lambda x: x[1],
								reverse = True)
		bands,sales = zip(*sorted_ticket_sales)
		return bands,sales
		
class Contestant(ndb.Model):
	'''
	A contestant is an artist.
	'''
	artist_key = ndb.KeyProperty(Artist,required=True)
#	artist_name = ndb.StringProperty(required=True)
#	track_id = ndb.StringProperty(required=True)
	@property
	def page_id(self):
		return self.key.parent().id()+self.key.id()
	@property
	def page_url(self):
		return '{}/e/{}'.format(BASE_URL,self.page_id)
	@property
	def local_url(self):
		return '/e/{}'.format(self.page_id)
	@staticmethod
	def get_ticket_count(key):
		'''
		Counts the number of tickets that have been sold to the contestant
		@param key: the key of a contestant
		@type key: ndb.Key
		@return: the number of tickets sold by that contestant
		@rtype: int
		'''
		return TicketSale.query(ancestor = key).count()
	def get_ticket_purchasers(self):
		'''
		@return: generator for everyone who purchased a ticket for the band
		'''
		purchaser_keys = TicketSale.query(ancestor = self.key).iter(keys_only = True)
		purchaser_futures = ndb.get_multi_async(purchaser_keys)
		purchasers = (f.get_result() for f in purchaser_futures)
		return purchasers
#	def package(self):
#		exclude = ('event','artist_key')
#		contestant_dict = self.to_dict(exclude=exclude)
#		return contestant_dict
	def get_ticket_purchaser_names(self):
		'''
		@return: list of names
		@rtype: list
		'''
		purchasers = self.get_ticket_purchasers()
		return [p.name for p in purchasers]


class TicketSale(ndb.Model):
	'''
	A person has reserved a ticket for the show.
	'''
	name = ndb.StringProperty(required=True)
	age = ndb.IntegerProperty()
	email = ndb.StringProperty(required=True)
	
	stripe_id = ndb.StringProperty(required=True)
	
	base_ticket_price = ndb.IntegerProperty(required=True)
	radius_fee = ndb.IntegerProperty(required=True)
	charge_id = ndb.StringProperty()
class Cantab(ndb.Model):
	'''
	A person who has signed up for the Cantab show, feb 28 2013
	'''
	email = ndb.StringProperty()
class LandingPageSignup(ndb.Model):
	'''
	A person has left their email on the landing page
	'''
	email = ndb.StringProperty()
	
'''
Unique pages!!

Event:
Event location aka venue name
Event "City,State"
Event Date - in words
num bands contesting
base ticket price
provider e.g. ticketfly
provider url
provider fee
radius fee

Leader information. Undefined.

Artist:
Artist name - artist entered value
number of tickets sold (for a band)
number of tickets required - the adjusted value (for a band)
number of tickets remaining (for a band)
names of people who have bought tickets
Artist Track id


Info from people:
name
email
phone
stripe token
name on card


'''