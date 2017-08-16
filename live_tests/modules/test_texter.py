import time
from django.test import TestCase
from modules.texter import Texter
from cshsms.settings import TEXTLOCAL_PHONENUMBER

TEXTER = Texter()
class TexterGetInboxesTests(TestCase):
	def test_read_inbox(self):
		inbox_dict = TEXTER.read_inbox()
		self.assertIsInstance(inbox_dict, dict)

	def test_send(self):
		time.sleep(120)
		send_status = TEXTER.send(message="Testing example message in Texter.", phone_number=TEXTLOCAL_PHONENUMBER)
		time.sleep(120)
		new_message_dict = TEXTER.read_inbox()
		self.assertTrue("Testing example message in Texter." in new_message_dict[0])