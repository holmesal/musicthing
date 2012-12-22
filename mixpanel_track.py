from google.appengine.api import urlfetch
import base64
import json
import logging
token = "080da319b25d8c64555d5d599cf7eb56"
def track_event(event,properties=None):
	"""
		A simple function for asynchronously logging to the mixpanel.com API on App Engine 
		(Python) using RPC URL Fetch object.
		@param event: The overall event/category you would like to log this data under
		@param properties: A dictionary of key-value pairs that describe the event
		See http://mixpanel.com/api/ for further detail. 
		@return Instance of RPC Object
	"""
	if properties == None:
		properties = {}
	if 'token' not in properties:
		properties['token'] = token
	
	params = {"event": event, "properties": properties}
	
	
	logging.info(params)
		
	data = base64.b64encode(json.dumps(params))
	request = "http://api.mixpanel.com/track/?data=" + data
	
	rpc = urlfetch.create_rpc()
	urlfetch.make_fetch_call(rpc, request)

	return rpc
	
def track_person(distinct_id,properties):
	'''
	Track some people
	@param distinct_id:
	@type distinct_id:
	@param properties:
	@type properties:
	'''
	params = {
		"$set"		:	properties,
		"$token"	:	token,
		"$distinct_id"	:	distinct_id
	}
	
	logging.info(params)
	
	data = base64.b64encode(json.dumps(params))
	request = "http://api.mixpanel.com/engage/?data="+data
	
	rpc = urlfetch.create_rpc()
	urlfetch.make_fetch_call(rpc, request)

	
	return rpc
	
def track_increment(distinct_id,to_increment):
	params = {
		"$add"		:	to_increment,
		"$token"	:	token,
		"$distinct_id"	:	distinct_id
	}
	logging.debug(params)
	data = base64.b64encode(json.dumps(params))
	request = "http://api.mixpanel.com/engage/?data="+data
	
	rpc = urlfetch.create_rpc()
	urlfetch.make_fetch_call(rpc, request)

	return rpc
	

	
	