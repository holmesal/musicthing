from google.appengine.ext import ndb
import contest_utils as cutils
import handlers
import jinja2
import os
import models
import webapp2
from gaesessions import get_current_session
import math

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
			# invalid contestant id --> redirect to landing page
			return self.redirect('/')
		
		#=======================================================================
		# # Calculate the minimum tickets per band
		#=======================================================================
		top_bands,top_sales = event.get_top_ticket_sales()
		total_tickets_sold = sum(top_sales)
		self.say(total_tickets_sold)
		if total_tickets_sold >= event.capacity:
			# tickets are not available
			tickets_available = False
			# check if contestant is one of the winners
			if contestant.key in top_bands:
				status = 'won'
			else:
				status = 'lost'
		else:
			# recalculate the tpb
			surplus_tickets = sum([count - event.nominal_tpb
							for count in top_sales if count > event.nominal_tpb])
			total_surplus = surplus_tickets - event.extra_tickets
			if total_surplus < 0:
				# no tbp adjustment
				min_tpb = event.nominal_tpb
			else:
				# must adjust the tpb to stay within capacity
				tpb_reduction = int(math.ceil(float(total_surplus)/float(event.num_available_positions)))
				min_tpb = event.nominal_tpb - tpb_reduction
			
			# have min tpb
			assert False, ''
		
		# calculate ticket stuff
		ticket_purchasers = contestant.get_ticket_purchaser_names()
		num_tickets_sold = ticket_purchasers.__len__()
#		num_tickets_per_band = event.tickets_per_band
		num_tickets_remaining = event.nominal_tpb - num_tickets_sold
		if num_tickets_remaining < 0:
			num_tickets_remaining = 0
		
		page_artist = contestant.artist_key.get()
		# Check if a logged in artist is viewing the page
		try:
			current_artist = self.get_artist_from_session()
		except self.SessionError:
			# no artist is logged in
			artist_logged_in = False
			artist_owns_page = False
		else:
			# an artist is logged in
			artist_logged_in = True
			# Check if artist owns the page
			if page_artist.key == current_artist.key:
				artist_owns_page = True
			else:
				artist_owns_page = False
		
		### SPOOF
		tickets_available = True
		contest_status = 'won'# 'lost' # 'in_progress'
		### /SPOOF
		
		# package template
		template_values = {
						'tickets_remaining' : num_tickets_remaining,
						'artist' : page_artist,
						'contestant_id' : contestant.page_id,
						'contestant_url' : contestant.page_url,
						'names' : ticket_purchasers,
						'tickets_available' : tickets_available,
						'status' : contest_status,
						'show_navbar' : artist_logged_in,
						'is_owner' : artist_owns_page
						}
		template_values.update(event.package())
		
		self.say(template_values)
	def post(self):
		pass
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
		Spoofs an event and a contestant
		'''
		artist = models.Artist.query().get()
#		event_id = cutils.generate_event_id()
		event = models.Event.query().get()
		contestant_id = cutils.generate_contestant_id(event.key)
#		event = models.Event(id=event_id,
#							min_tickets = 100,
#							max_tickets = 200,
#							available_positions = 4,
#							tickets_per_band = 50
#							)
		contestant = models.Contestant(id=contestant_id,
									parent=event.key,
									artist_key = artist.key,
									)
#		event.put()
		contestant.put()
		self.say(event)
		self.say(contestant)
		self.say(contestant.page_id)
app = webapp2.WSGIApplication([
							('/e/test',TestHandler),
							('/e/(.*)',BandPageHandler)
							])
