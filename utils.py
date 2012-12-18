import webapp2

class BaseHandler(webapp2.RequestHandler):
	def set_plaintext(self):
		self.response.headers['Content-Type'] = 'text/plain'
	def say(self,stuff=''):
		'''
		For debugging when I am too lazy to type
		'''
		self.response.out.write('\n')
		self.response.out.write(stuff)