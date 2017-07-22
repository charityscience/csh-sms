import mock
from mock import patch
from datetime import datetime
from django.test import TestCase

from modules.utils import quote
from modules.text_processor import TextProcessor
from modules.i18n import hindi_remind, hindi_information, msg_placeholder_child, \
                         msg_subscribe, msg_unsubscribe, msg_failure, msg_failed_date

class TextProcessorGetDataTests(TestCase):
    def test_all_caps(self):
        t = TextProcessor()
        keyword, child_name, date = t.get_data_from_message("REMIND NATHAN 25/11/2015")
        self.assertEqual(keyword, "remind")
        self.assertEqual(child_name, "nathan")
        self.assertEqual(date, datetime(2015, 11, 25, 0, 0).date())

    def test_all_lowercase(self):
        t = TextProcessor()
        keyword, child_name, date = t.get_data_from_message("remind nathan 25/11/2015")
        self.assertEqual(keyword, "remind")
        self.assertEqual(child_name, "nathan")
        self.assertEqual(date, datetime(2015, 11, 25, 0, 0).date())

    def test_normalcase(self):
        t = TextProcessor()
        keyword, child_name, date = t.get_data_from_message("Remind Nathan 25/11/2015")
        self.assertEqual(keyword, "remind")
        self.assertEqual(child_name, "nathan")
        self.assertEqual(date, datetime(2015, 11, 25, 0, 0).date())

    def test_date_short_year(self):
        t = TextProcessor()
        keyword, child_name, date = t.get_data_from_message("REMIND NATHAN 25/11/15")
        self.assertEqual(keyword, "remind")
        self.assertEqual(child_name, "nathan")
        self.assertEqual(date, datetime(2015, 11, 25, 0, 0).date())

    def test_date_hypen_separation(self):
        t = TextProcessor()
        keyword, child_name, date = t.get_data_from_message("REMIND NATHAN 25-11-2015")
        self.assertEqual(keyword, "remind")
        self.assertEqual(child_name, "nathan")
        self.assertEqual(date, datetime(2015, 11, 25, 0, 0).date())

    def test_join_keyword(self):
        t = TextProcessor()
        keyword, child_name, date = t.get_data_from_message("Join Charles 19/12/2012")
        self.assertEqual(keyword, "join")
        self.assertEqual(child_name, "charles")
        self.assertEqual(date, datetime(2012, 12, 19, 0, 0).date())

    def test_hindi_remind(self):
        t = TextProcessor()
        keyword, child_name, date = t.get_data_from_message(hindi_remind() + " Sai 11/09/2013")
        self.assertEqual(keyword, hindi_remind())
        self.assertEqual(child_name, "sai")
        self.assertEqual(date, datetime(2013, 9, 11, 0, 0).date())

    def test_hindi_remind_with_hindi_name(self):
        t = TextProcessor()
        keyword, child_name, date = t.get_data_from_message(hindi_remind() + " \xe0\xa4\x86\xe0\xa4\xb0\xe0\xa4\xb5 11/09/2013")
        self.assertEqual(keyword, hindi_remind())
        self.assertEqual(child_name, "\xe0\xa4\x86\xe0\xa4\xb0\xe0\xa4\xb5")
        self.assertEqual(date, datetime(2013, 9, 11, 0, 0).date())

    def test_hindi_information(self):
        t = TextProcessor()
        keyword, child_name, date = t.get_data_from_message(hindi_information() + " Sai 11/09/2013")
        self.assertEqual(keyword, hindi_information())
        self.assertEqual(child_name, "sai")
        self.assertEqual(date, datetime(2013, 9, 11, 0, 0).date())

    def test_no_child_name(self):
        t = TextProcessor()
        keyword, child_name, date = t.get_data_from_message("Remind 25/11/2015")
        self.assertEqual(keyword, "remind")
        self.assertEqual(child_name, None)
        self.assertEqual(date, datetime(2015, 11, 25, 0, 0).date())

    def test_stop(self):
        t = TextProcessor()
        keyword, child_name, date = t.get_data_from_message("STOP")
        self.assertEqual(keyword, "stop")
        self.assertEqual(child_name, None)
        self.assertEqual(date, None)


