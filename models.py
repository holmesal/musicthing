from google.appengine.ext import ndb
from google.appengine.api import images
from geo import geohash
BASEURL = 'http://local-music.appspot.com'
DEFAULT_IMAGE_URL = '{}/img/default_artwork.jpeg'.format(BASEURL)
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
	def to_dict(self):
		flat_key = self.key.flat()
		country = flat_key[1]
		admin1 = flat_key[3]
		city = flat_key[5]
		return {
			'country' : country,
			'administrative_area_level_1' : admin1,
			'locality' : city,
			'ghash' : self.ghash,
			'geo_point' : geohash.decode(self.ghash)
			}
class GHash(ndb.Model):
	pass


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
	
class Artist(ndb.Model):
	created = ndb.DateProperty(auto_now_add=True)
	
	access_token = ndb.StringProperty()
	username = ndb.StringProperty()
	description = ndb.StringProperty()
	email = ndb.StringProperty()
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
	def city_dicts(self):
		city_strings = []
		for city_key in self.city_keys:
			flat_key = city_key.flat()
			country = flat_key[1]
			admin1 = flat_key[3]
			city = flat_key[5]
			city_strings.append({
								'country' : country,
								'admin1' : admin1,
								'city' : city,
								})
		return city_strings
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
		


