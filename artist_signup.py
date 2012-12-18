import webapp2
import utils
import sc_creds
import logging
import jinja2
import os
import utils
import soundcloud
jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


class ConnectSCHandler(utils.BaseHandler):
	def get(self):
		
		template_values = {
		}
		
		template = jinja_environment.get_template('templates/artist_signup/connect_sc.html')
		self.response.out.write(template.render(template_values))
	def post(self):
		client = soundcloud.Client(
								client_id = sc_creds.client_id,
								client_secret = sc_creds.client_secret,
								redirect_uri = 'http://local-music.appspot.com/signup/complete'
								)
		self.set_plaintext()
		self.redirect(client.authorize_url())
class ConnectAccountHandler(utils.BaseHandler):
	def get(self):
		pass
app = webapp2.WSGIApplication([
							('/signup',ConnectSCHandler),
							('/signup/complete',ConnectAccountHandler)
							
							])