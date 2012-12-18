from google.appengine.ext import ndb,blobstore


class Artist(ndb.Model):
	email = ndb.StringProperty()
	pw = ndb.StringProperty()
	
#class Song(ndb.Model):
#	audio = blobstore.blob