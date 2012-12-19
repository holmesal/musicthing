from google.appengine.ext import ndb,blobstore

BASEURL = 'http://local-music.appspot.com'

class Artist(ndb.Model):
	access_token = ndb.StringProperty()
	username = ndb.StringProperty()
	image = blobstore.BlobReferenceProperty()
	audio_url = ndb.StringProperty()
	
	@property
	def img_url(self):
		'''Returns a url for serving the artists artwork
		'''
		return '{}/artist/{}/image'.format(BASEURL,self.strkey)
	
	@property
	def strkey(self):
		'''Returns a urlsafe version of the artists key
		'''
		return str(self.key.id())
#class Song(ndb.Model):
#	audio = blobstore.blob