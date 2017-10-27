from mock import patch
from datetime import datetime
from django.test import TestCase

from management.models import Contact, Message
from modules.utils import quote
from modules.text_processor import TextProcessor
from modules.i18n import hindi_remind, hindi_information, msg_placeholder_child, \
                         msg_subscribe, msg_unsubscribe, msg_failure, msg_failed_date, \
                         msg_already_sub, hindi_born

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

    def test_born_keyword(self):
        t = TextProcessor(phone_number="1-111-1111")
        keyword, child_name, date = t.get_data_from_message("Born Charles 19/12/2012")
        self.assertEqual(keyword, "born")
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

    def test_hindi_born(self):
        t = TextProcessor(phone_number="1-111-1111")
        keyword, child_name, date = t.get_data_from_message(hindi_born() + " Sai 11/09/2013")
        self.assertEqual(keyword, hindi_born())
        self.assertEqual(child_name, "sai")
        self.assertEqual(date, datetime(2013, 9, 11, 0, 0).date())

    def test_no_child_name(self):
        t = TextProcessor(phone_number="1-111-1111")
        keyword, child_name, date = t.get_data_from_message("Remind 25/11/2015")
        self.assertEqual(keyword, "remind")
        self.assertEqual(child_name, None)
        self.assertEqual(date, datetime(2015, 11, 25, 0, 0).date())

    def test_end(self):
        t = TextProcessor(phone_number="1-111-1111")
        keyword, child_name, date = t.get_data_from_message("END")
        self.assertEqual(keyword, "end")
        self.assertEqual(child_name, None)
        self.assertEqual(date, None)


