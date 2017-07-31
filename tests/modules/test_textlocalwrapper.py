from cshsms.settings import TEXTLOCAL_API, TEXTLOCAL_PRIMARY_ID
from django.test import TestCase
from modules.textlocalwrapper import TextLocal


class TextLocalGetInboxesTests(TestCase):
	def test_create_object(self):
		textlocal = TextLocal("fakekey")
		self.assertIsInstance(textlocal, TextLocal)
		
	def test_get_all_inboxes(self):
		textlocal = TextLocal(TEXTLOCAL_API)
		response, status = textlocal.all_inboxes()
		self.assertIsInstance(response, dict)
		self.assertGreaterEqual(int(response['num_inboxes']), 1)

	def test_get_primary_inbox(self):
		pass


	def test_get_inbox_by_id(self):
		pass