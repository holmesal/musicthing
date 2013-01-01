from google.appengine.api import mail
import handlers
import logging
import webapp2

class FeedbackHandler(handlers.BaseHandler):
#	def get(self):
#		pass
	def post(self):
		body = self.request.get('body')
		body = body.encode('ascii','ingore')
		
		try:
			message = mail.AdminEmailMessage(
											sender = 'patrick@levr.com',
											subject = 'New Merchant',
											)
			message.body += body
			message.check_initialized()
			message.send()
			
		except:
			logging.critical('Feedback Message could not send')
			logging.critical(body)
app = webapp2.WSGIApplication([
							('/feedback',FeedbackHandler)
							])