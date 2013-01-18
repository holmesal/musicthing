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
		num_tickets_remaining = -999
		tickets_available = None
		status = 'FLAG!'
		min_tpb = -888
		
		if total_tickets_sold >= event.capacity:
			# tickets are not available
			tickets_available = False
			# check if contestant is one of the winners
			if contestant.key in top_bands:
				# contest has ended, and the band has won
				status = 'won'
			else:
				# contest has ended, and the band has lost
				status = 'lost'
		else:
			# tickets are still available
			# recalculate the tpb, or tickets per band to win
			
			# calc the number of tickets that have been sold from the extra ticket pool
			surplus_tickets = sum([count - event.nominal_tpb
							for count in top_sales if count > event.nominal_tpb])
			# calc the number of remaining extra tickets
			total_oversell = surplus_tickets - event.extra_tickets
			if total_oversell < 0:
				# no tbp adjustment, there are still extra tickets to be sold
				min_tpb = event.nominal_tpb
			else:
				# no extra tickets are left. adjust the tpb
				# total oversell is a positive int
				tpb_reduction = int(math.ceil(float(total_oversell)/float(event.num_available_positions)))
				min_tpb = event.nominal_tpb - tpb_reduction
			
			# check if contest has ended by comparing adjusted tpb with top sales
			if filter(lambda x: x < min_tpb, top_sales) == []:
				# the top bands have all sold the minimum tickets
				if contestant.key in top_bands:
					# contest has ended, and band has won, but can still sell tickets
					tickets_available = True
					status = 'won'
				else:
					# contest has ended, and band has lost, and cannot sell tickets
					tickets_available = False
					num_tickets_remaining = 0
					status = 'lost'
			else:
				# the contest is still in progress
				# Calculate the number of tickets this contestant has sold
				ticket_purchasers = contestant.get_ticket_purchaser_names()
				num_tickets_sold = ticket_purchasers.__len__()
				# calc number of tickets remaining
				num_tickets_remaining = min_tpb - num_tickets_sold
				# check if the band has sold past the min tpb
				if num_tickets_remaining <= 0:
					# contest is in progress, but the band has won
					status = 'won'
					# don't send back a negative value for num_tickets_remaining
					num_tickets_remaining = 0
				else:
					# contest is in progress, and the band has not won yet
					status = 'in_progress'
			
		#=======================================================================
		# # Check if a logged in artist is viewing the page
		#=======================================================================
		page_artist = contestant.artist_key.get()
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
		
		
		# package template
		template_values = {
						'num_tickets_remaining' : num_tickets_remaining,
						'artist' : page_artist,
						'contestant_id' : contestant.page_id,
						'contestant_url' : contestant.page_url,
						'names' : ticket_purchasers,
						'tickets_available' : tickets_available,
						'status' : status,
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
