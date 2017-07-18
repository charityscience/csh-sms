import mock
from mock import patch
from datetime import datetime
from django.test import TestCase

from modules.text_processor import TextProcessor
from modules.i18n import hindi_remind, hindi_information, msg_placeholder_child, \
                         msg_subscribe, msg_unsubscribe, msg_failure, msg_failed_date

class TextProcessorGetDataTests(TestCase):
    def test_all_caps(self):
        t = TextProcessor()
        keyword, child_name, date = t.get_data_from_message("REMIND NATHAN 25/11/2015")
        self.assertEqual(keyword, "remind")
        self.assertEqual(child_name, "nathan")
        self.assertEqual(date, datetime(2015, 11, 25, 0, 0))

    def test_all_lowercase(self):
        t = TextProcessor()
        keyword, child_name, date = t.get_data_from_message("remind nathan 25/11/2015")
        self.assertEqual(keyword, "remind")
        self.assertEqual(child_name, "nathan")
        self.assertEqual(date, datetime(2015, 11, 25, 0, 0))

    def test_normalcase(self):
        t = TextProcessor()
        keyword, child_name, date = t.get_data_from_message("Remind Nathan 25/11/2015")
        self.assertEqual(keyword, "remind")
        self.assertEqual(child_name, "nathan")
        self.assertEqual(date, datetime(2015, 11, 25, 0, 0))

    def test_date_short_year(self):
        t = TextProcessor()
        keyword, child_name, date = t.get_data_from_message("REMIND NATHAN 25/11/15")
        self.assertEqual(keyword, "remind")
        self.assertEqual(child_name, "nathan")
        self.assertEqual(date, datetime(2015, 11, 25, 0, 0))

    def test_date_hypen_separation(self):
        t = TextProcessor()
        keyword, child_name, date = t.get_data_from_message("REMIND NATHAN 25-11-2015")
        self.assertEqual(keyword, "remind")
        self.assertEqual(child_name, "nathan")
        self.assertEqual(date, datetime(2015, 11, 25, 0, 0))

    def test_join_keyword(self):
        t = TextProcessor()
        keyword, child_name, date = t.get_data_from_message("Join Charles 19/12/2012")
        self.assertEqual(keyword, "join")
        self.assertEqual(child_name, "charles")
        self.assertEqual(date, datetime(2012, 12, 19, 0, 0))

    def test_hindi_remind(self):
        t = TextProcessor()
        keyword, child_name, date = t.get_data_from_message(hindi_remind() + " Sai 11/09/2013")
        self.assertEqual(keyword, hindi_remind())
        self.assertEqual(child_name, "sai")
        self.assertEqual(date, datetime(2013, 9, 11, 0, 0))

    def test_hindi_information(self):
        t = TextProcessor()
        keyword, child_name, date = t.get_data_from_message(hindi_information() + " Sai 11/09/2013")
        self.assertEqual(keyword, hindi_information())
        self.assertEqual(child_name, "sai")
        self.assertEqual(date, datetime(2013, 9, 11, 0, 0))

    def test_no_child_name(self):
        t = TextProcessor()
        keyword, child_name, date = t.get_data_from_message("Remind 25/11/2015")
        self.assertEqual(keyword, "remind")
        self.assertEqual(child_name, None)
        self.assertEqual(date, datetime(2015, 11, 25, 0, 0))

    def test_stop(self):
        t = TextProcessor()
        keyword, child_name, date = t.get_data_from_message("STOP")
        self.assertEqual(keyword, "stop")
        self.assertEqual(child_name, None)
        self.assertEqual(date, None)


class TextProcessorPlaceholerChildTests(TestCase):
    @patch("logging.error")
    def test_placeholder_child(self, mock):
        t = TextProcessor()
        self.assertEqual(msg_placeholder_child("English"), t.get_placeholder_child("English"))
        self.assertEqual(msg_placeholder_child("Hindi"), t.get_placeholder_child("Hindi"))
        self.assertEqual(msg_placeholder_child("Gujarati"), t.get_placeholder_child("Gujarati"))
        self.assertTrue(not mock.called)
        
    @patch("logging.error")
    def test_missing_language(self, mock):
        t = TextProcessor()
        self.assertEqual(t.get_placeholder_child("Bogus"), msg_placeholder_child("English"))
        mock.assert_called_with("A placeholder child name was requested for language `Bogus` but this is not supported.")


class TextProcessorProcessTests(TestCase):
    @patch("logging.info")
    @patch("modules.text_processor.send_text")  # See https://stackoverflow.com/questions/16134281/python-mocking-a-function-from-an-imported-module
    def test_subscribe(self, texting_mock, logging_mock):
        t = TextProcessor()
        response = t.process("JOIN PAULA 25-11-2012", "1-111-1111")
        # TODO: Test data is stored
        self.assertEqual(response, "Paula " + msg_subscribe("English"))
        logging_mock.assert_called_with("Subscribing `JOIN PAULA 25-11-2012`...")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")

    @patch("logging.info")
    @patch("modules.text_processor.send_text")
    def test_hindi_join(self, texting_mock, logging_mock):
        t = TextProcessor()
        response = t.process(hindi_remind() + " Sai 11/09/2013", "1-111-1111")
        # TODO: Test data is stored
        self.assertEqual(response, "Sai " + msg_subscribe("Hindi"))
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")

    @patch("logging.info")
    @patch("modules.text_processor.send_text")
    def test_process_with_placeholder_child(self, texting_mock, logging_mock):
        t = TextProcessor()
        response = t.process("JOIN 25-11-2012", "1-111-1111")
        # TODO: Test data is stored
        self.assertEqual(response, "Your child " + msg_subscribe("English"))
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")

    @patch("logging.info")
    @patch("modules.text_processor.send_text")
    def test_unsubscribe(self, texting_mock, logging_mock):
        t = TextProcessor()
        response = t.process("STOP", "1-111-1111")
        # TODO: Test data is removed
        self.assertEqual(response, msg_unsubscribe("English"))
        logging_mock.assert_called_with("Unsubscribing `STOP`...")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")

    @patch("logging.error")
    @patch("modules.text_processor.send_text")
    def test_keyword_failure(self, texting_mock, logging_mock):
        t = TextProcessor()
        response = t.process("JLORN COACHZ 25-11-2012", "1-111-1111")
        self.assertEqual(response, msg_failure("English"))
        logging_mock.assert_called_with("Keyword `jlorn` in message `JLORN COACHZ 25-11-2012` was not understood by the system.")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")

    @patch("logging.error")
    @patch("modules.text_processor.send_text")
    def test_keyword_failure_hindi(self, texting_mock, logging_mock):
        t = TextProcessor()
        response = t.process("\xe0\xa4 \xe0\xa4\x95\xe0 25-11-2012", "1-111-1111")
        self.assertEqual(response, msg_failure("Hindi"))
        logging_mock.assert_called_with("Keyword `\xe0\xa4` in message `\xe0\xa4 \xe0\xa4\x95\xe0 25-11-2012` was not understood by the system.")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")

    @patch("logging.error")
    @patch("modules.text_processor.send_text")
    def test_keyword_failed_date(self, texting_mock, logging_mock):
        t = TextProcessor()
        response = t.process("JOIN PAULA 25:11:2012", "1-111-1111")
        self.assertEqual(response, msg_failed_date("English"))
        logging_mock.assert_called_with("Date in message `JOIN PAULA 25:11:2012` is invalid.")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")