class TextProcessorProcessTests(TestCase):
    def create_contact(self, name, phone_number, delay_in_days, language_preference, method_of_sign_up):
        return Contact.objects.create(name=name,
                               phone_number=phone_number,
                               delay_in_days=delay_in_days,
                               language_preference=language_preference,
                               method_of_sign_up=method_of_sign_up)

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
        message = t.write_to_database(hindi_remind() + " Sai 11/09/2013")
        response = t.process(message)
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
        message_object = t.write_to_database(message)
        response = t.process(message_object)
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
        message_object = t.write_to_database("JOIN 25-11-2012")
        response = t.process(message_object)
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
        message_object = t.write_to_database(hindi_remind() + " 25-11-2012")
        response = t.process(message_object)
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
        self.assertTrue(Contact.objects.filter(phone_number="1-111-1111").exists())

    @patch("logging.info")
    @patch("modules.text_processor.Texter.send")
    def test_unsubscribe_english(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1112")
        t.process("JOIN Roland 12/11/2017")
        response = t.process("END")
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
        response = t.process("END")
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
        response = t.process("END")
        self.assertTrue(Contact.objects.filter(phone_number="1-111-1112").exists())
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
    def test_subscribe_twice_doesnt_change_preg_update_english(self, texting_mock, logging_info_mock, logging_error_mock):
        t = TextProcessor(phone_number="1-111-1114")
        self.assertFalse(Contact.objects.filter(name="Rose", phone_number="1-111-1114").exists())
        first_response = t.process("JOIN ROSE 25-11-2012")
        self.assertEqual(first_response, msg_subscribe("English").format(name="Rose"))
        texting_mock.assert_called_with(message=first_response, phone_number="1-111-1114")
        self.assertTrue(Contact.objects.filter(name="Rose", phone_number="1-111-1114", preg_update=False).exists())
        self.assertTrue(t.get_contacts().exists())
        t2 = TextProcessor(phone_number="1-111-1114")
        second_response = t2.process("JOIN ROSE 25-11-2012")
        self.assertTrue(t2.get_contacts().exists())
        self.assertEqual(second_response, msg_already_sub("English"))
        texting_mock.assert_called_with(message=second_response, phone_number="1-111-1114")
        logging_error_mock.assert_called_with("Contact for Rose at 1-111-1114 was subscribed but already exists!")
        contacts = Contact.objects.filter(name="Rose", phone_number="1-111-1114", preg_update=False)
        self.assertEqual(contacts.count(), 1)
        self.assertTrue(t2.get_contacts().exists())

    @patch("logging.error")
    @patch("logging.info")
    @patch("modules.text_processor.Texter.send")
    def test_subscribe_twice_doesnt_change_preg_update_hindi(self, texting_mock, logging_info_mock, logging_error_mock):
        t = TextProcessor(phone_number="1-111-1115")
        first_response = t.process(hindi_remind() + " SANJIV 25-11-2012")
        self.assertEqual(first_response, msg_subscribe("Hindi").format(name="Sanjiv"))
        texting_mock.assert_called_with(message=first_response, phone_number="1-111-1115")
        self.assertTrue(Contact.objects.filter(name="Sanjiv", phone_number="1-111-1115", preg_update=False).exists())
        self.assertTrue(t.get_contacts().exists())
        t2 = TextProcessor(phone_number="1-111-1115")
        self.assertTrue(t2.get_contacts().exists())
        second_response = t2.process(hindi_remind() + " SANJIV 25-11-2012")
        self.assertEqual(second_response, msg_already_sub("Hindi"))
        texting_mock.assert_called_with(message=second_response, phone_number="1-111-1115")
        logging_error_mock.assert_called_with("Contact for Sanjiv at 1-111-1115 was subscribed but already exists!")
        contacts = Contact.objects.filter(name="Sanjiv", phone_number="1-111-1115", preg_update=False)
        self.assertTrue(contacts.exists())
        self.assertEqual(contacts.count(), 1)
        self.assertTrue(t2.get_contacts().exists())

    @patch("modules.text_processor.Texter.send")
    def test_text_in_pregnancy_birthdate_update_english(self, texting_mock):
        t = TextProcessor(phone_number="1-111-1114")
        self.assertFalse(Contact.objects.filter(name="Rose", phone_number="1-111-1114").exists())
        first_response = t.process("JOIN ROSE 25-10-2012")
        self.assertEqual(first_response, msg_subscribe("English").format(name="Rose"))
        texting_mock.assert_called_with(message=first_response, phone_number="1-111-1114")
        self.assertTrue(Contact.objects.filter(name="Rose", phone_number="1-111-1114", date_of_birth=datetime(2012, 10, 25, 0, 0), preg_update=False).exists())
        self.assertTrue(t.get_contacts().exists())
        t2 = TextProcessor(phone_number="1-111-1114")
        second_response = t2.process("BORN ROSE 25-11-2012")
        self.assertTrue(t2.get_contacts().exists())
        self.assertEqual(second_response, msg_subscribe("English").format(name="Rose"))
        texting_mock.assert_called_with(message=second_response, phone_number="1-111-1114")
        self.assertFalse(Contact.objects.filter(name="Rose", phone_number="1-111-1114", date_of_birth=datetime(2012, 10, 25, 0, 0), preg_update=False).exists())
        self.assertFalse(Contact.objects.filter(name="Rose", phone_number="1-111-1114", date_of_birth=datetime(2012, 11, 25, 0, 0), preg_update=False).exists())
        self.assertTrue(Contact.objects.filter(name="Rose", phone_number="1-111-1114", date_of_birth=datetime(2012, 11, 25, 0, 0), preg_update=True).exists())
        self.assertTrue(t2.get_contacts().exists())
        actual_groups = [str(g) for g in t2.get_contacts().first().group_set.all()]
        expected_groups = ['Everyone - English', 'Text Sign Ups', 'Text Sign Ups - English']
        self.assertEqual(actual_groups, expected_groups)

    @patch("modules.text_processor.Texter.send")
    def test_existing_contact_pregnancy_birthdate_update_english(self, texting_mock):
        new_contact, _ = Contact.objects.update_or_create(name="Tina", phone_number="910003456789", language_preference="English", date_of_birth=datetime(2017, 7, 10, 0, 0), preg_signup=True)
        t3 = TextProcessor(phone_number="910003456789")
        self.assertTrue(t3.get_contacts().exists())
        self.assertTrue(Contact.objects.filter(name="Tina", phone_number="910003456789", language_preference="English", date_of_birth=datetime(2017, 7, 10, 0, 0), preg_signup=True, preg_update=False).exists())
        existing_contact_update = t3.process(Message.objects.create(contact=new_contact, direction="Incoming", body="BORN Tina 25-07-2017", is_processed=False))
        self.assertEqual(existing_contact_update, msg_subscribe("English").format(name="Tina"))
        texting_mock.assert_called_with(message=existing_contact_update, phone_number="910003456789")
        self.assertFalse(Contact.objects.filter(name="Tina", phone_number="910003456789", language_preference="English", date_of_birth=datetime(2017, 7, 10, 0, 0), preg_signup=True, preg_update=False).exists())
        self.assertFalse(Contact.objects.filter(name="Tina", phone_number="910003456789", language_preference="English", date_of_birth=datetime(2017, 7, 25, 0, 0), preg_signup=True, preg_update=False).exists())
        self.assertTrue(Contact.objects.filter(name="Tina", phone_number="910003456789", language_preference="English", date_of_birth=datetime(2017, 7, 25, 0, 0), preg_signup=True, preg_update=True).exists())
        new_contact.delete()

    @patch("modules.text_processor.Texter.send")
    def test_text_in_pregnancy_birthdate_update_hindi(self, texting_mock):
        t = TextProcessor(phone_number="1-111-1114")
        self.assertFalse(Contact.objects.filter(name="Sanjiv", phone_number="1-111-1114").exists())
        first_response = t.process(hindi_remind() + " Sanjiv 25-10-2012")
        self.assertEqual(first_response, msg_subscribe("Hindi").format(name="Sanjiv"))
        texting_mock.assert_called_with(message=first_response, phone_number="1-111-1114")
        self.assertTrue(Contact.objects.filter(name="Sanjiv", phone_number="1-111-1114", date_of_birth=datetime(2012, 10, 25, 0, 0), preg_update=False).exists())
        self.assertTrue(t.get_contacts().exists())
        t2 = TextProcessor(phone_number="1-111-1114")
        second_response = t2.process(hindi_born() + " Sanjiv 25-11-2012")
        self.assertTrue(t2.get_contacts().exists())
        self.assertEqual(second_response, msg_subscribe("Hindi").format(name="Sanjiv"))
        texting_mock.assert_called_with(message=second_response, phone_number="1-111-1114")
        self.assertFalse(Contact.objects.filter(name="Sanjiv", phone_number="1-111-1114", date_of_birth=datetime(2012, 10, 25, 0, 0), preg_update=False).exists())
        self.assertFalse(Contact.objects.filter(name="Sanjiv", phone_number="1-111-1114", date_of_birth=datetime(2012, 11, 25, 0, 0), preg_update=False).exists())
        self.assertTrue(Contact.objects.filter(name="Sanjiv", phone_number="1-111-1114", date_of_birth=datetime(2012, 11, 25, 0, 0), preg_update=True).exists())
        self.assertTrue(t2.get_contacts().exists())
        actual_groups = [str(g) for g in t2.get_contacts().first().group_set.all()]
        expected_groups = ['Everyone - Hindi', 'Text Sign Ups', 'Text Sign Ups - Hindi']
        self.assertEqual(actual_groups, expected_groups)

    @patch("modules.text_processor.Texter.send")
    def test_existing_contact_pregnancy_birthdate_update_hindi(self, texting_mock):
        new_contact, _ = Contact.objects.update_or_create(name="Sanjiv", phone_number="910003456789", language_preference="Hindi", date_of_birth=datetime(2017, 7, 10, 0, 0), preg_signup=True)
        t3 = TextProcessor(phone_number="910003456789")
        self.assertTrue(t3.get_contacts().exists())
        self.assertTrue(Contact.objects.filter(name="Sanjiv", phone_number="910003456789", language_preference="Hindi", date_of_birth=datetime(2017, 7, 10, 0, 0), preg_signup=True, preg_update=False).exists())
        existing_contact_update = t3.process(Message.objects.create(contact=new_contact, direction="Incoming", body=hindi_born() + " Sanjiv 25-07-2017", is_processed=False))
        self.assertEqual(existing_contact_update, msg_subscribe("Hindi").format(name="Sanjiv"))
        texting_mock.assert_called_with(message=existing_contact_update, phone_number="910003456789")
        self.assertFalse(Contact.objects.filter(name="Sanjiv", phone_number="910003456789", language_preference="Hindi", date_of_birth=datetime(2017, 7, 10, 0, 0), preg_signup=True, preg_update=False).exists())
        self.assertFalse(Contact.objects.filter(name="Sanjiv", phone_number="910003456789", language_preference="Hindi", date_of_birth=datetime(2017, 7, 25, 0, 0), preg_signup=True, preg_update=False).exists())
        self.assertTrue(Contact.objects.filter(name="Sanjiv", phone_number="910003456789", language_preference="Hindi", date_of_birth=datetime(2017, 7, 25, 0, 0), preg_signup=True, preg_update=True).exists())
        new_contact.delete()

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
        t2.process("END")
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
        t2.process("END")
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
        t2.process("END")
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
        t2.process("END")
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
        message_object = t.write_to_database("JLORN COACHZ 25-11-2012")
        response = t.process(message_object)
        self.assertEqual(response, msg_failure("English"))
        logging_mock.assert_called_with("Keyword `jlorn` in message `JLORN COACHZ 25-11-2012` was not understood by the system.")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")

    @patch("logging.error")
    @patch("modules.text_processor.Texter.send")
    def test_keyword_failure_hindi(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1111")
        message_object = t.write_to_database(u'\u0906\u0930 \u0906\u0930\u0935 25-11-2012')
        response = t.process(message_object)
        self.assertEqual(response, msg_failure("Hindi"))
        logging_mock.assert_called_with(u'Keyword `\u0906\u0930` in message `\u0906\u0930 \u0906\u0930\u0935 25-11-2012` was not understood by the system.')
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")

    @patch("logging.error")
    @patch("modules.text_processor.Texter.send")
    def test_keyword_failed_date_english(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1111")
        message = t.write_to_database("JOIN PAULA 25:11:2012")
        response = t.process(message)
        self.assertEqual(response, msg_failed_date("English"))
        logging_mock.assert_called_with("Date in message `JOIN PAULA 25:11:2012` is invalid.")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")

    @patch("logging.error")
    @patch("modules.text_processor.Texter.send")
    def test_keyword_failed_date_hindi(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1111")
        invalid_text_message = hindi_remind() + " Sai 11,09,2013"
        message_object = t.write_to_database(invalid_text_message)
        response = t.process(message_object)
        self.assertEqual(response, msg_failed_date("Hindi"))
        logging_mock.assert_called_with("Date in message " + quote(invalid_text_message) + " is invalid.")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")

    @patch("logging.error")
    @patch("modules.text_processor.Texter.send")
    def test_keyword_failed_date_hindi_with_hindi_name(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1111")
        invalid_text_message = hindi_remind() + u' \u0906\u0930\u0935 11,09,2013'
        message_object = t.write_to_database(invalid_text_message)
        response = t.process(message_object)
        self.assertEqual(response, msg_failed_date("Hindi"))
        logging_mock.assert_called_with("Date in message " + quote(invalid_text_message) + " is invalid.")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")

    @patch("logging.error")
    @patch("modules.text_processor.Texter.send")
    def test_blank_message(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1111")
        contact = self.create_contact(name="",
                                    phone_number="1-111-1111",
                                    delay_in_days=0,
                                    language_preference="English",
                                    method_of_sign_up="Text")
        response = t.process(Message.objects.create(contact=contact, direction="Incoming", body=" ", is_processed=False))
        self.assertEqual(response, msg_failure("English"))
        logging_mock.assert_called_with("Keyword `` in message ` ` was not understood by the system.")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")

    def test_outgoing_message_objects_created_for_existing_contacts(self):
        contact = Contact.objects.create(name="Existy",
                               phone_number="1-112-1111",
                               delay_in_days=0,
                               language_preference="English",
                               method_of_sign_up="Text")
        t = TextProcessor(phone_number="1-112-1111")
        self.assertFalse(Message.objects.filter(contact=contact, direction="Outgoing", body="Some words about Existy"))
        t.create_message_object(child_name="Existy", phone_number=t.phone_number, language="English",
                                body="Some words about Existy", direction="Outgoing")
        self.assertEqual(1, Message.objects.filter(contact=contact, direction="Outgoing", body="Some words about Existy").count())

        hin_contact = Contact.objects.create(name=msg_placeholder_child("Hindi"),
                               phone_number="1-112-1111",
                               delay_in_days=0,
                               language_preference="Hindi",
                               method_of_sign_up="Text")
        t = TextProcessor(phone_number="1-112-1111")
        self.assertFalse(Message.objects.filter(contact=hin_contact, direction="Outgoing", body="Some words about Existy"))
        t.create_message_object(child_name=msg_placeholder_child("Hindi"), phone_number=t.phone_number, language="Hindi",
                                body=msg_subscribe("Hindi"), direction="Outgoing")
        self.assertEqual(1, Message.objects.filter(contact=hin_contact, direction="Outgoing", body=msg_subscribe("Hindi")).count())

    def test_incoming_message_objects_created_for_existing_contacts(self):
        contact = Contact.objects.create(name="Existy",
                               phone_number="1-112-1111",
                               delay_in_days=0,
                               language_preference="English",
                               method_of_sign_up="Text")
        t = TextProcessor(phone_number="1-112-1111")
        self.assertFalse(Message.objects.filter(contact=contact, direction="Incoming", body="JOIN Existy 17-05-16"))
        t.create_message_object(child_name="Existy", phone_number=t.phone_number, language="English",
                                body="JOIN Existy 17-05-16", direction="Incoming")
        self.assertEqual(1, Message.objects.filter(contact=contact, direction="Incoming", body="JOIN Existy 17-05-16").count())

        hin_contact = Contact.objects.create(name=msg_placeholder_child("Hindi"),
                               phone_number="1-112-1111",
                               delay_in_days=0,
                               language_preference="Hindi",
                               method_of_sign_up="Text")
        t = TextProcessor(phone_number="1-112-1111")
        self.assertFalse(Message.objects.filter(contact=hin_contact, direction="Incoming", body="Some words about Existy"))
        t.create_message_object(child_name=msg_placeholder_child("Hindi"), phone_number=t.phone_number, language="Hindi",
                                body=hindi_remind() + u' \u0905\u0917\u0932\u0947 ' + "10/03/16", direction="Incoming")
        self.assertEqual(1, Message.objects.filter(contact=hin_contact, direction="Incoming",
                                                    body=hindi_remind() + u' \u0905\u0917\u0932\u0947 ' + "10/03/16").count())

    def test_incoming_message_objects_created_for_new_contacts(self):
        t = TextProcessor(phone_number="1-112-1111")
        t.create_message_object(child_name="Namey", phone_number=t.phone_number, language="English",
                                body="JOIN Namey 17-05-16", direction="Incoming")
        self.assertEqual(1, Message.objects.filter(contact=Contact.objects.get(phone_number=t.phone_number),
                                                    direction="Incoming", body="JOIN Namey 17-05-16").count())
        t = TextProcessor(phone_number="1-116-1111")
        t.create_message_object(child_name=msg_placeholder_child("Hindi"), phone_number=t.phone_number, language="Hindi",
                                body=hindi_remind() + u' \u0905\u0917\u0932\u0947 ' + "10/03/16" , direction="Incoming")
        self.assertEqual(1, Message.objects.filter(contact=Contact.objects.get(phone_number=t.phone_number),
                                                    direction="Incoming", body=hindi_remind() + u' \u0905\u0917\u0932\u0947 ' + "10/03/16").count())

    def test_outgoing_message_objects_created_for_new_contacts(self):
        t = TextProcessor(phone_number="1-112-1111")
        t.create_message_object(child_name="New name", phone_number=t.phone_number, language="English",
                                body="Some words about New name", direction="Outgoing")
        self.assertEqual(1, Message.objects.filter(contact=Contact.objects.get(phone_number=t.phone_number),
                                                    direction="Outgoing", body="Some words about New name").count())
        t = TextProcessor(phone_number="1-112-1111")
        t.create_message_object(child_name=msg_placeholder_child("Hindi"), phone_number=t.phone_number, language="Hindi",
                                body=msg_already_sub("Hindi"), direction="Outgoing")
        self.assertEqual(1, Message.objects.filter(contact=Contact.objects.get(phone_number=t.phone_number, language_preference="Hindi"),
                                                    direction="Outgoing", body=msg_already_sub("Hindi")).count())

    def test_message_objects_created_name_when_name_is_too_long(self):
        t = TextProcessor(phone_number="1-112-1111")
        long_name = "".join(["name" for _ in range(20)]) # length 100
        t.create_message_object(child_name=long_name, phone_number=t.phone_number, language="English",
                                body=msg_failure("English"), direction="Outgoing")
        self.assertEqual(1, Message.objects.filter(contact=Contact.objects.get(phone_number=t.phone_number),
                                                    direction="Outgoing", body=msg_failure("English")).count())

    def test_message_objects_created_when_name_is_blank(self):
        t = TextProcessor(phone_number="1-112-1111")
        t.create_message_object(child_name="", phone_number=t.phone_number, language="English",
                                body=msg_subscribe("English"), direction="Outgoing")
        self.assertEqual(1, Message.objects.filter(contact=Contact.objects.get(phone_number=t.phone_number),
                                                    direction="Outgoing", body=msg_subscribe("English")).count())

        t.create_message_object(child_name="", phone_number=t.phone_number, language="Hindi",
                                body=msg_subscribe("Hindi"), direction="Outgoing")
        self.assertEqual(1, Message.objects.filter(contact=Contact.objects.get(phone_number=t.phone_number, language_preference="Hindi"),
                                                    direction="Outgoing", body=msg_subscribe("Hindi")).count())

        t.create_message_object(child_name="", phone_number=t.phone_number, language="English",
                                body="JOIN 11/07/17", direction="Incoming")
        self.assertEqual(1, Message.objects.filter(contact=Contact.objects.get(phone_number=t.phone_number, language_preference="English"),
                                                    direction="Incoming", body="JOIN 11/07/17").count())

    @patch("logging.info")
    @patch("modules.text_processor.Texter.send")  # See https://stackoverflow.com/questions/16134281/python-mocking-a-function-from-an-imported-module
    def test_processing_subscriptions_creates_message_objects(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1111")
        self.assertFalse(Contact.objects.filter(name="Paula", phone_number="1-111-1111").exists())
        self.assertFalse(Contact.objects.filter(phone_number=t.phone_number).exists())
        self.assertFalse(Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                direction="Incoming", body="JOIN PAULA 25-11-2012"))
        response = t.process("JOIN PAULA 25-11-2012")
        self.assertTrue(Contact.objects.filter(name="Paula", phone_number="1-111-1111").exists())
        self.assertEqual(1, Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                direction="Incoming", body="JOIN PAULA 25-11-2012").count())
        self.assertEqual(1, Message.objects.filter(contact=Contact.objects.get(phone_number=t.phone_number),
                                                    direction="Outgoing", body=msg_subscribe("English").format(name="Paula")).count())
        logging_mock.assert_called_with("Subscribing `JOIN PAULA 25-11-2012`...")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")

        t = TextProcessor(phone_number="1-112-1111")
        self.assertFalse(Contact.objects.filter(name=u'\u0906\u0930\u0935', phone_number="1-112-1111").exists())
        self.assertFalse(Contact.objects.filter(phone_number=t.phone_number).exists())
        self.assertFalse(Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                direction="Incoming", body=hindi_remind() + u' \u0906\u0930\u0935' + " 30-11-2016"))
        response = t.process(hindi_remind() + u' \u0906\u0930\u0935' + " 30-11-2016")
        self.assertTrue(Contact.objects.filter(name=u'\u0906\u0930\u0935', phone_number="1-112-1111").exists())
        self.assertEqual(1, Message.objects.filter(contact=Contact.objects.get(phone_number=t.phone_number),
                                                    direction="Outgoing", body=msg_subscribe("Hindi").format(name=u'\u0906\u0930\u0935')).count())
        logging_mock.assert_called_with("Subscribing " + quote(hindi_remind() + u' \u0906\u0930\u0935' + " 30-11-2016") + "...")
        texting_mock.assert_called_with(message=response, phone_number="1-112-1111")
        self.assertEqual(2, texting_mock.call_count)

    @patch("logging.info")
    @patch("modules.text_processor.Texter.send")  # See https://stackoverflow.com/questions/16134281/python-mocking-a-function-from-an-imported-module
    def test_processing_subscriptions_creates_message_objects_with_no_names(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1111")
        self.assertFalse(Contact.objects.filter(name=msg_placeholder_child("English"), phone_number="1-111-1111").exists())
        self.assertFalse(Contact.objects.filter(phone_number=t.phone_number).exists())
        self.assertFalse(Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                direction="Incoming", body="JOIN 25-11-2012"))
        response = t.process("JOIN 25-11-2012")
        self.assertEqual(1, Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                direction="Incoming", body="JOIN 25-11-2012").count())
        self.assertTrue(Contact.objects.filter(name=msg_placeholder_child("English"), phone_number="1-111-1111").exists())
        self.assertEqual(1, Message.objects.filter(contact=Contact.objects.get(phone_number=t.phone_number),
                                                    direction="Outgoing", body=msg_subscribe("English").format(name=msg_placeholder_child("English"))).count())
        logging_mock.assert_called_with("Subscribing `JOIN 25-11-2012`...")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")

        t = TextProcessor(phone_number="1-112-1111")
        self.assertFalse(Contact.objects.filter(name="", phone_number="1-112-1111").exists())
        self.assertFalse(Contact.objects.filter(phone_number=t.phone_number).exists())
        self.assertFalse(Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                direction="Incoming", body=hindi_remind() + " 30-11-2016"))
        response = t.process(hindi_remind() + " 30-11-2016")
        self.assertTrue(Contact.objects.filter(name=msg_placeholder_child("Hindi"), phone_number="1-112-1111").exists())
        self.assertEqual(1, Message.objects.filter(contact=Contact.objects.get(phone_number=t.phone_number),
                                                    direction="Outgoing", body=msg_subscribe("Hindi").format(name=msg_placeholder_child("Hindi"))).count())
        logging_mock.assert_called_with("Subscribing " + quote(hindi_remind() + " 30-11-2016") + "...")
        texting_mock.assert_called_with(message=response, phone_number="1-112-1111")
        self.assertEqual(2, texting_mock.call_count)

    @patch("logging.info")
    @patch("modules.text_processor.Texter.send")  # See https://stackoverflow.com/questions/16134281/python-mocking-a-function-from-an-imported-module
    def test_processing_unsubscriptions_creates_message_objects(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1112")
        t.process("JOIN Roland 12/11/2017")
        self.assertFalse(Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                direction="Incoming", body="END"))
        response = t.process("END")
        self.assertTrue(t.get_contacts().first().cancelled)
        self.assertEqual(response, msg_unsubscribe("English"))
        logging_mock.assert_called_with("Unsubscribing `1-111-1112`...")
        texting_mock.assert_called_with(message=response, phone_number="1-111-1112")
        self.assertEqual(1, Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                direction="Incoming", body="END").count())

        t = TextProcessor(phone_number="1-111-1113")
        t.process(hindi_remind() + u' \u0906\u0930\u0935' + " 30-11-2016")
        self.assertFalse(Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                direction="Incoming", body="END"))
        response = t.process("END")
        self.assertTrue(t.get_contacts().first().cancelled)
        self.assertEqual(response, msg_unsubscribe("Hindi"))
        logging_mock.assert_called_with("Unsubscribing `1-111-1113`...")
        texting_mock.assert_called_with(message=response, phone_number="1-111-1113")
        self.assertEqual(1, Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                direction="Incoming", body="END").count())

    @patch("logging.error")
    @patch("modules.text_processor.Texter.send")  # See https://stackoverflow.com/questions/16134281/python-mocking-a-function-from-an-imported-module
    def test_processing_failure_messages_creates_message_objects(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1111")
        self.assertFalse(Contact.objects.filter(phone_number=t.phone_number).exists())
        response = t.process("JLORN COACHZ 25-11-2012")
        self.assertEqual(response, msg_failure("English"))
        logging_mock.assert_called_with("Keyword `jlorn` in message `JLORN COACHZ 25-11-2012` was not understood by the system.")
        texting_mock.assert_called_with(message=response, phone_number="1-111-1111")
        
        self.assertEqual(1, Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                direction="Incoming", body="JLORN COACHZ 25-11-2012").count())
        self.assertEqual(1, Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                direction="Outgoing", body=msg_failure("English")).count())


        t2 = TextProcessor(phone_number="1-111-1111")
        response2 = t2.process(u'\u0906\u0930 \u0906\u0930\u0935 25-11-2012')
        self.assertEqual(response2, msg_failure("Hindi"))
        logging_mock.assert_called_with(u'Keyword `\u0906\u0930` in message `\u0906\u0930 \u0906\u0930\u0935 25-11-2012` was not understood by the system.')
        texting_mock.assert_called_with(message=response2, phone_number="1-111-1111")

        self.assertEqual(1, Message.objects.filter(contact=Contact.objects.filter(phone_number=t2.phone_number),
                                                direction="Incoming", body=u'\u0906\u0930 \u0906\u0930\u0935 25-11-2012').count())
        self.assertEqual(1, Message.objects.filter(contact=Contact.objects.filter(phone_number=t2.phone_number),
                                                direction="Outgoing", body=msg_failure("Hindi")).count())


    @patch("modules.text_processor.Texter.send")
    def test_processing_pregnancy_updates_creates_message_objects(self, texting_mock):
        new_contact, _ = Contact.objects.update_or_create(name="Tina", phone_number="910003456789", language_preference="English", date_of_birth=datetime(2017, 7, 10, 0, 0), preg_signup=True)
        t = TextProcessor(phone_number="910003456789")
        self.assertTrue(t.get_contacts().exists())
        self.assertTrue(Contact.objects.filter(name="Tina", phone_number="910003456789", language_preference="English", date_of_birth=datetime(2017, 7, 10, 0, 0), preg_signup=True, preg_update=False).exists())
        existing_contact_update = t.process("BORN Tina 25-07-2017")
        self.assertEqual(existing_contact_update, msg_subscribe("English").format(name="Tina"))
        self.assertTrue(Contact.objects.filter(name="Tina", phone_number="910003456789", language_preference="English", date_of_birth=datetime(2017, 7, 25, 0, 0), preg_signup=True, preg_update=True).exists())

        self.assertEqual(1, Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                direction="Incoming", body="BORN Tina 25-07-2017").count())
        self.assertEqual(1, Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                direction="Outgoing", body=msg_subscribe("English").format(name="Tina")).count())
        new_contact.delete()

        hin_contact, _ = Contact.objects.update_or_create(name="Sanjiv", phone_number="910003456789", language_preference="Hindi", date_of_birth=datetime(2017, 7, 10, 0, 0), preg_signup=True)
        t2 = TextProcessor(phone_number="910003456789")
        self.assertTrue(t2.get_contacts().exists())
        self.assertTrue(Contact.objects.filter(name="Sanjiv", phone_number="910003456789", language_preference="Hindi", date_of_birth=datetime(2017, 7, 10, 0, 0), preg_signup=True, preg_update=False).exists())
        existing_contact_update = t2.process(hindi_born() + " Sanjiv 25-07-2017")
        self.assertEqual(existing_contact_update, msg_subscribe("Hindi").format(name="Sanjiv"))
        texting_mock.assert_called_with(message=existing_contact_update, phone_number="910003456789")
        self.assertTrue(Contact.objects.filter(name="Sanjiv", phone_number="910003456789", language_preference="Hindi", date_of_birth=datetime(2017, 7, 25, 0, 0), preg_signup=True, preg_update=True).exists())
        self.assertEqual(1, Message.objects.filter(contact=Contact.objects.filter(phone_number=t2.phone_number),
                                                direction="Incoming", body=hindi_born() + " Sanjiv 25-07-2017").count())
        self.assertEqual(1, Message.objects.filter(contact=Contact.objects.filter(phone_number=t2.phone_number),
                                                direction="Outgoing", body=msg_subscribe("Hindi").format(name="Sanjiv")).count())

        hin_contact.delete()

    @patch("logging.info")
    @patch("modules.text_processor.Texter.send")  # See https://stackoverflow.com/questions/16134281/python-mocking-a-function-from-an-imported-module
    def test_processing_creates_correct_amount_of_message_objects(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1111")
        self.assertFalse(Contact.objects.filter(name="Paula", phone_number="1-111-1111").exists())
        self.assertFalse(Contact.objects.filter(phone_number=t.phone_number).exists())
        self.assertFalse(Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                direction="Incoming", body="JOIN PAULA 25-11-2012"))
        message_object = t.write_to_database("JOIN PAULA 25-11-2012")
        self.assertTrue(Contact.objects.filter(name="Paula", phone_number="1-111-1111").exists())
        self.assertEqual(1, Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number).first(),
                                                direction="Incoming", body="JOIN PAULA 25-11-2012").count())
        response = t.process(message_object)
        self.assertEqual(1, Message.objects.filter(contact=Contact.objects.get(phone_number=t.phone_number),
                                                    direction="Outgoing", body=msg_subscribe("English").format(name="Paula")).count())
        logging_mock.assert_called_with("Subscribing `JOIN PAULA 25-11-2012`...")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")

        t2 = TextProcessor(phone_number="1-112-1111")
        second_message = t2.write_to_database("JOIN SMITH 25-11-2012")
        t2.process(second_message)
        t3 = TextProcessor(phone_number="1-113-1111")
        third_message = t3.write_to_database("JOIN Aaja 25-11-2012")
        t3.process(third_message)
        t4 = TextProcessor(phone_number="1-114-1111")
        fourth_message = t4.write_to_database("JOIN Lauren 25-11-2012")
        t4.process(fourth_message)
        end_message = t.write_to_database("END")
        t.process(end_message)

        self.assertEqual(2, Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                direction="Incoming").count())
        self.assertEqual(2, Message.objects.filter(contact=Contact.objects.get(phone_number=t.phone_number),
                                                    direction="Outgoing").count())

        self.assertEqual(5, Message.objects.filter(direction="Outgoing").count())
        self.assertEqual(5, Message.objects.filter(direction="Incoming").count())
        self.assertEqual(10, Message.objects.all().count())

        t5 = TextProcessor(phone_number="1-111-1115")
        self.assertFalse(Contact.objects.filter(name=u'\u0906\u0930\u0935', phone_number="1-111-1115").exists())
        self.assertFalse(Contact.objects.filter(phone_number=t5.phone_number).exists())
        self.assertFalse(Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                direction="Incoming", body=hindi_remind() + u' \u0906\u0930\u0935' + " 30-11-2016"))
        response = t5.process(hindi_remind() + u' \u0906\u0930\u0935' + " 30-11-2016")
        self.assertTrue(Contact.objects.filter(name=u'\u0906\u0930\u0935', phone_number="1-111-1115").exists())
        self.assertEqual(1, Message.objects.filter(contact=Contact.objects.get(phone_number=t5.phone_number),
                                                    direction="Outgoing", body=msg_subscribe("Hindi").format(name=u'\u0906\u0930\u0935')).count())
        logging_mock.assert_called_with("Subscribing " + quote(hindi_remind() + u' \u0906\u0930\u0935' + " 30-11-2016") + "...")
        texting_mock.assert_called_with(message=response, phone_number="1-111-1115")

        t6 = TextProcessor(phone_number="1-111-1116")
        t6.process(hindi_information() + " SMITH 25-11-2012")
        t7 = TextProcessor(phone_number="1-111-1117")
        t7.process(hindi_information() + " Aaja 25-11-2012")
        t8 = TextProcessor(phone_number="1-111-1118")
        t8.process(hindi_information() + " Lauren 25-11-2012")
        t5.process("END")

        self.assertEqual(2, Message.objects.filter(contact=Contact.objects.filter(phone_number=t5.phone_number),
                                                direction="Incoming").count())
        self.assertEqual(2, Message.objects.filter(contact=Contact.objects.get(phone_number=t5.phone_number),
                                                    direction="Outgoing").count())

        self.assertEqual(10, Message.objects.filter(direction="Outgoing").count())
        self.assertEqual(10, Message.objects.filter(direction="Incoming").count())
        self.assertEqual(20, Message.objects.all().count())

        self.assertEqual(10, texting_mock.call_count)

    @patch("logging.info")
    @patch("modules.text_processor.Texter.send")
    def test_processing_updates_contact_last_heard_from_english(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1111")
        response = t.process("JOIN PAULA 25-11-2012")
        original_contact = Contact.objects.filter(name="Paula", phone_number="1-111-1111").first()
        logging_mock.assert_called_with("Subscribing `JOIN PAULA 25-11-2012`...")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")

        born_response = t.process("BORN PAULA 25-11-2012")
        texting_mock.assert_called_with(message=born_response, phone_number="1-111-1111")
        updated_contact = Contact.objects.filter(name="Paula", phone_number="1-111-1111").first()
        self.assertNotEqual(original_contact.last_heard_from, updated_contact.last_heard_from)
        self.assertLess(original_contact.last_heard_from, updated_contact.last_heard_from)
        
        end_response = t.process("END")
        texting_mock.assert_called_with(message=end_response, phone_number="1-111-1111")
        unsub_contact = Contact.objects.filter(name="Paula", phone_number="1-111-1111").first()
        self.assertNotEqual(original_contact.last_heard_from, unsub_contact.last_heard_from)
        self.assertLess(original_contact.last_heard_from, unsub_contact.last_heard_from)
        self.assertNotEqual(updated_contact.last_heard_from, unsub_contact.last_heard_from)
        self.assertLess(updated_contact.last_heard_from, unsub_contact.last_heard_from)

    @patch("logging.info")
    @patch("modules.text_processor.Texter.send")
    def test_processing_updates_contact_last_heard_from_hindi(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1111")
        join_message = hindi_remind() + " Aarav 25-11-2012"
        response = t.process(hindi_remind() + " Aarav 25-11-2012")
        original_contact = Contact.objects.filter(name="Aarav", phone_number="1-111-1111").first()
        logging_mock.assert_called_with("Subscribing " + quote(join_message) + "...")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")

        born_response = t.process("BORN Aarav 25-11-2012")
        texting_mock.assert_called_with(message=born_response, phone_number="1-111-1111")
        updated_contact = Contact.objects.filter(name="Aarav", phone_number="1-111-1111").first()
        self.assertNotEqual(original_contact.last_heard_from, updated_contact.last_heard_from)
        self.assertLess(original_contact.last_heard_from, updated_contact.last_heard_from)
        
        end_response = t.process("END")
        texting_mock.assert_called_with(message=end_response, phone_number="1-111-1111")
        unsub_contact = Contact.objects.filter(name="Aarav", phone_number="1-111-1111").first()
        self.assertNotEqual(original_contact.last_heard_from, unsub_contact.last_heard_from)
        self.assertLess(original_contact.last_heard_from, unsub_contact.last_heard_from)
        self.assertNotEqual(updated_contact.last_heard_from, unsub_contact.last_heard_from)
        self.assertLess(updated_contact.last_heard_from, unsub_contact.last_heard_from)

    @patch("logging.info")
    @patch("modules.text_processor.Texter.send")
    def test_processing_updates_contact_last_contacted_english(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1111")
        response = t.process("JOIN PAULA 25-11-2012")
        original_contact = Contact.objects.filter(name="Paula", phone_number="1-111-1111").first()
        logging_mock.assert_called_with("Subscribing `JOIN PAULA 25-11-2012`...")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")

        born_response = t.process("BORN PAULA 25-11-2012")
        texting_mock.assert_called_with(message=born_response, phone_number="1-111-1111")
        updated_contact = Contact.objects.filter(name="Paula", phone_number="1-111-1111").first()
        self.assertNotEqual(original_contact.last_contacted, updated_contact.last_contacted)
        self.assertLess(original_contact.last_contacted, updated_contact.last_contacted)
        
        end_response = t.process("END")
        texting_mock.assert_called_with(message=end_response, phone_number="1-111-1111")
        unsub_contact = Contact.objects.filter(name="Paula", phone_number="1-111-1111").first()
        self.assertNotEqual(original_contact.last_contacted, unsub_contact.last_contacted)
        self.assertLess(original_contact.last_contacted, unsub_contact.last_contacted)
        self.assertNotEqual(updated_contact.last_contacted, unsub_contact.last_contacted)
        self.assertLess(updated_contact.last_contacted, unsub_contact.last_contacted)

    @patch("logging.info")
    @patch("modules.text_processor.Texter.send")
    def test_processing_updates_contact_last_contacted_hindi(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1111")
        join_message = hindi_remind() + " Aarav 25-11-2012"
        response = t.process(hindi_remind() + " Aarav 25-11-2012")
        original_contact = Contact.objects.filter(name="Aarav", phone_number="1-111-1111").first()
        logging_mock.assert_called_with("Subscribing " + quote(join_message) + "...")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")

        born_response = t.process("BORN Aarav 25-11-2012")
        texting_mock.assert_called_with(message=born_response, phone_number="1-111-1111")
        updated_contact = Contact.objects.filter(name="Aarav", phone_number="1-111-1111").first()
        self.assertNotEqual(original_contact.last_contacted, updated_contact.last_contacted)
        self.assertLess(original_contact.last_contacted, updated_contact.last_contacted)
        
        end_response = t.process("END")
        texting_mock.assert_called_with(message=end_response, phone_number="1-111-1111")
        unsub_contact = Contact.objects.filter(name="Aarav", phone_number="1-111-1111").first()
        self.assertNotEqual(original_contact.last_contacted, unsub_contact.last_contacted)
        self.assertLess(original_contact.last_contacted, unsub_contact.last_contacted)
        self.assertNotEqual(updated_contact.last_contacted, unsub_contact.last_contacted)
        self.assertLess(updated_contact.last_contacted, unsub_contact.last_contacted)

    @patch("logging.info")
    @patch("modules.text_processor.Texter.send")
    def test_processing_makes_contact_last_heard_from_time_message_time(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1111")
        response = t.process("JOIN PAULA 25-11-2012")
        original_contact = Contact.objects.filter(name="Paula", phone_number="1-111-1111").first()
        logging_mock.assert_called_with("Subscribing `JOIN PAULA 25-11-2012`...")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")
        join_message = Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                direction="Incoming", body="JOIN PAULA 25-11-2012").first()
        self.assertEqual(join_message.time, original_contact.last_heard_from)

        born_response = t.process("BORN PAULA 25-11-2012")
        texting_mock.assert_called_with(message=born_response, phone_number="1-111-1111")
        born_message = Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                direction="Incoming", body="BORN PAULA 25-11-2012").first()
        updated_contact = Contact.objects.filter(name="Paula", phone_number="1-111-1111").first()
        self.assertEqual(born_message.time, updated_contact.last_heard_from)
        
        end_response = t.process("END")
        texting_mock.assert_called_with(message=end_response, phone_number="1-111-1111")
        end_message = Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                direction="Incoming", body="END").first()
        unsub_contact = Contact.objects.filter(name="Paula", phone_number="1-111-1111").first()
        self.assertEqual(end_message.time, unsub_contact.last_heard_from)

    @patch("logging.info")
    @patch("modules.text_processor.Texter.send")
    def test_processing_makes_contact_last_contacted_time_message_time(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1111")
        response = t.process("JOIN PAULA 25-11-2012")
        original_contact = Contact.objects.filter(name="Paula", phone_number="1-111-1111").first()
        logging_mock.assert_called_with("Subscribing `JOIN PAULA 25-11-2012`...")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")
        subscribe_message = Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                direction="Outgoing", body=msg_subscribe("English").format(name="Paula")).first()
        self.assertEqual(subscribe_message.time, original_contact.last_contacted)

        born_response = t.process("BORN PAULA 25-11-2012")
        texting_mock.assert_called_with(message=born_response, phone_number="1-111-1111")
        subscribe_message2 = Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                direction="Outgoing", body=msg_subscribe("English").format(name="Paula")).last()
        updated_contact = Contact.objects.filter(name="Paula", phone_number="1-111-1111").first()
        self.assertEqual(subscribe_message2.time, updated_contact.last_contacted)
        
        end_response = t.process("END")
        texting_mock.assert_called_with(message=end_response, phone_number="1-111-1111")
        end_message = Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                direction="Outgoing", body=msg_unsubscribe("English")).first()
        unsub_contact = Contact.objects.filter(name="Paula", phone_number="1-111-1111").first()
        self.assertEqual(end_message.time, unsub_contact.last_contacted)

    @patch("logging.error")
    @patch("modules.text_processor.Texter.send")
    def test_processing_english_failed_messages_updates_contact_time_references(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1111")
        keyword = "SDFDAJFDF"
        fail_message = "SDFDAJFDF PAULA 25-11-2012"
        response = t.process(fail_message)
        original_contact = Contact.objects.filter(phone_number="1-111-1111").first()
        logging_mock.assert_called_with("Keyword " + quote(keyword.lower()) + " in message " + quote(fail_message) +
                          " was not understood by the system.")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")
        fail_message_object = Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                        direction="Incoming", body=fail_message).first()
        failed_message_response = Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                        direction="Outgoing", body=msg_failure("English")).first()
        self.assertEqual(fail_message_object.time, original_contact.last_heard_from)
        self.assertEqual(failed_message_response.time, original_contact.last_contacted)

        failed_date_response = t.process("BORN PAULA 60-11-2012")
        updated_contact = Contact.objects.filter(phone_number="1-111-1111").first()
        fail_date_object = Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                        direction="Incoming", body="BORN PAULA 60-11-2012").first()
        failed_date_response = Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                        direction="Outgoing", body=msg_failed_date("English")).first()
        self.assertEqual(fail_date_object.time, updated_contact.last_heard_from)
        self.assertEqual(failed_date_response.time, updated_contact.last_contacted)

    @patch("logging.error")
    @patch("modules.text_processor.Texter.send")
    def test_processing_hindi_failed_messages_updates_contact_time_references(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1111")
        keyword = u"\u0906\u092a"
        fail_message = keyword + " Aarav 25-11-2012"
        response = t.process(fail_message)
        original_contact = Contact.objects.filter(phone_number="1-111-1111").first()
        logging_mock.assert_called_with("Keyword " + quote(keyword.lower()) + " in message " + quote(fail_message) +
                          " was not understood by the system.")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")
        fail_message_object = Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                        direction="Incoming", body=fail_message).first()
        failed_message_response = Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                        direction="Outgoing", body=msg_failure("Hindi")).first()
        self.assertEqual(fail_message_object.time, original_contact.last_heard_from)
        self.assertEqual(failed_message_response.time, original_contact.last_contacted)

    @patch("logging.error")
    @patch("modules.text_processor.Texter.send")
    def test_processing_only_updates_contact_time_references_for_correct_contact(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1111")
        keyword = "SDFDAJFDF"
        fail_message = "SDFDAJFDF PAULA 25-11-2012"
        response = t.process(fail_message)
        original_contact = Contact.objects.filter(phone_number="1-111-1111").first()
        logging_mock.assert_called_with("Keyword " + quote(keyword.lower()) + " in message " + quote(fail_message) +
                          " was not understood by the system.")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")

        t2 = TextProcessor(phone_number="5-555-5555")
        failed_date_response = t2.process("BORN PAULA 60-11-2012")
        second_contact = Contact.objects.filter(phone_number="5-555-5555").first()

        self.assertNotEqual(original_contact.last_heard_from, second_contact.last_heard_from)
        self.assertNotEqual(original_contact.last_contacted, second_contact.last_contacted)

    def test_write_to_database_writes_correct_message(self):
        t = TextProcessor(phone_number="1-111-1111")
        self.assertFalse(Message.objects.filter(contact=Contact.objects.filter(phone_number="1-111-1111").first()))
        t.write_to_database("Test message")
        self.assertEqual(1, Message.objects.filter(contact=Contact.objects.filter(phone_number="1-111-1111").first(),
                                                    body="Test message",
                                                    direction="Incoming").count())
        t2 = TextProcessor(phone_number="1-111-2222")
        t2.write_to_database("JOIN Marshall 20-10-2017")
        self.assertEqual(1, Message.objects.filter(contact=Contact.objects.filter(phone_number="1-111-2222").first(),
                                                    body="JOIN Marshall 20-10-2017",
                                                    direction="Incoming").count())
        t2.write_to_database("END")
        self.assertEqual(1, Message.objects.filter(contact=Contact.objects.filter(phone_number="1-111-2222").first(),
                                                    body="END",
                                                    direction="Incoming").count())
