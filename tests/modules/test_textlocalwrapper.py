import mock
import json
from mock import patch
from django.test import TestCase

from modules.textlocalwrapper import TextLocal
from modules.i18n import hindi_remind, hindi_information
from six import u
from mock import patch


class MockResponse():
    def __init__(self, read_value):
        self.read_value = read_value

    def read(self):
        return self.read_value


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


    @patch("modules.textlocalwrapper.request")
    def test_new_messages_by_number(self, mock_request):
        textlocal = TextLocal(apikey='mock_key', primary_id='mock_id')
        old_message = {'number': '910987654321', 'message': 'Old message', 'date': '2017-08-05 21:12:07', 'isNew': None}
        new_message = {'number': '910987654321', 'message': 'New message', 'date': '2017-09-06 12:12:07', 'isNew': True}
        new_message2 = {'number': '910987654321', 'message': 'Newer message', 'date': '2017-09-06 21:12:07', 'isNew': True}
        mock_request.urlopen.return_value = MockResponse(read_value=json.dumps({'messages': [new_message, new_message2, old_message]}).encode('latin1'))
        fake_num_message_dict = textlocal.new_messages_by_number()
        self.assertIsInstance(fake_num_message_dict, dict)
        self.assertIsInstance(fake_num_message_dict['910987654321'], list)
        self.assertFalse(old_message['message'] in fake_num_message_dict['910987654321'])
        self.assertTrue(new_message['message'] in fake_num_message_dict['910987654321'])
        self.assertTrue(new_message2['message'] in fake_num_message_dict['910987654321'])


    @patch("modules.textlocalwrapper.request")
    def test_get_primary_inbox_messages(self, mock_request):
        textlocal = TextLocal(apikey='mock_key', primary_id='mock_id')
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


    @patch("modules.textlocalwrapper.request")
    def test_combine_messages(self, mock_request):
        textlocal = TextLocal(apikey='mock_key', primary_id='mock_id')
        not_combine = {'id': '000000024', 'number': 1112223334, 'message': 'Not combine', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'}
        also_not_combine = {'id': '00000449', 'number': 0, 'message': 'Also do not combine', 'date': '2017-08-05 21:11:07', 'isNew': None, 'status': '?'}
        combine_this = {'id': '00000450', 'number': 0, 'message': 'This message might just be long enough to be worth combining with the next message that comes up. Getting to 250+ characters is pretty hard though and requires concerted effort and a lot of mocked text to read. If you are expecting something cool you are looking in the wrong place.', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}
        with_this = {'id': '00000451', 'number': 0, 'message': 'This message should combine onto the prior one.', 'date': '2017-08-05 21:12:09', 'isNew': None, 'status': '?'}
        mock_request.urlopen.return_value = MockResponse(read_value=json.dumps({'messages': [not_combine, also_not_combine, combine_this, with_this]}).encode('latin1'))
        combine = {'id': with_this['id'],
                    'number': with_this['number'],
                    'message': combine_this['message'] + with_this['message'],
                    'date': with_this['date'],
                    'isNew': with_this['isNew'],
                    'status': with_this['status']}
        self.assertEqual(textlocal.combine_messages(textlocal.get_primary_inbox_messages()), [not_combine, also_not_combine, combine])


    def test_is_message_new(self):
        textlocal = TextLocal(apikey='mock_key', primary_id='mock_id')
        new_message = {'number': '910987654321', 'message': 'New message',
            'isNew': True}
        old_message = {'number': '910987654321', 'message': 'Old message',
            'isNew': None}
        self.assertTrue(textlocal.is_message_new(new_message))
        self.assertFalse(textlocal.is_message_new(old_message))


    def test_doesnt_correct_corrupted_unicode_matches_english(self):
        textlocal = TextLocal(apikey='mock_key', primary_id='mock_id')
        self.assertEqual(textlocal.correct_corrupted_unicode_matches("Here's a test"), "Here's a test")
        self.assertEqual(textlocal.correct_corrupted_unicode_matches("Remind Tina 09-12-10"), "Remind Tina 09-12-10")
        self.assertEqual(textlocal.correct_corrupted_unicode_matches("JOIN Tina 09-12-10"), "JOIN Tina 09-12-10")
        self.assertEqual(textlocal.correct_corrupted_unicode_matches("Remind Tina 09/12/10"), "Remind Tina 09/12/10")
        self.assertEqual(textlocal.correct_corrupted_unicode_matches("Remind Tina 09-09-10"), "Remind Tina 09-09-10")
        self.assertEqual(textlocal.correct_corrupted_unicode_matches("Remind Tina 09/09/10"), "Remind Tina 09/09/10")
        self.assertEqual(textlocal.correct_corrupted_unicode_matches("Remind Tina 09-09-09"), "Remind Tina 09-09-09")
        self.assertEqual(textlocal.correct_corrupted_unicode_matches("Remind Tina 09/09/09"), "Remind Tina 09/09/09")
        self.assertEqual(textlocal.correct_corrupted_unicode_matches("Remind Tina 09/09/09 "), "Remind Tina 09/09/09 ")
        self.assertEqual(textlocal.correct_corrupted_unicode_matches("Remind Tina 09/09/09  "), "Remind Tina 09/09/09  ")
        self.assertEqual(textlocal.correct_corrupted_unicode_matches("Remind Tina 09/09/09a!"), "Remind Tina 09/09/09a!")
        self.assertEqual(textlocal.correct_corrupted_unicode_matches("Remind Tina 08/09/09"), "Remind Tina 08/09/09")
        self.assertEqual(textlocal.correct_corrupted_unicode_matches("Remind Tina 09/07/09"), "Remind Tina 09/07/09")
        self.assertEqual(textlocal.correct_corrupted_unicode_matches("Remind Tina 08/07/04"), "Remind Tina 08/07/04")
        self.assertEqual(textlocal.correct_corrupted_unicode_matches("BORN Tina 08/07/14"), "BORN Tina 08/07/14")
        self.assertEqual(textlocal.correct_corrupted_unicode_matches("BORN Tina 08/07/2014"), "BORN Tina 08/07/2014")
        self.assertEqual(textlocal.correct_corrupted_unicode_matches("BORN Tina 08/07/2094"), "BORN Tina 08/07/2094")
        self.assertEqual(textlocal.correct_corrupted_unicode_matches("BORN Tina 08-07-2014"), "BORN Tina 08-07-2014")


    def test_correct_regex_matches_unicode(self):
        textlocal = TextLocal(apikey='mock_key', primary_id='mock_id')
        self.assertEqual(textlocal.correct_corrupted_unicode_matches("0907 test"), u"\u0907 test")
        self.assertEqual(textlocal.correct_corrupted_unicode_matches("096509430922 test"), u"\u0965\u0943\u0922 test")
        self.assertEqual(textlocal.correct_corrupted_unicode_matches("09070924094d0924093f0932093e Tina 09-12-10"), u"\u0907\u0924\u094d\u0924\u093f\u0932\u093e Tina 09-12-10")
        self.assertEqual(textlocal.correct_corrupted_unicode_matches("09070924094d0924093f0932093e 09070924094D 10-12-09"), u"\u0907\u0924\u094d\u0924\u093f\u0932\u093e \u0907\u0924\u094D 10-12-09")


    @patch("modules.textlocalwrapper.TextLocal.get_primary_inbox_messages")
    def test_correct_unicode_no_unicode(self, mock_primary_inbox_messages):
        textlocal = TextLocal(apikey='mock_key', primary_id='mock_id')
        mock_primary_inbox_messages.return_value = [{'id': '000000024', 'number': 1112223334, 'message': 'Testy test', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': 'Example message testy', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}]
        messages = textlocal.correct_unicode(textlocal.get_primary_inbox_messages())
        self.assertIsInstance(messages, list)
        self.assertEqual(messages, [{'id': '000000024', 'number': 1112223334, 'message': 'Testy test', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': 'Example message testy', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}])

        mock_primary_inbox_messages.return_value = [{'id': '000000024', 'number': 1112223334, 'message': 'Join Tina 10-09-10', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': 'Remind Tina 09-12-10', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': 'Remind Tina 10-12-09', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}]
        messages = textlocal.correct_unicode(textlocal.get_primary_inbox_messages())
        self.assertEqual(messages, [{'id': '000000024', 'number': 1112223334, 'message': 'Join Tina 10-09-10', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': 'Remind Tina 09-12-10', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': 'Remind Tina 10-12-09', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}])

        mock_primary_inbox_messages.return_value = [{'id': '000000024', 'number': 1112223334, 'message': 'Join Tina 10/09/10', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': 'Remind Tina 09/12/10', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': 'Remind Tina 10/12/09', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}]
        messages = textlocal.correct_unicode(textlocal.get_primary_inbox_messages())
        self.assertEqual(messages, [{'id': '000000024', 'number': 1112223334, 'message': 'Join Tina 10/09/10', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': 'Remind Tina 09/12/10', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': 'Remind Tina 10/12/09', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}])


    @patch("modules.textlocalwrapper.TextLocal.get_primary_inbox_messages")
    def test_correct_unicode_with_unicode(self, mock_primary_inbox_messages):
        textlocal = TextLocal(apikey='mock_key', primary_id='mock_id')
        mock_primary_inbox_messages.return_value = [{'id': '000000024', 'number': 1112223334, 'message': '0907 test', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': 'Example message testy', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}]
        messages = textlocal.correct_unicode(textlocal.get_primary_inbox_messages())
        self.assertIsInstance(messages, list)
        self.assertEqual(messages, [{'id': '000000024', 'number': 1112223334, 'message': u'\u0907 test', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': 'Example message testy', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}])

        mock_primary_inbox_messages.return_value = [{'id': '000000024', 'number': 1112223334, 'message': 'Example message two', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': '09B7 test', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}]
        messages = textlocal.correct_unicode(textlocal.get_primary_inbox_messages())
        self.assertEqual(messages, [{'id': '000000024', 'number': 1112223334, 'message': 'Example message two', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': u'\u09B7 test', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}])

        mock_primary_inbox_messages.return_value = [{'id': '000000024', 'number': 1112223334, 'message': u'\u0938\u094d\u092e\u0930\u0923 Tina 10-09-10', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': '0938094d092e09300923 Tina 09-12-10', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': '09070924094d0924093f0932093e Tina 10-12-09', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}]
        messages = textlocal.correct_unicode(textlocal.get_primary_inbox_messages())
        self.assertEqual(messages, [{'id': '000000024', 'number': 1112223334, 'message': u'\u0938\u094d\u092e\u0930\u0923 Tina 10-09-10', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': hindi_remind() + ' Tina 09-12-10', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': hindi_information() + ' Tina 10-12-09', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}])

        mock_primary_inbox_messages.return_value = [{'id': '000000024', 'number': 1112223334, 'message': 'Join Tina 10/09/10', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': 'Remind Tina 09/12/10', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': '09070924094d0924093f0932093e 090609300935 10/12/09', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': '09070924094d0924093f 0932093e 09070924094D 10-12-09', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}]
        messages = textlocal.correct_unicode(textlocal.get_primary_inbox_messages())
        self.assertEqual(messages, [{'id': '000000024', 'number': 1112223334, 'message': 'Join Tina 10/09/10', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': 'Remind Tina 09/12/10', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': hindi_information() + u' \u0906\u0930\u0935 10/12/09', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': u'\u0907\u0924\u094d\u0924\u093f \u0932\u093e \u0907\u0924\u094D 10-12-09', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}])
