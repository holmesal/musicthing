import webapp2
from google.appengine.ext.webapp import blobstore_handlers
import jinja2
import os
import models
import logging
from gaesessions import get_current_session

#from excepts import *
jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class BaseHandler(webapp2.RequestHandler):
	def set_plaintext(self):
		self.response.headers['Content-Type'] = 'text/plain'
	def say(self,stuff=''):
		'''For debugging when I am too lazy to type
		'''
		self.response.out.write('\n')
		self.response.out.write(stuff)
	def get_artist(self,artist_id):
		'''
		Fetches an artist from the ndb.
		@raise SessionError: 
			if artist_id does not yield an artist entity from the db
		
		@param artist_id: The soundcloud id of an artist
		@type artist_id: str
		
		@return: The artist that corresponds to the provided artist_id
		@rtype: models.Artist
		'''
		try:
			artist_id = str(artist_id)
			artist = models.Artist.get_by_id(artist_id)
			assert artist, 'Artist does not exist'
			return artist
		except AssertionError,e:
			raise self.SessionError(e)
	class SessionError(Exception):
		'''Session is invalid'''
class ArtistHandler(BaseHandler):
	def log_in(self,artist_id):
		'''
		Creates a session, setting logged_in to true, 
			and assigning any other session variables
		@param artist_id: the artists ndb key
		@type artist_id: str
		'''
		session = get_current_session()
		session['logged_in'] = True
		session['artist_id'] = str(artist_id)
	def log_out(self):
		'''
		Changes the session to a logged out status, setting logged_in to false,
		and deleting other session variables
		'''
		session = get_current_session()
		session['logged_in'] = False
		try:
			del session['artist_id']
		except:
			pass
	def get_artist_from_session(self):
		'''
		Assures that the artist is logged in
		@raise SessionError: 
			if logged_in is False
			if either logged_in or artist_id do not exist as session keys
			if artist_id is invalid, i.e. no artist by that id exists in the db
		@return: the artist entity
		@rtype: models.Artist
		'''
		try:
			session = get_current_session()
			# make sure they are logged in
			assert session['logged_in'] == True, 'Not logged in.'
			
			# grab the artist by the session artist_id and make sure it exists in the db
			artist_id =  session['artist_id']
			logging.debug(artist_id)
			artist = models.Artist.get_by_id(artist_id)
			assert artist, 'Artist does not exist'
			artist.artist_id = artist_id
			return artist
		except AssertionError,e:
			raise self.SessionError(e)
		except KeyError,e:
			raise self.SessionError(e)
class UserHandler(BaseHandler):
	pass
class UploadHandler(ArtistHandler,blobstore_handlers.BlobstoreUploadHandler):
	pass

