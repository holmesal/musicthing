import string
import random
import models
event_id_length = 3
contestant_id_length = 2
def generate_contestant_id(event_key):
	'''
	Generate a unique contestant id
	@param event_key: The key of the event the contestant is being generated for
	@type event_key: ndb.Key
	@return: random alphanumeric str
	@rtype: str
	'''
	return _generate_id(contestant_id_length, models.Contestant, event_key)
def generate_event_id():
	'''
	Generates a unique event id
	@return: random alphanumeric str
	@rtype: str
	'''
	return _generate_id(event_id_length, models.Event)
def _generate_id(n,model,parent_key = None):
	'''
	Generates a UNIQUE random alphanumeric str id of length n
	@param n: length of the id
	@type n: int
	@return: random alphanumeric str
	@rtype: str
	'''
	# create ids until a unique one is found
	while True:
		chars = string.ascii_letters + string.digits
		id_ = ''.join(random.choice(chars) for _ in range(n))
		existing_entity = model.get_by_id(id_, parent_key)
		if existing_entity is None:
			break
	return id_


	