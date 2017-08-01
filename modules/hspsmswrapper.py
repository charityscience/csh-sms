from cshsms.settings import HSPSMS_API, HSPSMS_USERNAME, HSPSMS_SENDERNAME

class Hspsms(object):
	def __init__(self, apikey, username, sendername):
		self.apikey = apikey
		self.username = username
		self.sendername = sendername