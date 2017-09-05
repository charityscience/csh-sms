import mock
import json
from mock import patch
from django.test import TestCase

from modules.textlocalwrapper import TextLocal
from modules.i18n import hindi_remind, hindi_information
from six import u
from mock import patch

class TextLocalInboxesTests(TestCase):
	def test_create_object(self):
		textlocal = TextLocal(apikey='mock_key', primary_id='mock_id')
		self.assertIsInstance(textlocal, TextLocal)

	def test_is_message_new(self):
		textlocal = TextLocal(apikey='mock_key', primary_id='mock_id')
		new_message = {'number': '910987654321', 'message': 'New message',
			'isNew': True}
		old_message = {'number': '910987654321', 'message': 'Old message',
			'isNew': None}

		self.assertTrue(textlocal.is_message_new(new_message))
		self.assertFalse(textlocal.is_message_new(old_message))

	def test_new_messages_by_number(self):
		textlocal = TextLocal(apikey='mock_key', primary_id='mock_id')
		new_message = {'number': '910987654321', 'message': 'New message',
			'isNew': True}
		new_message2 = {'number': '910987654321', 'message': 'Newer message',
			'isNew': True}
		old_message = {'number': '910987654321', 'message': 'Old message',
			'isNew': None}
		fake_num_message_dict = textlocal.new_messages_by_number([new_message, new_message2, old_message])
		one_message_num_dict = textlocal.new_messages_by_number([new_message2])

		self.assertIsInstance(fake_num_message_dict, dict)
		self.assertIsInstance(one_message_num_dict, dict)
		self.assertIsInstance(fake_num_message_dict['910987654321'], list)
		self.assertFalse(old_message['message'] in fake_num_message_dict['910987654321'])
		self.assertTrue(new_message['message'] in fake_num_message_dict['910987654321'])
		self.assertTrue(new_message2['message'] in fake_num_message_dict['910987654321'])
		self.assertTrue(new_message2['message'] in one_message_num_dict['910987654321'])

	@patch("modules.textlocalwrapper.request")
	def test_get_primary_inbox_messages(self, mock_request):
		class MockResponse():
			def __init__(self, read_value):
				self.read_value = read_value

			def read(self):
				return self.read_value

		mock_request.urlopen.return_value = MockResponse(read_value=json.dumps({'messages': ['yay']}).encode('latin1'))
		textlocal = TextLocal(apikey='mock_key', primary_id='mock_id')
		self.assertEqual(textlocal.get_primary_inbox_messages(), ['yay'])
		mock_request.urlopen.return_value = MockResponse(read_value=json.dumps({'messages': [{'id': '000000024', 'number': 1112223334,
			'message': 'Testy test', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
			{'id': '00000449', 'number': 0, 'message': 'Example message testy', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}]}).encode('latin1'))
		self.assertEqual(textlocal.get_primary_inbox_messages(), [{'id': '000000024', 'number': 1112223334,
			'message': 'Testy test', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
			{'id': '00000449', 'number': 0, 'message': 'Example message testy', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}])
		mock_request.urlopen.return_value = MockResponse(read_value=json.dumps({'inbox_id': 10001, 'num_messages': 1, 'min_time': 1010101101, 'max_time': 101010101101, 'sort_order': 'asc', 'sort_field': 'date', 'start': 0, 'limit': 1000,
			'messages': [{'id': '000000024', 'number': 1112223334, 'message': 'Testy test', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'}]}).encode('latin1'))
		self.assertEqual(textlocal.get_primary_inbox_messages(), [{'id': '000000024', 'number': 1112223334, 'message': 'Testy test', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'}])
		mock_request.urlopen.return_value = MockResponse(read_value=json.dumps({'inbox_id': 10001, 'num_messages': 0, 'min_time': 1010101101, 'max_time': 101010101101, 'sort_order': 'asc', 'sort_field': 'date', 'start': 0, 'limit': 1000, 'messages': []}).encode('latin1'))
		self.assertEqual(textlocal.get_primary_inbox_messages(), [])

	def test_doesnt_find_corrupted_hindi_unicode_matches_english(self):
		textlocal = TextLocal(apikey='mock_key', primary_id='mock_id')
		self.assertEqual(textlocal.find_corrupted_hindi_unicode_matches("Here's a test"), [])
		self.assertEqual(textlocal.find_corrupted_hindi_unicode_matches("Remind Tina 09-12-10"), [])
		self.assertEqual(textlocal.find_corrupted_hindi_unicode_matches("JOIN Tina 09-12-10"), [])
		self.assertEqual(textlocal.find_corrupted_hindi_unicode_matches("Remind Tina 09/12/10"), [])
		self.assertEqual(textlocal.find_corrupted_hindi_unicode_matches("Remind Tina 09-09-10"), [])
		self.assertEqual(textlocal.find_corrupted_hindi_unicode_matches("Remind Tina 09/09/10"), [])
		self.assertEqual(textlocal.find_corrupted_hindi_unicode_matches("Remind Tina 09-09-09"), [])
		self.assertEqual(textlocal.find_corrupted_hindi_unicode_matches("Remind Tina 09/09/09"), [])
		self.assertEqual(textlocal.find_corrupted_hindi_unicode_matches("Remind Tina 09/09/09 "), [])
		self.assertEqual(textlocal.find_corrupted_hindi_unicode_matches("Remind Tina 09/09/09  "), [])
		self.assertEqual(textlocal.find_corrupted_hindi_unicode_matches("Remind Tina 09/09/09a!"), [])
		self.assertEqual(textlocal.find_corrupted_hindi_unicode_matches("Remind Tina 08/09/09"), [])
		self.assertEqual(textlocal.find_corrupted_hindi_unicode_matches("Remind Tina 08/07/09"), [])
		self.assertEqual(textlocal.find_corrupted_hindi_unicode_matches("Remind Tina 08/07/04"), [])
		self.assertEqual(textlocal.find_corrupted_hindi_unicode_matches("BORN Tina 08/07/14"), [])
		self.assertEqual(textlocal.find_corrupted_hindi_unicode_matches("BORN Tina 08/07/2014"), [])
		self.assertEqual(textlocal.find_corrupted_hindi_unicode_matches("BORN Tina 08/07/2094"), [])
		self.assertEqual(textlocal.find_corrupted_hindi_unicode_matches("BORN Tina 08-07-2014"), [])

	def test_doesnt_find_corrupted_hindi_unicode_matches_hindi(self):
		textlocal = TextLocal(apikey='mock_key', primary_id='mock_id')
		self.assertEqual(textlocal.find_corrupted_hindi_unicode_matches(hindi_remind() + u"\u0906\u0930\u0935"), [])
		self.assertEqual(textlocal.find_corrupted_hindi_unicode_matches(hindi_remind() + u"\u0906\u0930\u0935 09-17-14"), [])
		self.assertEqual(textlocal.find_corrupted_hindi_unicode_matches(hindi_information() + u"\u0906\u0930\u0935 09-17-14"), [])

	def test_find_corrupted_hindi_unicode_matches(self):
		textlocal = TextLocal(apikey='mock_key', primary_id='mock_id')
		self.assertEqual(textlocal.find_corrupted_hindi_unicode_matches("0907 test"), ["0907"])
		self.assertEqual(textlocal.find_corrupted_hindi_unicode_matches("09A7 test"), ["09A7"])
		self.assertEqual(textlocal.find_corrupted_hindi_unicode_matches("09AD test"), ["09AD"])
		self.assertEqual(textlocal.find_corrupted_hindi_unicode_matches("096509430922 test"), ["0965", "0943", "0922"])
		self.assertEqual(textlocal.find_corrupted_hindi_unicode_matches("096509430922test"), ["0965", "0943", "0922"])
		self.assertEqual(textlocal.find_corrupted_hindi_unicode_matches("09070924094d0924093f0932093e Tina 09-12-10"), ["0907", "0924", "094d", "0924", "093f", "0932", "093e"])
		self.assertEqual(textlocal.find_corrupted_hindi_unicode_matches("09070924094d0924093f0932093e Tina 09-12-10 093a"), ["0907", "0924", "094d", "0924", "093f", "0932", "093e", "093a"])
		self.assertEqual(textlocal.find_corrupted_hindi_unicode_matches("09070924094d0924093f0932093e 09070924094D 10-12-09"),
			["0907", "0924", "094d", "0924", "093f", "0932", "093e", "0907", "0924", "094D"])
		
	def test_doesnt_corrupted_hindi_unicode_in_non_hindi_unicode_literals(self):
		textlocal = TextLocal(apikey='mock_key', primary_id='mock_id')
		self.assertEqual(textlocal.find_corrupted_hindi_unicode_matches("0A80 test"), [])
		self.assertEqual(textlocal.find_corrupted_hindi_unicode_matches("0AFC test"), [])
		self.assertEqual(textlocal.find_corrupted_hindi_unicode_matches("0030 0121 0D00 0185 004A"), [])
		self.assertEqual(textlocal.find_corrupted_hindi_unicode_matches("05C0 01C0 0D00 13190 1770 1BCO 2000 2090 2095"), [])
		self.assertEqual(textlocal.find_corrupted_hindi_unicode_matches("05C001C00D00 1319017701BCO20002090 2095"), [])

	def test_correct_regex_matches_unicode(self):
		textlocal = TextLocal(apikey='mock_key', primary_id='mock_id')
		self.assertEqual(textlocal.correct_corrupted_unicode_matches(matches=["0907"], original_message="0907 test"), u"\u0907 test")
		self.assertEqual(textlocal.correct_corrupted_unicode_matches(matches=["0965", "0943", "0922"], original_message="096509430922 test"), u"\u0965\u0943\u0922 test")
		self.assertEqual(textlocal.correct_corrupted_unicode_matches(matches=["0907", "0924", "094d", "0924", "093f", "0932", "093e"],
			original_message="09070924094d0924093f0932093e Tina 09-12-10"), u"\u0907\u0924\u094d\u0924\u093f\u0932\u093e Tina 09-12-10")
		self.assertEqual(textlocal.correct_corrupted_unicode_matches(matches=["0907", "0924", "094d", "0924", "093f", "0932", "093e", "0907", "0924", "094D"],
			original_message="09070924094d0924093f0932093e 09070924094D 10-12-09"), u"\u0907\u0924\u094d\u0924\u093f\u0932\u093e \u0907\u0924\u094D 10-12-09")

	@patch("modules.textlocalwrapper.TextLocal.get_primary_inbox_messages")
	def test_unicode_inbox_messages_no_unicode(self, mock_primary_inbox_messages):
		textlocal = TextLocal(apikey='mock_key', primary_id='mock_id')
		mock_primary_inbox_messages.return_value = [{'id': '000000024', 'number': 1112223334, 'message': 'Testy test', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
			{'id': '00000449', 'number': 0, 'message': 'Example message testy', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}]
		self.assertIsInstance(textlocal.unicode_inbox_messages(), list)

		self.assertEqual(textlocal.unicode_inbox_messages(), [{'id': '000000024', 'number': 1112223334, 'message': 'Testy test', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
			{'id': '00000449', 'number': 0, 'message': 'Example message testy', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}])
		mock_primary_inbox_messages.return_value = [{'id': '000000024', 'number': 1112223334, 'message': 'Join Tina 10-09-10', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
			{'id': '00000449', 'number': 0, 'message': 'Remind Tina 09-12-10', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'},
			{'id': '00000449', 'number': 0, 'message': 'Remind Tina 10-12-09', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}]
		self.assertEqual(textlocal.unicode_inbox_messages(), [{'id': '000000024', 'number': 1112223334, 'message': 'Join Tina 10-09-10', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
			{'id': '00000449', 'number': 0, 'message': 'Remind Tina 09-12-10', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'},
			{'id': '00000449', 'number': 0, 'message': 'Remind Tina 10-12-09', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}])
		mock_primary_inbox_messages.return_value = [{'id': '000000024', 'number': 1112223334, 'message': 'Join Tina 10/09/10', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
			{'id': '00000449', 'number': 0, 'message': 'Remind Tina 09/12/10', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'},
			{'id': '00000449', 'number': 0, 'message': 'Remind Tina 10/12/09', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}]
		self.assertEqual(textlocal.unicode_inbox_messages(), [{'id': '000000024', 'number': 1112223334, 'message': 'Join Tina 10/09/10', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
			{'id': '00000449', 'number': 0, 'message': 'Remind Tina 09/12/10', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'},
			{'id': '00000449', 'number': 0, 'message': 'Remind Tina 10/12/09', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}])

	@patch("modules.textlocalwrapper.TextLocal.get_primary_inbox_messages")
	def test_unicode_inbox_messages_with_unicode(self, mock_primary_inbox_messages):
		textlocal = TextLocal(apikey='mock_key', primary_id='mock_id')
		mock_primary_inbox_messages.return_value = [{'id': '000000024', 'number': 1112223334, 'message': '0907 test', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
			{'id': '00000449', 'number': 0, 'message': 'Example message testy', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}]
		self.assertIsInstance(textlocal.unicode_inbox_messages(), list)

		self.assertEqual(textlocal.unicode_inbox_messages(), [{'id': '000000024', 'number': 1112223334, 'message': u'\u0907 test', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
			{'id': '00000449', 'number': 0, 'message': 'Example message testy', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}])
		mock_primary_inbox_messages.return_value = [{'id': '000000024', 'number': 1112223334, 'message': 'Example message two', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
			{'id': '00000449', 'number': 0, 'message': '09B7 test', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}]
		self.assertEqual(textlocal.unicode_inbox_messages(), [{'id': '000000024', 'number': 1112223334, 'message': 'Example message two', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
			{'id': '00000449', 'number': 0, 'message': u'\u09B7 test', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}])
		mock_primary_inbox_messages.return_value = [{'id': '000000024', 'number': 1112223334, 'message': u'\u0938\u094d\u092e\u0930\u0923 Tina 10-09-10', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
			{'id': '00000449', 'number': 0, 'message': '0938094d092e09300923 Tina 09-12-10', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'},
			{'id': '00000449', 'number': 0, 'message': '09070924094d0924093f0932093e Tina 10-12-09', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}]
		self.assertEqual(textlocal.unicode_inbox_messages(), [{'id': '000000024', 'number': 1112223334, 'message': u'\u0938\u094d\u092e\u0930\u0923 Tina 10-09-10', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
			{'id': '00000449', 'number': 0, 'message': hindi_remind() + ' Tina 09-12-10', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'},
			{'id': '00000449', 'number': 0, 'message': hindi_information() + ' Tina 10-12-09', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}])
		mock_primary_inbox_messages.return_value = [{'id': '000000024', 'number': 1112223334, 'message': 'Join Tina 10/09/10', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
			{'id': '00000449', 'number': 0, 'message': 'Remind Tina 09/12/10', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'},
			{'id': '00000449', 'number': 0, 'message': '09070924094d0924093f0932093e 090609300935 10/12/09', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'},
			{'id': '00000449', 'number': 0, 'message': '09070924094d0924093f 0932093e 09070924094D 10-12-09', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}]
		self.assertEqual(textlocal.unicode_inbox_messages(), [{'id': '000000024', 'number': 1112223334, 'message': 'Join Tina 10/09/10', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
			{'id': '00000449', 'number': 0, 'message': 'Remind Tina 09/12/10', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'},
			{'id': '00000449', 'number': 0, 'message': hindi_information() + u' \u0906\u0930\u0935 10/12/09', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'},
			{'id': '00000449', 'number': 0, 'message': u'\u0907\u0924\u094d\u0924\u093f \u0932\u093e \u0907\u0924\u094D 10-12-09', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}])