import json
import re
from six import u, unichr
from six.moves.urllib import request, parse
from cshsms.settings import TEXTLOCAL_API, TEXTLOCAL_PRIMARY_ID

class TextLocal(object):
	def __init__(self, apikey, primary_id):
		self.apikey = apikey
		self.primary_id = primary_id

	def get_all_inboxes(self):
		params = {'apikey': self.apikey}
		inboxes_url = 'https://api.textlocal.in/get_inboxes/?'
		return self.get_url_response(request_url=inboxes_url, params=params)

	def get_primary_inbox(self):
		params = {'apikey': self.apikey, 'inbox_id': self.primary_id}
		messages_url = 'https://api.textlocal.in/get_messages/?'
		return self.get_url_response(request_url=messages_url, params=params)

	def get_url_response(self, request_url, params):
		f = request.urlopen(request_url + parse.urlencode(params))
		return json.loads(f.read().decode('latin1'))

	def get_primary_inbox_messages(self):
		inbox = self.get_primary_inbox()
		return inbox['messages']

	def unicode_inbox_messages(self):
		messages = self.get_primary_inbox_messages()
		for message in messages:
			corrupt_unicode_matches = self.find_corrupted_hindi_unicode_matches(message=message['message'])
			if corrupt_unicode_matches:
				message['message'] = self.correct_corrupted_unicode_matches(matches=corrupt_unicode_matches, original_message=message['message'])
		return messages

	def find_corrupted_hindi_unicode_matches(self, message):
		return re.findall("(?<!\\\w)09\w{2}", message)

	def correct_corrupted_unicode_matches(self, matches, original_message):
		updated_message = ""
		for match in set(matches):
			altered = unichr(int(match, 16))
			if updated_message:
				updated_message = re.sub(match, altered, updated_message)
			else:
				updated_message = re.sub(match, altered, original_message)

		return u(updated_message)
		 

	def is_message_new(self, message):
		return True if message['isNew'] == True else False

	def new_messages_by_number(self, messages):
		num_message_dict = {}
		for message in messages:
			if self.is_message_new(message):
				num_message_dict.setdefault(message['number'], []).append(message['message'])
		return num_message_dict
