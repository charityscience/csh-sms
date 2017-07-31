import json
from urllib import request, parse
from cshsms.settings import TEXTLOCAL_API, TEXTLOCAL_PRIMARY_ID

class TextLocal(object):
	def __init__(self, apikey, primary_id):
		self.apikey = apikey
		self.primary_id = primary_id

	def get_all_inboxes(self):
		params = {'apikey': self.apikey}
		inboxes_url = 'https://api.textlocal.in/get_inboxes/?'
		f = request.urlopen(inboxes_url + parse.urlencode(params))
		return json.loads(f.read().decode('latin1')), f.code

	def get_primary_inbox(self):
		params = {'apikey': self.apikey, 'inbox_id': self.primary_id}
		messages_url = 'https://api.textlocal.in/get_messages/?'
		f = request.urlopen(messages_url + parse.urlencode(params))
		return json.loads(f.read().decode('latin1')), f.code

	def get_primary_inbox_messages(self):
		inbox_and_code = self.get_primary_inbox()
		inbox = inbox_and_code[0]
		return inbox['messages']

	def is_message_new(self, message):
		return True if message['isNew'] == 'True'.lower() else False