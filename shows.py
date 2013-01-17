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


class ShowHandler(handlers.ArtistHandler):
	def get(self):
	
		jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
		template = jinja_environment.get_template('templates/bandshowsignup.html')
		self.response.out.write(template.render())


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
			session['login_redirect'] = 'event_signup'
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
		#=======================================================================
		# SPOOF THE EVENT KEY FOR NOW BECAUSE WE ONLY HAVE ONE SHOW
		event_key = ndb.Key(models.Event,'KGB')
		#=======================================================================
		# create the contestant
		contestant = self.sign_up_artist_for_event(artist, event_key)
		redirect_url = contestant.page_url
		return self.redirect(redirect_url)
app = webapp2.WSGIApplication([
							('/shows',ShowHandler),
							('/shows/playcheck',PlayCheckHandler)
							('/shows/signup',SignupHandler)
							])