class TextProcessorProcessTests(TestCase):
    @patch("logging.info")
    @patch("modules.text_processor.send_text")  # See https://stackoverflow.com/questions/16134281/python-mocking-a-function-from-an-imported-module
    def test_subscribe(self, texting_mock, logging_mock):
        t = TextProcessor()
        response = t.process("JOIN PAULA 25-11-2012", "1-111-1111")
        # TODO: Test data is stored
        self.assertEqual(response, msg_subscribe("English").format(name="Paula"))
        logging_mock.assert_called_with("Subscribing `JOIN PAULA 25-11-2012`...")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")

    @patch("logging.info")
    @patch("modules.text_processor.send_text")
    def test_hindi_join(self, texting_mock, logging_mock):
        t = TextProcessor()
        response = t.process(hindi_remind() + " Sai 11/09/2013", "1-111-1111")
        # TODO: Test data is stored
        self.assertEqual(response, msg_subscribe("Hindi").format(name="Sai"))
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")

    @patch("logging.info")
    @patch("modules.text_processor.send_text")
    def test_hindi_join_with_hindi_name(self, texting_mock, logging_mock):
        t = TextProcessor()
        response = t.process(hindi_remind() + " \xe0\xa4\x86\xe0\xa4\xb0\xe0\xa4\xb5 11/09/2013", "1-111-1111")
        # TODO: Test data is stored
        self.assertEqual(response, msg_subscribe("Hindi").format(name="\xe0\xa4\x86\xe0\xa4\xb0\xe0\xa4\xb5"))
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")

    @patch("logging.info")
    @patch("modules.text_processor.send_text")
    def test_process_with_placeholder_child_english(self, texting_mock, logging_mock):
        t = TextProcessor()
        response = t.process("JOIN 25-11-2012", "1-111-1111")
        # TODO: Test data is stored
        self.assertEqual(response, msg_subscribe("English").format(name="Your child"))
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")

    @patch("logging.info")
    @patch("modules.text_processor.send_text")
    def test_process_with_placeholder_child_hindi(self, texting_mock, logging_mock):
        t = TextProcessor()
        response = t.process(hindi_remind() + " 25-11-2012", "1-111-1111")
        self.assertEqual(response,
                         msg_subscribe("Hindi").format(name=msg_placeholder_child("Hindi")))
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")

    @patch("logging.info")
    @patch("modules.text_processor.send_text")
    def test_unsubscribe_english(self, texting_mock, logging_mock):
        t = TextProcessor()
        response = t.process("STOP", "1-111-1111")
        # TODO: Test data is marked cancelled
        # TODO: Test in Hindi once Hindi can be triggered.
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
    def test_keyword_failed_date_english(self, texting_mock, logging_mock):
        t = TextProcessor()
        response = t.process("JOIN PAULA 25:11:2012", "1-111-1111")
        self.assertEqual(response, msg_failed_date("English"))
        logging_mock.assert_called_with("Date in message `JOIN PAULA 25:11:2012` is invalid.")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")

    @patch("logging.error")
    @patch("modules.text_processor.send_text")
    def test_keyword_failed_date_hindi(self, texting_mock, logging_mock):
        t = TextProcessor()
        invalid_text_message = hindi_remind() + " Sai 11,09,2013"
        response = t.process(invalid_text_message, "1-111-1111")
        self.assertEqual(response, msg_failed_date("Hindi"))
        logging_mock.assert_called_with("Date in message " + quote(invalid_text_message) + " is invalid.")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")

    @patch("logging.error")
    @patch("modules.text_processor.send_text")
    def test_keyword_failed_date_hindi_with_hindi_name(self, texting_mock, logging_mock):
        t = TextProcessor()
        invalid_text_message = hindi_remind() + " \xe0\xa4\x86\xe0\xa4\xb0\xe0\xa4\xb5 11,09,2013"
        response = t.process(invalid_text_message, "1-111-1111")
        self.assertEqual(response, msg_failed_date("Hindi"))
        logging_mock.assert_called_with("Date in message " + quote(invalid_text_message) + " is invalid.")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")
