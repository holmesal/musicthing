from google.appengine.ext import ndb
from google.appengine.api import images
BASEURL = 'http://local-music.appspot.com'
DEFAULT_IMAGE_URL = '{}/img/default_artwork.jpeg'.format(BASEURL)
class Artist(ndb.Model):
	access_token = ndb.StringProperty()
	username = ndb.StringProperty()
	image_key = ndb.BlobKeyProperty()
	external_image_url = ndb.StringProperty()
	track_url = ndb.StringProperty()
	track_id = ndb.StringProperty()
	description = ndb.StringProperty()
	
	# external urls
	bandcamp_url = ndb.StringProperty()
	facebook_url = ndb.StringProperty()
	lastfm_url = ndb.StringProperty()
	myspace_url = ndb.StringProperty()
	soundcloud_url = ndb.StringProperty()
	tumblr_url = ndb.StringProperty()
	twitter_url = ndb.StringProperty()
	youtube_url = ndb.StringProperty()
	website_url = ndb.StringProperty()
	other_urls = ndb.StringProperty(repeated=True)
	
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
#class Song(ndb.Model):
#	audio = blobstore.blob