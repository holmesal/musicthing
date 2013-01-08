import handlers
import json
import logging
import models
import webapp2

class LoginHandler(handlers.UserHandler):
	def post(self):
		'''
		User is logging in
		'''
		self.say('Log in is just a stub right now!')
#		return self.redirect('/music')
class LogoutHandler(handlers.UserHandler):
	def get(self):
		'''
		User is logging out
		'''
		# destroy session
		self.log_out()
		# redirect to home page
		return self.redirect('/')
		
class FavoriteArtistHandler(handlers.UserHandler):
	def post(self):
		'''User favorites an artist
		'''
		artist_id = self.request.get('artist_id')
		try:
			# get the artist
			artist = self.get_artist_by_id(artist_id)
			# grab the user
			user = self.get_user_from_session()
			# add the favorite
			user.add_interaction(models.Favorite,artist.key)
		except self.SessionError,e:
			self.response.out.write(json.dumps({'message':str(e)}))
		except Exception,e:
			logging.error(e)
			self.response.out.write(json.dumps({'message':e}))
		else:
			self.response.out.write(json.dumps({'status':200,'message':'OK'}))
class UnFavoriteArtistHandler(handlers.UserHandler):
	def post(self):
		'''User unfavorites an artist
		'''
		artist_id = self.request.get('artist_id')
		try:
			# get the artist
			artist = self.get_artist_by_id(artist_id)
			# grab the user
			user = self.get_user_from_session()
			# add the favorite
			user.remove_interaction(models.Favorite,artist.key)
		except self.SessionError,e:
			self.response.out.write(json.dumps({'message':str(e)}))
		except Exception,e:
			logging.error(e)
			self.response.out.write(json.dumps({'message':e}))
		else:
			self.response.out.write(json.dumps({'status':200,'message':'OK'}))
class FollowArtistHandler(handlers.UserHandler):
	def post(self):
		'''User follows an artist
		'''
		artist_id = self.request.get('artist_id')
		try:
			# get the artist
			artist = self.get_artist_by_id(artist_id)
			# grab the user
			user = self.get_user_from_session()
			# add the favorite
			user.add_interaction(models.Follow,artist.key)
		except self.SessionError,e:
			self.response.out.write(json.dumps({'message':str(e)}))
		except Exception,e:
			logging.error(e)
			self.response.out.write(json.dumps({'message':e}))
		else:
			self.response.out.write(json.dumps({'status':200,'message':'OK'}))
class UnFollowArtistHandler(handlers.UserHandler):
	def post(self):
		'''User stops following an artist
		'''
		artist_id = self.request.get('artist_id')
		try:
			# get the artist
			artist = self.get_artist_by_id(artist_id)
			# grab the user
			user = self.get_user_from_session()
			# add the favorite
			user.remove_interaction(models.Follow,artist.key)
		except self.SessionError,e:
			self.response.out.write(json.dumps({'message':str(e)}))
		except Exception,e:
			logging.error(e)
			self.response.out.write(json.dumps({'message':e}))
		else:
			self.response.out.write(json.dumps({'status':200,'message':'OK'}))
class NeverPlayAgainHandler(handlers.UserHandler):
	def post(self):
		'''User has decided that they never want to hear the track again
		'''
		artist_id = self.request.get('artist_id')
		try:
			# get the artist
			artist = self.get_artist_by_id(artist_id)
			# grab the user
			user = self.get_user_from_session()
			# add the favorite
			user.add_interaction(models.NeverPlay,artist.key)
			
#			user.add_never_play(artist_key)
		except self.SessionError,e:
			self.response.out.write(json.dumps({'message':str(e)}))
		except Exception,e:
			logging.error(e)
			self.response.out.write(json.dumps({'message':e}))
		else:
			self.response.out.write(json.dumps({'status':200,'message':'OK'}))

app = webapp2.WSGIApplication([
							('/user/login',),
							('/user/logout',),
							('/user/favorite',FavoriteArtistHandler),
							('/user/unfavorite',UnFavoriteArtistHandler),
							('/user/follow',FollowArtistHandler),
							('/user/unfollow',UnFollowArtistHandler),
							('/user/neverPlay',NeverPlayAgainHandler)
							])
