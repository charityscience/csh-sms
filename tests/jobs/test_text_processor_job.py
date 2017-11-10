import mock
from mock import patch, call
from django.test import TestCase
from django.utils import timezone
from datetime import datetime

from management.models import Contact, Message
from modules.i18n import msg_subscribe, msg_unsubscribe, hindi_remind
from jobs import text_processor_job

class TextProcessorJobTests(TestCase):
    @patch("logging.info")
    @patch("modules.text_reminder.Texter.send")
    @patch("jobs.text_processor_job.Texter.read_inbox")
    def test_check_and_process_registrations(self, mocked_texter_read, mocked_texter_send, mocked_logger):
        mocked_texter_read.return_value = {'1-111-1111': [("JOIN ROLAND 29/5/2017", datetime(2017, 8, 1, 15, 20, 20).replace(tzinfo=timezone.get_default_timezone()))],
                                           '1-112-1111': [(hindi_remind() + " SAI 29/5/2017", datetime(2017, 8, 1, 15, 20, 20).replace(tzinfo=timezone.get_default_timezone())),
                                                          ("END", datetime(2017, 8, 1, 17, 20, 20).replace(tzinfo=timezone.get_default_timezone()))]}
        text_processor_job.check_and_process_registrations()

        # All incoming messages are recorded in DB
        incoming_messages_in_db = Message.objects.filter(direction="Incoming")
        self.assertEqual(len(incoming_messages_in_db), 3)
        self.assertTrue(any(['SAI' in m.body for m in incoming_messages_in_db]))
        self.assertTrue(any(['ROLAND' in m.body for m in incoming_messages_in_db]))
        self.assertTrue(any(['END' in m.body for m in incoming_messages_in_db]))
        first_contact = Contact.objects.get(phone_number="1-111-1111")
        second_contact = Contact.objects.get(phone_number="1-112-1111")
        self.assertTrue(Message.objects.get(contact=first_contact,
                                            direction="Incoming",
                                            body="JOIN ROLAND 29/5/2017",
                                            sent_at=None,
                                            received_at=datetime(2017, 8, 1, 15, 20, 20).replace(tzinfo=timezone.get_default_timezone())))
        self.assertTrue(Message.objects.get(contact=second_contact,
                                            direction="Incoming",
                                            body=hindi_remind() + " SAI 29/5/2017",
                                            sent_at=None,
                                            received_at=datetime(2017, 8, 1, 15, 20, 20).replace(tzinfo=timezone.get_default_timezone())))
        self.assertTrue(Message.objects.get(contact=second_contact,
                                            direction="Incoming",
                                            body="END",
                                            sent_at=None,
                                            received_at=datetime(2017, 8, 1, 17, 20, 20).replace(tzinfo=timezone.get_default_timezone())))

        # All outgoing messages are recorded in DB
        outgoing_messages_in_db = Message.objects.filter(direction="Outgoing")
        self.assertEqual(len(outgoing_messages_in_db), 3)
        self.assertTrue(Message.objects.get(contact=first_contact,
                                            direction="Outgoing",
                                            body=msg_subscribe("English").format(name="Roland"),
                                            received_at=None))
        self.assertTrue(Message.objects.get(contact=second_contact,
                                            direction="Outgoing",
                                            body=msg_subscribe("Hindi").format(name="Sai"),
                                            received_at=None))
        self.assertTrue(Message.objects.get(contact=second_contact,
                                            direction="Outgoing",
                                            body=msg_unsubscribe("Hindi"),
                                            received_at=None))

        # All messages are marked processed
        self.assertTrue(all([m.is_processed for m in outgoing_messages_in_db]))
        self.assertTrue(all([m.is_processed for m in incoming_messages_in_db]))

        # Texter sends a text for each outgoing message
        calls = [call(message=msg_subscribe("English").format(name="Roland"),
                      phone_number="1-111-1111"),
                 call(message=msg_subscribe("Hindi").format(name="Sai"),
                      phone_number="1-112-1111"),
                 call(message=msg_unsubscribe("Hindi"),
                      phone_number="1-112-1111")]
        mocked_texter_send.assert_has_calls(calls, any_order=True)
        self.assertEqual(mocked_texter_send.call_count, 3)

        # The messages actually have effects (create and cancel contacts)
        self.assertEqual(Contact.objects.count(), 2)
        contacts = Contact.objects.all()
        self.assertFalse(contacts[0].cancelled)
        self.assertEqual(contacts[0].language_preference, "English")
        self.assertTrue(contacts[1].cancelled)
        self.assertEqual(contacts[1].language_preference, "Hindi")
