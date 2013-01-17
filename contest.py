from google.appengine.ext import ndb
import contest_utils as cutils
import handlers
import jinja2
import os
import models
import webapp2
from gaesessions import get_current_session

jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


class BandPageHandler(handlers.ContestHandler):
	def get(self,request_id):
		'''
		This is the page where people can buy tickets
		@param contestant_id: The id of the event and contestant
		@type contestant_id: str
		'''
		try:
			event,contestant = self.get_event_and_contestant(request_id)
		except self.SessionError,e:
			assert False, e
			# invalid id --> redirect to landing page
			return self.redirect('/')
		self.say(event)
		self.say(contestant)
		self.say(contestant.page_id)
		# calculate ticket stuff
		ticket_purchasers = contestant.get_ticket_purchaser_names()
		num_tickets_sold = ticket_purchasers.__len__()
		num_tickets_per_band = event.tickets_per_band
		num_tickets_remaining = num_tickets_per_band - num_tickets_sold
		if num_tickets_remaining < 0:
			tickets_remaining = 0
		
		# package template
		template_values = {}
		template_values.update(event.package())
		template_values.update(contestant.package())
		self.say(template_values)
class SignupHandler(handlers.ContestHandler):
	def get(self):
		'''
		The first signup page for an event
		'''
		template_values = {}
		template = jinja_environment.get_template('/contest/signup_1.html')
		self.response.out.write(template.render(template_values))
class SignupConfirmHandler(handlers.ContestHandler):
	def get(self):
		'''
		The second signup page for an event
		'''
		try:
			artist = self.get_artist_from_session() #@UnusedVariable
		except:
			logged_in = False
			session = get_current_session()
			session['login_redirect'] = 'event_signup'
		else:
			logged_in = True
		template_values = {
						'logged_id' : logged_in
						}
		template = jinja_environment.get_template('/contest/signup_2.html')
		self.response.out.write(template.render(template_values))
		
'''
Unique pages!!

Event:
Event location aka venue name
Event "City,State"
Event Date - in words
num bands contesting
base ticket price
provider e.g. ticketfly
provider url
provider fee
radius fee

Leader information. Undefined.

Artist:
Artist name - artist entered value
number of tickets sold (for a band)
number of tickets required - the adjusted value (for a band)
number of tickets remaining (for a band)
names of people who have bought tickets
Artist Track id


Info from people:
name
email
phone
stripe token
name on card


'''
class TestHandler(handlers.ContestHandler):
	def get(self):
		'''
		Admin page to create events
		'''
		template_values = {}
		template = jinja_environment.get_template('/templates/admin/create_event.html')
		self.response.out.write(template.render(template_values))
	def get_(self):
		'''
		Spoofs an event and a contestant
		'''
		artist = models.Artist.query().get()
		event_id = cutils.generate_event_id()
		contestant_id = cutils.generate_contestant_id()
		event = models.Event(id=event_id,
							min_tickets = 100,
							max_tickets = 200,
							available_positions = 4,
							tickets_per_band = 50
							)
		contestant = models.Contestant(id=contestant_id,
									parent=event.key,
									artist_key = artist.key
									)
		event.put()
		contestant.put()
		self.say(event)
		self.say(contestant)
		self.say(contestant.page_id)
app = webapp2.WSGIApplication([
							('/e/test',TestHandler),
							('/e/(.*)',BandPageHandler),
							])
