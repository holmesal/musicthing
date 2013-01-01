from google.appengine.api import mail
import handlers
import logging
import webapp2

class FeedbackHandler(handlers.BaseHandler):
#	def get(self):
#		pass
	def post(self):
		body = self.request.get('body')
		sender = self.request.get('from')
		body = body.encode('ascii','ingore')
		sender = sender.encode('ascii','ignore')
		
		try:
			message = mail.AdminEmailMessage(
											sender = 'patrick@levr.com',
											subject = 'New Merchant',
											)
			message.body = 'From: '+sender+'\n\n\n'
			message.body += body
			message.check_initialized()
			message.send()
			
		except:
			logging.critical('Feedback Message could not send')
			logging.critical(sender)
			logging.critical(body)
app = webapp2.WSGIApplication([
							('/feedback',FeedbackHandler)
							])