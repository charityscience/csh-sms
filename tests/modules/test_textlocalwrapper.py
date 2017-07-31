from cshsms.settings import TEXTLOCAL_API, TEXTLOCAL_PRIMARY_ID
from django.test import TestCase
from modules.textlocalwrapper import TextLocal


class TextLocalInboxesTests(TestCase):
	def test_create_object(self):
		textlocal = TextLocal(TEXTLOCAL_API, TEXTLOCAL_PRIMARY_ID)
		self.assertIsInstance(textlocal, TextLocal)
		
	def test_get_all_inboxes(self):
		textlocal = TextLocal(TEXTLOCAL_API, TEXTLOCAL_PRIMARY_ID)
		response, status = textlocal.get_all_inboxes()
		self.assertIsInstance(response, dict)
		self.assertGreaterEqual(int(response['num_inboxes']), 1)

	def test_get_primary_inbox(self):
		textlocal = TextLocal(TEXTLOCAL_API, TEXTLOCAL_PRIMARY_ID)
		primary_inbox, status = textlocal.get_primary_inbox()
		self.assertTrue(primary_inbox)
		self.assertIsInstance(primary_inbox, dict)
		self.assertTrue(primary_inbox['status'])
		self.assertEqual(primary_inbox['status'], 'success')

	def test_get_primary_inbox_messages(self):
		textlocal = TextLocal(TEXTLOCAL_API, TEXTLOCAL_PRIMARY_ID)
		primary_inbox_messages = textlocal.get_primary_inbox_messages()
		self.assertTrue(primary_inbox_messages)
		self.assertIsInstance(primary_inbox_messages, list)

	def test_is_message_new(self):
		textlocal = TextLocal(TEXTLOCAL_API, TEXTLOCAL_PRIMARY_ID)
		new_message = {'number': '910987654321', 'message': 'New message',
			'isNew': 'true'}
		old_message = {'number': '910987654321', 'message': 'Old message',
			'isNew': 'None'}

		self.assertTrue(textlocal.is_message_new(new_message))
		self.assertFalse(textlocal.is_message_new(old_message))