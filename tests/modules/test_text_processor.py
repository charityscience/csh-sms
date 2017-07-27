from mock import patch
from datetime import datetime
from django.test import TestCase

from management.models import Contact
from modules.utils import quote
from modules.text_processor import TextProcessor
from modules.i18n import hindi_remind, hindi_information, msg_placeholder_child, \
                         msg_subscribe, msg_unsubscribe, msg_failure, msg_failed_date, \
                         msg_already_sub

class TextProcessorGetDataTests(TestCase):
    def test_all_caps(self):
        t = TextProcessor(phone_number="1-111-1111")
        keyword, child_name, date = t.get_data_from_message("REMIND NATHAN 25/11/2015")
        self.assertEqual(keyword, "remind")
        self.assertEqual(child_name, "nathan")
        self.assertEqual(date, datetime(2015, 11, 25, 0, 0).date())

    def test_all_lowercase(self):
        t = TextProcessor(phone_number="1-111-1111")
        keyword, child_name, date = t.get_data_from_message("remind nathan 25/11/2015")
        self.assertEqual(keyword, "remind")
        self.assertEqual(child_name, "nathan")
        self.assertEqual(date, datetime(2015, 11, 25, 0, 0).date())

    def test_normalcase(self):
        t = TextProcessor(phone_number="1-111-1111")
        keyword, child_name, date = t.get_data_from_message("Remind Nathan 25/11/2015")
        self.assertEqual(keyword, "remind")
        self.assertEqual(child_name, "nathan")
        self.assertEqual(date, datetime(2015, 11, 25, 0, 0).date())

    def test_date_short_year(self):
        t = TextProcessor(phone_number="1-111-1111")
        keyword, child_name, date = t.get_data_from_message("REMIND NATHAN 25/11/15")
        self.assertEqual(keyword, "remind")
        self.assertEqual(child_name, "nathan")
        self.assertEqual(date, datetime(2015, 11, 25, 0, 0).date())

    def test_date_hypen_separation(self):
        t = TextProcessor(phone_number="1-111-1111")
        keyword, child_name, date = t.get_data_from_message("REMIND NATHAN 25-11-2015")
        self.assertEqual(keyword, "remind")
        self.assertEqual(child_name, "nathan")
        self.assertEqual(date, datetime(2015, 11, 25, 0, 0).date())

    def test_join_keyword(self):
        t = TextProcessor(phone_number="1-111-1111")
        keyword, child_name, date = t.get_data_from_message("Join Charles 19/12/2012")
        self.assertEqual(keyword, "join")
        self.assertEqual(child_name, "charles")
        self.assertEqual(date, datetime(2012, 12, 19, 0, 0).date())

    def test_hindi_remind(self):
        t = TextProcessor(phone_number="1-111-1111")
        keyword, child_name, date = t.get_data_from_message(hindi_remind() + " Sai 11/09/2013")
        self.assertEqual(keyword, hindi_remind())
        self.assertEqual(child_name, "sai")
        self.assertEqual(date, datetime(2013, 9, 11, 0, 0).date())

    def test_hindi_remind_with_hindi_name(self):
        t = TextProcessor(phone_number="1-111-1111")
        keyword, child_name, date = t.get_data_from_message(hindi_remind() + u' \u0906\u0930\u0935 11/09/2013')
        self.assertEqual(keyword, hindi_remind())
        self.assertEqual(child_name, u'\u0906\u0930\u0935')
        self.assertEqual(date, datetime(2013, 9, 11, 0, 0).date())

    def test_hindi_information(self):
        t = TextProcessor(phone_number="1-111-1111")
        keyword, child_name, date = t.get_data_from_message(hindi_information() + " Sai 11/09/2013")
        self.assertEqual(keyword, hindi_information())
        self.assertEqual(child_name, "sai")
        self.assertEqual(date, datetime(2013, 9, 11, 0, 0).date())

    def test_no_child_name(self):
        t = TextProcessor(phone_number="1-111-1111")
        keyword, child_name, date = t.get_data_from_message("Remind 25/11/2015")
        self.assertEqual(keyword, "remind")
        self.assertEqual(child_name, None)
        self.assertEqual(date, datetime(2015, 11, 25, 0, 0).date())

    def test_stop(self):
        t = TextProcessor(phone_number="1-111-1111")
        keyword, child_name, date = t.get_data_from_message("STOP")
        self.assertEqual(keyword, "stop")
        self.assertEqual(child_name, None)
        self.assertEqual(date, None)


