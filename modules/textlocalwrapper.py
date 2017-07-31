import json
from urllib import request, parse
from cshsms.settings import TEXTLOCAL_API, TEXTLOCAL_PRIMARY_ID
from modules.texter import Texter

class TextLocal(object):
	def __init__(self, apikey):
		self.apikey = apikey

	def all_inboxes(self):
		params = {'apikey': self.apikey}
		inboxes_url = 'https://api.textlocal.in/get_inboxes/?'
		f = request.urlopen(inboxes_url + parse.urlencode(params))
		return json.loads(f.read().decode('latin1')), f.code