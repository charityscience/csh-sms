import time
import logging

from django.test import TestCase

from cshsms.settings import TEXTLOCAL_API, TEXTLOCAL_PRIMARY_ID, TEXTLOCAL_PHONENUMBER
from modules.textlocalwrapper import TextLocal
from modules.texter import Texter


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
        logging.info("sleeping for 60 before sending a text.")
        time.sleep(60)
        logging.info("sending text")
        texter = Texter()
        texter.send(message="This is a live test message.", phone_number=TEXTLOCAL_PHONENUMBER)
        logging.info("sleeping for 120 before reading text")
        time.sleep(120)
        logging.info("reading text")
        messages = textlocal.get_primary_inbox_messages()
        new_message_dict = textlocal.new_messages_by_number(messages)
        self.assertTrue("This is a live test message." in new_message_dict[0])
