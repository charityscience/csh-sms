import time
import logging

from django.test import TestCase

from cshsms.settings import HSPSMS_API, HSPSMS_USERNAME, HSPSMS_SENDERNAME, TEXTLOCAL_PHONENUMBER
from modules.hspsmswrapper import Hspsms
from modules.texter import Texter
from modules.i18n import hindi_remind, msg_placeholder_child

HSPSMS = Hspsms(apikey=HSPSMS_API, username=HSPSMS_USERNAME, sendername=HSPSMS_SENDERNAME)

class HspsmsSendingTests(TestCase):
    def test_send_message_to_fake_number(self):
        logging.info("sending transactional message")
        fr = HSPSMS.send_transactional_message(message='Example Hspsms message to fake number',
                                               phone_number='0000000')
        self.assertTrue(fr)
        self.assertIsInstance(fr, list)
        self.assertTrue(fr[0]['responseCode'])
        self.assertEqual(fr[0]['responseCode'], "Message SuccessFully Submitted")
        self.assertTrue(fr[1])
        self.assertTrue(fr[2]['invalidnumber'])
        self.assertEqual(fr[2]['invalidnumber'], '0000000')

    def test_send_transactional_message(self):
        logging.info("sending transactional message - English")
        fr = HSPSMS.send_transactional_message(message='Testing example message in Hspsms.',
                                               phone_number=TEXTLOCAL_PHONENUMBER)
        texter = Texter()
        logging.info("sleeping three minutes before reading the inbox")
        time.sleep(180)
        logging.info("reading the inbox")
        new_message_dict = texter.read_inbox()
        self.assertTrue(fr)
        self.assertIsInstance(fr, list)
        self.assertTrue(fr[0]['responseCode'])
        self.assertEqual(fr[0]['responseCode'], "Message SuccessFully Submitted")
        self.assertTrue(fr[1])
        self.assertTrue("Testing example message in Hspsms." in new_message_dict[0])

    def test_send_transactional_message_in_hindi(self):
        logging.info("sending transactional message - Hindi")
        hindi_message = hindi_remind() + ' ' + msg_placeholder_child('Hindi')
        fr = HSPSMS.send_transactional_message(message=hindi_message,
                                               phone_number=TEXTLOCAL_PHONENUMBER)
        texter = Texter()
        logging.info("sleeping three minutes before reading the inbox")
        time.sleep(180)
        logging.info("reading the inbox")
        new_message_dict = texter.read_inbox()
        self.assertTrue(fr)
        self.assertIsInstance(fr, list)
        self.assertTrue(fr[0]['responseCode'])
        self.assertEqual(fr[0]['responseCode'], "Message SuccessFully Submitted")
        self.assertTrue(fr[1])
        self.assertTrue(hindi_message in new_message_dict[0])
