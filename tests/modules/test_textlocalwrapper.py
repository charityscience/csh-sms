import mock
import json
from mock import patch
from freezegun import freeze_time
from django.test import TestCase
from datetime import datetime
from django.utils import timezone

from modules.textlocalwrapper import TextLocal
from modules.i18n import hindi_remind, hindi_information, msg_subscribe, msg_unsubscribe, \
                            msg_already_sub, six_week_reminder_one_day
from modules.date_helper import datetime_from_date_string
import six

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
        old_message_datetime = datetime_from_date_string(old_message['date'], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.get_default_timezone())
        new_message_datetime = datetime_from_date_string(new_message['date'], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.get_default_timezone())
        new_message2_datetime = datetime_from_date_string(new_message2['date'], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.get_default_timezone())
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
        old_message_datetime = datetime_from_date_string(old_message['datetime'], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.get_default_timezone())
        new_message_datetime = datetime_from_date_string(new_message['datetime'], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.get_default_timezone())
        new_message2_datetime = datetime_from_date_string(new_message2['datetime'], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.get_default_timezone())
        self.assertFalse((old_message['content'], old_message_datetime) in fake_num_message_dict['910987654321'])
        self.assertIsInstance(fake_num_message_dict['910987654321'][0], tuple)
        self.assertIsInstance(fake_num_message_dict['910987654321'][1], tuple)
        self.assertTrue((new_message['content'], new_message_datetime) in fake_num_message_dict['910987654321'])
        self.assertTrue((new_message2['content'], new_message2_datetime) in fake_num_message_dict['910987654321'])

    def test_add_to_num_message_dict_with_empty_dict(self):
        textlocal = TextLocal(apikey='mock_key', primary_id='mock_id', sendername='mock_sendername')
        new_message = {'number': '910987654321', 'message': 'New message', 'date': '2017-09-06 12:12:07', 'isNew': True}
        result = textlocal.add_to_num_message_dict(num_message_dict={},
                                                message=new_message,
                                                message_key_name="message",
                                                date_key_name="date")
        num_message_dict = {'910987654321': [('New message', datetime(2017, 9, 6, 12, 12, 7).replace(tzinfo=timezone.get_default_timezone()))]}
        self.assertEqual(result, num_message_dict)

    def test_add_to_num_message_dict_with_existing_dict(self):
        textlocal = TextLocal(apikey='mock_key', primary_id='mock_id', sendername='mock_sendername')
        new_message = {'number': '910987654321', 'message': 'New message', 'date': '2017-09-06 12:12:07', 'isNew': True}
        new_message2 = {'number': '910987654321', 'message': 'Newer message', 'date': '2017-09-06 21:12:07', 'isNew': True}
        first_add_result = textlocal.add_to_num_message_dict(num_message_dict={},
                                                message=new_message,
                                                message_key_name="message",
                                                date_key_name="date")
        second_add_result = textlocal.add_to_num_message_dict(num_message_dict=first_add_result,
                                                message=new_message2,
                                                message_key_name="message",
                                                date_key_name="date")
        two_adds_dict = {'910987654321': [('New message', datetime(2017, 9, 6, 12, 12, 7).replace(tzinfo=timezone.get_default_timezone())),
                                            ('Newer message', datetime(2017, 9, 6, 21, 12, 7).replace(tzinfo=timezone.get_default_timezone()))]}
        self.assertEqual(second_add_result, two_adds_dict)

    def test_add_to_num_message_dict_with_different_keynames(self):
        textlocal = TextLocal(apikey='mock_key', primary_id='mock_id', sendername='mock_sendername')
        new_message = {'number': '910987654321', 'message': 'New message', 'date': '2017-09-06 12:12:07', 'isNew': True}
        new_message2 = {'number': '910987654321', 'content': 'Newer message', 'datetime': '2017-09-06 21:12:07', 'isNew': True}

        first_add_result = textlocal.add_to_num_message_dict(num_message_dict={},
                                                message=new_message,
                                                message_key_name="message",
                                                date_key_name="date")
        second_add_result = textlocal.add_to_num_message_dict(num_message_dict=first_add_result,
                                                message=new_message2,
                                                message_key_name="content",
                                                date_key_name="datetime")
        two_adds_dict = {'910987654321': [('New message', datetime(2017, 9, 6, 12, 12, 7).replace(tzinfo=timezone.get_default_timezone())),
                                            ('Newer message', datetime(2017, 9, 6, 21, 12, 7).replace(tzinfo=timezone.get_default_timezone()))]}
        self.assertEqual(second_add_result, two_adds_dict)

        message_date_result = textlocal.add_to_num_message_dict(num_message_dict={},
                                                                message=new_message,
                                                                message_key_name="message",
                                                                date_key_name="date")

        num_message_dict = {'910987654321': [('New message', datetime(2017, 9, 6, 12, 12, 7).replace(tzinfo=timezone.get_default_timezone()))]}
        self.assertEqual(message_date_result, num_message_dict)
        content_datetime_result = textlocal.add_to_num_message_dict(num_message_dict={},
                                                                    message=new_message2,
                                                                    message_key_name="content",
                                                                    date_key_name="datetime")
        num_message_dict2 = {'910987654321': [('Newer message', datetime(2017, 9, 6, 21, 12, 7).replace(tzinfo=timezone.get_default_timezone()))]}
        self.assertEqual(content_datetime_result, num_message_dict2)

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

    def test_response_unicode_encoder(self):
        textlocal = TextLocal(apikey='mock_key', primary_id='mock_id', sendername='mock_sendername')
        hindi_unsub_response = "@U0906092A091509400020093809260938094D092F0924093E00200938092E093E092A094D092400200915093000200926094000200917092F0940002009390948002E"
        unsub_correction = textlocal.response_unicode_encoder(hindi_unsub_response)
        self.assertEqual(msg_unsubscribe("Hindi"), unsub_correction)
        hindi_already_sub_response = "@U0906092A0020092A093909320947002009380947002009390940002009380940002E090F0938002E091A00200938094D0935093E0938094D0925094D092F00200938094D092E093009230020092A094D0930093E092A094D09240020091509300928094700200915094700200932093F090F0020092A0902091C09400915094309240020093909480902002E"
        already_sub_correction = textlocal.response_unicode_encoder(hindi_already_sub_response)
        self.assertEqual(msg_already_sub("Hindi"), already_sub_correction)
        hindi_six_week_one_day_response_name_erin = "@U09050917093209470020003100200926093F09280020092E094709020020004500720069006E0020091509400020091C093C09300942093009400020091F09400915093E0915093009230020090509350936094D092F0020091509300935093E090F0901002E"
        six_week_one_day_response = textlocal.response_unicode_encoder(hindi_six_week_one_day_response_name_erin)
        self.assertEqual(six_week_reminder_one_day("Hindi").format(name="Erin"), six_week_one_day_response)

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