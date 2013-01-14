import string
import random
event_id_length = 3
contestant_id_length = 2
def generate_contestant_id():
	'''
	@param num: desired length of the string
	@type num: int
	@return: random alphanumeric str
	@rtype: str
	'''
	chars = string.ascii_letters+string.digits
	return ''.join(random.choice(chars) 
						for _ in range(contestant_id_length))
def generate_event_id():
	'''
	Generates an event id
	@return: random alphanumeric str
	@rtype: str
	'''
	chars = string.ascii_letters+string.digits
	return ''.join(random.choice(chars) for _ in range(event_id_length))

