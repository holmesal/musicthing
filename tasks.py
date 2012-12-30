from datetime import datetime
from google.appengine.api import urlfetch
from google.appengine.ext import db
import base64
import json
import logging
import urllib
import webapp2
				
class TextTaskHandler(webapp2.RequestHandler):
	def post(self):
		try:
			
			logging.info('''
				
				SKYNET IS TEXTING THE FOUNDERS
				
				''')
			
			payload = json.loads(self.request.body)
			logging.info(payload['artist_name'])
			#twilio credentials
			sid = 'AC4880dbd1ff355288728be2c5f5f7406b'
			token = 'ea7cce49e3bb805b04d00f76253f9f2b'
			twiliourl='https://api.twilio.com/2010-04-01/Accounts/AC4880dbd1ff355288728be2c5f5f7406b/SMS/Messages.json'
			
			auth_header = 'Basic '+base64.b64encode(sid+':'+token)
			logging.info(auth_header)
			
			numbers = ['+16052610083','+16173124536','+12036329029']
			
			for number in numbers:
				request = {'From':'+16173608582',
							'To':number,
							'Body':'KABOOM. New band signup! '+payload['artist_name']}
			
				result = urlfetch.fetch(url=twiliourl,
									payload=urllib.urlencode(request),
									method=urlfetch.POST,
									headers={'Authorization':auth_header})
			
		except:
			logging.debug('Ah man this failed')
			
class UserTaskHandler(webapp2.RequestHandler):
	def post(self):
		try:
			
			logging.info('''
				
				SKYNET IS TEXTING THE FOUNDERS
				
				''')
			
			payload = json.loads(self.request.body)
			logging.info(payload['email'])
			#twilio credentials
			sid = 'AC4880dbd1ff355288728be2c5f5f7406b'
			token = 'ea7cce49e3bb805b04d00f76253f9f2b'
			twiliourl='https://api.twilio.com/2010-04-01/Accounts/AC4880dbd1ff355288728be2c5f5f7406b/SMS/Messages.json'
			
			auth_header = 'Basic '+base64.b64encode(sid+':'+token)
			logging.info(auth_header)
			
			numbers = ['+16052610083','+16173124536','+12036329029']
			
			for number in numbers:
				request = {'From':'+16173608582',
							'To':number,
							'Body':'Woohoo! New (Radius) user signup! '+payload['email']}
			
				result = urlfetch.fetch(url=twiliourl,
									payload=urllib.urlencode(request),
									method=urlfetch.POST,
									headers={'Authorization':auth_header})
			
		except:
			logging.debug('Ah man this failed')
			
app = webapp2.WSGIApplication([('/tasks/textTask', TextTaskHandler),
								('/tasks/userTask', UserTaskHandler)
								],debug=True)