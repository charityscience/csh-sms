import mock
from mock import patch, call
from freezegun import freeze_time
from datetime import datetime
from django.test import TestCase

from tests.fixtures import contact_object
from modules.text_reminder import TextReminder
from jobs import text_reminder_job

FAKE_NOW = datetime(2017, 7, 17, 0, 0)

class TextReminderJobTests(TestCase):
    @freeze_time(FAKE_NOW)
    @patch("logging.info")
    @patch("modules.text_reminder.Texter.send")
    def test_remind_two_people(self, mocked_send_text, mocked_logger):
        c1 = contact_object(name="Roland",
                            phone_number="1-111-1111",
                            date_of_birth="12/6/2017") # 7 days before 6 week appointment
        c2 = contact_object(name="Sai",
                            phone_number="1-112-1111",
                            date_of_birth="12/6/2017",
                            language="Hindi")
        text_reminder_job.remind_all()
        calls = [call(message=TextReminder(c1).get_reminder_msg(),
                      phone_number=c1.phone_number),
                 call(message=TextReminder(c2).get_reminder_msg(),
                      phone_number=c2.phone_number)]
        mocked_send_text.assert_has_calls(calls, any_order=True)
        self.assertEqual(mocked_send_text.call_count, 2)

    @freeze_time(FAKE_NOW)
    @patch("logging.info")
    @patch("modules.text_reminder.Texter.send")
    def test_remind_two_people_but_not_the_cancelled_one(self, mocked_send_text, mocked_logger):
        c1 = contact_object(name="Roland",
                            phone_number="1-111-1111",
                            date_of_birth="12/6/2017") # 7 days before 6 week appointment
        c2 = contact_object(name="Sai",
                            phone_number="1-112-1111",
                            date_of_birth="12/6/2017",
                            language="Hindi")
        c3 = contact_object(name="Cancelled",
                            phone_number="1-111-1112",
                            date_of_birth="12/6/2017")
        c3.cancelled = True
        c3.save()
        text_reminder_job.remind_all()
        calls = [call(message=TextReminder(c1).get_reminder_msg(),
                      phone_number=c1.phone_number),
                 call(message=TextReminder(c2).get_reminder_msg(),
                      phone_number=c2.phone_number)]
        mocked_send_text.assert_has_calls(calls, any_order=True)
        self.assertEqual(mocked_send_text.call_count, 2)