class TextProcessorProcessTests(TestCase):
    @patch("logging.info")
    @patch("modules.text_processor.Texter.send")  # See https://stackoverflow.com/questions/16134281/python-mocking-a-function-from-an-imported-module
    def test_subscribe(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1111")
        self.assertFalse(Contact.objects.filter(name="Paula", phone_number="1-111-1111").exists())
        self.assertFalse(t.get_contacts().exists())
        response = t.process("JOIN PAULA 25-11-2012")
        self.assertEqual(response, msg_subscribe("English").format(name="Paula"))
        logging_mock.assert_called_with("Subscribing `JOIN PAULA 25-11-2012`...")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")
        self.assertTrue(Contact.objects.filter(name="Paula", phone_number="1-111-1111").exists())
        self.assertTrue(t.get_contacts().exists())
        actual_groups = [str(g) for g in t.get_contacts().first().group_set.all()]
        expected_groups = ['Everyone - English', 'Text Sign Ups', 'Text Sign Ups - English']
        self.assertEqual(actual_groups, expected_groups)

    @patch("logging.info")
    @patch("modules.text_processor.Texter.send")
    def test_hindi_join(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-112-1111")
        self.assertFalse(Contact.objects.filter(name="Sai", phone_number="1-112-1111").exists())
        self.assertFalse(t.get_contacts().exists())
        response = t.process(hindi_remind() + " Sai 11/09/2013")
        self.assertEqual(response, msg_subscribe("Hindi").format(name="Sai"))
        texting_mock.assert_called_once_with(message=response, phone_number="1-112-1111")
        self.assertTrue(Contact.objects.filter(name="Sai", phone_number="1-112-1111").exists())
        self.assertTrue(t.get_contacts().exists())

    @patch("logging.info")
    @patch("modules.text_processor.Texter.send")
    def test_hindi_join_with_hindi_name(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-112-1112")
        message = hindi_remind() + u' \u0906\u0930\u0935 11/09/2013'
        self.assertFalse(Contact.objects.filter(name=u'\u0906\u0930\u0935',
                                                phone_number="1-112-1112").exists())
        self.assertFalse(t.get_contacts().exists())
        response = t.process(message=message)
        expected_response = msg_subscribe('Hindi').format(name=u'\u0906\u0930\u0935')
        self.assertEqual(response, expected_response)
        texting_mock.assert_called_once_with(message=response, phone_number="1-112-1112")
        self.assertTrue(Contact.objects.filter(name=u'\u0906\u0930\u0935',
                                               phone_number="1-112-1112").exists())
        self.assertTrue(t.get_contacts().exists())

    @patch("logging.info")
    @patch("modules.text_processor.Texter.send")
    def test_process_with_placeholder_child_english(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1113")
        self.assertFalse(Contact.objects.filter(name=msg_placeholder_child("English"),
                                                phone_number="1-111-1113").exists())
        self.assertFalse(t.get_contacts().exists())
        response = t.process("JOIN 25-11-2012")
        self.assertEqual(response, msg_subscribe("English").format(name=msg_placeholder_child("English")))
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1113")
        self.assertTrue(Contact.objects.filter(name=msg_placeholder_child("English"),
                                               phone_number="1-111-1113").exists())
        self.assertTrue(t.get_contacts().exists())

    @patch("logging.info")
    @patch("modules.text_processor.Texter.send")
    def test_process_with_placeholder_child_hindi(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-112-1113")
        self.assertFalse(Contact.objects.filter(name=msg_placeholder_child("Hindi"),
                                                phone_number="1-112-1113").exists())
        self.assertFalse(t.get_contacts().exists())
        response = t.process(hindi_remind() + " 25-11-2012")
        self.assertEqual(response,
                         msg_subscribe("Hindi").format(name=msg_placeholder_child("Hindi")))
        texting_mock.assert_called_once_with(message=response, phone_number="1-112-1113")
        self.assertTrue(Contact.objects.filter(name=msg_placeholder_child("Hindi"),
                                               phone_number="1-112-1113").exists())
        self.assertTrue(t.get_contacts().exists())

    @patch("logging.info")
    @patch("modules.text_processor.Texter.send")
    def test_subscribe_with_too_long_name(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1111")
        long_name = "".join(["name" for _ in range(20)]) # length 100
        response = t.process("JOIN " + long_name + " 25-11-2012")
        self.assertEqual(response, msg_failure("English"))
        self.assertFalse(Contact.objects.filter(name=long_name.title(), phone_number="1-111-1111").exists())
        self.assertFalse(t.get_contacts().exists())


    @patch("logging.info")
    @patch("modules.text_processor.Texter.send")
    def test_unsubscribe_english(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1112")
        t.process("JOIN Roland 12/11/2017")
        response = t.process("STOP")
        self.assertTrue(t.get_contacts().first().cancelled)
        self.assertEqual(response, msg_unsubscribe("English"))
        logging_mock.assert_called_with("Unsubscribing `1-111-1112`...")
        texting_mock.assert_called_with(message=response, phone_number="1-111-1112")
        actual_groups = [str(g) for g in t.get_contacts().first().group_set.all()]
        expected_groups = ['Everyone - English', 'Text Sign Ups', 'Text Sign Ups - English']
        self.assertEqual(actual_groups, expected_groups)

    @patch("logging.info")
    @patch("modules.text_processor.Texter.send")
    def test_unsubscribe_hindi(self, texting_mock, logging_mock):
        Contact.objects.create(name="Sai",
                               phone_number="1-112-1112",
                               delay_in_days=0,
                               language_preference="Hindi",
                               method_of_sign_up="Text")
        t = TextProcessor(phone_number="1-112-1112")
        response = t.process("STOP")
        self.assertTrue(t.get_contacts().first().cancelled)
        self.assertEqual(response, msg_unsubscribe("Hindi"))
        logging_mock.assert_called_with("Unsubscribing `1-112-1112`...")
        texting_mock.assert_called_once_with(message=response, phone_number="1-112-1112")

    @patch("logging.error")
    @patch("logging.info")
    @patch("modules.text_processor.Texter.send")
    def test_unsubscribe_without_contact(self, texting_mock, logging_info_mock, logging_error_mock):
        self.assertFalse(Contact.objects.filter(phone_number="1-111-1112").exists())
        t = TextProcessor(phone_number="1-111-1112")
        response = t.process("STOP")
        self.assertFalse(Contact.objects.filter(phone_number="1-111-1112").exists())
        self.assertEqual(response, msg_unsubscribe("English"))
        logging_error_mock.assert_called_with("`1-111-1112` asked to be unsubscribed but does not exist.")

    @patch("logging.error")
    @patch("logging.info")
    @patch("modules.text_processor.Texter.send")
    def test_subscribe_twice_english(self, texting_mock, logging_info_mock, logging_error_mock):
        t = TextProcessor(phone_number="1-111-1114")
        self.assertFalse(Contact.objects.filter(name="Rose", phone_number="1-111-1114").exists())
        first_response = t.process("JOIN ROSE 25-11-2012")
        self.assertEqual(first_response, msg_subscribe("English").format(name="Rose"))
        texting_mock.assert_called_with(message=first_response, phone_number="1-111-1114")
        self.assertTrue(Contact.objects.filter(name="Rose", phone_number="1-111-1114").exists())
        self.assertTrue(t.get_contacts().exists())
        t2 = TextProcessor(phone_number="1-111-1114")
        second_response = t2.process("JOIN ROSE 25-11-2012")
        self.assertTrue(t2.get_contacts().exists())
        self.assertEqual(second_response, msg_already_sub("English"))
        texting_mock.assert_called_with(message=second_response, phone_number="1-111-1114")
        logging_error_mock.assert_called_with("Contact for Rose at 1-111-1114 was subscribed but already exists!")
        self.assertTrue(Contact.objects.filter(name="Rose", phone_number="1-111-1114").exists())
        self.assertTrue(t2.get_contacts().exists())
        actual_groups = [str(g) for g in t2.get_contacts().first().group_set.all()]
        expected_groups = ['Everyone - English', 'Text Sign Ups', 'Text Sign Ups - English']
        self.assertEqual(actual_groups, expected_groups)

    @patch("logging.error")
    @patch("logging.info")
    @patch("modules.text_processor.Texter.send")
    def test_subscribe_twice_hindi(self, texting_mock, logging_info_mock, logging_error_mock):
        t = TextProcessor(phone_number="1-111-1115")
        first_response = t.process(hindi_remind() + " SANJIV 25-11-2012")
        self.assertEqual(first_response, msg_subscribe("Hindi").format(name="Sanjiv"))
        texting_mock.assert_called_with(message=first_response, phone_number="1-111-1115")
        self.assertTrue(Contact.objects.filter(name="Sanjiv", phone_number="1-111-1115").exists())
        self.assertTrue(t.get_contacts().exists())
        t2 = TextProcessor(phone_number="1-111-1115")
        self.assertTrue(t2.get_contacts().exists())
        second_response = t2.process(hindi_remind() + " SANJIV 25-11-2012")
        self.assertEqual(second_response, msg_already_sub("Hindi"))
        texting_mock.assert_called_with(message=second_response, phone_number="1-111-1115")
        logging_error_mock.assert_called_with("Contact for Sanjiv at 1-111-1115 was subscribed but already exists!")
        contacts = Contact.objects.filter(name="Sanjiv", phone_number="1-111-1115")
        self.assertTrue(contacts.exists())
        self.assertEqual(contacts.count(), 1)
        self.assertTrue(t2.get_contacts().exists())

    @patch("logging.error")
    @patch("logging.info")
    @patch("modules.text_processor.Texter.send")
    def test_subscribe_two_children(self, texting_mock, logging_info_mock, logging_error_mock):
        t = TextProcessor(phone_number="1-111-1120")
        self.assertFalse(Contact.objects.filter(name="Peter", phone_number="1-111-1120").exists())
        self.assertFalse(Contact.objects.filter(name="Ben", phone_number="1-111-1120").exists())
        first_response = t.process("JOIN PETER 11-12-2016")
        self.assertEqual(first_response, msg_subscribe("English").format(name="Peter"))
        texting_mock.assert_called_with(message=first_response, phone_number="1-111-1120")
        self.assertTrue(Contact.objects.filter(name="Peter", phone_number="1-111-1120").exists())
        self.assertEqual(Contact.objects.filter(phone_number="1-111-1120").count(), 1)
        t2 = TextProcessor(phone_number="1-111-1120")
        second_response = t2.process("JOIN BEN 4-10-2016")
        self.assertEqual(second_response, msg_subscribe("English").format(name="Ben"))
        texting_mock.assert_called_with(message=second_response, phone_number="1-111-1120")
        self.assertTrue(Contact.objects.filter(name="Ben", phone_number="1-111-1120").exists())
        self.assertEqual(Contact.objects.filter(phone_number="1-111-1120").count(), 2)
        actual_groups = [str(g) for g in t2.get_contacts().first().group_set.all()]
        expected_groups = ['Everyone - English', 'Text Sign Ups', 'Text Sign Ups - English']
        self.assertEqual(actual_groups, expected_groups)

    @patch("logging.info")
    @patch("modules.text_processor.Texter.send")
    def test_subscribe_then_cancel(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1116")
        self.assertFalse(Contact.objects.filter(name="Rob", phone_number="1-111-1116").exists())
        t.process("JOIN ROB 25-11-2012")
        contacts = Contact.objects.filter(name="Rob", phone_number="1-111-1116")
        self.assertTrue(contacts.exists())
        self.assertEqual(contacts.count(), 1)
        self.assertFalse(contacts.first().cancelled)
        t2 = TextProcessor(phone_number="1-111-1116")
        t2.process("STOP")
        contacts = Contact.objects.filter(name="Rob", phone_number="1-111-1116")
        self.assertTrue(contacts.exists())
        self.assertTrue(contacts.first().cancelled)
        actual_groups = [str(g) for g in contacts.first().group_set.all()]
        expected_groups = ['Everyone - English', 'Text Sign Ups', 'Text Sign Ups - English']
        self.assertEqual(actual_groups, expected_groups)

    @patch("logging.info")
    @patch("modules.text_processor.Texter.send")
    def test_subscribe_then_cancel_then_subscribe(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1117")
        self.assertFalse(Contact.objects.filter(name="Cheyenne", phone_number="1-111-1117").exists())
        t.process("JOIN CHEYENNE 25-11-2012")
        contacts = Contact.objects.filter(name="Cheyenne", phone_number="1-111-1117")
        self.assertTrue(contacts.exists())
        self.assertFalse(contacts.first().cancelled)
        t2 = TextProcessor(phone_number="1-111-1117")
        t2.process("STOP")
        contacts = Contact.objects.filter(name="Cheyenne", phone_number="1-111-1117")
        self.assertTrue(contacts.exists())
        self.assertTrue(contacts.first().cancelled)
        t3 = TextProcessor(phone_number="1-111-1117")
        t3.process("JOIN CHEYENNE 25-11-2012")
        contacts = Contact.objects.filter(name="Cheyenne", phone_number="1-111-1117")
        self.assertTrue(contacts.exists())
        self.assertFalse(contacts.first().cancelled)
        actual_groups = [str(g) for g in contacts.first().group_set.all()]
        expected_groups = ['Everyone - English', 'Text Sign Ups', 'Text Sign Ups - English']
        self.assertEqual(actual_groups, expected_groups)

    @patch("logging.info")
    @patch("modules.text_processor.Texter.send")
    def test_subscribe_then_cancel_then_update_dob(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1118")
        self.assertFalse(Contact.objects.filter(name="Cheyenne", phone_number="1-111-1118").exists())
        t.process("JOIN CHEYENNE 25-11-2012")
        contacts = Contact.objects.filter(name="Cheyenne", phone_number="1-111-1118")
        self.assertTrue(contacts.exists())
        self.assertEqual(contacts.first().date_of_birth, datetime(2012, 11, 25, 0, 0).date())
        t2 = TextProcessor(phone_number="1-111-1118")
        t2.process("STOP")
        contacts = Contact.objects.filter(name="Cheyenne", phone_number="1-111-1118")
        self.assertTrue(contacts.exists())
        self.assertEqual(contacts.first().date_of_birth, datetime(2012, 11, 25, 0, 0).date())
        t3 = TextProcessor(phone_number="1-111-1118")
        t3.process("JOIN CHEYENNE 25-12-2012")
        contacts = Contact.objects.filter(name="Cheyenne", phone_number="1-111-1118")
        self.assertTrue(contacts.exists())
        self.assertEqual(contacts.first().date_of_birth, datetime(2012, 12, 25, 0, 0).date())
        actual_groups = [str(g) for g in contacts.first().group_set.all()]
        expected_groups = ['Everyone - English', 'Text Sign Ups', 'Text Sign Ups - English']
        self.assertEqual(actual_groups, expected_groups)

    @patch("logging.info")
    @patch("modules.text_processor.Texter.send")
    def test_subscribe_then_cancel_then_update_language(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1118")
        self.assertFalse(Contact.objects.filter(name="Larissa", phone_number="1-111-1118").exists())
        first_response = t.process("JOIN LARISSA 25-11-2012")
        self.assertEqual(first_response, msg_subscribe("English").format(name="Larissa"))
        contacts = Contact.objects.filter(name="Larissa", phone_number="1-111-1118")
        self.assertTrue(contacts.exists())
        self.assertEqual(contacts.first().language_preference, "English")
        t2 = TextProcessor(phone_number="1-111-1118")
        t2.process("STOP")
        t3 = TextProcessor(phone_number="1-111-1118")
        third_response = t.process(hindi_remind() + " LARISSA 25-11-2012")
        self.assertEqual(third_response, msg_subscribe("Hindi").format(name="Larissa"))
        contacts = Contact.objects.filter(name="Larissa", phone_number="1-111-1118")
        self.assertTrue(contacts.exists())
        self.assertEqual(contacts.first().language_preference, "Hindi")

    @patch("logging.error")
    @patch("modules.text_processor.Texter.send")
    def test_keyword_failure(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1111")
        response = t.process("JLORN COACHZ 25-11-2012")
        self.assertEqual(response, msg_failure("English"))
        logging_mock.assert_called_with("Keyword `jlorn` in message `JLORN COACHZ 25-11-2012` was not understood by the system.")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")

    @patch("logging.error")
    @patch("modules.text_processor.Texter.send")
    def test_keyword_failure_hindi(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1111")
        response = t.process(u'\u0906\u0930 \u0906\u0930\u0935 25-11-2012')
        self.assertEqual(response, msg_failure("Hindi"))
        logging_mock.assert_called_with(u'Keyword `\u0906\u0930` in message `\u0906\u0930 \u0906\u0930\u0935 25-11-2012` was not understood by the system.')
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")

    @patch("logging.error")
    @patch("modules.text_processor.Texter.send")
    def test_keyword_failed_date_english(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1111")
        response = t.process("JOIN PAULA 25:11:2012")
        self.assertEqual(response, msg_failed_date("English"))
        logging_mock.assert_called_with("Date in message `JOIN PAULA 25:11:2012` is invalid.")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")

    @patch("logging.error")
    @patch("modules.text_processor.Texter.send")
    def test_keyword_failed_date_hindi(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1111")
        invalid_text_message = hindi_remind() + " Sai 11,09,2013"
        response = t.process(invalid_text_message)
        self.assertEqual(response, msg_failed_date("Hindi"))
        logging_mock.assert_called_with("Date in message " + quote(invalid_text_message) + " is invalid.")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")

    @patch("logging.error")
    @patch("modules.text_processor.Texter.send")
    def test_keyword_failed_date_hindi_with_hindi_name(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1111")
        invalid_text_message = hindi_remind() + u' \u0906\u0930\u0935 11,09,2013'
        response = t.process(invalid_text_message)
        self.assertEqual(response, msg_failed_date("Hindi"))
        logging_mock.assert_called_with("Date in message " + quote(invalid_text_message) + " is invalid.")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")

    @patch("logging.error")
    @patch("modules.text_processor.Texter.send")
    def test_blank_message(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1111")
        response = t.process(" ")
        self.assertEqual(response, msg_failure("English"))
        logging_mock.assert_called_with("Keyword `` in message ` ` was not understood by the system.")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")
