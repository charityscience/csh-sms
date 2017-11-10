from mock import patch
from datetime import datetime
from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time

from management.models import Contact, Message
from modules.utils import quote
from modules.text_processor import TextProcessor
from modules.i18n import hindi_remind, hindi_information, msg_placeholder_child, \
                         msg_subscribe, msg_unsubscribe, msg_failure, msg_failed_date, \
                         msg_already_sub, hindi_born

FAKE_NOW = datetime(2017, 7, 17, 0, 0)

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
        join_message = t.write_to_database(("JOIN PAULA 25-11-2012", FAKE_NOW.replace(tzinfo=timezone.get_default_timezone())))
        response = t.process(join_message)
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
        message = t.write_to_database((hindi_remind() + " Sai 11/09/2013",
                                        FAKE_NOW.replace(tzinfo=timezone.get_default_timezone())))
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
        message_object = t.write_to_database((message, FAKE_NOW.replace(tzinfo=timezone.get_default_timezone())))
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
        message_object = t.write_to_database(("JOIN 25-11-2012", FAKE_NOW.replace(tzinfo=timezone.get_default_timezone())))
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
        message_object = t.write_to_database((hindi_remind() + " 25-11-2012",
                                                FAKE_NOW.replace(tzinfo=timezone.get_default_timezone())))
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
        long_name_join = t.write_to_database(("JOIN " + long_name + " 25-11-2012",
                                                FAKE_NOW.replace(tzinfo=timezone.get_default_timezone())))
        response = t.process(long_name_join)
        self.assertEqual(response, msg_failure("English"))
        self.assertFalse(Contact.objects.filter(name=long_name.title(), phone_number="1-111-1111").exists())
        self.assertTrue(Contact.objects.filter(phone_number="1-111-1111").exists())

    @patch("logging.info")
    @patch("modules.text_processor.Texter.send")
    def test_unsubscribe_english(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1112")
        join_message = t.write_to_database(("JOIN Roland 12/11/2017", datetime(2017, 8, 9, 0, 5, 10).replace(tzinfo=timezone.get_default_timezone())))
        t.process(join_message)
        end_message = t.write_to_database(("END", datetime(2017, 8, 10, 0, 5, 10).replace(tzinfo=timezone.get_default_timezone())))
        response = t.process(end_message)
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
        end_message = t.write_to_database(("END", FAKE_NOW.replace(tzinfo=timezone.get_default_timezone())))
        response = t.process(end_message)
        self.assertTrue(t.get_contacts().first().cancelled)
        self.assertEqual(response, msg_unsubscribe("Hindi"))
        logging_mock.assert_called_with("Unsubscribing `1-112-1112`...")
        texting_mock.assert_called_once_with(message=response, phone_number="1-112-1112")

    @patch("logging.info")
    @patch("modules.text_processor.Texter.send")
    def test_unsubscribe_as_first_message(self, texting_mock, logging_info_mock):
        self.assertFalse(Contact.objects.filter(phone_number="1-111-1112").exists())
        t = TextProcessor(phone_number="1-111-1112")
        end_message = t.write_to_database(("END", FAKE_NOW.replace(tzinfo=timezone.get_default_timezone())))
        self.assertTrue(Contact.objects.filter(phone_number="1-111-1112").exists())
        response = t.process(end_message)
        self.assertTrue(Contact.objects.filter(phone_number="1-111-1112").exists())
        self.assertEqual(response, msg_unsubscribe("English"))

    @patch("logging.error")
    @patch("logging.info")
    @patch("modules.text_processor.Texter.send")
    def test_subscribe_twice_english(self, texting_mock, logging_info_mock, logging_error_mock):
        t = TextProcessor(phone_number="1-111-1114")
        self.assertFalse(Contact.objects.filter(name="Rose", phone_number="1-111-1114").exists())
        join_message = t.write_to_database(("JOIN ROSE 25-11-2012", datetime(2016, 10, 30, 10, 5, 5).replace(tzinfo=timezone.get_default_timezone())))
        first_response = t.process(join_message)
        self.assertEqual(first_response, msg_subscribe("English").format(name="Rose"))
        texting_mock.assert_called_with(message=first_response, phone_number="1-111-1114")
        self.assertTrue(Contact.objects.filter(name="Rose", phone_number="1-111-1114").exists())
        self.assertTrue(t.get_contacts().exists())
        t2 = TextProcessor(phone_number="1-111-1114")
        second_join = t2.write_to_database(("JOIN ROSE 25-11-2012", datetime(2016, 10, 31, 10, 5, 5).replace(tzinfo=timezone.get_default_timezone())))
        second_response = t2.process(second_join)
        self.assertTrue(t2.get_contacts().exists())
        self.assertEqual(second_response, msg_already_sub("English"))
        texting_mock.assert_called_with(message=second_response, phone_number="1-111-1114")
        logging_error_mock.assert_called_with("Contact for Rose at 1-111-1114 was subscribed but already exists!")
        self.assertTrue(Contact.objects.filter(name="Rose", phone_number="1-111-1114").exists())
        self.assertEqual(1, Contact.objects.filter(name="Rose", phone_number="1-111-1114").count())
        self.assertTrue(t2.get_contacts().exists())
        actual_groups = [str(g) for g in t2.get_contacts().first().group_set.all()]
        expected_groups = ['Everyone - English', 'Text Sign Ups', 'Text Sign Ups - English']
        self.assertEqual(actual_groups, expected_groups)

    @patch("logging.error")
    @patch("logging.info")
    @patch("modules.text_processor.Texter.send")
    def test_subscribe_twice_hindi(self, texting_mock, logging_info_mock, logging_error_mock):
        t = TextProcessor(phone_number="1-111-1115")
        join_message = t.write_to_database((hindi_remind() + " SANJIV 25-11-2012",
                                            datetime(2016, 10, 30, 10, 5, 5).replace(tzinfo=timezone.get_default_timezone())))
        first_response = t.process(join_message)
        self.assertEqual(first_response, msg_subscribe("Hindi").format(name="Sanjiv"))
        texting_mock.assert_called_with(message=first_response, phone_number="1-111-1115")
        self.assertTrue(Contact.objects.filter(name="Sanjiv", phone_number="1-111-1115").exists())
        self.assertTrue(t.get_contacts().exists())
        t2 = TextProcessor(phone_number="1-111-1115")
        self.assertTrue(t2.get_contacts().exists())
        second_join = t.write_to_database((hindi_remind() + " SANJIV 25-11-2012",
                                            datetime(2016, 10, 31, 10, 5, 5).replace(tzinfo=timezone.get_default_timezone())))
        second_response = t2.process(second_join)
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
        join_message = t.write_to_database(("JOIN ROSE 25-11-2012", datetime(2016, 10, 30, 10, 5, 5).replace(tzinfo=timezone.get_default_timezone())))
        first_response = t.process(join_message)
        self.assertEqual(first_response, msg_subscribe("English").format(name="Rose"))
        texting_mock.assert_called_with(message=first_response, phone_number="1-111-1114")
        self.assertTrue(Contact.objects.filter(name="Rose", phone_number="1-111-1114", preg_update=False).exists())
        self.assertTrue(t.get_contacts().exists())
        t2 = TextProcessor(phone_number="1-111-1114")
        second_join = t2.write_to_database(("JOIN ROSE 25-11-2012", datetime(2016, 10, 31, 10, 5, 5).replace(tzinfo=timezone.get_default_timezone())))
        second_response = t2.process(second_join)
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
        join_message = t.write_to_database((hindi_remind() + " SANJIV 25-11-2012",
                                            datetime(2016, 10, 30, 10, 5, 5).replace(tzinfo=timezone.get_default_timezone())))
        first_response = t.process(join_message)
        self.assertEqual(first_response, msg_subscribe("Hindi").format(name="Sanjiv"))
        texting_mock.assert_called_with(message=first_response, phone_number="1-111-1115")
        self.assertTrue(Contact.objects.filter(name="Sanjiv", phone_number="1-111-1115", preg_update=False).exists())
        self.assertTrue(t.get_contacts().exists())
        t2 = TextProcessor(phone_number="1-111-1115")
        self.assertTrue(t2.get_contacts().exists())
        second_join = t.write_to_database((hindi_remind() + " SANJIV 25-11-2012",
                                            datetime(2016, 10, 31, 10, 5, 5).replace(tzinfo=timezone.get_default_timezone())))
        second_response = t2.process(second_join)
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
        join_message = t.write_to_database(("JOIN ROSE 25-10-2012",
                                            datetime(2016, 10, 30, 10, 5, 5).replace(tzinfo=timezone.get_default_timezone())))
        first_response = t.process(join_message)
        self.assertEqual(first_response, msg_subscribe("English").format(name="Rose"))
        texting_mock.assert_called_with(message=first_response, phone_number="1-111-1114")
        self.assertTrue(Contact.objects.filter(name="Rose", phone_number="1-111-1114", date_of_birth=datetime(2012, 10, 25, 0, 0), preg_update=False).exists())
        self.assertTrue(t.get_contacts().exists())
        t2 = TextProcessor(phone_number="1-111-1114")
        born_update = t2.write_to_database(("BORN ROSE 25-11-2012",
                                            datetime(2016, 10, 31, 10, 5, 5).replace(tzinfo=timezone.get_default_timezone())))
        second_response = t2.process(born_update)
        self.assertTrue(t2.get_contacts().exists())
        self.assertEqual(second_response, msg_subscribe("English").format(name="Rose"))
        texting_mock.assert_called_with(message=second_response, phone_number="1-111-1114")
        self.assertFalse(Contact.objects.filter(name="Rose", phone_number="1-111-1114", date_of_birth=datetime(2012, 10, 25, 0, 0), preg_update=False).exists())
        self.assertFalse(Contact.objects.filter(name="Rose", phone_number="1-111-1114", date_of_birth=datetime(2012, 11, 25, 0, 0), preg_update=False).exists())
        self.assertTrue(Contact.objects.filter(name="Rose", phone_number="1-111-1114", date_of_birth=datetime(2012, 11, 25, 0, 0), preg_update=True).exists())
        self.assertEqual(1, Contact.objects.all().count())
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
        born_update = t3.write_to_database(("BORN Tina 25-07-2017",
                                            FAKE_NOW.replace(tzinfo=timezone.get_default_timezone())))
        existing_contact_update = t3.process(born_update)
        self.assertEqual(existing_contact_update, msg_subscribe("English").format(name="Tina"))
        texting_mock.assert_called_with(message=existing_contact_update, phone_number="910003456789")
        self.assertFalse(Contact.objects.filter(name="Tina", phone_number="910003456789", language_preference="English", date_of_birth=datetime(2017, 7, 10, 0, 0), preg_signup=True, preg_update=False).exists())
        self.assertFalse(Contact.objects.filter(name="Tina", phone_number="910003456789", language_preference="English", date_of_birth=datetime(2017, 7, 25, 0, 0), preg_signup=True, preg_update=False).exists())
        self.assertTrue(Contact.objects.filter(name="Tina", phone_number="910003456789", language_preference="English", date_of_birth=datetime(2017, 7, 25, 0, 0), preg_signup=True, preg_update=True).exists())
        self.assertEqual(1, Contact.objects.all().count())
        new_contact.delete()

    @patch("modules.text_processor.Texter.send")
    def test_text_in_pregnancy_birthdate_update_hindi(self, texting_mock):
        t = TextProcessor(phone_number="1-111-1114")
        self.assertFalse(Contact.objects.filter(name="Sanjiv", phone_number="1-111-1114").exists())
        join_message = t.write_to_database((hindi_remind() + " Sanjiv 25-10-2012",
                                            datetime(2016, 10, 30, 10, 5, 5).replace(tzinfo=timezone.get_default_timezone())))
        first_response = t.process(join_message)
        self.assertEqual(first_response, msg_subscribe("Hindi").format(name="Sanjiv"))
        texting_mock.assert_called_with(message=first_response, phone_number="1-111-1114")
        self.assertTrue(Contact.objects.filter(name="Sanjiv", phone_number="1-111-1114", date_of_birth=datetime(2012, 10, 25, 0, 0), preg_update=False).exists())
        self.assertTrue(t.get_contacts().exists())
        t2 = TextProcessor(phone_number="1-111-1114")
        born_update = t2.write_to_database((hindi_born() + " Sanjiv 25-11-2012",
                                            datetime(2016, 10, 31, 10, 5, 5).replace(tzinfo=timezone.get_default_timezone())))
        second_response = t2.process(born_update)
        self.assertTrue(t2.get_contacts().exists())
        self.assertEqual(second_response, msg_subscribe("Hindi").format(name="Sanjiv"))
        texting_mock.assert_called_with(message=second_response, phone_number="1-111-1114")
        self.assertFalse(Contact.objects.filter(name="Sanjiv", phone_number="1-111-1114", date_of_birth=datetime(2012, 10, 25, 0, 0), preg_update=False).exists())
        self.assertFalse(Contact.objects.filter(name="Sanjiv", phone_number="1-111-1114", date_of_birth=datetime(2012, 11, 25, 0, 0), preg_update=False).exists())
        self.assertTrue(Contact.objects.filter(name="Sanjiv", phone_number="1-111-1114", date_of_birth=datetime(2012, 11, 25, 0, 0), preg_update=True).exists())
        self.assertTrue(t2.get_contacts().exists())
        self.assertEqual(1, Contact.objects.all().count())
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

    @patch("logging.info")
    @patch("modules.text_processor.Texter.send")
    def test_preg_updates_with_opposite_language_keep_original_language_hindi(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1111")
        join_message = t.write_to_database((hindi_remind() + " Aarav 25-11-2012",
                                            datetime(2016, 10, 30, 10, 5, 5).replace(tzinfo=timezone.get_default_timezone())))
        response = t.process(join_message)
        logging_mock.assert_called_with("Subscribing " + quote(join_message.body) + "...")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")
        contact = Contact.objects.filter(name="Aarav", phone_number="1-111-1111").first()
        self.assertEqual("Hindi", contact.language_preference)

        born_message = t.write_to_database(("BORN Aarav 25-11-2012",
                                            datetime(2016, 10, 31, 10, 5, 5).replace(tzinfo=timezone.get_default_timezone())))
        born_response = t.process(born_message)
        texting_mock.assert_called_with(message=born_response, phone_number="1-111-1111")
        contact = Contact.objects.filter(name="Aarav", phone_number="1-111-1111").first()
        self.assertEqual("Hindi", contact.language_preference)

    @patch("logging.error")
    @patch("logging.info")
    @patch("modules.text_processor.Texter.send")
    def test_subscribe_two_children(self, texting_mock, logging_info_mock, logging_error_mock):
        t = TextProcessor(phone_number="1-111-1120")
        self.assertFalse(Contact.objects.filter(name="Peter", phone_number="1-111-1120").exists())
        self.assertFalse(Contact.objects.filter(name="Ben", phone_number="1-111-1120").exists())
        peter_join = t.write_to_database(("JOIN PETER 11-12-2016",
                                        datetime(2016, 10, 31, 10, 5, 5).replace(tzinfo=timezone.get_default_timezone())))
        first_response = t.process(peter_join)
        self.assertEqual(first_response, msg_subscribe("English").format(name="Peter"))
        texting_mock.assert_called_with(message=first_response, phone_number="1-111-1120")
        self.assertTrue(Contact.objects.filter(name="Peter", phone_number="1-111-1120").exists())
        self.assertEqual(Contact.objects.filter(phone_number="1-111-1120").count(), 1)
        t2 = TextProcessor(phone_number="1-111-1120")
        ben_join = t2.write_to_database(("JOIN BEN 4-10-2016",
                                        datetime(2016, 10, 31, 10, 10, 5).replace(tzinfo=timezone.get_default_timezone())))
        second_response = t2.process(ben_join)
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
        sub_message = t.write_to_database(("JOIN ROB 25-11-2012",
                                            datetime(2016, 10, 31, 10, 5, 5).replace(tzinfo=timezone.get_default_timezone())))
        t.process(sub_message)
        contacts = Contact.objects.filter(name="Rob", phone_number="1-111-1116")
        self.assertTrue(contacts.exists())
        self.assertEqual(contacts.count(), 1)
        self.assertFalse(contacts.first().cancelled)
        t2 = TextProcessor(phone_number="1-111-1116")
        end_message = t.write_to_database(("END",
                                            datetime(2016, 11, 28, 10, 5, 5, 10).replace(tzinfo=timezone.get_default_timezone())))
        t2.process(end_message)
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
        join_message = t.write_to_database(("JOIN CHEYENNE 25-11-2012",
                                            datetime(2016, 10, 29, 10, 5, 5).replace(tzinfo=timezone.get_default_timezone())))
        t.process(join_message)
        contacts = Contact.objects.filter(name="Cheyenne", phone_number="1-111-1117")
        self.assertTrue(contacts.exists())
        self.assertFalse(contacts.first().cancelled)
        t2 = TextProcessor(phone_number="1-111-1117")
        end_message = t2.write_to_database(("END",
                                            datetime(2016, 10, 30, 10, 5, 5).replace(tzinfo=timezone.get_default_timezone())))
        t2.process(end_message)
        contacts = Contact.objects.filter(name="Cheyenne", phone_number="1-111-1117")
        self.assertTrue(contacts.exists())
        self.assertTrue(contacts.first().cancelled)
        t3 = TextProcessor(phone_number="1-111-1117")
        join_again_message = t3.write_to_database(("JOIN CHEYENNE 25-11-2012",
                                                    datetime(2016, 10, 31, 10, 5, 5).replace(tzinfo=timezone.get_default_timezone())))
        t3.process(join_again_message)
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
        join_message = t.write_to_database(("JOIN CHEYENNE 25-11-2012",
                                            datetime(2016, 10, 29, 10, 5, 5).replace(tzinfo=timezone.get_default_timezone())))
        t.process(join_message)
        contacts = Contact.objects.filter(name="Cheyenne", phone_number="1-111-1118")
        self.assertTrue(contacts.exists())
        self.assertEqual(contacts.first().date_of_birth, datetime(2012, 11, 25, 0, 0).date())
        t2 = TextProcessor(phone_number="1-111-1118")
        end_message = t2.write_to_database(("END",
                                            datetime(2016, 10, 30, 10, 5, 5).replace(tzinfo=timezone.get_default_timezone())))
        t2.process(end_message)
        contacts = Contact.objects.filter(name="Cheyenne", phone_number="1-111-1118")
        self.assertTrue(contacts.exists())
        self.assertEqual(contacts.first().date_of_birth, datetime(2012, 11, 25, 0, 0).date())
        t3 = TextProcessor(phone_number="1-111-1118")
        join_again_message = t3.write_to_database(("JOIN CHEYENNE 25-12-2012",
                                                    datetime(2016, 10, 31, 10, 5, 5).replace(tzinfo=timezone.get_default_timezone())))
        t3.process(join_again_message)
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
        join_message = t.write_to_database(("JOIN LARISSA 25-11-2012",
                                            datetime(2017, 10, 31, 10, 5, 5).replace(tzinfo=timezone.get_default_timezone())))
        first_response = t.process(join_message)
        self.assertEqual(first_response, msg_subscribe("English").format(name="Larissa"))
        contacts = Contact.objects.filter(name="Larissa", phone_number="1-111-1118")
        self.assertTrue(contacts.exists())
        self.assertEqual(contacts.first().language_preference, "English")
        t2 = TextProcessor(phone_number="1-111-1118")
        end_message = t2.write_to_database(("END",
                                            datetime(2017, 10, 31, 10, 5, 5).replace(tzinfo=timezone.get_default_timezone())))
        t2.process(end_message)
        t3 = TextProcessor(phone_number="1-111-1118")
        resub_message = t.write_to_database((hindi_remind() + " LARISSA 25-11-2012",
                                            datetime(2017, 10, 31, 10, 5, 5).replace(tzinfo=timezone.get_default_timezone())))
        third_response = t.process(resub_message)
        self.assertEqual(third_response, msg_subscribe("Hindi").format(name="Larissa"))
        contacts = Contact.objects.filter(name="Larissa", phone_number="1-111-1118")
        self.assertTrue(contacts.exists())
        self.assertEqual(contacts.first().language_preference, "Hindi")

    @patch("logging.error")
    @patch("modules.text_processor.Texter.send")
    def test_keyword_failure(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1111")
        message_object = t.write_to_database(("JLORN COACHZ 25-11-2012", FAKE_NOW.replace(tzinfo=timezone.get_default_timezone())))
        response = t.process(message_object)
        self.assertEqual(response, msg_failure("English"))
        logging_mock.assert_called_with("Keyword `jlorn` in message `JLORN COACHZ 25-11-2012` was not understood by the system.")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")

    @patch("logging.error")
    @patch("modules.text_processor.Texter.send")
    def test_keyword_failure_hindi(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1111")
        message_object = t.write_to_database((u'\u0906\u0930 \u0906\u0930\u0935 25-11-2012',
                                                FAKE_NOW.replace(tzinfo=timezone.get_default_timezone())))
        response = t.process(message_object)
        self.assertEqual(response, msg_failure("Hindi"))
        logging_mock.assert_called_with(u'Keyword `\u0906\u0930` in message `\u0906\u0930 \u0906\u0930\u0935 25-11-2012` was not understood by the system.')
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")

    @patch("logging.error")
    @patch("modules.text_processor.Texter.send")
    def test_keyword_failed_date_english(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1111")
        message = t.write_to_database(("JOIN PAULA 25:11:2012", FAKE_NOW.replace(tzinfo=timezone.get_default_timezone())))
        response = t.process(message)
        self.assertEqual(response, msg_failed_date("English"))
        logging_mock.assert_called_with("Date in message `JOIN PAULA 25:11:2012` is invalid.")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")

    @patch("logging.error")
    @patch("modules.text_processor.Texter.send")
    def test_keyword_failed_date_hindi(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1111")
        invalid_text_message = hindi_remind() + " Sai 11,09,2013"
        message_object = t.write_to_database((invalid_text_message, FAKE_NOW.replace(tzinfo=timezone.get_default_timezone())))
        response = t.process(message_object)
        self.assertEqual(response, msg_failed_date("Hindi"))
        logging_mock.assert_called_with("Date in message " + quote(invalid_text_message) + " is invalid.")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")

    @patch("logging.error")
    @patch("modules.text_processor.Texter.send")
    def test_keyword_failed_date_hindi_with_hindi_name(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1111")
        invalid_text_message = hindi_remind() + u' \u0906\u0930\u0935 11,09,2013'
        message_object = t.write_to_database((invalid_text_message, FAKE_NOW.replace(tzinfo=timezone.get_default_timezone())))
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
        message = t.write_to_database("JOIN PAULA 25-11-2012")
        response = t.process(message)
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
        hindi_message = t.write_to_database(hindi_remind() + u' \u0906\u0930\u0935' + " 30-11-2016")
        response = t.process(hindi_message)
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
        no_name_join = t.write_to_database("JOIN 25-11-2012")
        response = t.process(no_name_join)
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
        hindi_no_name_join = t.write_to_database(hindi_remind() + " 30-11-2016")
        response = t.process(hindi_no_name_join)
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
        join_message = t.write_to_database("JOIN Roland 12/11/2017")
        self.assertFalse(Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                direction="Incoming", body="END"))
        t.process(join_message)
        end_message = t.write_to_database("END")
        response = t.process(end_message)
        self.assertTrue(t.get_contacts().first().cancelled)
        self.assertEqual(response, msg_unsubscribe("English"))
        logging_mock.assert_called_with("Unsubscribing `1-111-1112`...")
        texting_mock.assert_called_with(message=response, phone_number="1-111-1112")
        self.assertEqual(1, Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                direction="Incoming", body="END").count())

        t = TextProcessor(phone_number="1-111-1113")
        hindi_sub_message = t.write_to_database(hindi_remind() + u' \u0906\u0930\u0935' + " 30-11-2016")
        t.process(hindi_sub_message)
        self.assertFalse(Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                direction="Incoming", body="END"))
        hindi_end = t.write_to_database("END")
        response = t.process(hindi_end)
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
        fail_message = t.write_to_database("JLORN COACHZ 25-11-2012")
        response = t.process(fail_message)
        self.assertEqual(response, msg_failure("English"))
        logging_mock.assert_called_with("Keyword `jlorn` in message `JLORN COACHZ 25-11-2012` was not understood by the system.")
        texting_mock.assert_called_with(message=response, phone_number="1-111-1111")
        
        self.assertEqual(1, Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                direction="Incoming", body="JLORN COACHZ 25-11-2012").count())
        self.assertEqual(1, Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                direction="Outgoing", body=msg_failure("English")).count())


        t2 = TextProcessor(phone_number="1-111-1112")
        hindi_fail_message = t2.write_to_database(u'\u0906\u0930 \u0906\u0930\u0935 25-11-2012')
        response2 = t2.process(hindi_fail_message)
        self.assertEqual(response2, msg_failure("Hindi"))
        logging_mock.assert_called_with(u'Keyword `\u0906\u0930` in message `\u0906\u0930 \u0906\u0930\u0935 25-11-2012` was not understood by the system.')
        texting_mock.assert_called_with(message=response2, phone_number="1-111-1112")
        self.assertEqual(1, Message.objects.filter(contact=Contact.objects.filter(phone_number=t2.phone_number),
                                                direction="Incoming", body=hindi_fail_message.body).count())
        self.assertEqual(1, Message.objects.filter(contact=Contact.objects.filter(phone_number=t2.phone_number),
                                                direction="Outgoing", body=msg_failure("Hindi")).count())


    @patch("modules.text_processor.Texter.send")
    def test_processing_pregnancy_updates_creates_message_objects(self, texting_mock):
        new_contact, _ = Contact.objects.update_or_create(name="Tina", phone_number="910003456789", language_preference="English", date_of_birth=datetime(2017, 7, 10, 0, 0), preg_signup=True)
        t = TextProcessor(phone_number="910003456789")
        self.assertTrue(t.get_contacts().exists())
        self.assertTrue(Contact.objects.filter(name="Tina", phone_number="910003456789", language_preference="English", date_of_birth=datetime(2017, 7, 10, 0, 0), preg_signup=True, preg_update=False).exists())
        born_message = t.write_to_database("BORN Tina 25-07-2017")
        existing_contact_update = t.process(born_message)
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
        hin_born_message = t2.write_to_database(hindi_born() + " Sanjiv 25-07-2017")
        existing_contact_update = t2.process(hin_born_message)
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
        t_end_message = t.write_to_database("END")
        t.process(t_end_message)

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
        t5_message = t5.write_to_database(hindi_remind() + u' \u0906\u0930\u0935' + " 30-11-2016")
        response = t5.process(t5_message)
        self.assertTrue(Contact.objects.filter(name=u'\u0906\u0930\u0935', phone_number="1-111-1115").exists())
        self.assertEqual(1, Message.objects.filter(contact=Contact.objects.get(phone_number=t5.phone_number),
                                                    direction="Outgoing", body=msg_subscribe("Hindi").format(name=u'\u0906\u0930\u0935')).count())
        logging_mock.assert_called_with("Subscribing " + quote(hindi_remind() + u' \u0906\u0930\u0935' + " 30-11-2016") + "...")
        texting_mock.assert_called_with(message=response, phone_number="1-111-1115")

        t6 = TextProcessor(phone_number="1-111-1116")
        t6_message = t6.write_to_database(hindi_information() + " SMITH 25-11-2012")
        t6.process(t6_message)
        t7 = TextProcessor(phone_number="1-111-1117")
        t7_message = t7.write_to_database(hindi_information() + " Aaja 25-11-2012")
        t7.process(t7_message)
        t8 = TextProcessor(phone_number="1-111-1118")
        t8_message = t8.write_to_database(hindi_information() + " Lauren 25-11-2012")
        t8.process(t8_message)
        t5_end_message = t5.write_to_database("END")
        t5.process(t5_end_message)

        self.assertEqual(2, Message.objects.filter(contact=Contact.objects.filter(phone_number=t5.phone_number),
                                                direction="Incoming").count())
        self.assertEqual(2, Message.objects.filter(contact=Contact.objects.get(phone_number=t5.phone_number),
                                                    direction="Outgoing").count())

        self.assertEqual(10, Message.objects.filter(direction="Outgoing").count())
        self.assertEqual(10, Message.objects.filter(direction="Incoming").count())
        self.assertEqual(20, Message.objects.all().count())

        self.assertEqual(10, texting_mock.call_count)

    @patch("logging.error")
    def test_processing_updates_contact_last_heard_from_english(self, logging_error):
        t = TextProcessor(phone_number="1-111-1111")
        join_message = t.write_to_database("JOIN PAULA 25-11-2012")
        t.process(join_message)
        original_contact = Contact.objects.filter(name="Paula", phone_number="1-111-1111").first()
        
        t2 = TextProcessor(phone_number="1-111-1111")
        fail_message = t2.write_to_database("Stuff")
        t2.process(fail_message)
        fail_contact = Contact.objects.filter(name="Paula", phone_number="1-111-1111").first()
        self.assertNotEqual(original_contact.last_heard_from, fail_contact.last_heard_from)
        self.assertLess(original_contact.last_heard_from, fail_contact.last_heard_from)
        self.assertEqual(fail_message.created_at, fail_contact.last_heard_from)

        t3 = TextProcessor(phone_number="1-111-1111")
        born_message = t3.write_to_database("BORN PAULA 25-11-2012")
        born_response = t3.process(born_message)
        updated_contact = Contact.objects.filter(name="Paula", phone_number="1-111-1111").first()
        self.assertNotEqual(fail_contact.last_heard_from, updated_contact.last_heard_from)
        self.assertLess(fail_contact.last_heard_from, updated_contact.last_heard_from)
        self.assertEqual(born_message.created_at, updated_contact.last_heard_from)

        stop_message = t3.write_to_database("STOP")
        stop_response = t3.process(born_message)
        stop_contact = Contact.objects.filter(name="Paula", phone_number="1-111-1111").first()
        self.assertNotEqual(updated_contact.last_heard_from, stop_contact.last_heard_from)
        self.assertLess(updated_contact.last_heard_from, stop_contact.last_heard_from)
        self.assertEqual(stop_message.created_at, stop_contact.last_heard_from)

        t4 = TextProcessor(phone_number="1-111-1111")
        rejoin_message = t.write_to_database("JOIN PAULA 25-11-2012")
        t4.process(join_message)
        rejoin_contact = Contact.objects.filter(name="Paula", phone_number="1-111-1111").first()
        self.assertNotEqual(stop_contact.last_heard_from, rejoin_contact.last_heard_from)
        self.assertLess(stop_contact.last_heard_from, rejoin_contact.last_heard_from)
        self.assertEqual(stop_message.created_at, stop_contact.last_heard_from)
        self.assertEqual(1, Contact.objects.filter(name="Paula", phone_number="1-111-1111").count())

    @patch("logging.error")
    def test_processing_updates_contact_last_heard_from_during_unsub(self, logging_error):
        t = TextProcessor(phone_number="1-111-1111")
        join_message = t.write_to_database("JOIN PAULA 25-11-2012")
        t.process(join_message)
        original_contact = Contact.objects.filter(name="Paula", phone_number="1-111-1111").first()

        end_message = t.write_to_database("END")
        t.process(end_message)
        end_contact = Contact.objects.filter(name="Paula", phone_number="1-111-1111").first()
        self.assertEqual(end_message.created_at, end_contact.last_heard_from)
        self.assertNotEqual(original_contact.last_heard_from, end_contact.last_heard_from)
        self.assertLess(original_contact.last_heard_from, end_contact.last_heard_from)
        
        t2 = TextProcessor(phone_number="1-111-4444")
        second_join_message = t2.write_to_database("JOIN Namey 25-11-2014")
        t2.process(second_join_message)
        second_join_contact = Contact.objects.filter(name="Namey", phone_number="1-111-4444").first()
        self.assertNotEqual(original_contact.last_heard_from, second_join_contact.last_heard_from)
        self.assertLess(original_contact.last_heard_from, second_join_contact.last_heard_from)
        self.assertEqual(second_join_message.created_at, second_join_contact.last_heard_from)

        t3 = TextProcessor(phone_number="1-111-4444")
        second_end_message = t3.write_to_database("END")
        t3.process(second_end_message)
        second_end_contact = Contact.objects.filter(name="Namey", phone_number="1-111-4444").first()
        self.assertNotEqual(second_join_contact.last_heard_from, second_end_contact.last_heard_from)
        self.assertLess(second_join_contact.last_heard_from, second_end_contact.last_heard_from)
        self.assertEqual(second_end_message.created_at, second_end_contact.last_heard_from)

    @patch("logging.info")
    @patch("modules.text_processor.Texter.send")
    def test_processing_updates_contact_last_heard_from_hindi(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1111")
        join_message = hindi_remind() + " Aarav 25-11-2012"
        join_message = t.write_to_database(hindi_remind() + " Aarav 25-11-2012")
        response = t.process(join_message)
        original_contact = Contact.objects.filter(name="Aarav", phone_number="1-111-1111").first()
        logging_mock.assert_called_with("Subscribing " + quote(join_message.body) + "...")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")

        born_message = t.write_to_database("BORN Aarav 25-11-2012")
        born_response = t.process(born_message)
        texting_mock.assert_called_with(message=born_response, phone_number="1-111-1111")
        updated_contact = Contact.objects.filter(name="Aarav", phone_number="1-111-1111").first()
        self.assertNotEqual(original_contact.last_heard_from, updated_contact.last_heard_from)
        self.assertLess(original_contact.last_heard_from, updated_contact.last_heard_from)
        
        end_message = t.write_to_database("END")
        end_response = t.process(end_message)
        texting_mock.assert_called_with(message=end_response, phone_number="1-111-1111")
        unsub_contact = Contact.objects.filter(name="Aarav", phone_number="1-111-1111").first()
        self.assertNotEqual(original_contact.last_heard_from, unsub_contact.last_heard_from)
        self.assertLess(original_contact.last_heard_from, unsub_contact.last_heard_from)
        self.assertNotEqual(updated_contact.last_heard_from, unsub_contact.last_heard_from)
        self.assertLess(updated_contact.last_heard_from, unsub_contact.last_heard_from)

    @patch("logging.error")
    def test_processing_updates_contact_last_heard_from_for_failures(self, logging_error_mock):
        t = TextProcessor(phone_number="1-111-1111")
        join_message = t.write_to_database("JOIN PAULA 25-11-2012")
        response = t.process(join_message)
        original_contact = Contact.objects.filter(name="Paula", phone_number="1-111-1111").first()
        
        fail_message = t.write_to_database("Nonsense")
        fail_response = t.process(fail_message)
        fail_contact = Contact.objects.filter(name="Paula", phone_number="1-111-1111").first()
        logging_error_mock.assert_called()
        self.assertNotEqual(original_contact.last_heard_from, fail_contact.last_heard_from)
        self.assertLess(original_contact.last_heard_from, fail_contact.last_heard_from)

        t2 = TextProcessor(phone_number="1-111-3333")
        hin_join_message = hindi_remind() + " Aarav 25-11-2012"
        hin_join_message = t2.write_to_database(hindi_remind() + " Aarav 25-11-2012")
        response = t2.process(hin_join_message)
        hin_original_contact = Contact.objects.filter(name="Aarav", phone_number="1-111-3333").first()
        
        hin_fail_message = t2.write_to_database(u"\u0926\u093f\u0928")
        hin_fail_response = t2.process(hin_fail_message)
        self.assertEqual(2, logging_error_mock.call_count)
        hin_fail_contact = Contact.objects.filter(name="Aarav", phone_number="1-111-3333").first()
        self.assertNotEqual(hin_original_contact.last_heard_from, hin_fail_contact.last_heard_from)
        self.assertLess(hin_original_contact.last_heard_from, hin_fail_contact.last_heard_from)

    @patch("logging.info")
    @patch("modules.text_processor.Texter.send")
    def test_processing_updates_contact_last_contacted_english(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1111")
        join_message = t.write_to_database("JOIN PAULA 25-11-2012")
        response = t.process(join_message)
        original_contact = Contact.objects.filter(name="Paula", phone_number="1-111-1111").first()
        logging_mock.assert_called_with("Subscribing `JOIN PAULA 25-11-2012`...")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")

        born_update = t.write_to_database("BORN PAULA 25-11-2012")
        born_response = t.process(born_update)
        texting_mock.assert_called_with(message=born_response, phone_number="1-111-1111")
        updated_contact = Contact.objects.filter(name="Paula", phone_number="1-111-1111").first()
        self.assertNotEqual(original_contact.last_contacted, updated_contact.last_contacted)
        self.assertLess(original_contact.last_contacted, updated_contact.last_contacted)
        
        end_message = t.write_to_database("END")
        end_response = t.process(end_message)
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
        join_message = t.write_to_database(hindi_remind() + " Aarav 25-11-2012")
        response = t.process(join_message)
        original_contact = Contact.objects.filter(name="Aarav", phone_number="1-111-1111").first()
        original_last_contacted = original_contact.last_contacted
        logging_mock.assert_called_with("Subscribing " + quote(join_message.body) + "...")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")

        born_message = t.write_to_database("BORN Aarav 25-11-2012")
        born_response = t.process(born_message)
        texting_mock.assert_called_with(message=born_response, phone_number="1-111-1111")
        updated_contact = Contact.objects.filter(name="Aarav", phone_number="1-111-1111").first()
        self.assertNotEqual(original_last_contacted, updated_contact.last_contacted)
        self.assertLess(original_contact.last_contacted, updated_contact.last_contacted)
        
        end_message = t.write_to_database("END")
        end_response = t.process(end_message)
        texting_mock.assert_called_with(message=end_response, phone_number="1-111-1111")
        unsub_contact = Contact.objects.filter(name="Aarav", phone_number="1-111-1111").first()
        self.assertNotEqual(original_contact.last_contacted, unsub_contact.last_contacted)
        self.assertLess(original_contact.last_contacted, unsub_contact.last_contacted)
        self.assertNotEqual(updated_contact.last_contacted, unsub_contact.last_contacted)
        self.assertLess(updated_contact.last_contacted, unsub_contact.last_contacted)

    @patch("logging.error")
    def test_processing_updates_contact_last_contacted_for_failures_english(self, logging_error_mock):
        t = TextProcessor(phone_number="1-111-1111")
        join_message = t.write_to_database("JOIN PAULA 25-11-2012")
        response = t.process(join_message)
        original_contact = Contact.objects.filter(name="Paula", phone_number="1-111-1111").first()
        
        fail_message = t.write_to_database("Nonsense")
        fail_response = t.process(fail_message)
        fail_contact = Contact.objects.filter(name="Paula", phone_number="1-111-1111").first()
        logging_error_mock.assert_called()
        fail_message_object = Message.objects.filter(direction="Outgoing", body=fail_response).first()
        self.assertEqual(1, logging_error_mock.call_count)
        self.assertEqual(fail_message_object.created_at, fail_contact.last_contacted)
        self.assertNotEqual(original_contact.last_contacted, fail_contact.last_contacted)
        self.assertLess(original_contact.last_contacted, fail_contact.last_contacted)

    @patch("logging.error")
    def test_processing_updates_contact_last_contacted_for_failures_hindi(self, logging_error_mock):
        t2 = TextProcessor(phone_number="1-111-3333")
        hin_join_message = hindi_remind() + " Aarav 25-11-2012"
        hin_join_message = t2.write_to_database(hindi_remind() + " Aarav 25-11-2012")
        response = t2.process(hin_join_message)
        hin_original_contact = Contact.objects.filter(name="Aarav", phone_number="1-111-3333").first()
        
        hin_fail_message = t2.write_to_database(u"\u0926\u093f\u0928")
        hin_fail_response = t2.process(hin_fail_message)
        hin_fail_message_object = Message.objects.filter(direction="Outgoing", body=hin_fail_response).first()
        self.assertEqual(1, logging_error_mock.call_count)
        hin_fail_contact = Contact.objects.filter(name="Aarav", phone_number="1-111-3333").first()
        self.assertEqual(hin_fail_message_object.created_at, hin_fail_contact.last_contacted)
        self.assertNotEqual(hin_original_contact.last_contacted, hin_fail_contact.last_contacted)
        self.assertLess(hin_original_contact.last_contacted, hin_fail_contact.last_contacted)

    @patch("logging.info")
    @patch("modules.text_processor.Texter.send")
    def test_processing_makes_contact_last_heard_from_time_message_time(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1111")
        join_message = t.write_to_database("JOIN PAULA 25-11-2012")
        response = t.process(join_message)
        original_contact = Contact.objects.filter(name="Paula", phone_number="1-111-1111").first()
        logging_mock.assert_called_with("Subscribing `JOIN PAULA 25-11-2012`...")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")
        join_message_object = Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                direction="Incoming", body="JOIN PAULA 25-11-2012").first()
        self.assertEqual(join_message_object.created_at, original_contact.last_heard_from)

        born_message = t.write_to_database("BORN PAULA 25-11-2012")
        born_response = t.process(born_message)
        texting_mock.assert_called_with(message=born_response, phone_number="1-111-1111")
        born_message_object = Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                    direction="Incoming", body="BORN PAULA 25-11-2012").first()
        updated_contact = Contact.objects.filter(name="Paula", phone_number="1-111-1111").first()
        self.assertEqual(born_message_object.created_at, updated_contact.last_heard_from)
        
        end_message = t.write_to_database("END")
        end_response = t.process(end_message)
        texting_mock.assert_called_with(message=end_response, phone_number="1-111-1111")
        end_message_object = Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                    direction="Incoming", body="END").first()
        unsub_contact = Contact.objects.filter(name="Paula", phone_number="1-111-1111").first()
        self.assertEqual(end_message_object.created_at, unsub_contact.last_heard_from)

    @patch("logging.info")
    @patch("modules.text_processor.Texter.send")
    def test_processing_makes_contact_last_contacted_time_message_time(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1111")
        join_message = t.write_to_database("JOIN PAULA 25-11-2012")
        response = t.process(join_message)
        original_contact = Contact.objects.filter(name="Paula", phone_number="1-111-1111").first()
        logging_mock.assert_called_with("Subscribing `JOIN PAULA 25-11-2012`...")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")
        subscribe_message = Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                direction="Outgoing", body=msg_subscribe("English").format(name="Paula")).first()
        self.assertEqual(subscribe_message.created_at, original_contact.last_contacted)

        born_message = t.write_to_database("BORN PAULA 25-11-2012")
        born_response = t.process(born_message)
        texting_mock.assert_called_with(message=born_response, phone_number="1-111-1111")
        subscribe_message2 = Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                direction="Outgoing", body=msg_subscribe("English").format(name="Paula")).last()
        updated_contact = Contact.objects.filter(name="Paula", phone_number="1-111-1111").first()
        self.assertEqual(subscribe_message2.created_at, updated_contact.last_contacted)
        
        end_message = t.write_to_database("END")
        end_response = t.process(end_message)
        texting_mock.assert_called_with(message=end_response, phone_number="1-111-1111")
        end_message_object = Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                direction="Outgoing", body=msg_unsubscribe("English")).first()
        unsub_contact = Contact.objects.filter(name="Paula", phone_number="1-111-1111").first()
        self.assertEqual(end_message_object.created_at, unsub_contact.last_contacted)

    @patch("logging.error")
    @patch("modules.text_processor.Texter.send")
    def test_processing_english_failed_messages_updates_contact_time_references(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1111")
        keyword = "SDFDAJFDF"
        fail_message = t.write_to_database("SDFDAJFDF PAULA 25-11-2012")
        response = t.process(fail_message)
        original_contact = Contact.objects.filter(phone_number="1-111-1111").first()
        logging_mock.assert_called_with("Keyword " + quote(keyword.lower()) + " in message " + quote(fail_message.body) +
                          " was not understood by the system.")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")
        fail_message_object = Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                        direction="Incoming", body=fail_message.body).first()
        failed_message_response = Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                        direction="Outgoing", body=msg_failure("English")).first()
        self.assertEqual(fail_message_object.created_at, original_contact.last_heard_from)
        self.assertEqual(failed_message_response.created_at, original_contact.last_contacted)

        failed_date_message = t.write_to_database("BORN PAULA 60-11-2012")
        failed_date_response = t.process(failed_date_message)
        updated_contact = Contact.objects.filter(phone_number="1-111-1111").first()
        fail_date_object = Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                        direction="Incoming", body="BORN PAULA 60-11-2012").first()
        failed_date_response = Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                        direction="Outgoing", body=msg_failed_date("English")).first()
        self.assertEqual(fail_date_object.created_at, updated_contact.last_heard_from)
        self.assertEqual(failed_date_response.created_at, updated_contact.last_contacted)

    @patch("logging.error")
    @patch("modules.text_processor.Texter.send")
    def test_processing_hindi_failed_messages_updates_contact_time_references(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1111")
        keyword = u"\u0906\u092a"
        fail_message = t.write_to_database(keyword + " Aarav 25-11-2012")
        response = t.process(fail_message)
        original_contact = Contact.objects.filter(phone_number="1-111-1111").first()
        logging_mock.assert_called_with("Keyword " + quote(keyword.lower()) + " in message " + quote(fail_message.body) +
                          " was not understood by the system.")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")
        fail_message_object = Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                        direction="Incoming", body=fail_message).first()
        failed_message_response = Message.objects.filter(contact=Contact.objects.filter(phone_number=t.phone_number),
                                                        direction="Outgoing", body=msg_failure("Hindi")).first()
        self.assertEqual(fail_message_object.created_at, original_contact.last_heard_from)
        self.assertEqual(failed_message_response.created_at, original_contact.last_contacted)

    @patch("logging.error")
    @patch("modules.text_processor.Texter.send")
    def test_processing_only_updates_contact_time_references_for_correct_contact(self, texting_mock, logging_mock):
        t = TextProcessor(phone_number="1-111-1111")
        keyword = "SDFDAJFDF"
        fail_message = t.write_to_database("SDFDAJFDF PAULA 25-11-2012")
        response = t.process(fail_message)
        original_contact = Contact.objects.filter(phone_number="1-111-1111").first()
        logging_mock.assert_called_with("Keyword " + quote(keyword.lower()) + " in message " + quote(fail_message.body) +
                          " was not understood by the system.")
        texting_mock.assert_called_once_with(message=response, phone_number="1-111-1111")

        t2 = TextProcessor(phone_number="5-555-5555")
        failed_date = t2.write_to_database("BORN PAULA 60-11-2012")
        failed_date_response = t2.process(failed_date)
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

    def test_write_to_database_finds_existing_contact_names_english(self):
        t = TextProcessor(phone_number="1-111-1111")
        self.assertFalse(Message.objects.filter(contact=Contact.objects.filter(phone_number="1-111-1111").first()))
        incoming = t.write_to_database("JOIN Marshall 20-10-2017")
        t.process(incoming)
        contact = Contact.objects.get(phone_number=t.phone_number)
        self.assertEqual("Marshall", contact.name)
        t.write_to_database("END")
        end_message = Message.objects.get(body="END", direction="Incoming")
        t.process(end_message)
        self.assertEqual(contact.name, end_message.contact.name)
        self.assertEqual(contact.id, end_message.contact.id)
        self.assertEqual(1, Contact.objects.all().count())

        second_contact = self.create_contact(name="Existy",
                                            phone_number="9101234567890",
                                            delay_in_days=0,
                                            language_preference="English",
                                            method_of_sign_up="Door to Door")
        t2 = TextProcessor(phone_number="9101234567890")
        self.assertTrue(Contact.objects.get(pk=second_contact.id))
        t2.write_to_database("END")
        second_end_message = Message.objects.get(contact=second_contact, body="END", direction="Incoming")
        t2.process(end_message)
        self.assertEqual(second_contact.name, second_end_message.contact.name)
        self.assertEqual(second_contact.id, second_end_message.contact.id)
        self.assertEqual(2, Contact.objects.all().count())

    def test_write_to_database_finds_existing_contact_names_hindi(self):
        t = TextProcessor(phone_number="1-111-1111")
        self.assertFalse(Message.objects.filter(contact=Contact.objects.filter(phone_number="1-111-1111").first()))
        incoming = t.write_to_database(hindi_remind() + " Marshall 20-10-2017")
        t.process(incoming)
        contact = Contact.objects.get(phone_number=t.phone_number)
        self.assertEqual("Marshall", contact.name)
        t.write_to_database("END")
        contact = Contact.objects.get(phone_number=t.phone_number)
        end_message = Message.objects.get(body="END", direction="Incoming")
        t.process(end_message)
        self.assertEqual(contact.name, end_message.contact.name)
        self.assertEqual(contact.id, end_message.contact.id)
        self.assertEqual(1, Contact.objects.all().count())

    def test_write_to_database_assigns_incoming_datetime_as_message_received_at_english(self):
        t = TextProcessor(phone_number="1-111-1111")
        self.assertFalse(Message.objects.filter(contact=Contact.objects.filter(phone_number="1-111-1111").first()))
        incoming = t.write_to_database(("JOIN Marshall 20-10-2017", datetime(2017, 6, 5, 10, 15).replace(tzinfo=timezone.get_default_timezone())))
        self.assertEqual(incoming.received_at, datetime(2017, 6, 5, 10, 15).replace(tzinfo=timezone.get_default_timezone()))
        t.process(incoming)
        self.assertEqual(incoming.received_at, datetime(2017, 6, 5, 10, 15).replace(tzinfo=timezone.get_default_timezone()))
        contact = Contact.objects.get(phone_number=t.phone_number)
        born = t.write_to_database(("BORN Marshall 20-10-2017", datetime(2017, 6, 8, 10, 15).replace(tzinfo=timezone.get_default_timezone())))
        self.assertEqual(born.received_at, datetime(2017, 6, 8, 10, 15).replace(tzinfo=timezone.get_default_timezone()))
        t.process(born)
        self.assertEqual(born.received_at, datetime(2017, 6, 8, 10, 15).replace(tzinfo=timezone.get_default_timezone()))
        t.write_to_database(("END", datetime(2017, 6, 6, 0, 5).replace(tzinfo=timezone.get_default_timezone())))
        end_message = Message.objects.get(body="END", direction="Incoming")
        self.assertEqual(end_message.received_at, datetime(2017, 6, 6, 0, 5).replace(tzinfo=timezone.get_default_timezone()))
        t.process(end_message)
        self.assertEqual(end_message.received_at, datetime(2017, 6, 6, 0, 5).replace(tzinfo=timezone.get_default_timezone()))
        self.assertEqual(1, Contact.objects.all().count())

        second_contact = self.create_contact(name="Existy",
                                            phone_number="9101234567890",
                                            delay_in_days=0,
                                            language_preference="English",
                                            method_of_sign_up="Door to Door")
        t2 = TextProcessor(phone_number="9101234567890")
        self.assertTrue(Contact.objects.get(pk=second_contact.id))
        t2.write_to_database(("END", datetime(2017, 10, 6, 0, 5).replace(tzinfo=timezone.get_default_timezone())))
        second_end_message = Message.objects.get(contact=second_contact, body="END", direction="Incoming")
        self.assertEqual(second_end_message.received_at, datetime(2017, 10, 6, 0, 5).replace(tzinfo=timezone.get_default_timezone()))
        t2.process(end_message)
        self.assertEqual(second_end_message.received_at, datetime(2017, 10, 6, 0, 5).replace(tzinfo=timezone.get_default_timezone()))
        self.assertEqual(second_contact.id, second_end_message.contact.id)

    def test_write_to_database_assigns_incoming_datetime_as_message_received_at_hindi(self):
        t = TextProcessor(phone_number="1-111-1111")
        self.assertFalse(Message.objects.filter(contact=Contact.objects.filter(phone_number="1-111-1111").first()))
        incoming = t.write_to_database((hindi_remind() + " Marshall 20-10-2017", datetime(2017, 6, 5, 10, 15).replace(tzinfo=timezone.get_default_timezone())))
        self.assertEqual(incoming.received_at, datetime(2017, 6, 5, 10, 15).replace(tzinfo=timezone.get_default_timezone()))
        t.process(incoming)
        self.assertEqual(incoming.received_at, datetime(2017, 6, 5, 10, 15).replace(tzinfo=timezone.get_default_timezone()))
        born = t.write_to_database((hindi_born() + " Marshall 20-10-2017", datetime(2017, 6, 8, 10, 15).replace(tzinfo=timezone.get_default_timezone())))
        self.assertEqual(born.received_at, datetime(2017, 6, 8, 10, 15).replace(tzinfo=timezone.get_default_timezone()))
        t.process(born)
        self.assertEqual(born.received_at, datetime(2017, 6, 8, 10, 15).replace(tzinfo=timezone.get_default_timezone()))
        
        t.write_to_database(("END", datetime(2017, 6, 10, 0, 5).replace(tzinfo=timezone.get_default_timezone())))
        end_message = Message.objects.get(body="END", direction="Incoming")
        self.assertEqual(end_message.received_at, datetime(2017, 6, 10, 0, 5).replace(tzinfo=timezone.get_default_timezone()))
        t.process(end_message)
        self.assertEqual(end_message.received_at, datetime(2017, 6, 10, 0, 5).replace(tzinfo=timezone.get_default_timezone()))
        self.assertEqual(1, Contact.objects.all().count())

        second_contact = self.create_contact(name="Existy",
                                            phone_number="9101234567890",
                                            delay_in_days=0,
                                            language_preference="Hindi",
                                            method_of_sign_up="Door to Door")
        t2 = TextProcessor(phone_number="9101234567890")
        self.assertTrue(Contact.objects.get(pk=second_contact.id))
        t2.write_to_database(("END", datetime(2017, 10, 6, 0, 5).replace(tzinfo=timezone.get_default_timezone())))
        second_end_message = Message.objects.get(contact=second_contact, body="END", direction="Incoming")
        self.assertEqual(second_end_message.received_at, datetime(2017, 10, 6, 0, 5).replace(tzinfo=timezone.get_default_timezone()))
        t2.process(end_message)
        self.assertEqual(second_end_message.received_at, datetime(2017, 10, 6, 0, 5).replace(tzinfo=timezone.get_default_timezone()))
        self.assertEqual(second_contact.id, second_end_message.contact.id)

    @patch("logging.error")
    def test_write_to_database_assigns_incoming_datetime_as_message_received_at_for_failures(self, logging_error):
        t = TextProcessor(phone_number="1-111-1111")
        self.assertFalse(Message.objects.filter(contact=Contact.objects.filter(phone_number="1-111-1111").first()))
        incoming = t.write_to_database(("JOIN Marshall 20-10-2017", datetime(2017, 6, 5, 10, 15).replace(tzinfo=timezone.get_default_timezone())))
        t.process(incoming)
        contact = Contact.objects.get(phone_number=t.phone_number)
        fail_incoming = t.write_to_database(("NOT READABLE", datetime(2017, 6, 8, 10, 15).replace(tzinfo=timezone.get_default_timezone())))
        self.assertEqual(fail_incoming.received_at, datetime(2017, 6, 8, 10, 15).replace(tzinfo=timezone.get_default_timezone()))
        t.process(fail_incoming)
        self.assertEqual(fail_incoming.received_at, datetime(2017, 6, 8, 10, 15).replace(tzinfo=timezone.get_default_timezone()))
        t.write_to_database(("---ASDFad", datetime(2017, 6, 6, 0, 5).replace(tzinfo=timezone.get_default_timezone())))
        fail_two = Message.objects.get(body="---ASDFad", direction="Incoming")
        self.assertEqual(fail_two.received_at, datetime(2017, 6, 6, 0, 5).replace(tzinfo=timezone.get_default_timezone()))
        t.process(fail_two)
        self.assertEqual(fail_two.received_at, datetime(2017, 6, 6, 0, 5).replace(tzinfo=timezone.get_default_timezone()))
        
        t.write_to_database((" ", datetime(2017, 6, 6, 0, 45).replace(tzinfo=timezone.get_default_timezone())))
        empty_fail = Message.objects.get(body=" ", direction="Incoming")
        self.assertEqual(empty_fail.received_at, datetime(2017, 6, 6, 0, 45).replace(tzinfo=timezone.get_default_timezone()))
        t.process(empty_fail)
        self.assertEqual(empty_fail.received_at, datetime(2017, 6, 6, 0, 45).replace(tzinfo=timezone.get_default_timezone()))
        self.assertEqual(1, Contact.objects.all().count())

        t2 = TextProcessor(phone_number="1-111-2222")
        self.assertFalse(Message.objects.filter(contact=Contact.objects.filter(phone_number="1-111-2222").first()))
        incoming = t2.write_to_database((hindi_information() + " Marshall 20-10-2017", datetime(2017, 6, 5, 10, 15).replace(tzinfo=timezone.get_default_timezone())))
        t2.process(incoming)
        contact = Contact.objects.get(phone_number=t.phone_number)
        fail_incoming = t2.write_to_database((u"\u0936\u093f\u0936", datetime(2017, 6, 8, 10, 15).replace(tzinfo=timezone.get_default_timezone())))
        self.assertEqual(fail_incoming.received_at, datetime(2017, 6, 8, 10, 15).replace(tzinfo=timezone.get_default_timezone()))
        t2.process(fail_incoming)
        self.assertEqual(fail_incoming.received_at, datetime(2017, 6, 8, 10, 15).replace(tzinfo=timezone.get_default_timezone()))
        t.write_to_database((u"\u0940\u091c\u093f", datetime(2017, 6, 6, 0, 5).replace(tzinfo=timezone.get_default_timezone())))
        fail_two = Message.objects.get(body=u"\u0940\u091c\u093f", direction="Incoming")
        self.assertEqual(fail_two.received_at, datetime(2017, 6, 6, 0, 5).replace(tzinfo=timezone.get_default_timezone()))
        t2.process(fail_two)
        self.assertEqual(fail_two.received_at, datetime(2017, 6, 6, 0, 5).replace(tzinfo=timezone.get_default_timezone()))
        self.assertEqual(2, Contact.objects.all().count())

    def test_processing_updates_message_is_processed_hindi(self):
        t2 = TextProcessor(phone_number="1-111-1111")
        self.assertFalse(Message.objects.filter(contact=Contact.objects.filter(phone_number="1-111-1111").first()))
        hindi_join = t2.write_to_database(hindi_remind() + " Marshall 20-10-2017")
        self.assertFalse(hindi_join.is_processed)
        contact = Message.objects.filter(contact=Contact.objects.filter(phone_number="1-111-1111")).first().contact
        self.assertEqual(1, Message.objects.filter(contact=contact).count())
        t2.process(hindi_join)
        self.assertEqual(2, Message.objects.filter(contact=contact).count())
        hindi_join = Message.objects.filter(contact=contact, direction="Incoming").first()
        self.assertTrue(hindi_join.is_processed)
        outgoing = Message.objects.filter(contact=contact, direction="Outgoing").first()
        self.assertTrue(outgoing.is_processed)
        hindi_end_message = t2.write_to_database("END")
        self.assertFalse(hindi_end_message.is_processed)
        t2.process(hindi_end_message)
        eng_end_message = Message.objects.filter(contact=contact, body="END").first()
        self.assertTrue(hindi_end_message.is_processed)

    def test_processing_updates_message_is_processed_english(self):
        t2 = TextProcessor(phone_number="1-111-2222")
        self.assertFalse(Message.objects.filter(contact=Contact.objects.filter(phone_number="1-111-2222").first()))
        eng_join = t2.write_to_database("JOIN Marshall 20-10-2017")
        self.assertFalse(eng_join.is_processed)
        contact = Message.objects.filter(contact=Contact.objects.filter(phone_number="1-111-2222")).first().contact
        self.assertEqual(1, Message.objects.filter(contact=contact).count())
        t2.process(eng_join)
        self.assertEqual(2, Message.objects.filter(contact=contact).count())
        eng_join = Message.objects.filter(contact=contact, direction="Incoming").first()
        self.assertTrue(eng_join.is_processed)
        outgoing = Message.objects.filter(contact=contact, direction="Outgoing").first()
        self.assertTrue(outgoing.is_processed)
        eng_end_message = t2.write_to_database("END")
        self.assertFalse(eng_end_message.is_processed)
        t2.process(eng_end_message)
        eng_end_message = Message.objects.filter(contact=contact, body="END").first()
        self.assertTrue(eng_end_message.is_processed)

    @patch("modules.text_processor.Texter.send")
    def test_processing_assigns_message_sent_at_to_now_english(self, texting_mock):
        with freeze_time(datetime(2017, 7, 17, 0, 0)):
            t2 = TextProcessor(phone_number="1-111-2222")
            self.assertFalse(Message.objects.filter(contact=Contact.objects.filter(phone_number="1-111-2222").first()))
            eng_join = t2.write_to_database("JOIN Marshall 20-10-2017")
            contact = Message.objects.filter(contact=Contact.objects.filter(phone_number="1-111-2222")).first().contact
            self.assertEqual(1, Message.objects.filter(contact=contact).count())
            t2.process(eng_join)
            self.assertEqual(2, Message.objects.filter(contact=contact).count())
            join_outgoing = Message.objects.filter(contact=contact, direction="Outgoing").first()
            self.assertEqual(datetime.now().replace(tzinfo=timezone.get_default_timezone()), join_outgoing.sent_at)

            eng_born_message = t2.write_to_database("BORN Marshall 20-10-2017")
            born_outgoing_response_body = t2.process(eng_born_message)
            self.assertEqual(4, Message.objects.filter(contact=contact).count())
            born_outgoing = Message.objects.filter(contact=contact, body=born_outgoing_response_body).first()
            self.assertEqual(datetime.now().replace(tzinfo=timezone.get_default_timezone()), born_outgoing.sent_at)

            eng_end_message = t2.write_to_database("END")
            end_outgoing_response_body = t2.process(eng_end_message)
            self.assertEqual(6, Message.objects.filter(contact=contact).count())
            end_outgoing = Message.objects.filter(contact=contact, body=end_outgoing_response_body).first()
            self.assertEqual(datetime.now().replace(tzinfo=timezone.get_default_timezone()), end_outgoing.sent_at)
        
        self.assertNotEqual(datetime.now().replace(tzinfo=timezone.get_default_timezone()), join_outgoing.sent_at)
        self.assertNotEqual(datetime.now().replace(tzinfo=timezone.get_default_timezone()), born_outgoing.sent_at)
        self.assertNotEqual(datetime.now().replace(tzinfo=timezone.get_default_timezone()), end_outgoing.sent_at)

        with freeze_time(datetime(2017, 7, 17, 5, 10)):
            t3 = TextProcessor(phone_number="1-111-5555")
            self.assertFalse(Message.objects.filter(contact=Contact.objects.filter(phone_number="1-111-5555").first()))
            eng_join = t3.write_to_database("JOIN Marshall 20-10-2017")
            contact = Message.objects.filter(contact=Contact.objects.filter(phone_number="1-111-5555")).first().contact
            self.assertEqual(1, Message.objects.filter(contact=contact).count())
            t3.process(eng_join)
            self.assertEqual(2, Message.objects.filter(contact=contact).count())
            join_outgoing = Message.objects.filter(contact=contact, direction="Outgoing").first()
            self.assertEqual(datetime.now().replace(tzinfo=timezone.get_default_timezone()), join_outgoing.sent_at)
        self.assertNotEqual(datetime.now().replace(tzinfo=timezone.get_default_timezone()), join_outgoing.sent_at)
        
        with freeze_time(datetime(2017, 7, 18, 23, 47, 12)):
            t4 = TextProcessor(phone_number="1-111-5555")
            eng_end_message = t4.write_to_database("END")
            end_outgoing_response_body = t4.process(eng_end_message)
            self.assertEqual(4, Message.objects.filter(contact=contact).count())
            end_outgoing = Message.objects.filter(contact=contact, body=end_outgoing_response_body).first()
            self.assertEqual(datetime.now().replace(tzinfo=timezone.get_default_timezone()), end_outgoing.sent_at)
        self.assertNotEqual(datetime.now().replace(tzinfo=timezone.get_default_timezone()), end_outgoing.sent_at)

    @patch("modules.text_processor.Texter.send")
    def test_processing_assigns_message_sent_at_to_now_hindi(self, texting_mock):
        with freeze_time(datetime(2017, 7, 17, 0, 0)):
            t2 = TextProcessor(phone_number="1-111-2222")
            self.assertFalse(Message.objects.filter(contact=Contact.objects.filter(phone_number="1-111-2222").first()))
            hin_join = t2.write_to_database(hindi_remind() + " Aarav 20-10-2017")
            contact = Message.objects.filter(contact=Contact.objects.filter(phone_number="1-111-2222")).first().contact
            self.assertEqual(1, Message.objects.filter(contact=contact).count())
            t2.process(hin_join)
            self.assertEqual(2, Message.objects.filter(contact=contact).count())
            join_outgoing = Message.objects.filter(contact=contact, direction="Outgoing").first()
            self.assertEqual(datetime.now().replace(tzinfo=timezone.get_default_timezone()), join_outgoing.sent_at)

            hin_born_message = t2.write_to_database(hindi_born() + " Aarav 20-10-2017")
            born_outgoing_response_body = t2.process(hin_born_message)
            self.assertEqual(4, Message.objects.filter(contact=contact).count())
            born_outgoing = Message.objects.filter(contact=contact, body=born_outgoing_response_body).first()
            self.assertEqual(datetime.now().replace(tzinfo=timezone.get_default_timezone()), born_outgoing.sent_at)

            hin_end_message = t2.write_to_database("END")
            end_outgoing_response_body = t2.process(hin_end_message)
            self.assertEqual(6, Message.objects.filter(contact=contact).count())
            end_outgoing = Message.objects.filter(contact=contact, body=end_outgoing_response_body).first()
            self.assertEqual(datetime.now().replace(tzinfo=timezone.get_default_timezone()), end_outgoing.sent_at)
        
        self.assertNotEqual(datetime.now().replace(tzinfo=timezone.get_default_timezone()), join_outgoing.sent_at)
        self.assertNotEqual(datetime.now().replace(tzinfo=timezone.get_default_timezone()), end_outgoing.sent_at)

        with freeze_time(datetime(2017, 7, 17, 5, 10)):
            t3 = TextProcessor(phone_number="1-111-5555")
            self.assertFalse(Message.objects.filter(contact=Contact.objects.filter(phone_number="1-111-5555").first()))
            hin_join = t3.write_to_database(hindi_remind() + " Marshall 20-10-2017")
            contact = Message.objects.filter(contact=Contact.objects.filter(phone_number="1-111-5555")).first().contact
            self.assertEqual(1, Message.objects.filter(contact=contact).count())
            t3.process(hin_join)
            self.assertEqual(2, Message.objects.filter(contact=contact).count())
            join_outgoing = Message.objects.filter(contact=contact, direction="Outgoing").first()
            self.assertEqual(datetime.now().replace(tzinfo=timezone.get_default_timezone()), join_outgoing.sent_at)
        self.assertNotEqual(datetime.now().replace(tzinfo=timezone.get_default_timezone()), join_outgoing.sent_at)
        
        with freeze_time(datetime(2017, 7, 18, 23, 47, 12)):
            t4 = TextProcessor(phone_number="1-111-5555")
            hin_end_message = t4.write_to_database("END")
            end_outgoing_response_body = t4.process(hin_end_message)
            self.assertEqual(4, Message.objects.filter(contact=contact).count())
            end_outgoing = Message.objects.filter(contact=contact, body=end_outgoing_response_body).first()
            self.assertEqual(datetime.now().replace(tzinfo=timezone.get_default_timezone()), end_outgoing.sent_at)
        self.assertNotEqual(datetime.now().replace(tzinfo=timezone.get_default_timezone()), end_outgoing.sent_at)

    @patch("logging.error")
    @patch("modules.text_processor.Texter.send")
    def test_processing_assigns_message_sent_at_for_failures(self, texting_mock, logging_error_mock):
        with freeze_time(datetime(2017, 7, 17, 0, 0)):
            t = TextProcessor(phone_number="1-111-1111")
            join_message = t.write_to_database("JOIN PAULA 25-11-2012")
            contact = Contact.objects.filter(name="Paula", phone_number="1-111-1111").first()
            self.assertEqual(1, Message.objects.filter(contact=contact).count())
            response = t.process(join_message)
            self.assertEqual(2, Message.objects.filter(contact=contact).count())
            join_outgoing = Message.objects.filter(contact=contact, direction="Outgoing").first()
            self.assertEqual(datetime.now().replace(tzinfo=timezone.get_default_timezone()), join_outgoing.sent_at)
        self.assertNotEqual(datetime.now().replace(tzinfo=timezone.get_default_timezone()), join_outgoing.sent_at)

        with freeze_time(datetime(2018, 8, 17, 14, 54, 59)):
            t2 = TextProcessor(phone_number="1-111-1111")
            fail_message = t2.write_to_database("Nonsense")
            fail_response = t2.process(fail_message)
            fail_contact = Contact.objects.filter(name="Paula", phone_number="1-111-1111").first()
            logging_error_mock.assert_called()
            fail_message_object = Message.objects.filter(direction="Outgoing", body=fail_response).first()
            self.assertEqual(1, logging_error_mock.call_count)
            self.assertEqual(datetime.now().replace(tzinfo=timezone.get_default_timezone()), fail_message_object.sent_at)
        self.assertNotEqual(datetime.now().replace(tzinfo=timezone.get_default_timezone()), fail_message_object.sent_at)

        with freeze_time(datetime(2017, 7, 18, 23, 47, 12)):
            t3 = TextProcessor(phone_number="1-111-3333")
            hin_join_message = hindi_remind() + " Aarav 25-11-2012"
            hin_join_message = t3.write_to_database(hindi_remind() + " Aarav 25-11-2012")
            response = t3.process(hin_join_message)
            hin_contact = Contact.objects.filter(name="Aarav", phone_number="1-111-3333").first()
        
        with freeze_time(datetime(2018, 8, 17, 14, 54, 59)):
            t4 = TextProcessor(phone_number="1-111-3333")
            hin_fail_message = t4.write_to_database(u"\u0926\u093f\u0928")
            hin_fail_response = t4.process(hin_fail_message)
            hin_fail_contact = Contact.objects.filter(name="Aarav", phone_number="1-111-3333").first()
            hin_fail_message_object = Message.objects.filter(direction="Outgoing",
                                                            contact=hin_fail_contact,
                                                            body=hin_fail_response).first()
            self.assertEqual(datetime.now().replace(tzinfo=timezone.get_default_timezone()), hin_fail_message_object.sent_at)
        self.assertNotEqual(datetime.now().replace(tzinfo=timezone.get_default_timezone()), hin_fail_message_object.sent_at)
        self.assertEqual(2, logging_error_mock.call_count)

    def test_get_language_returns_inferred_language_if_keyword_is_subscribe_word(self):
        t = TextProcessor(phone_number="1-111-2222")
        updated_language_remind = t.get_language(language="English",
                                                    inferred_language="Hindi",
                                                    keyword=hindi_remind())
        self.assertEqual("Hindi", updated_language_remind)

        updated_language_info = t.get_language(language="English",
                                                inferred_language="Hindi",
                                                keyword=hindi_information())
        self.assertEqual("Hindi", updated_language_info)

        updated_language_born = t.get_language(language="English",
                                                inferred_language="Hindi",
                                                keyword=hindi_born())
        self.assertEqual("Hindi", updated_language_info)

        updated_language_join = t.get_language(language="Hindi",
                                                inferred_language="English",
                                                keyword="join")
        self.assertEqual("English", updated_language_join)

        updated_language_eng_remind = t.get_language(language="Hindi",
                                                        inferred_language="English",
                                                        keyword="remind")
        self.assertEqual("English", updated_language_eng_remind)


        both_hindi = t.get_language(language="Hindi",
                                    inferred_language="Hindi",
                                    keyword=hindi_remind())
        self.assertEqual("Hindi", both_hindi)

        both_english = t.get_language(language="English",
                                        inferred_language="English",
                                        keyword=hindi_remind())
        self.assertEqual("English", both_english)

    def test_get_language_returns_language_if_keyword_is_born(self):
        t = TextProcessor(phone_number="1-111-2222")
        lan_english = t.get_language(language="English",
                                        inferred_language="Hindi",
                                        keyword="born")
        self.assertEqual("English", lan_english)

        both_english = t.get_language(language="English",
                                        inferred_language="English",
                                        keyword="born")
        self.assertEqual("English", both_english)

        lan_hindi = t.get_language(language="Hindi",
                                        inferred_language="English",
                                        keyword="born")
        self.assertEqual("Hindi", lan_hindi)

        both_hindi = t.get_language(language="Hindi",
                                        inferred_language="Hindi",
                                        keyword="born")
        self.assertEqual("Hindi", both_hindi)

    def test_get_language_returns_language_if_keyword_not_in_subscribe_keywords(self):
        t = TextProcessor(phone_number="1-111-2222")
        hindi_random_chars1 = t.get_language(language="English",
                                                inferred_language="Hindi",
                                                keyword=u"\u092e\u0947\u0902")
        self.assertEqual("English", hindi_random_chars1)

        hindi_random_chars2 = t.get_language(language="English",
                                                inferred_language="Hindi",
                                                keyword=u"\u0917\u0932\u0947")
        self.assertEqual("English", hindi_random_chars2)

        blank_key = t.get_language(language="Hindi",
                                    inferred_language="English",
                                    keyword=" ")
        self.assertEqual("Hindi", blank_key)

        none_key = t.get_language(language="Hindi",
                                    inferred_language="English",
                                    keyword=None)
        self.assertEqual("Hindi", none_key)

        blank_key_eng = t.get_language(language="English",
                                        inferred_language="Hindi",
                                        keyword=" ")
        self.assertEqual("English", blank_key_eng)

        none_key_eng = t.get_language(language="English",
                                        inferred_language="Hindi",
                                        keyword=None)
        self.assertEqual("English", none_key_eng)

        stop_key = t.get_language(language="Hindi",
                                    inferred_language="English",
                                    keyword="stop")
        self.assertEqual("Hindi", stop_key)

        end_key = t.get_language(language="Hindi",
                                    inferred_language="English",
                                    keyword="end")
        self.assertEqual("Hindi", end_key)

        end_key_eng = t.get_language(language="English",
                                        inferred_language="English",
                                        keyword="end")
        self.assertEqual("English", end_key_eng)