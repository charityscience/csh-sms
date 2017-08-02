from cshsms.settings import HSPSMS_API, HSPSMS_USERNAME, HSPSMS_SENDERNAME
from django.test import TestCase
from modules.hspsmswrapper import Hspsms

class HspsmsSendingTests(TestCase):
	def test_create_objects(self):
		hspsms = Hspsms(apikey=HSPSMS_API, username=HSPSMS_USERNAME, sendername=HSPSMS_SENDERNAME)
		self.assertIsInstance(hspsms, Hspsms)

	def test_send_transactional_message(self):
		hspsms = Hspsms(apikey=HSPSMS_API, username=HSPSMS_USERNAME, sendername=HSPSMS_SENDERNAME)
		fr = hspsms.send_transactional_message(message='Example message', phone_number='0000000')
		self.assertTrue(fr)
		self.assertIsInstance(fr, list)
		self.assertTrue(fr[0]['responseCode'])
		self.assertEqual(fr[0]['responseCode'], "Message SuccessFully Submitted")
		self.assertTrue(fr[1])