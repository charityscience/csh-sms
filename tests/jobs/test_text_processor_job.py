import mock
from mock import patch, call
from django.test import TestCase

from management.models import Contact
from modules.i18n import msg_subscribe, msg_unsubscribe, hindi_remind
from jobs import text_processor_job

class TextProcessorJobTests(TestCase):
    @patch("logging.info")
    @patch("modules.text_reminder.Texter.send")
    @patch("jobs.text_processor_job.Texter.read_inbox")
    def test_check_and_process_registrations(self, mocked_texter_read, mocked_texter_send, mocked_logger):
        mocked_texter_read.return_value = {'1-111-1111': ["JOIN ROLAND 29/5/2017"],
                                           '1-112-1111': [hindi_remind() + " SAI 29/5/2017",
                                                          "END"]}
        text_processor_job.check_and_process_registrations()
        calls = [call(message=msg_subscribe("English").format(name="Roland"),
                      phone_number="1-111-1111"),
                 call(message=msg_subscribe("Hindi").format(name="Sai"),
                      phone_number="1-112-1111"),
                 call(message=msg_unsubscribe("Hindi"),
                      phone_number="1-112-1111")]
        mocked_texter_send.assert_has_calls(calls)
        self.assertEqual(mocked_texter_send.call_count, 3)
        self.assertEqual(Contact.objects.count(), 2)
        contacts = Contact.objects.all()
        self.assertFalse(contacts[0].cancelled)
        self.assertEqual(contacts[0].language_preference, "English")
        self.assertTrue(contacts[1].cancelled)
        self.assertEqual(contacts[1].language_preference, "Hindi")
