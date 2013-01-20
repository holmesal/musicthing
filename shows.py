import handlers
import jinja2
import logging
import models
import webapp2
import json
import os
import json
from gaesessions import get_current_session
from google.appengine.ext import ndb
import utils


class ShowHandler(handlers.ArtistHandler):
	def get(self):
	
		jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
		template = jinja_environment.get_template('templates/bandshowsignup.html')
		self.response.out.write(template.render())
		
class TestHandler(handlers.BaseHandler):
	def get(self):
		
		going = ["going person 1","going person 2","going person 3"]
		
		artist = {
			"track_id"		:	71788795,
			"artist_name"	:	"testband",
			"facebook_url"	:	"facebook.com",
			"myspace_url"	:	"myspace.com",
			"twitter_url"	:	"@alonsoholmes",
			"youtube_url"	:	"youtube.com",
			"bandcamp_url"	:	"bandcamp.com",
			"website_url"	:	"www.alonsoholmes.com"
		}
		
		template_values = {
			"tickets_per_band"	:	40,
			"tickets_remaining"	:	0,
			"tickets_sold"		:	40,
			"place_string"		:	"2nd",
			"going"			:	going,
			"artist"		:	artist,
			"contestant_id"	:	"1x3rp",
			"status"		:	"lost",
			"purchase_allowed"	:	False,
			"is_owner"		:	True,
			"show_navbar"	:	True
		}
		
		jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
		template = jinja_environment.get_template('templates/bandpage.html')
		self.response.out.write(template.render(template_values))


class PlayCheckHandler(handlers.ArtistHandler):
	def get(self):
		'''
		Check login state of a band.
		'''
		try:
			artist = self.get_artist_from_session() #@UnusedVariable
		except:
			logged_in = False
			# create session data for after a user signs up through soundcloud
			session = get_current_session()
			session['login_redirect'] = '/shows/signup'
			#respond with true if logged in, false if not
			logging.info('SET LOGIN REDIRECT: {}'.format(session['login_redirect']))
			
		else:
			logged_in = True
		response = {
			"loggedin"	:	logged_in
		}
		self.response.out.write(json.dumps(response))
class SignupHandler(handlers.ContestHandler):
	def get(self):
		'''
		A band is signing up for a show
		'''
		# do not handle the exception.
		# If they try to go here without being signed in, FUCKEM!
		artist = self.get_artist_from_session()
		
		session = get_current_session()
		# destroy the redirect item in the session
		try:
			del session['login_redirect']
		except KeyError,e:
			logging.error(e)
		#=======================================================================
		# SPOOF THE EVENT KEY FOR NOW BECAUSE WE ONLY HAVE ONE SHOW
		event_key = ndb.Key(models.Event,'G9b')
		#=======================================================================
		
		# check if artist has already signed up as a contestant
		existing_contestant = models.Contestant.query(models.Contestant.artist_key == artist.key).get()
		if existing_contestant:
			return self.redirect(existing_contestant.local_url)
		# Artist has not signed up for this competition yet.
		contestant = self.sign_up_artist_for_event(artist, event_key)
		return self.redirect(contestant.local_url)

		
		
app = webapp2.WSGIApplication([
							('/shows',ShowHandler),
							('/shows/test',TestHandler),
							('/shows/playcheck',PlayCheckHandler),
							('/shows/signup',SignupHandler),
							])

