import mock
from mock import patch
from freezegun import freeze_time
from django.test import TestCase

from datetime import datetime

from tests.fixtures import contact_object, text_reminder_object
from management.models import Message, Contact
from modules.text_processor import TextProcessor
from modules.text_reminder import TextReminder
from modules.i18n import six_week_reminder_seven_days, six_week_reminder_one_day, \
                         ten_week_reminder_seven_days, ten_week_reminder_one_day, \
                         fourteen_week_reminder_seven_days, fourteen_week_reminder_one_day, \
                         nine_month_reminder_seven_days, nine_month_reminder_one_day, \
                         sixteen_month_reminder_seven_days, sixteen_month_reminder_one_day, \
                         five_year_reminder_seven_days, five_year_reminder_one_day, \
                         verify_pregnant_signup_birthdate

FAKE_NOW = datetime(2017, 7, 17, 0, 0)

class TextReminderTests(TestCase):
    @freeze_time(FAKE_NOW)
    def test_no_eligible_reminders(self):
        tr = text_reminder_object("14/7/2017") # Born 3 days ago (relative to FAKE_NOW)
        self.assertFalse(tr.should_remind_today())
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=6,
                                                      days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=6,
                                                      days_before_appointment=1))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=10,
                                                      days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(months_after_birth=9,
                                                      days_before_appointment=7))
        self.assertEqual(tr.get_reminder_msg(), None)


    @freeze_time(FAKE_NOW)
    def test_remind_at_six_weeks_seven_days_english(self):
        tr = text_reminder_object("12/6/2017") # 7 days before the 6 week appointment
        self.assertTrue(tr.correct_date_for_reminder(weeks_after_birth=6,
                                                     days_before_appointment=7))
        self.assertTrue(tr.should_remind_today())
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=6,
                                                      days_before_appointment=1))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=10,
                                                      days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(months_after_birth=9,
                                                      days_before_appointment=7))
        self.assertEqual(tr.get_reminder_msg(),
                         six_week_reminder_seven_days("English").format(name="Roland"))

    @freeze_time(FAKE_NOW)
    def test_remind_at_six_weeks_seven_days_hindi(self):
        tr = text_reminder_object("12/6/2017", language="Hindi")
        self.assertTrue(tr.correct_date_for_reminder(weeks_after_birth=6,
                                                     days_before_appointment=7))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         six_week_reminder_seven_days('Hindi').format(name=u'\u0906\u0930\u0935'))

    @freeze_time(FAKE_NOW)
    def test_remind_at_six_weeks_seven_days_gujarati(self):
        tr = text_reminder_object("12/6/2017", language="Gujarati")
        self.assertTrue(tr.correct_date_for_reminder(weeks_after_birth=6,
                                                     days_before_appointment=7))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         six_week_reminder_seven_days("Gujarati").format(name=u'\u0906\u0930\u0935'))


    @freeze_time(FAKE_NOW)
    def test_remind_at_six_weeks_one_day_english(self):
        tr = text_reminder_object("6/6/2017") # One day before the 6 week appointment
        self.assertTrue(tr.correct_date_for_reminder(weeks_after_birth=6,
                                                     days_before_appointment=1))
        self.assertTrue(tr.should_remind_today())
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=6,
                                                      days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=10,
                                                      days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(months_after_birth=9,
                                                      days_before_appointment=7))
        self.assertEqual(tr.get_reminder_msg(),
                         six_week_reminder_one_day("English").format(name="Roland"))

    @freeze_time(FAKE_NOW)
    def test_remind_at_six_weeks_one_day_hindi(self):
        tr = text_reminder_object("6/6/2017", language="Hindi")
        self.assertTrue(tr.correct_date_for_reminder(weeks_after_birth=6,
                                                     days_before_appointment=1))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         six_week_reminder_one_day("Hindi").format(name=u'\u0906\u0930\u0935'))

    @freeze_time(FAKE_NOW)
    def test_remind_at_six_weeks_one_day_gujarati(self):
        tr = text_reminder_object("6/6/2017", language="Gujarati")
        self.assertTrue(tr.correct_date_for_reminder(weeks_after_birth=6,
                                                     days_before_appointment=1))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         six_week_reminder_one_day("Gujarati").format(name=u'\u0906\u0930\u0935'))


    @freeze_time(FAKE_NOW)
    def test_remind_at_ten_weeks_seven_days_english(self):
        tr = text_reminder_object("15/5/2017") # 7 days before the 10 week appointment
        self.assertTrue(tr.correct_date_for_reminder(weeks_after_birth=10,
                                                     days_before_appointment=7))
        self.assertTrue(tr.should_remind_today())
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=10,
                                                      days_before_appointment=1))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=6,
                                                      days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(months_after_birth=9,
                                                      days_before_appointment=7))
        self.assertEqual(tr.get_reminder_msg(),
                         ten_week_reminder_seven_days("English").format(name="Roland"))

    @freeze_time(FAKE_NOW)
    def test_remind_at_ten_weeks_seven_days_hindi(self):
        tr = text_reminder_object("15/5/2017", language="Hindi")
        self.assertTrue(tr.correct_date_for_reminder(weeks_after_birth=10,
                                                     days_before_appointment=7))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         ten_week_reminder_seven_days("Hindi").format(name=u'\u0906\u0930\u0935'))

    @freeze_time(FAKE_NOW)
    def test_remind_at_ten_weeks_seven_days_gujarati(self):
        tr = text_reminder_object("15/5/2017", language="Gujarati")
        self.assertTrue(tr.correct_date_for_reminder(weeks_after_birth=10,
                                                     days_before_appointment=7))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         ten_week_reminder_seven_days("Gujarati").format(name=u'\u0906\u0930\u0935'))


    @freeze_time(FAKE_NOW)
    def test_remind_at_ten_weeks_one_day_english(self):
        tr = text_reminder_object("9/5/2017") # 1 day before the 10 week appointment
        self.assertTrue(tr.correct_date_for_reminder(weeks_after_birth=10,
                                                     days_before_appointment=1))
        self.assertTrue(tr.should_remind_today())
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=10,
                                                      days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=6,
                                                      days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(months_after_birth=9,
                                                      days_before_appointment=7))
        self.assertEqual(tr.get_reminder_msg(),
                         ten_week_reminder_one_day("English").format(name="Roland"))

    @freeze_time(FAKE_NOW)
    def test_remind_at_ten_weeks_one_day_hindi(self):
        tr = text_reminder_object("9/5/2017", language="Hindi")
        self.assertTrue(tr.correct_date_for_reminder(weeks_after_birth=10,
                                                     days_before_appointment=1))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         ten_week_reminder_one_day("Hindi").format(name=u'\u0906\u0930\u0935'))

    @freeze_time(FAKE_NOW)
    def test_remind_at_ten_weeks_one_day_gujarati(self):
        tr = text_reminder_object("9/5/2017", language="Gujarati")
        self.assertTrue(tr.correct_date_for_reminder(weeks_after_birth=10,
                                                     days_before_appointment=1))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         ten_week_reminder_one_day("Gujarati").format(name=u'\u0906\u0930\u0935'))


    @freeze_time(FAKE_NOW)
    def test_remind_at_fourteen_weeks_seven_days_english(self):
        tr = text_reminder_object("17/4/2017") # 7 days before the 14 week appointment
        self.assertTrue(tr.correct_date_for_reminder(weeks_after_birth=14,
                                                     days_before_appointment=7))
        self.assertTrue(tr.should_remind_today())
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=10,
                                                      days_before_appointment=1))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=6,
                                                      days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(months_after_birth=9,
                                                      days_before_appointment=7))
        self.assertEqual(tr.get_reminder_msg(),
                         fourteen_week_reminder_seven_days("English").format(name="Roland"))

    @freeze_time(FAKE_NOW)
    def test_remind_at_fourteen_weeks_seven_days_hindi(self):
        tr = text_reminder_object("17/4/2017", language="Hindi")
        self.assertTrue(tr.correct_date_for_reminder(weeks_after_birth=14,
                                                     days_before_appointment=7))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         fourteen_week_reminder_seven_days("Hindi").format(name=u'\u0906\u0930\u0935'))

    @freeze_time(FAKE_NOW)
    def test_remind_at_fourteen_weeks_seven_days_gujarati(self):
        tr = text_reminder_object("17/4/2017", language="Gujarati")
        self.assertTrue(tr.correct_date_for_reminder(weeks_after_birth=14,
                                                     days_before_appointment=7))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         fourteen_week_reminder_seven_days("Gujarati").format(name=u'\u0906\u0930\u0935'))


    @freeze_time(FAKE_NOW)
    def test_remind_at_fourteen_weeks_one_day_english(self):
        tr = text_reminder_object("11/4/2017") # 1 day before the 14 week appointment
        self.assertTrue(tr.correct_date_for_reminder(weeks_after_birth=14,
                                                     days_before_appointment=1))
        self.assertTrue(tr.should_remind_today())
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=10,
                                                      days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=6,
                                                      days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(months_after_birth=9,
                                                      days_before_appointment=7))
        self.assertEqual(tr.get_reminder_msg(),
                         fourteen_week_reminder_one_day("English").format(name="Roland"))

    @freeze_time(FAKE_NOW)
    def test_remind_at_fourteen_weeks_one_day_hindi(self):
        tr = text_reminder_object("11/4/2017", language="Hindi")
        self.assertTrue(tr.correct_date_for_reminder(weeks_after_birth=14,
                                                     days_before_appointment=1))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         fourteen_week_reminder_one_day("Hindi").format(name=u'\u0906\u0930\u0935'))

    @freeze_time(FAKE_NOW)
    def test_remind_at_fourteen_weeks_one_day_gujarati(self):
        tr = text_reminder_object("11/4/2017", language="Gujarati")
        self.assertTrue(tr.correct_date_for_reminder(weeks_after_birth=14,
                                                     days_before_appointment=1))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         fourteen_week_reminder_one_day("Gujarati").format(name=u'\u0906\u0930\u0935'))


    @freeze_time(FAKE_NOW)
    def test_remind_at_nine_months_seven_days_english(self):
        tr = text_reminder_object("24/10/2016") # 7 days before the 9 month appointment
        self.assertTrue(tr.correct_date_for_reminder(months_after_birth=9,
                                                     days_before_appointment=7))
        self.assertTrue(tr.should_remind_today())
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=10,
                                                      days_before_appointment=1))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=6,
                                                      days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=14,
                                                      days_before_appointment=7))
        self.assertEqual(tr.get_reminder_msg(),
                         nine_month_reminder_seven_days("English").format(name="Roland"))

    @freeze_time(FAKE_NOW)
    def test_remind_at_nine_months_seven_days_hindi(self):
        tr = text_reminder_object("24/10/2016", language="Hindi")
        self.assertTrue(tr.correct_date_for_reminder(months_after_birth=9,
                                                     days_before_appointment=7))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         nine_month_reminder_seven_days("Hindi").format(name=u'\u0906\u0930\u0935'))

    @freeze_time(FAKE_NOW)
    def test_remind_at_nine_months_seven_days_gujarati(self):
        tr = text_reminder_object("24/10/2016", language="Gujarati")
        self.assertTrue(tr.correct_date_for_reminder(months_after_birth=9,
                                                     days_before_appointment=7))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         nine_month_reminder_seven_days("Gujarati").format(name=u'\u0906\u0930\u0935'))


    @freeze_time(FAKE_NOW)
    def test_remind_at_nine_months_one_day_english(self):
        tr = text_reminder_object("18/10/2016") # 1 day before the 9 month appointment
        self.assertTrue(tr.correct_date_for_reminder(months_after_birth=9,
                                                     days_before_appointment=1))
        self.assertTrue(tr.should_remind_today())
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=10,
                                                      days_before_appointment=1))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=6,
                                                      days_before_appointment=1))
        self.assertFalse(tr.correct_date_for_reminder(months_after_birth=9,
                                                      days_before_appointment=7))
        self.assertEqual(tr.get_reminder_msg(),
                         nine_month_reminder_one_day("English").format(name="Roland"))

    @freeze_time(FAKE_NOW)
    def test_remind_at_nine_months_one_day_hindi(self):
        tr = text_reminder_object("18/10/2016", language="Hindi")
        self.assertTrue(tr.correct_date_for_reminder(months_after_birth=9,
                                                     days_before_appointment=1))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         nine_month_reminder_one_day("Hindi").format(name=u'\u0906\u0930\u0935'))

    @freeze_time(FAKE_NOW)
    def test_remind_at_nine_months_one_day_gujarati(self):
        tr = text_reminder_object("18/10/2016", language="Gujarati")
        self.assertTrue(tr.correct_date_for_reminder(months_after_birth=9,
                                                     days_before_appointment=1))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         nine_month_reminder_one_day("Gujarati").format(name=u'\u0906\u0930\u0935'))


    @freeze_time(FAKE_NOW)
    def test_remind_at_sixteen_months_seven_days_english(self):
        tr = text_reminder_object("24/3/2016") # 7 days before the 16 month appointment
        self.assertTrue(tr.correct_date_for_reminder(months_after_birth=16,
                                                     days_before_appointment=7))
        self.assertTrue(tr.should_remind_today())
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=10,
                                                      days_before_appointment=1))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=6,
                                                      days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(months_after_birth=16,
                                                      days_before_appointment=1))
        self.assertEqual(tr.get_reminder_msg(),
                         sixteen_month_reminder_seven_days("English").format(name="Roland"))

    @freeze_time(FAKE_NOW)
    def test_remind_at_sixteen_months_seven_days_hindi(self):
        tr = text_reminder_object("24/3/2016", language="Hindi")
        self.assertTrue(tr.correct_date_for_reminder(months_after_birth=16,
                                                     days_before_appointment=7))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         sixteen_month_reminder_seven_days("Hindi").format(name=u'\u0906\u0930\u0935'))

    @freeze_time(FAKE_NOW)
    def test_remind_at_sixteen_months_seven_days_gujarati(self):
        tr = text_reminder_object("24/3/2016", language="Gujarati")
        self.assertTrue(tr.correct_date_for_reminder(months_after_birth=16,
                                                     days_before_appointment=7))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         sixteen_month_reminder_seven_days("Gujarati").format(name=u'\u0906\u0930\u0935'))


    @freeze_time(FAKE_NOW)
    def test_remind_at_sixteen_months_one_day_english(self):
        tr = text_reminder_object("18/3/2016") # 1 day before the 16 month appointment
        self.assertTrue(tr.correct_date_for_reminder(months_after_birth=16,
                                                     days_before_appointment=1))
        self.assertTrue(tr.should_remind_today())
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=10,
                                                      days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=6,
                                                      days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(months_after_birth=16,
                                                      days_before_appointment=7))
        self.assertEqual(tr.get_reminder_msg(),
                         sixteen_month_reminder_one_day("English").format(name="Roland"))

    @freeze_time(FAKE_NOW)
    def test_remind_at_sixteen_months_one_day_hindi(self):
        tr = text_reminder_object("18/3/2016", language="Hindi")
        self.assertTrue(tr.correct_date_for_reminder(months_after_birth=16,
                                                     days_before_appointment=1))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         sixteen_month_reminder_one_day("Hindi").format(name=u'\u0906\u0930\u0935'))

    @freeze_time(FAKE_NOW)
    def test_remind_at_sixteen_months_one_day_gujarati(self):
        tr = text_reminder_object("18/3/2016", language="Gujarati")
        self.assertTrue(tr.correct_date_for_reminder(months_after_birth=16,
                                                     days_before_appointment=1))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         sixteen_month_reminder_one_day("Gujarati").format(name=u'\u0906\u0930\u0935'))


    @freeze_time(FAKE_NOW)
    def test_remind_at_five_years_seven_days_english(self):
        tr = text_reminder_object("24/7/2012") # 7 days before the 5 year appointment
        self.assertTrue(tr.correct_date_for_reminder(years_after_birth=5,
                                                     days_before_appointment=7))
        self.assertTrue(tr.should_remind_today())
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=10,
                                                      days_before_appointment=1))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=6,
                                                      days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(years_after_birth=5,
                                                      days_before_appointment=1))
        self.assertEqual(tr.get_reminder_msg(),
                         five_year_reminder_seven_days("English").format(name="Roland"))

    @freeze_time(FAKE_NOW)
    def test_remind_at_five_years_seven_days_hindi(self):
        tr = text_reminder_object("24/7/2012", language="Hindi")
        self.assertTrue(tr.correct_date_for_reminder(years_after_birth=5,
                                                     days_before_appointment=7))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         five_year_reminder_seven_days("Hindi").format(name=u'\u0906\u0930\u0935'))

    @freeze_time(FAKE_NOW)
    def test_remind_at_five_years_seven_days_gujarati(self):
        tr = text_reminder_object("24/7/2012", language="Gujarati")
        self.assertTrue(tr.correct_date_for_reminder(years_after_birth=5,
                                                     days_before_appointment=7))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         five_year_reminder_seven_days("Gujarati").format(name=u'\u0906\u0930\u0935'))


    @freeze_time(FAKE_NOW)
    def test_remind_at_five_years_one_day_english(self):
        tr = text_reminder_object("18/7/2012") # 1 day before the 5 year appointment
        self.assertTrue(tr.correct_date_for_reminder(years_after_birth=5,
                                                     days_before_appointment=1))
        self.assertTrue(tr.should_remind_today())
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=10,
                                                      days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=6,
                                                      days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(years_after_birth=5,
                                                      days_before_appointment=7))
        self.assertEqual(tr.get_reminder_msg(),
                         five_year_reminder_one_day("English").format(name="Roland"))

    @freeze_time(FAKE_NOW)
    def test_remind_at_five_years_one_day_hindi(self):
        tr = text_reminder_object("18/7/2012", language="Hindi")
        self.assertTrue(tr.correct_date_for_reminder(years_after_birth=5,
                                                     days_before_appointment=1))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         five_year_reminder_one_day("Hindi").format(name=u'\u0906\u0930\u0935'))

    @freeze_time(FAKE_NOW)
    def test_remind_at_five_years_one_day_gujarati(self):
        tr = text_reminder_object("18/7/2012", language="Gujarati")
        self.assertTrue(tr.correct_date_for_reminder(years_after_birth=5,
                                                     days_before_appointment=1))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         five_year_reminder_one_day("Gujarati").format(name=u'\u0906\u0930\u0935'))


    @freeze_time(FAKE_NOW)
    @patch("modules.text_reminder.Texter.send")
    def test_send_text_when_eligible(self, mocked_send_text):
        tr = text_reminder_object("12/6/2017") # 7 days before the 6 week appointment
        self.assertTrue(tr.should_remind_today())
        tr.remind()
        mocked_send_text.assert_called_once_with(message=tr.get_reminder_msg(),
                                                 phone_number="1-111-1111")

    @freeze_time(FAKE_NOW)
    @patch("modules.text_reminder.Texter.send")
    def test_do_not_send_text_when_not_eligible(self, mocked_send_text):
        tr = text_reminder_object("10/7/2017") # 7 days ago
        self.assertFalse(tr.should_remind_today())
        self.assertTrue("Contact has no reminders for today's date." in tr.why_not_remind_reasons())
        tr.remind()
        self.assertFalse(mocked_send_text.called)

    @freeze_time(FAKE_NOW)
    @patch("logging.info")
    @patch("modules.text_reminder.Texter.send")
    @patch("modules.text_processor.Texter.send")
    def test_remind_when_good_dont_remind_when_cancelled(self, r_mocked_send_text, t_mocked_send_text, mocked_logging):
        tr = text_reminder_object("12/6/2017") # 7 days before the 6 week appointment
        self.assertTrue(tr.should_remind_today())
        tp = TextProcessor(phone_number=tr.phone_number)
        tp.process("END")
        self.assertTrue("Contact is cancelled." in tr.why_not_remind_reasons())
        self.assertFalse(tr.should_remind_today())

    @freeze_time(FAKE_NOW)
    @patch("modules.text_reminder.Texter.send")
    def test_message_object_created_upon_remind(self, mocked_send_text):
        tr = text_reminder_object("12/6/2017") # 7 days before the 6 week appointment
        self.assertTrue(tr.should_remind_today())
        self.assertFalse(Message.objects.filter(contact=tr.contact, direction="Outgoing", body=tr.get_reminder_msg()))
        tr.remind()
        self.assertEqual(1, Message.objects.filter(contact=tr.contact, direction="Outgoing", body=tr.get_reminder_msg()).count())
        mocked_send_text.assert_called_once_with(message=tr.get_reminder_msg(),
                                                 phone_number="1-111-1111")

    @freeze_time(FAKE_NOW)
    @patch("modules.text_reminder.Texter.send")
    def test_message_object_not_created_when_no_remind(self, mocked_send_text):
       tr = text_reminder_object("10/7/2017") # 7 days ago
       self.assertFalse(tr.should_remind_today())
       self.assertFalse(Message.objects.filter(contact=tr.contact, direction="Outgoing", body=tr.get_reminder_msg()))
       tr.remind()
       self.assertEqual(0, Message.objects.filter(contact=tr.contact, direction="Outgoing", body=tr.get_reminder_msg()).count())
       self.assertFalse(mocked_send_text.called)

    @patch("modules.text_reminder.Texter.send")
    def test_multiple_message_objects_created_for_multiple_reminders(self, mocked_send_text):
        tr = text_reminder_object("12/6/2017") 
        with freeze_time(datetime(2017, 7, 17, 0, 0)): # 7 days before the 6 week appointment on July 24th
            self.assertTrue(tr.should_remind_today())
            self.assertFalse(Message.objects.filter(contact=tr.contact, direction="Outgoing", body=tr.get_reminder_msg()))
            tr.remind()
            self.assertEqual(1, Message.objects.filter(contact=tr.contact, direction="Outgoing", body=tr.get_reminder_msg()).count())
            mocked_send_text.assert_called_once_with(message=tr.get_reminder_msg(),
                                                        phone_number="1-111-1111")

        with freeze_time(datetime(2017, 7, 23, 0, 0)): # 1 day before the 6 week appointment on July 24th
            self.assertTrue(tr.should_remind_today())
            self.assertTrue(Message.objects.filter(contact=tr.contact, direction="Outgoing"))
            tr.remind()
            self.assertEqual(2, Message.objects.filter(contact=tr.contact, direction="Outgoing").count())
            self.assertEqual(2, mocked_send_text.call_count)

        with freeze_time(datetime(2017, 8, 14, 0, 0)): # 7 days before the 10 week appointment on August 21th
            self.assertTrue(tr.should_remind_today())
            self.assertTrue(Message.objects.filter(contact=tr.contact, direction="Outgoing"))
            tr.remind()
            self.assertEqual(3, Message.objects.filter(contact=tr.contact, direction="Outgoing").count())
            self.assertEqual(3, mocked_send_text.call_count)

        with freeze_time(datetime(2017, 8, 20, 0, 0)): # 1 day before the 10 week appointment on August 21th
            self.assertTrue(tr.should_remind_today())
            self.assertTrue(Message.objects.filter(contact=tr.contact, direction="Outgoing"))
            tr.remind()
            self.assertEqual(4, Message.objects.filter(contact=tr.contact, direction="Outgoing").count())
            self.assertEqual(4, mocked_send_text.call_count)

    @patch("modules.text_reminder.Texter.send")
    def test_message_objects_created_only_when_reminders_sent(self, mocked_send_text):
        tr = text_reminder_object("12/6/2017") 
        with freeze_time(datetime(2017, 7, 17, 0, 0)): # 7 days before the 6 week appointment on July 24th
            self.assertTrue(tr.should_remind_today())
            self.assertFalse(Message.objects.filter(contact=tr.contact, direction="Outgoing", body=tr.get_reminder_msg()))
            tr.remind()
            self.assertEqual(1, Message.objects.filter(contact=tr.contact, direction="Outgoing", body=tr.get_reminder_msg()).count())
            mocked_send_text.assert_called_once_with(message=tr.get_reminder_msg(),
                                                        phone_number="1-111-1111")

        with freeze_time(datetime(2017, 7, 20, 0, 0)): # 4 days before the 6 week appointment on July 24th
            self.assertFalse(tr.should_remind_today())
            self.assertTrue(Message.objects.filter(contact=tr.contact, direction="Outgoing"))
            tr.remind()
            self.assertEqual(1, Message.objects.filter(contact=tr.contact, direction="Outgoing").count())
            self.assertEqual(1, mocked_send_text.call_count)

        with freeze_time(datetime(2017, 7, 23, 0, 0)): # 1 days before the 6 week appointment on July 24th
            self.assertTrue(tr.should_remind_today())
            self.assertTrue(Message.objects.filter(contact=tr.contact, direction="Outgoing"))
            tr.remind()
            self.assertEqual(2, Message.objects.filter(contact=tr.contact, direction="Outgoing").count())
            self.assertEqual(2, mocked_send_text.call_count)

        with freeze_time(datetime(2017, 7, 27, 0, 0)): # 3 days after the 6 week appointment on July 24th
            self.assertFalse(tr.should_remind_today())
            self.assertTrue(Message.objects.filter(contact=tr.contact, direction="Outgoing"))
            tr.remind()
            self.assertEqual(2, Message.objects.filter(contact=tr.contact, direction="Outgoing").count())
            self.assertEqual(2, mocked_send_text.call_count)

        with freeze_time(datetime(2017, 8, 14, 0, 0)): # 7 days before the 10 week appointment on August 21th
            self.assertTrue(tr.should_remind_today())
            self.assertTrue(Message.objects.filter(contact=tr.contact, direction="Outgoing"))
            tr.remind()
            self.assertEqual(3, Message.objects.filter(contact=tr.contact, direction="Outgoing").count())
            self.assertEqual(3, mocked_send_text.call_count)

    def test_preg_signup_check(self):
        signup_and_update = text_reminder_object("4/6/2017", language="Hindi", preg_signup=True, preg_update=True)
        signup_no_update = text_reminder_object("4/6/2017", language="Hindi", preg_signup=True, preg_update=False)
        update_no_signup = text_reminder_object("4/6/2017", language="Hindi", preg_signup=False, preg_update=True)
        no_signup_no_update = text_reminder_object("4/6/2017", language="Hindi", preg_signup=False, preg_update=False)
        
        self.assertTrue(signup_no_update.preg_signup_check())
        self.assertFalse(signup_and_update.preg_signup_check())
        self.assertFalse(update_no_signup.preg_signup_check())
        self.assertFalse(no_signup_no_update.preg_signup_check())

    @freeze_time(FAKE_NOW)
    def test_remind_at_two_weeks_english(self):
        tr = text_reminder_object("03/7/2017", preg_signup=True, preg_update=False) # 2 weeks, 0 days ago
        self.assertTrue(tr.correct_date_for_reminder(weeks_after_birth=2, days_before_appointment=0))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=4, days_before_appointment=0))
        self.assertTrue(tr.should_remind_today())
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=6, days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=6, days_before_appointment=1))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=10, days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=10, days_before_appointment=1))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=14, days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=14, days_before_appointment=1))
        self.assertFalse(tr.correct_date_for_reminder(months_after_birth=9, days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(months_after_birth=9, days_before_appointment=1))
        self.assertFalse(tr.correct_date_for_reminder(months_after_birth=16, days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(months_after_birth=16, days_before_appointment=1))
        self.assertFalse(tr.correct_date_for_reminder(years_after_birth=5, days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(years_after_birth=5, days_before_appointment=1))
        self.assertEqual(tr.get_reminder_msg(),
                         verify_pregnant_signup_birthdate("English").format(name="Roland"))

    @freeze_time(FAKE_NOW)
    def test_dont_remind_at_two_weeks_english(self):
        no_signup_no_update = text_reminder_object("03/7/2017", language="English", preg_signup=False, preg_update=False) # 2 weeks, 0 days ago
        self.assertIsNone(no_signup_no_update.get_reminder_msg())
        self.assertFalse(no_signup_no_update.should_remind_today())
        update_no_signup = text_reminder_object("03/7/2017", language="English", preg_signup=False, preg_update=True) # 2 weeks, 0 days ago
        self.assertIsNone(update_no_signup.get_reminder_msg())
        self.assertFalse(update_no_signup.should_remind_today())
        signup_and_update = text_reminder_object("03/7/2017", language="English", preg_signup=True, preg_update=True) # 2 weeks, 0 days ago
        self.assertIsNone(signup_and_update.get_reminder_msg())
        self.assertFalse(signup_and_update.should_remind_today())

    @freeze_time(FAKE_NOW)
    def test_remind_at_four_weeks_english(self):
        tr = text_reminder_object("19/6/2017", preg_signup=True, preg_update=False) # 4 weeks, 0 days ago
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=2, days_before_appointment=0))
        self.assertTrue(tr.correct_date_for_reminder(weeks_after_birth=4, days_before_appointment=0))
        self.assertTrue(tr.should_remind_today())
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=6, days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=6, days_before_appointment=1))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=10, days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=10, days_before_appointment=1))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=14, days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=14, days_before_appointment=1))
        self.assertFalse(tr.correct_date_for_reminder(months_after_birth=9, days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(months_after_birth=9, days_before_appointment=1))
        self.assertFalse(tr.correct_date_for_reminder(months_after_birth=16, days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(months_after_birth=16, days_before_appointment=1))
        self.assertFalse(tr.correct_date_for_reminder(years_after_birth=5, days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(years_after_birth=5, days_before_appointment=1))
        self.assertEqual(tr.get_reminder_msg(),
                         verify_pregnant_signup_birthdate("English").format(name="Roland"))

    @freeze_time(FAKE_NOW)
    def test_dont_remind_at_four_weeks_english(self):
        no_signup_no_update = text_reminder_object("19/6/2017", language="English", preg_signup=False, preg_update=False) # 4 weeks, 0 days ago
        self.assertIsNone(no_signup_no_update.get_reminder_msg())
        self.assertFalse(no_signup_no_update.should_remind_today())
        update_no_signup = text_reminder_object("19/6/2017", language="English", preg_signup=False, preg_update=True) # 4 weeks, 0 days ago
        self.assertIsNone(update_no_signup.get_reminder_msg())
        self.assertFalse(update_no_signup.should_remind_today())
        signup_and_update = text_reminder_object("19/6/2017", language="English", preg_signup=True, preg_update=True) # 4 weeks, 0 days ago
        self.assertIsNone(signup_and_update.get_reminder_msg())
        self.assertFalse(signup_and_update.should_remind_today())


    @freeze_time(FAKE_NOW)
    def test_remind_at_two_weeks_hindi(self):
        tr = text_reminder_object("03/7/2017", language="Hindi", preg_signup=True, preg_update=False)
        self.assertTrue(tr.correct_date_for_reminder(weeks_after_birth=2, days_before_appointment=0))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         verify_pregnant_signup_birthdate('Hindi').format(name=u'\u0906\u0930\u0935'))

    @freeze_time(FAKE_NOW)
    def test_dont_remind_at_two_weeks_hindi(self):
        no_signup_no_update = text_reminder_object("03/7/2017", language="Hindi", preg_signup=False, preg_update=False) # 2 weeks, 0 days ago
        self.assertIsNone(no_signup_no_update.get_reminder_msg())
        self.assertFalse(no_signup_no_update.should_remind_today())
        update_no_signup = text_reminder_object("03/7/2017", language="Hindi", preg_signup=False, preg_update=True) # 2 weeks, 0 days ago
        self.assertIsNone(update_no_signup.get_reminder_msg())
        self.assertFalse(update_no_signup.should_remind_today())
        signup_and_update = text_reminder_object("03/7/2017", language="Hindi", preg_signup=True, preg_update=True) # 2 weeks, 0 days ago
        self.assertIsNone(signup_and_update.get_reminder_msg())
        self.assertFalse(signup_and_update.should_remind_today())

    @freeze_time(FAKE_NOW)
    def test_remind_at_four_weeks_hindi(self):
        tr = text_reminder_object("19/6/2017", language="Hindi", preg_signup=True, preg_update=False)
        self.assertTrue(tr.correct_date_for_reminder(weeks_after_birth=4, days_before_appointment=0))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         verify_pregnant_signup_birthdate('Hindi').format(name=u'\u0906\u0930\u0935'))

    @freeze_time(FAKE_NOW)
    def test_dont_remind_at_four_weeks_hindi(self):
        no_signup_no_update = text_reminder_object("19/6/2017", language="Hindi", preg_signup=False, preg_update=False) # 4 weeks, 0 days ago
        self.assertIsNone(no_signup_no_update.get_reminder_msg())
        self.assertFalse(no_signup_no_update.should_remind_today())
        update_no_signup = text_reminder_object("19/6/2017", language="Hindi", preg_signup=False, preg_update=True) # 4 weeks, 0 days ago
        self.assertIsNone(update_no_signup.get_reminder_msg())
        self.assertFalse(update_no_signup.should_remind_today())
        signup_and_update = text_reminder_object("19/6/2017", language="Hindi", preg_signup=True, preg_update=True) # 4 weeks, 0 days ago
        self.assertIsNone(signup_and_update.get_reminder_msg())
        self.assertFalse(signup_and_update.should_remind_today())

    @freeze_time(FAKE_NOW)
    def test_preg_signups_with_update_messaged_at_correct_times(self):
        tr = text_reminder_object("12/6/2017", preg_signup=True, preg_update=True) # 6 weeks, 7 days ago
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=2, days_before_appointment=0))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=4, days_before_appointment=0))
        self.assertTrue(tr.should_remind_today())
        self.assertTrue(tr.correct_date_for_reminder(weeks_after_birth=6, days_before_appointment=7))
        tr = text_reminder_object("6/6/2017", preg_signup=True, preg_update=True) # 6 weeks, 1 days ago
        self.assertTrue(tr.should_remind_today())
        self.assertTrue(tr.correct_date_for_reminder(weeks_after_birth=6, days_before_appointment=1))
        tr = text_reminder_object("15/5/2017", preg_signup=True, preg_update=True) # 10 weeks, 7 days ago
        self.assertTrue(tr.should_remind_today())
        self.assertTrue(tr.correct_date_for_reminder(weeks_after_birth=10, days_before_appointment=7))
        tr = text_reminder_object("9/5/2017", preg_signup=True, preg_update=True) # 10 weeks, 1 days ago
        self.assertTrue(tr.should_remind_today())
        self.assertTrue(tr.correct_date_for_reminder(weeks_after_birth=10, days_before_appointment=1))

        tr = text_reminder_object("17/4/2017", preg_signup=True, preg_update=True) # 14 weeks, 7 days ago
        self.assertTrue(tr.should_remind_today())
        self.assertTrue(tr.correct_date_for_reminder(weeks_after_birth=14, days_before_appointment=7))
        tr = text_reminder_object("11/4/2017", preg_signup=True, preg_update=True) # 14 weeks, 1 days ago
        self.assertTrue(tr.should_remind_today())
        self.assertTrue(tr.correct_date_for_reminder(weeks_after_birth=14, days_before_appointment=1))

        tr = text_reminder_object("24/10/2016", preg_signup=True, preg_update=True) # # 9 months, 7 days ago
        self.assertTrue(tr.should_remind_today())
        self.assertTrue(tr.correct_date_for_reminder(months_after_birth=9, days_before_appointment=7))
        tr = text_reminder_object("18/10/2016", preg_signup=True, preg_update=True) # # 9 months, 1 days ago
        self.assertTrue(tr.should_remind_today())
        self.assertTrue(tr.correct_date_for_reminder(months_after_birth=9, days_before_appointment=1))

        tr = text_reminder_object("24/3/2016", preg_signup=True, preg_update=True) # 16 months, 7 days ago
        self.assertTrue(tr.should_remind_today())
        self.assertTrue(tr.correct_date_for_reminder(months_after_birth=16, days_before_appointment=7))
        tr = text_reminder_object("18/3/2016", preg_signup=True, preg_update=True) # 16 months, 1 days ago
        self.assertTrue(tr.should_remind_today())
        self.assertTrue(tr.correct_date_for_reminder(months_after_birth=16, days_before_appointment=1))
        tr = text_reminder_object("24/7/2012", preg_signup=True, preg_update=True) # 5 years, 7 days ago
        self.assertTrue(tr.should_remind_today())
        self.assertTrue(tr.correct_date_for_reminder(years_after_birth=5, days_before_appointment=7))
        tr = text_reminder_object("18/7/2012", preg_signup=True, preg_update=True) # 5 years, 1 days ago
        self.assertTrue(tr.should_remind_today())
        self.assertTrue(tr.correct_date_for_reminder(years_after_birth=5, days_before_appointment=1))

    @freeze_time(FAKE_NOW)
    def test_preg_signups_without_updates_messaged_at_correct_times(self):
        tr = text_reminder_object("12/6/2017", preg_signup=True, preg_update=False) # 6 weeks, 7 days ago
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=2, days_before_appointment=0))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=4, days_before_appointment=0))
        self.assertTrue(tr.should_remind_today())
        self.assertTrue(tr.correct_date_for_reminder(weeks_after_birth=6, days_before_appointment=7))
        tr = text_reminder_object("6/6/2017", preg_signup=True, preg_update=False) # 6 weeks, 1 days ago
        self.assertTrue(tr.should_remind_today())
        self.assertTrue(tr.correct_date_for_reminder(weeks_after_birth=6, days_before_appointment=1))
        tr = text_reminder_object("15/5/2017", preg_signup=True, preg_update=False) # 10 weeks, 7 days ago
        self.assertTrue(tr.should_remind_today())
        self.assertTrue(tr.correct_date_for_reminder(weeks_after_birth=10, days_before_appointment=7))
        tr = text_reminder_object("9/5/2017", preg_signup=True, preg_update=False) # 10 weeks, 1 days ago
        self.assertTrue(tr.should_remind_today())
        self.assertTrue(tr.correct_date_for_reminder(weeks_after_birth=10, days_before_appointment=1))

        tr = text_reminder_object("17/4/2017", preg_signup=True, preg_update=False) # 14 weeks, 7 days ago
        self.assertTrue(tr.should_remind_today())
        self.assertTrue(tr.correct_date_for_reminder(weeks_after_birth=14, days_before_appointment=7))
        tr = text_reminder_object("11/4/2017", preg_signup=True, preg_update=False) # 14 weeks, 1 days ago
        self.assertTrue(tr.should_remind_today())
        self.assertTrue(tr.correct_date_for_reminder(weeks_after_birth=14, days_before_appointment=1))

        tr = text_reminder_object("24/10/2016", preg_signup=True, preg_update=False) # # 9 months, 7 days ago
        self.assertTrue(tr.should_remind_today())
        self.assertTrue(tr.correct_date_for_reminder(months_after_birth=9, days_before_appointment=7))
        tr = text_reminder_object("18/10/2016", preg_signup=True, preg_update=False) # # 9 months, 1 days ago
        self.assertTrue(tr.should_remind_today())
        self.assertTrue(tr.correct_date_for_reminder(months_after_birth=9, days_before_appointment=1))

        tr = text_reminder_object("24/3/2016", preg_signup=True, preg_update=False) # 16 months, 7 days ago
        self.assertTrue(tr.should_remind_today())
        self.assertTrue(tr.correct_date_for_reminder(months_after_birth=16, days_before_appointment=7))
        tr = text_reminder_object("18/3/2016", preg_signup=True, preg_update=False) # 16 months, 1 days ago
        self.assertTrue(tr.should_remind_today())
        self.assertTrue(tr.correct_date_for_reminder(months_after_birth=16, days_before_appointment=1))
        tr = text_reminder_object("24/7/2012", preg_signup=True, preg_update=False) # 5 years, 7 days ago
        self.assertTrue(tr.should_remind_today())
        self.assertTrue(tr.correct_date_for_reminder(years_after_birth=5, days_before_appointment=7))
        tr = text_reminder_object("18/7/2012", preg_signup=True, preg_update=False) # 5 years, 1 days ago
        self.assertTrue(tr.should_remind_today())
        self.assertTrue(tr.correct_date_for_reminder(years_after_birth=5, days_before_appointment=1))


    @freeze_time(FAKE_NOW)
    def test_preg_signups_not_messaged_at_wrong_times(self):
        tr = text_reminder_object("1/7/2017", preg_signup=True, preg_update=False) # 2 weeks, 2 days ago
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=2, days_before_appointment=0))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=4, days_before_appointment=0))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=6, days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=6, days_before_appointment=1))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=10, days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=10, days_before_appointment=1))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=14, days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=14, days_before_appointment=1))
        self.assertFalse(tr.correct_date_for_reminder(months_after_birth=9, days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(months_after_birth=9, days_before_appointment=1))
        self.assertFalse(tr.correct_date_for_reminder(months_after_birth=16, days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(months_after_birth=16, days_before_appointment=1))
        self.assertFalse(tr.correct_date_for_reminder(years_after_birth=5, days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(years_after_birth=5, days_before_appointment=1))

        tr = text_reminder_object("21/6/2017", preg_signup=True, preg_update=False) # 4 weeks, 2 days ago
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=2, days_before_appointment=0))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=4, days_before_appointment=0))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=6, days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=6, days_before_appointment=1))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=10, days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=10, days_before_appointment=1))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=14, days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(weeks_after_birth=14, days_before_appointment=1))
        self.assertFalse(tr.correct_date_for_reminder(months_after_birth=9, days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(months_after_birth=9, days_before_appointment=1))
        self.assertFalse(tr.correct_date_for_reminder(months_after_birth=16, days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(months_after_birth=16, days_before_appointment=1))
        self.assertFalse(tr.correct_date_for_reminder(years_after_birth=5, days_before_appointment=7))
        self.assertFalse(tr.correct_date_for_reminder(years_after_birth=5, days_before_appointment=1))

    @freeze_time(FAKE_NOW)
    def test_remind_updates_last_contacted_english(self):
        tr = text_reminder_object("03/7/2017", preg_signup=True, preg_update=False) # 2 weeks, 0 days ago
        tr.remind()
        two_week_message = Message.objects.filter(contact=tr.contact, direction="Outgoing").first()
        self.assertEqual(tr.contact.last_contacted, two_week_message.time)

        tr2 = text_reminder_object("19/6/2017", preg_signup=True, preg_update=False)
        tr2.remind()
        four_week_message = Message.objects.filter(contact=tr2.contact, direction="Outgoing").first()
        self.assertEqual(tr2.contact.last_contacted, four_week_message.time)

    @freeze_time(FAKE_NOW)
    def test_remind_updates_last_contacted_hindi(self):
        tr = text_reminder_object("03/7/2017", language="Hindi", preg_signup=True, preg_update=False) # 2 weeks, 0 days ago
        tr.remind()
        two_week_message = Message.objects.filter(contact=tr.contact, direction="Outgoing").first()
        self.assertEqual(tr.contact.last_contacted, two_week_message.time)

        tr2 = text_reminder_object("19/6/2017", language="Hindi", preg_signup=True, preg_update=False)
        tr2.remind()
        four_week_message = Message.objects.filter(contact=tr2.contact, direction="Outgoing").first()
        self.assertEqual(tr2.contact.last_contacted, four_week_message.time)