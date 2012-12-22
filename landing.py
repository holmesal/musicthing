from google.appengine.ext import ndb
import handlers
import jinja2
import logging
import models
import os
import random
import webapp2

class LandingHandler(handlers.BaseHandler):
	def get(self):
# 		# fetch keys
# 		artist_keys = models.Artist.query().fetch(None,keys_only=True)
# 		try:
# 			# get a random sample
# 			random_artists = random.sample(artist_keys,50)
# 		except ValueError:
# 			# list is not big enough, return all of them
# 			random_artists = artist_keys
# 		# shuffle list
# 		random.shuffle(random_artists)
# 		artists = ndb.get_multi(random_artists)
# 		
# 		# package the suckers
# 		template_values = {
# 						'artists' : artists
# 		}

		
		
		jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
		template = jinja_environment.get_template('templates/hype.html')
		self.response.out.write(template.render())

	def post(self):
		email = self.request.get('email')
		
		user = models.User.query().filter(models.User.email == email).get()
		if not user:
			models.User(email=email).put()
		
		template_values = {
			"state"	:	"signedup"
		}
		
		jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
		template = jinja_environment.get_template('templates/hype.html')
		self.response.out.write(template.render(template_values))
	

app = webapp2.WSGIApplication([('/',LandingHandler)])


