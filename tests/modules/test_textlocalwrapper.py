from cshsms.settings import TEXTLOCAL_API, TEXTLOCAL_PRIMARY_ID
from django.test import TestCase
from modules.textlocalwrapper import TextLocal


class TextLocalGetInboxesTests(TestCase):
	def test_create_object(self):
		textlocal = TextLocal(TEXTLOCAL_API, TEXTLOCAL_PRIMARY_ID)
		self.assertIsInstance(textlocal, TextLocal)
		
	def test_get_all_inboxes(self):
		textlocal = TextLocal(TEXTLOCAL_API, TEXTLOCAL_PRIMARY_ID)
		response, status = textlocal.all_inboxes()
		self.assertIsInstance(response, dict)
		self.assertGreaterEqual(int(response['num_inboxes']), 1)

	def test_get_primary_inbox(self):
		textlocal = TextLocal(TEXTLOCAL_API, TEXTLOCAL_PRIMARY_ID)
		primary_inbox, status = textlocal.primary_inbox()
		self.assertTrue(primary_inbox)
		self.assertIsInstance(primary_inbox, dict)
		self.assertTrue(primary_inbox['status'])
		self.assertEqual(primary_inbox['status'], 'success')
