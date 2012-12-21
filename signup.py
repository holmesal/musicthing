import webapp2
import logging
import jinja2
import os
import handlers

class SignupHandler(handlers.BaseHandler):
	def get(self):
	
		template_values = {
			
		}
		
		jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
		template = jinja_environment.get_template('templates/signup.html')
		self.response.out.write(template.render(template_values))


app = webapp2.WSGIApplication([('/signup',SignupHandler)])


