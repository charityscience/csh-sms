import mock
import json
from mock import patch
from freezegun import freeze_time
from django.test import TestCase
from datetime import datetime

from modules.textlocalwrapper import TextLocal
from modules.i18n import hindi_remind, hindi_information, msg_subscribe
from modules.date_helper import datetime_from_date_string

class MockResponse():
    def __init__(self, read_value):
        self.read_value = read_value

    def read(self):
        return self.read_value


class TextLocalInboxesTests(TestCase):
    def test_create_object(self):
        textlocal = TextLocal(apikey='mock_key', primary_id='mock_id', sendername='mock_sendername')
        self.assertIsInstance(textlocal, TextLocal)

    @freeze_time(datetime(2017, 7, 30, 15, 0, 0))
    def test_is_message_new_with_isnew_true_or_falsey(self):
        textlocal = TextLocal(apikey='mock_key', primary_id='mock_id', sendername='mock_sendername')
        new_message_with_new_flag = {'number': '910987654321', 'message': 'New message',
            'isNew': True, 'date': '2017-07-30 06:52:09'}
        new_message_with_no_new_flag = {'number': '910987654321', 'message': 'New message',
            'isNew': None, 'date': '2017-07-30 06:52:09'}
        old_message_with_new_flag = {'number': '910987654321', 'message': 'Old message',
            'isNew': True, 'date': '2017-07-29 06:52:09'}
        old_message_with_no_new_flag = {'number': '910987654321', 'message': 'Old message',
            'isNew': None, 'date': '2017-07-29 06:52:09'}
        self.assertTrue(textlocal.is_message_new(message=new_message_with_new_flag, date_key_name="date"))
        self.assertTrue(textlocal.is_message_new(message=new_message_with_no_new_flag, date_key_name="date"))
        self.assertFalse(textlocal.is_message_new(message=old_message_with_new_flag, date_key_name="date"))
        self.assertFalse(textlocal.is_message_new(message=old_message_with_no_new_flag, date_key_name="date"))

    @freeze_time(datetime(2017, 7, 30, 15, 0, 0))
    def test_is_message_new_with_different_keynames(self):
        textlocal = TextLocal(apikey='mock_key', primary_id='mock_id', sendername='mock_sendername')
        new_message_with_date_key = {'number': '910987654321', 'message': 'New message',
            'isNew': True, 'date': '2017-07-30 06:52:09'}
        new_message_with_datetime_key = {'number': '910987654321', 'message': 'New message',
            'isNew': None, 'datetime': '2017-07-30 06:52:09'}
        old_message_with_date_key = {'number': '910987654321', 'message': 'Old message',
            'isNew': True, 'date': '2017-07-29 06:52:09'}
        old_message_with_datetime_key = {'number': '910987654321', 'message': 'Old message',
            'isNew': None, 'datetime': '2017-07-29 06:52:09'}
        self.assertTrue(textlocal.is_message_new(message=new_message_with_date_key, date_key_name="date"))
        self.assertTrue(textlocal.is_message_new(message=new_message_with_datetime_key, date_key_name="datetime"))
        with self.assertRaises(KeyError):
            textlocal.is_message_new(message=new_message_with_date_key, date_key_name="datetime")
        with self.assertRaises(KeyError):
            textlocal.is_message_new(message=new_message_with_datetime_key, date_key_name="date")
            
        self.assertFalse(textlocal.is_message_new(message=old_message_with_date_key, date_key_name="date"))
        self.assertFalse(textlocal.is_message_new(message=old_message_with_datetime_key, date_key_name="datetime"))

    @freeze_time(datetime(2017, 7, 30, 15, 0, 0))
    def test_is_message_new_with_dates_within_one_day(self):
        textlocal = TextLocal(apikey='mock_key', primary_id='mock_id', sendername='mock_sendername')
        same_time = {'number': '910987654321', 'message': 'New message',
            'isNew': True, 'date': '2017-07-30 15:00:00'}
        one_second_before = {'number': '910987654321', 'message': 'New message',
                    'isNew': True, 'date': '2017-07-30 14:59:59'}
        one_minute_before = {'number': '910987654321', 'message': 'New message',
                    'isNew': True, 'date': '2017-07-30 14:59:00'}
        one_hour_before = {'number': '910987654321', 'message': 'New message',
                    'isNew': True, 'date': '2017-07-30 14:00:00'}
        twelve_hours_before = {'number': '910987654321', 'message': 'New message',
            'isNew': True, 'date': '2017-07-30 03:00:00'}
        twenty_four_hours_before = {'number': '910987654321', 'message': 'New message',
            'isNew': True, 'date': '2017-07-29 15:00:00'}

        self.assertTrue(textlocal.is_message_new(message=same_time, date_key_name="date"))
        self.assertTrue(textlocal.is_message_new(message=one_second_before, date_key_name="date"))
        self.assertTrue(textlocal.is_message_new(message=one_minute_before, date_key_name="date"))
        self.assertTrue(textlocal.is_message_new(message=one_hour_before, date_key_name="date"))
        self.assertTrue(textlocal.is_message_new(message=twelve_hours_before, date_key_name="date"))
        self.assertTrue(textlocal.is_message_new(message=twenty_four_hours_before, date_key_name="date"))

    @freeze_time(datetime(2017, 7, 30, 15, 0, 0))
    def test_is_message_new_with_dates_before_one_day(self):
        textlocal = TextLocal(apikey='mock_key', primary_id='mock_id', sendername='mock_sendername')
        twenty_four_hours_one_second_before = {'number': '910987654321', 'message': 'New message',
                    'isNew': True, 'date': '2017-07-29 14:59:59'}
        twenty_four_hours_five_minutes_before = {'number': '910987654321', 'message': 'New message',
                    'isNew': True, 'date': '2017-07-29 14:55:00'}
        twenty_five_hours_before = {'number': '910987654321', 'message': 'New message',
                    'isNew': True, 'date': '2017-07-29 14:00:00'}
        thirty_six_hours_before = {'number': '910987654321', 'message': 'New message',
            'isNew': True, 'date': '2017-07-29 03:00:00'}
        forty_eight_hours_before = {'number': '910987654321', 'message': 'New message',
            'isNew': True, 'date': '2017-07-28 15:00:00'}
        one_week_before = {'number': '910987654321', 'message': 'New message',
            'isNew': True, 'date': '2017-07-23 15:00:00'}
        one_month_before = {'number': '910987654321', 'message': 'New message',
            'isNew': True, 'date': '2017-06-30 15:00:00'}
        one_year_before = {'number': '910987654321', 'message': 'New message',
            'isNew': True, 'date': '2016-07-30 15:00:00'}
        
        self.assertFalse(textlocal.is_message_new(message=twenty_four_hours_one_second_before, date_key_name="date"))
        self.assertFalse(textlocal.is_message_new(message=twenty_four_hours_five_minutes_before, date_key_name="date"))
        self.assertFalse(textlocal.is_message_new(message=twenty_five_hours_before, date_key_name="date"))
        self.assertFalse(textlocal.is_message_new(message=thirty_six_hours_before, date_key_name="date"))
        self.assertFalse(textlocal.is_message_new(message=forty_eight_hours_before, date_key_name="date"))
        self.assertFalse(textlocal.is_message_new(message=one_week_before, date_key_name="date"))
        self.assertFalse(textlocal.is_message_new(message=one_month_before, date_key_name="date"))
        self.assertFalse(textlocal.is_message_new(message=one_year_before, date_key_name="date"))

    @freeze_time(datetime(2017, 9, 6, 22, 0, 0))
    @patch("modules.textlocalwrapper.request")
    def test_new_messages_by_number_returns_message_and_datetime(self, mock_request):
        textlocal = TextLocal(apikey='mock_key', primary_id='mock_id', sendername='mock_sendername')
        old_message = {'number': '910987654321', 'message': 'Old message', 'date': '2017-08-05 21:12:07', 'isNew': None}
        new_message = {'number': '910987654321', 'message': 'New message', 'date': '2017-09-06 12:12:07', 'isNew': True}
        new_message2 = {'number': '910987654321', 'message': 'Newer message', 'date': '2017-09-06 21:12:07', 'isNew': True}
        mock_request.urlopen.return_value = MockResponse(read_value=json.dumps({'messages': [new_message, new_message2, old_message]}).encode('latin1'))
        fake_num_message_dict = textlocal.new_messages_by_number()
        self.assertIsInstance(fake_num_message_dict, dict)
        self.assertIsInstance(fake_num_message_dict['910987654321'], list)
        old_message_datetime = datetime_from_date_string(old_message['date'], "%Y-%m-%d %H:%M:%S")
        new_message_datetime = datetime_from_date_string(new_message['date'], "%Y-%m-%d %H:%M:%S")
        new_message2_datetime = datetime_from_date_string(new_message2['date'], "%Y-%m-%d %H:%M:%S")
        self.assertFalse((old_message['message'], old_message_datetime) in fake_num_message_dict['910987654321'])
        self.assertIsInstance(fake_num_message_dict['910987654321'][0], tuple)
        self.assertIsInstance(fake_num_message_dict['910987654321'][1], tuple)
        self.assertTrue((new_message['message'], new_message_datetime) in fake_num_message_dict['910987654321'])
        self.assertTrue((new_message2['message'], new_message2_datetime) in fake_num_message_dict['910987654321'])

    @freeze_time(datetime(2017, 9, 6, 22, 0, 0))
    @patch("modules.textlocalwrapper.request")
    def test_new_api_send_messages_by_number_returns_message_and_datetime(self, mock_request):
        textlocal = TextLocal(apikey='mock_key', primary_id='mock_id', sendername='mock_sendername')
        old_message = {'number': '910987654321', 'content': 'Old message', 'datetime': '2017-08-05 21:12:07', 'isNew': None}
        new_message = {'number': '910987654321', 'content': 'New message', 'datetime': '2017-09-06 12:12:07', 'isNew': True}
        new_message2 = {'number': '910987654321', 'content': 'Newer message', 'datetime': '2017-09-06 21:12:07', 'isNew': True}
        mock_request.urlopen.return_value = MockResponse(read_value=json.dumps({'messages': [new_message, new_message2, old_message]}).encode('latin1'))
        fake_num_message_dict = textlocal.new_api_send_messages_by_number()
        self.assertIsInstance(fake_num_message_dict, dict)
        self.assertIsInstance(fake_num_message_dict['910987654321'], list)
        old_message_datetime = datetime_from_date_string(old_message['datetime'], "%Y-%m-%d %H:%M:%S")
        new_message_datetime = datetime_from_date_string(new_message['datetime'], "%Y-%m-%d %H:%M:%S")
        new_message2_datetime = datetime_from_date_string(new_message2['datetime'], "%Y-%m-%d %H:%M:%S")
        self.assertFalse((old_message['content'], old_message_datetime) in fake_num_message_dict['910987654321'])
        self.assertIsInstance(fake_num_message_dict['910987654321'][0], tuple)
        self.assertIsInstance(fake_num_message_dict['910987654321'][1], tuple)
        self.assertTrue((new_message['content'], new_message_datetime) in fake_num_message_dict['910987654321'])
        self.assertTrue((new_message2['content'], new_message2_datetime) in fake_num_message_dict['910987654321'])

    @patch("modules.textlocalwrapper.request")
    def test_get_primary_inbox_messages(self, mock_request):
        textlocal = TextLocal(apikey='mock_key', primary_id='mock_id', sendername='mock_sendername')
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

    def test_doesnt_correct_corrupted_unicode_matches_english(self):
        textlocal = TextLocal(apikey='mock_key', primary_id='mock_id', sendername='mock_sendername')
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
        self.assertEqual(textlocal.correct_corrupted_unicode_matches(msg_subscribe("English").format(name="Paul")),
                                                                     msg_subscribe("English").format(name="Paul"))


    def test_correct_regex_matches_unicode(self):
        textlocal = TextLocal(apikey='mock_key', primary_id='mock_id', sendername='mock_sendername')
        self.assertEqual(textlocal.correct_corrupted_unicode_matches("0907 test"), u"\u0907 test")
        self.assertEqual(textlocal.correct_corrupted_unicode_matches("096509430922 test"), u"\u0965\u0943\u0922 test")
        self.assertEqual(textlocal.correct_corrupted_unicode_matches("09070924094d0924093f0932093e Tina 09-12-10"), u"\u0907\u0924\u094d\u0924\u093f\u0932\u093e Tina 09-12-10")
        self.assertEqual(textlocal.correct_corrupted_unicode_matches("09070924094d0924093f0932093e 09070924094D 10-12-09"), u"\u0907\u0924\u094d\u0924\u093f\u0932\u093e \u0907\u0924\u094D 10-12-09")


    @patch("modules.textlocalwrapper.TextLocal.get_primary_inbox_messages")
    def test_correct_unicode_no_unicode(self, mock_primary_inbox_messages):
        textlocal = TextLocal(apikey='mock_key', primary_id='mock_id', sendername='mock_sendername')
        mock_primary_inbox_messages.return_value = [{'id': '000000024', 'number': 1112223334, 'message': 'Testy test', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': 'Example message testy', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}]
        messages = textlocal.correct_unicode(messages=textlocal.get_primary_inbox_messages(), key_name="message")
        self.assertIsInstance(messages, list)
        self.assertEqual(messages, [{'id': '000000024', 'number': 1112223334, 'message': 'Testy test', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': 'Example message testy', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}])

        mock_primary_inbox_messages.return_value = [{'id': '000000024', 'number': 1112223334, 'message': 'Join Tina 10-09-10', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': 'Remind Tina 09-12-10', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': 'Remind Tina 10-12-09', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}]
        messages = textlocal.correct_unicode(messages=textlocal.get_primary_inbox_messages(), key_name="message")
        self.assertEqual(messages, [{'id': '000000024', 'number': 1112223334, 'message': 'Join Tina 10-09-10', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': 'Remind Tina 09-12-10', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': 'Remind Tina 10-12-09', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}])

        mock_primary_inbox_messages.return_value = [{'id': '000000024', 'number': 1112223334, 'message': 'Join Tina 10/09/10', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': 'Remind Tina 09/12/10', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': 'Remind Tina 10/12/09', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}]
        messages = textlocal.correct_unicode(messages=textlocal.get_primary_inbox_messages(), key_name="message")
        self.assertEqual(messages, [{'id': '000000024', 'number': 1112223334, 'message': 'Join Tina 10/09/10', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': 'Remind Tina 09/12/10', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': 'Remind Tina 10/12/09', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}])


    @patch("modules.textlocalwrapper.TextLocal.get_primary_inbox_messages")
    def test_correct_unicode_with_unicode(self, mock_primary_inbox_messages):
        textlocal = TextLocal(apikey='mock_key', primary_id='mock_id', sendername='mock_sendername')
        mock_primary_inbox_messages.return_value = [{'id': '000000024', 'number': 1112223334, 'message': '0907 test', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': 'Example message testy', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}]
        messages = textlocal.correct_unicode(messages=textlocal.get_primary_inbox_messages(), key_name="message")
        self.assertIsInstance(messages, list)
        self.assertEqual(messages, [{'id': '000000024', 'number': 1112223334, 'message': u'\u0907 test', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': 'Example message testy', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}])

        mock_primary_inbox_messages.return_value = [{'id': '000000024', 'number': 1112223334, 'message': 'Example message two', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': '09B7 test', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}]
        messages = textlocal.correct_unicode(messages=textlocal.get_primary_inbox_messages(), key_name="message")
        self.assertEqual(messages, [{'id': '000000024', 'number': 1112223334, 'message': 'Example message two', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': u'\u09B7 test', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}])

        mock_primary_inbox_messages.return_value = [{'id': '000000024', 'number': 1112223334, 'message': u'\u0938\u094d\u092e\u0930\u0923 Tina 10-09-10', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': '0938094d092e09300923 Tina 09-12-10', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': '09070924094d0924093f0932093e Tina 10-12-09', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}]
        messages = textlocal.correct_unicode(messages=textlocal.get_primary_inbox_messages(), key_name="message")
        self.assertEqual(messages, [{'id': '000000024', 'number': 1112223334, 'message': u'\u0938\u094d\u092e\u0930\u0923 Tina 10-09-10', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': hindi_remind() + ' Tina 09-12-10', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': hindi_information() + ' Tina 10-12-09', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}])

        mock_primary_inbox_messages.return_value = [{'id': '000000024', 'number': 1112223334, 'message': 'Join Tina 10/09/10', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': 'Remind Tina 09/12/10', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': '09070924094d0924093f0932093e 090609300935 10/12/09', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': '09070924094d0924093f 0932093e 09070924094D 10-12-09', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}]
        messages = textlocal.correct_unicode(messages=textlocal.get_primary_inbox_messages(), key_name="message")
        self.assertEqual(messages, [{'id': '000000024', 'number': 1112223334, 'message': 'Join Tina 10/09/10', 'date': '2017-07-30 06:52:09', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': 'Remind Tina 09/12/10', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': hindi_information() + u' \u0906\u0930\u0935 10/12/09', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'},
            {'id': '00000449', 'number': 0, 'message': u'\u0907\u0924\u094d\u0924\u093f \u0932\u093e \u0907\u0924\u094D 10-12-09', 'date': '2017-08-05 21:12:07', 'isNew': None, 'status': '?'}])

    @patch("modules.textlocalwrapper.request")
    def test_send_message(self, mock_request):
        class MockResponse():
            def read(self):
                return json.dumps({'message': 'yay'}).encode('latin1')
        mock_request.urlopen.return_value = MockResponse()
        tl = TextLocal(apikey='mock_key',
                        primary_id='mock_id',
                        sendername='mock_sendername')
        response = tl.send_message(message='Test',
                                    phone_numbers='0000000')
        self.assertEqual(response['message'], 'yay')

    @patch("modules.textlocalwrapper.request")
    def test_send_message_hindi(self, mock_request):
        class MockResponse():
            def read(self):
                return json.dumps({'message': hindi_remind()}).encode('latin1')
        mock_request.urlopen.return_value = MockResponse()
        tl = TextLocal(apikey='mock_key',
                        primary_id='mock_id',
                        sendername='mock_sendername')
        response = tl.send_message(message='Test',
                                    phone_numbers='0000000')
        self.assertEqual(response['message'], hindi_remind())