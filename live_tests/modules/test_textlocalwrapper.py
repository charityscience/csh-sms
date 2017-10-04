import time
import logging

from django.test import TestCase

from cshsms.settings import TEXTLOCAL_API, TEXTLOCAL_PRIMARY_ID, TEXTLOCAL_PHONENUMBER
from modules.textlocalwrapper import TextLocal
from modules.texter import Texter
from modules.i18n import hindi_remind, msg_placeholder_child


class TextLocalInboxesTests(TestCase):
    def test_create_object(self):
        textlocal = TextLocal(TEXTLOCAL_API, TEXTLOCAL_PRIMARY_ID)
        self.assertIsInstance(textlocal, TextLocal)
        
    def test_get_all_inboxes(self):
        textlocal = TextLocal(TEXTLOCAL_API, TEXTLOCAL_PRIMARY_ID)
        response = textlocal.get_all_inboxes()
        self.assertIsInstance(response, dict)
        self.assertGreaterEqual(int(response['num_inboxes']), 1)

    def test_get_primary_inbox(self):
        textlocal = TextLocal(TEXTLOCAL_API, TEXTLOCAL_PRIMARY_ID)
        primary_inbox = textlocal.get_primary_inbox()
        self.assertTrue(primary_inbox)
        self.assertIsInstance(primary_inbox, dict)
        self.assertTrue(primary_inbox['status'])
        self.assertEqual(primary_inbox['status'], 'success')

    def test_get_primary_inbox_messages(self):
        textlocal = TextLocal(TEXTLOCAL_API, TEXTLOCAL_PRIMARY_ID)
        primary_inbox_messages = textlocal.get_primary_inbox_messages()
        self.assertTrue(primary_inbox_messages)
        self.assertIsInstance(primary_inbox_messages, list)

    def test_new_messages_by_number(self):
        textlocal = TextLocal(TEXTLOCAL_API, TEXTLOCAL_PRIMARY_ID)
        logging.info("sending text - English")
        texter = Texter()
        texter.send(message="This is a live test message.", phone_number=TEXTLOCAL_PHONENUMBER)
        logging.info("sleeping three minutes before reading text")
        time.sleep(180)
        logging.info("reading text")
        new_message_dict = textlocal.new_messages_by_number()
        self.assertTrue("This is a live test message." in new_message_dict[0])

    def test_new_messages_by_number_hindi(self):
        textlocal = TextLocal(TEXTLOCAL_API, TEXTLOCAL_PRIMARY_ID)
        logging.info("sending text - Hindi")
        texter = Texter()
        hindi_message = hindi_remind() + ' ' + msg_placeholder_child('Hindi')
        texter.send(message=hindi_message, phone_number=TEXTLOCAL_PHONENUMBER)
        logging.info("sleeping three minutes before reading hindi text")
        time.sleep(180)
        logging.info("reading text")
        new_message_dict = textlocal.new_messages_by_number()
        self.assertTrue(hindi_message in new_message_dict[0])