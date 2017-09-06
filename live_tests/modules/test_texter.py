import logging
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

from django.test import TestCase
from freezegun import freeze_time

from cshsms.settings import TEXTLOCAL_PHONENUMBER
from management.models import Contact, Group
from modules.texter import Texter
from modules.text_reminder import TextReminder
from modules.text_processor import TextProcessor
from modules.date_helper import date_to_date_string
from modules.i18n import msg_subscribe, msg_unsubscribe, hindi_remind, \
                         six_week_reminder_one_day, six_week_reminder_seven_days


class TexterGetInboxesTests(TestCase):
    def test_read_inbox(self):
        inbox_dict = Texter().read_inbox()
        self.assertIsInstance(inbox_dict, dict)

    def test_send(self):
        logging.info("sleeping two minutes before sending a text")
        time.sleep(120)
        t = Texter()
        logging.info("sending text")
        send_status = t.send(message="Testing example message in Texter.",
                             phone_number=TEXTLOCAL_PHONENUMBER)
        logging.info("sleeping two minutes before reading the text")
        time.sleep(120)
        logging.info("reading text")
        new_message_dict = t.read_inbox()
        self.assertTrue("Testing example message in Texter." in new_message_dict[0])

    def test_full_e2e_english_signup_and_cancel_flow(self):
        logging.info("running e2e full flow for sign up + cancel in English...")
        self.run_flow_for_language(language="English",
                                   person_name="Testjohnson",
                                   join_keyword="JOIN")

    def test_full_e2e_hindi_signup_and_cancel_flow(self):
        logging.info("running e2e full flow for sign up + cancel in Hindi...")
        self.run_flow_for_language(language="Hindi",
                                   person_name=u'\u0906\u0930\u0935',
                                   join_keyword=hindi_remind())


    def run_flow_for_language(self, language, person_name, join_keyword):
        logging.info("sleeping two minutes before sending a text")
        time.sleep(120)
        logging.info("sending text")
        subscribe_date = datetime(2017, 1, 30).date()
        join_text = join_keyword + " " + person_name + " " + date_to_date_string(subscribe_date)
        t = Texter()
        send_status = t.send(message=join_text,
                             phone_number=TEXTLOCAL_PHONENUMBER)
        self.assertTrue('SuccessFully' in send_status[0]['responseCode'])
        logging.info("sleeping two minutes before reading the text")
        time.sleep(120)
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

        logging.info("sleeping two minutes before checking for subscription text")
        time.sleep(120)
        logging.info("checking subscription text")
        new_message = t.read_inbox()[0][0]
        self.assertEqual(new_message, msg_subscribe(language).format(name=person_name))
        logging.info("checking person can be reminded at the correct times")
        r = TextReminder(contact)

        logging.info("Two days after...")
        with freeze_time(subscribe_date + relativedelta(days = 2)):
            self.assertFalse(r.remind())
            self.assertEqual(r.why_not_remind_reasons(),
                             ["Contact has no reminders for today's date."])
            logging.info("sleeping two minutes before checking for reminder text")
            time.sleep(120)
            self.assertEqual(t.read_inbox(), {})

        logging.info("Six weeks, one day after...")
        with freeze_time(subscribe_date + relativedelta(weeks = 6, days = 1)):  # TODO: These dates seem off.
            self.assertTrue(r.remind())
            logging.info("sleeping two minutes before checking for reminder text")
            time.sleep(120)
            logging.info("checking for reminder text")
            new_message = t.read_inbox()[0][0]
            self.assertEqual(new_message,
                             six_week_reminder_one_day(language).format(name=person_name))

        logging.info("Six weeks, seven days after...")
        with freeze_time(subscribe_date + relativedelta(weeks = 6, days = 7)): 
            self.assertTrue(r.remind())
            logging.info("sleeping two minutes before checking for reminder text")
            time.sleep(120)
            logging.info("checking for reminder text")
            new_message = t.read_inbox()[0][0]
            self.assertEqual(new_message,
                             six_week_reminder_seven_days(language).format(name=person_name))

        logging.info("sending cancel text")
        send_status = t.send(message='END',
                             phone_number=TEXTLOCAL_PHONENUMBER)
        self.assertTrue('SuccessFully' in send_status[0]['responseCode'])
        logging.info("sleeping one minute before checking for confirmation")
        time.sleep(60)
        logging.info("checking cancellation text can be processed")
        new_messages = t.read_inbox()[0]
        processed = False
        for text in new_messages:
            if text == "END":
                processed = True
                tp.process(text)
        self.assertTrue(processed)
        logging.info("sleeping two minutes before checking for confirmation")
        time.sleep(120)
        logging.info("checking person is cancelled")
        new_message = t.read_inbox()[0][0]
        self.assertEqual(new_message, msg_unsubscribe(language))
        contact = tp.get_contacts().first()
        self.assertTrue(contact.cancelled)

        logging.info("checking that cancelled person can no longer be reminded")
        with freeze_time(subscribe_date + relativedelta(weeks = 6, days = 1)):
            self.assertFalse(r.remind())  # ...cannot be reminded
            self.assertEqual(r.why_not_remind_reasons(), ["Contact is cancelled."])
            logging.info("sleeping two minutes before checking for reminder text")
            time.sleep(120)
            self.assertEqual(t.read_inbox(), {})
