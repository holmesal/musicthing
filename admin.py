import handlers
import jinja2
import os
import webapp2
import contest_utils as cutils
import models


jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class CreateEventHandler(handlers.ContestHandler):
	def get(self):
		'''
		Admin page to create events
		'''
		template_values = {}
		template = jinja_environment.get_template('/templates/admin/create_event.html')
		self.response.out.write(template.render(template_values))
	def post(self):
		'''
		Create the event
		'''
		p = self.request.get
		event_id = cutils.generate_event_id()
#		self.say(event_id)
		event = models.Event(id = event_id)
		event.populate(
					venue_name = p('venue_name'),
					venue_location = p('venue_location'),
					event_date = p('event_date'),
					min_age = int(p('min_age')),
					max_tickets = int(p('max_tickets')),
					min_tickets = int(p('min_tickets')),
					available_positions = int(p('available_positions')),
					tickets_per_band = int(p('tickets_per_band')),
					base_ticket_price = float(p('base_ticket_price')),
					radius_fee = float(p('radius_fee'))
					)
		event.put()
		self.say(event)
		self.say('\n\n\n PLEASE CLOSE THE TAB SO THAT YOU DONT CREATE DUPLICATE EVENTS BY REFRESHING')
		
		
app = webapp2.WSGIApplication([
							('/admin/create_event',CreateEventHandler)
							])