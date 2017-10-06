import logging
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

from django.test import TestCase
from freezegun import freeze_time

from cshsms.settings import TEXTLOCAL_PHONENUMBER
from management.models import Contact, Group, Message
from modules.texter import Texter
from modules.text_reminder import TextReminder
from modules.text_processor import TextProcessor
from modules.date_helper import date_to_date_string
from modules.i18n import msg_subscribe, msg_unsubscribe, hindi_remind, \
                         six_week_reminder_one_day, six_week_reminder_seven_days, \
                         msg_placeholder_child, hindi_born, verify_pregnant_signup_birthdate


class TexterGetInboxesTests(TestCase):
    def test_read_inbox(self):
        inbox_dict = Texter().read_inbox()
        self.assertIsInstance(inbox_dict, dict)

    def test_full_e2e_english_signup_and_cancel_flow(self):
        logging.info("running e2e full flow for sign up + cancel in English...")
        self.run_e2e_flow_for_language(language="English",
                                       person_name="Testjohnson",
                                       join_keyword="JOIN")

    def test_full_e2e_hindi_signup_and_cancel_flow(self):
        logging.info("running e2e full flow for sign up + cancel in Hindi...")
        self.run_e2e_flow_for_language(language="Hindi",
                                       person_name=u'\u0906\u0930\u0935',
                                       join_keyword=hindi_remind())

    def test_preg_update_english_flow(self):
        logging.info("running preg update flow in English...")
        self.run_preg_update_flow_for_language(language="English",
                                               person_name="Testjohnson",
                                               join_keyword="JOIN",
                                               born_keyword="BORN")

    def test_preg_update_hindi_flow(self):
        logging.info("running preg update flow in Hindi...")
        self.run_preg_update_flow_for_language(language="Hindi",
                                               person_name=u'\u0906\u0930\u0935',
                                               join_keyword=hindi_remind(),
                                               born_keyword=hindi_born())


    def run_e2e_flow_for_language(self, language, person_name, join_keyword):
        logging.info("sending text")
        subscribe_date = datetime(2017, 1, 30).date()
        join_text = join_keyword + " " + person_name + " " + date_to_date_string(subscribe_date)
        t = Texter()
        send_status = t.send(message=join_text,
                             phone_number=TEXTLOCAL_PHONENUMBER)
        self.assertTrue('SuccessFully' in send_status[0]['responseCode'])
        logging.info("sleeping three minutes before reading the text")
        time.sleep(180)
        logging.info("reading text")
        new_messages = t.read_inbox()[0]  # TODO: Match to job
        tp = TextProcessor(TEXTLOCAL_PHONENUMBER)
        processed = False
        logging.info("checking text can be processed")
        for text in new_messages:
            if text == join_text:
                processed = True
                tp.process(text)
        self.assertTrue(processed)

        logging.info("checking contact object is created")
        self.assertTrue(Contact.objects.filter(name=person_name,
                                               phone_number=TEXTLOCAL_PHONENUMBER).exists())
        self.assertTrue(tp.get_contacts().exists())

        logging.info("checking groups are created")
        contact = tp.get_contacts().first()
        actual_groups = [str(g) for g in contact.group_set.all()]
        expected_groups = ['Everyone - {}'.format(language.title()),
                           'Text Sign Ups',
                           'Text Sign Ups - {}'.format(language.title())]
        self.assertEqual(actual_groups, expected_groups)

        logging.info("sleeping three minutes before checking for subscription text")
        time.sleep(180)
        logging.info("checking subscription text")
        messages = t.read_inbox()[0]
        self.assertTrue(len(messages) >= 1)
        self.assertTrue(all([m in msg_subscribe(language).format(name=person_name) for m in messages]))
        logging.info("checking person can be reminded at the correct times")
        tr = TextReminder(contact)

        logging.info("Two days after...")
        with freeze_time(subscribe_date + relativedelta(days = 2)):
            self.assertFalse(Message.objects.filter(contact=tr.contact, direction="Outgoing"))
            self.assertFalse(tr.remind())
            self.assertEqual(0, Message.objects.filter(contact=tr.contact, direction="Outgoing").count())
            self.assertEqual(tr.why_not_remind_reasons(),
                             ["Contact has no reminders for today's date."])
        logging.info("sleeping three minutes before checking for reminder text")
        time.sleep(180)
        self.assertEqual(t.read_inbox(), {})

        logging.info("Seven days before the six week mark...")
        with freeze_time(subscribe_date + relativedelta(weeks = 6) - relativedelta(days = 7)): 
            self.assertFalse(Message.objects.filter(contact=tr.contact, direction="Outgoing", body=tr.get_reminder_msg()))
            self.assertTrue(tr.remind())
            self.assertEqual(1, Message.objects.filter(contact=tr.contact, direction="Outgoing", body=tr.get_reminder_msg()).count())
        logging.info("sleeping three minutes before checking for reminder text")
        time.sleep(180)
        logging.info("checking for reminder text")
        messages = t.read_inbox()[0]
        self.assertTrue(len(messages) >= 1)
        self.assertTrue(all([m in six_week_reminder_seven_days(language).format(name=person_name) for m in messages]))

        logging.info("One day before the six week mark...")
        with freeze_time(subscribe_date + relativedelta(weeks = 6) - relativedelta(days = 1)):
            self.assertTrue(Message.objects.filter(contact=tr.contact, direction="Outgoing", body=tr.get_reminder_msg()))
            self.assertTrue(tr.remind())
            self.assertEqual(2, Message.objects.filter(contact=tr.contact, direction="Outgoing").count())
        logging.info("sleeping three minutes before checking for reminder text")
        time.sleep(180)
        logging.info("checking for reminder text")
        messages = t.read_inbox()[0]
        self.assertTrue(len(messages) >= 1)
        self.assertTrue(all([m in six_week_reminder_one_day(language).format(name=person_name) for m in messages]))

        logging.info("checking contact is not yet cancelled")
        contact = tp.get_contacts().first()
        self.assertFalse(contact.cancelled)

        logging.info("sending cancel text")
        send_status = t.send(message='END',
                             phone_number=TEXTLOCAL_PHONENUMBER)
        self.assertTrue("SuccessFully" in send_status[0]["responseCode"])
        logging.info("sleeping three minutes before checking for confirmation")
        time.sleep(180)
        logging.info("checking cancellation text can be processed")
        self.assertEqual(t.read_inbox()[0][0], "END")
        tp.process("END")
        logging.info("sleeping four minutes before checking for confirmation")
        time.sleep(240)
        logging.info("checking person is cancelled")
        messages = t.read_inbox()[0]
        self.assertTrue(len(messages) >= 1)
        self.assertTrue(all([m in msg_unsubscribe(language) for m in messages]))
        contact = tp.get_contacts().first()
        self.assertTrue(contact.cancelled)

        logging.info("checking that cancelled person can no longer be reminded")
        with freeze_time(subscribe_date + relativedelta(weeks = 6) - relativedelta(days = 1)):
            self.assertEqual(2, Message.objects.filter(contact=tr.contact, direction="Outgoing").count())
            self.assertFalse(tr.remind())  # ...cannot be reminded
            self.assertEqual(2, Message.objects.filter(contact=tr.contact, direction="Outgoing").count())
            self.assertEqual(tr.why_not_remind_reasons(), ["Contact is cancelled."])
        logging.info("sleeping three minutes before checking for lack of reminder text")
        time.sleep(180)
        self.assertEqual(t.read_inbox(), {})


    def run_preg_update_flow_for_language(self, language, person_name, join_keyword, born_keyword):
        logging.info("processing a join text")
        subscribe_date = datetime(2017, 10, 20).date()
        join_text = join_keyword + " " + person_name + " " + date_to_date_string(subscribe_date)
        tp = TextProcessor(TEXTLOCAL_PHONENUMBER)
        tp.process(join_text)
        logging.info("sleeping three minutes before checking for subscription text")
        time.sleep(180)
        logging.info("checking subscription text")
        t = Texter()
        messages = t.read_inbox()[0]
        self.assertTrue(len(messages) >= 1)
        self.assertTrue(all([m in msg_subscribe(language).format(name=person_name) for m in messages]))
        logging.info("checking contact object is created")
        self.assertTrue(Contact.objects.filter(name=person_name,
                                               phone_number=TEXTLOCAL_PHONENUMBER).exists())
        self.assertTrue(tp.get_contacts().exists())
        contact = tp.get_contacts().first()
        # Right now there is no way to become a preg_signup solely through texting in,
        # so we have to manually set preg_signup = True.
        contact.preg_signup = True
        contact.save()

        logging.info("checking person can be reminded at the correct times")
        tr = TextReminder(contact)

        logging.info("Two weeks after...")
        with freeze_time(subscribe_date + relativedelta(weeks = 2)):
            self.assertEqual(0, Message.objects.filter(contact=tr.contact, direction="Outgoing").count())
            self.assertTrue(tr.remind())
            self.assertEqual(1, Message.objects.filter(contact=tr.contact, direction="Outgoing", body=tr.get_reminder_msg()).count())
        logging.info("sleeping three minutes before checking for reminder text")
        time.sleep(180)
        logging.info("checking for born reminder text")
        messages = t.read_inbox()[0]
        self.assertTrue(len(messages) >= 1)
        self.assertTrue(all([m in verify_pregnant_signup_birthdate(language) for m in messages]))

        logging.info("Four weeks after...")
        with freeze_time(subscribe_date + relativedelta(weeks = 4)):
            self.assertTrue(Message.objects.filter(contact=tr.contact, direction="Outgoing"))
            self.assertTrue(tr.remind())
            self.assertEqual(2, Message.objects.filter(contact=tr.contact, direction="Outgoing").count())
        logging.info("sleeping three minutes before checking for reminder text")
        time.sleep(180)
        logging.info("checking for born reminder text")
        messages = t.read_inbox()[0]
        self.assertTrue(len(messages) >= 1)
        self.assertTrue(all([m in verify_pregnant_signup_birthdate(language) for m in messages]))

        logging.info("sending born text")
        born_date = datetime(2017, 10, 30).date()
        born_text = born_keyword + " " + person_name + " " + date_to_date_string(born_date)
        send_status = t.send(message=born_text,
                             phone_number=TEXTLOCAL_PHONENUMBER)
        self.assertTrue('SuccessFully' in send_status[0]['responseCode'])
        logging.info("sleeping three minutes before reading the text")
        time.sleep(180)
        logging.info("reading born text")
        new_messages = t.read_inbox()[0]  # TODO: Match to job
        processed = False
        logging.info("checking text can be processed")
        for text in new_messages:
            if text == born_text:
                processed = True
                tp.process(text)
        self.assertTrue(processed)

        logging.info("sleeping four minutes before checking for subscription text")
        time.sleep(240)
        logging.info("checking subscription text")
        messages = t.read_inbox()[0]
        self.assertTrue(len(messages) >= 1)
        self.assertTrue(all([m in msg_subscribe(language).format(name=person_name) for m in messages]))

        logging.info("checking preg_update flag, preg_signup flag, and DOB")
        self.assertTrue(contact.preg_signup)
        self.assertFalse(contact.preg_update)
        self.assertEqual(contact.date_of_birth, subscribe_date)
        contact = tp.get_contacts().first()
        self.assertTrue(contact.preg_signup)
        self.assertTrue(contact.preg_update)
        self.assertEqual(contact.date_of_birth, born_date)
        tr = TextReminder(contact)

        logging.info("Seven days before the six week mark after first texting...")
        with freeze_time(subscribe_date + relativedelta(weeks = 6) - relativedelta(days = 7)): 
            self.assertEqual(2, Message.objects.filter(contact=tr.contact, direction="Outgoing").count())
            self.assertFalse(tr.remind())  # ...cannot be reminded
            self.assertEqual(2, Message.objects.filter(contact=tr.contact, direction="Outgoing").count())
            self.assertEqual(tr.why_not_remind_reasons(),
                             ["Contact has no reminders for today's date."])
        logging.info("sleeping three minutes before checking for lack of reminder text")
        time.sleep(180)
        self.assertEqual(t.read_inbox(), {})

        logging.info("Seven days before the six week mark after birth...")
        with freeze_time(born_date + relativedelta(weeks = 6) - relativedelta(days = 7)): 
            self.assertEqual(0, Message.objects.filter(contact=tr.contact, direction="Outgoing", body=tr.get_reminder_msg()).count())
            self.assertTrue(tr.remind())
            self.assertEqual(1, Message.objects.filter(contact=tr.contact, direction="Outgoing", body=tr.get_reminder_msg()).count())
        logging.info("sleeping three minutes before checking for reminder text")
        time.sleep(180)
        logging.info("checking for reminder text")
        messages = t.read_inbox()[0]
        self.assertTrue(len(messages) >= 1)
        self.assertTrue(all([m in six_week_reminder_seven_days(language).format(name=person_name) for m in messages]))