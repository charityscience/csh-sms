from cshsms.settings import TEXTLOCAL_API, TEXTLOCAL_PRIMARY_ID
from django.test import TestCase
from modules.textlocalwrapper import TextLocal


class TextLocalGetInboxesTests(TestCase):
	def test_all_inboxes(self):

		textlocal = TextLocal("fakekey")
		response, status = textlocal.all_inboxes()
		self.assertIsInstance(textlocal, TextLocal)

	def test_get_primary_inbox(self):
		pass


	def test_get_inbox_by_id(self):
		pass