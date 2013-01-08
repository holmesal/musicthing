from google.appengine.ext import ndb
from google.appengine.api import images
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
			'admin1' : admin1,
			'city' : city,
			'ghash' : self.ghash
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
	@property
	def intkey(self):
		'''Returns the integer id from the users key
		@return: the users numeric id
		@rtype: int
		'''
		return self.key.id()
	@ndb.transactional
	def add_favorite(self,artist_key):
		'''
		Adds a favorite track/artist to the user
		The favorite has the same id as the artist.
		@param key: reference key to the favorited track/artist
		@type key: ndb.Key
		'''
		existing_favorite = Favorite.get_by_id(artist_key.id(), parent = self.key)
		if existing_favorite is None:
			Favorite(id = artist_key.id(), parent = self.key, artist_key = artist_key).put()
#		f = Favorite.get_or_insert(artist_key.id(),parent = self.key, artist_key = artist_key)
	@ndb.transactional
	def remove_favorite(self,artist_key):
		'''
		Deletes a favorited track/artist
		@param key: key of the track/artist
		@type key: ndb.Key
		'''
		# TODO: make sure the favorite exists?
		favorite_key = ndb.Key(Favorite,artist_key.id(),parent = self.key)
		
		favorite_key.delete()
class Favorite(ndb.Model):
	# Only create these using User.add_favorite
	# parent must be a user entity
	artist_key = ndb.KeyProperty(required = True)
	created = ndb.DateTimeProperty(auto_now_add = True)
class Station(ndb.Model):
	serendipity = ndb.IntegerProperty()
	tags_ = ndb.StructuredProperty(TagProperty,repeated=True)
	
	@property
	def tags(self):
		return [{'name':tag.genre,'count':tag.count} for tag in self.tags_]
	@property
	def tags_dict(self):
		return {tag.genre:tag.count for tag in self.tags_}
		


