import time
from django.test import TestCase
from modules.texter import Texter
from cshsms.settings import TEXTLOCAL_PHONENUMBER

class TexterGetInboxesTests(TestCase):
	def test_read_inbox(self):
		texter = Texter()
		inbox_dict = texter.read_inbox()
		self.assertIsInstance(inbox_dict, dict)

	def test_send(self):
		texter = Texter()
		send_status = texter.send(message="Testing example message in Texter.", phone_number=TEXTLOCAL_PHONENUMBER)
		time.sleep(120)
		new_message_dict = texter.read_inbox()
		self.assertTrue("Testing example message in Texter." in new_message_dict[0])
