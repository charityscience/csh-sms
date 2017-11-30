import time
import logging

from django.test import TestCase
from datetime import datetime

from cshsms.settings import TEXTLOCAL_API, TEXTLOCAL_PRIMARY_ID, TEXTLOCAL_SENDERNAME, \
                            TEXTLOCAL_PHONENUMBER
from modules.textlocalwrapper import TextLocal
from modules.texter import Texter
from modules.i18n import hindi_remind, msg_placeholder_child, msg_already_sub


class TextLocalInboxesTests(TestCase):
    def test_create_object(self):
        textlocal = TextLocal(apikey=TEXTLOCAL_API,
                                primary_id=TEXTLOCAL_PRIMARY_ID,
                                sendername=TEXTLOCAL_SENDERNAME)
        self.assertIsInstance(textlocal, TextLocal)
        
    def test_get_all_inboxes(self):
        textlocal = TextLocal(apikey=TEXTLOCAL_API,
                                primary_id=TEXTLOCAL_PRIMARY_ID,
                                sendername=TEXTLOCAL_SENDERNAME)
        response = textlocal.get_all_inboxes()
        self.assertIsInstance(response, dict)
        self.assertGreaterEqual(int(response['num_inboxes']), 1)

    def test_get_primary_inbox(self):
        textlocal = TextLocal(apikey=TEXTLOCAL_API,
                                primary_id=TEXTLOCAL_PRIMARY_ID,
                                sendername=TEXTLOCAL_SENDERNAME)
        primary_inbox = textlocal.get_primary_inbox()
        self.assertTrue(primary_inbox)
        self.assertIsInstance(primary_inbox, dict)
        self.assertTrue(primary_inbox['status'])
        self.assertEqual(primary_inbox['status'], 'success')

    def test_get_primary_inbox_messages(self):
        textlocal = TextLocal(apikey=TEXTLOCAL_API,
                                primary_id=TEXTLOCAL_PRIMARY_ID,
                                sendername=TEXTLOCAL_SENDERNAME)
        primary_inbox_messages = textlocal.get_primary_inbox_messages()
        self.assertTrue(primary_inbox_messages)
        self.assertIsInstance(primary_inbox_messages, list)

    def test_api_send_history_messages(self):
        textlocal = TextLocal(apikey=TEXTLOCAL_API,
                                primary_id=TEXTLOCAL_PRIMARY_ID,
                                sendername=TEXTLOCAL_SENDERNAME)
        api_send_history_messages = textlocal.get_api_send_history_messages()
        self.assertTrue(api_send_history_messages)
        self.assertIsInstance(api_send_history_messages, list)

    def test_new_api_send_messages_by_number(self):
        textlocal = TextLocal(apikey=TEXTLOCAL_API,
                                primary_id=TEXTLOCAL_PRIMARY_ID,
                                sendername=TEXTLOCAL_SENDERNAME)
        logging.info("sending text - English")
        texter = Texter()
        texter.send(message=msg_already_sub("English"), phone_number=TEXTLOCAL_PHONENUMBER)
        logging.info("sleeping three minutes before reading text")
        time.sleep(180)
        logging.info("reading text")
        new_message_dict = textlocal.new_api_send_messages_by_number()
        message_list_by_phonenumber = new_message_dict[TEXTLOCAL_PHONENUMBER]
        self.assertTrue(msg_already_sub("English") in message_list_by_phonenumber[0][0])
        self.assertIsInstance(message_list_by_phonenumber[0][1], datetime)

