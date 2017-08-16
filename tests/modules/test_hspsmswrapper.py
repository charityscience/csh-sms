from cshsms.settings import HSPSMS_API, HSPSMS_USERNAME, HSPSMS_SENDERNAME
from django.test import TestCase
from modules.hspsmswrapper import Hspsms

class HspsmsSendingTests(TestCase):
	def test_create_objects(self):
		hspsms = Hspsms(apikey=HSPSMS_API, username=HSPSMS_USERNAME, sendername=HSPSMS_SENDERNAME)
		self.assertIsInstance(hspsms, Hspsms)