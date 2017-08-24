import time
import logging

import mock
from mock import patch
from django.test import TestCase
from freezegun import freeze_time

from cshsms.settings import TEXTLOCAL_PHONENUMBER
from modules.texter import Texter
from modules.text_reminder import TextReminder


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


    @patch("logging.info")
    def test_full_e2e_english_signup_and_cancel_flow(self, logging_mock):
        logging.info("sleeping two minutes before sending a text")
        time.sleep(120)
        logging.info("sending text")
        t = Texter()
        send_status = t.send(message="JOIN TestPerson 30/1/2017",
                             phone_number=TEXTLOCAL_PHONENUMBER)
        import pdb
        pdb.set_trace()
        logging.info("sleeping two minutes before reading the text")
        time.sleep(120)
        logging.info("reading text")
        new_messages = t.read_inbox()[0]
        p = TextProcessor(TEXTLOCAL_PHONENUMBER)
        processed = False
        logging.info("checking text can be processed")
        for phone_number, texts in new_messages.items():
            for text in texts:
                if text == "JOIN TestPerson 30/1/2017":
                    processed = True
                    p.process(text)
        self.assertTrue(processed)

        logging.info("checking contact object is created")
        self.assertTrue(Contact.objects.filter(name="TestPerson",
                                               phone_number=TEXTLOCAL_PHONENUMBER).exists())
        self.assertTrue(p.get_contacts().exists())

        logging.info("checking groups are created")
        contact = p.get_contacts().first()
        actual_groups = [str(g) for g in contact.group_set.all()]
        expected_groups = ['Everyone - English', 'Text Sign Ups', 'Text Sign Ups - English']
        self.assertEqual(actual_groups, expected_groups)

        logging.info("sleeping two minutes before checking for subscription text")
        time.sleep(120)
        logging.info("checking subscription text")
        # TODO write code to check

        logging.info("checking person can be reminded at the correct times")
        r = TextReminder(contact)
        with freeze_time("2017-02-1"): # Two days after...
            self.assertFalse(r.remind())  # ...cannot be reminded
            self.assertEqual(r.why_not_remind_reasons(),
                             ["Contact has no reminders for today's date."])
            # TODO: Check no messages went out
        with freeze_time("2017-02-1"): # Six weeks, one day after...
            self.assertTrue(r.remind())  # ...can be reminded
            logging.info("sleeping two minutes before checking for reminder text")
            time.sleep(120)
            logging.info("checking for reminder text")
            # TODO: Check that a reminder message went out
        with freeze_time("2017-02-1"): # Six weeks, seven days after...
            self.assertTrue(r.remind())  # ...can be reminded
            logging.info("sleeping two minutes before checking for reminder text")
            time.sleep(120)
            logging.info("checking for reminder text")
            # TODO: Check that a reminder message went out

        # Person cancels
        # TODO: Write cancel text
        time.sleep(120)

        # Check person is cancelled
        # TODO: Write check

        # Person can no longer be reminded
        # TODO: Write code


    @patch("logging.info")
    def test_full_e2e_hindi_signup_and_cancel_flow(self, logging_mock):
        self.assertTrue(False)
