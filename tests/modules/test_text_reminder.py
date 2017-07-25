import mock
from mock import patch
from freezegun import freeze_time
from django.test import TestCase

from datetime import datetime

from management.models import Contact
from modules.date_helper import date_string_to_date
from modules.text_reminder import TextReminder
from modules.text_processor import TextProcessor
from modules.i18n import six_week_reminder_seven_days, six_week_reminder_one_day, \
                         ten_week_reminder_seven_days, ten_week_reminder_one_day, \
                         fourteen_week_reminder_seven_days, fourteen_week_reminder_one_day, \
                         nine_month_reminder_seven_days, nine_month_reminder_one_day, \
                         sixteen_month_reminder_seven_days, sixteen_month_reminder_one_day, \
                         five_year_reminder_seven_days, five_year_reminder_one_day

FAKE_NOW = datetime(2017, 7, 17, 0, 0)

def contact_object(date_of_birth, language="English"):
    child = 'Roland' if language == 'English' else u'\u0906\u0930\u0935'
    return Contact.objects.create(name=child,
                                  phone_number="1-111-1111",
                                  delay_in_days=0,
                                  language_preference=language,
                                  date_of_birth=date_string_to_date(date_of_birth),
                                  functional_date_of_birth=date_string_to_date(date_of_birth),
                                  method_of_sign_up="text")

def text_reminder_test_object(date_of_birth, language="English"):
    return TextReminder(contact_object(date_of_birth=date_of_birth, language=language))


class TextReminderTests(TestCase):
    @freeze_time(FAKE_NOW)
    def test_no_eligible_reminders(self):
        tr = text_reminder_test_object("14/7/2017") # 3 days ago (relative to FAKE_NOW)
        self.assertFalse(tr.should_remind_today())
        self.assertFalse(tr.correct_date_for_reminder(weeks=6, days=7))
        self.assertFalse(tr.correct_date_for_reminder(weeks=6, days=1))
        self.assertFalse(tr.correct_date_for_reminder(weeks=10, days=7))
        self.assertFalse(tr.correct_date_for_reminder(months=9, days=7))
        self.assertEqual(tr.get_reminder_msg(), None)


    @freeze_time(FAKE_NOW)
    def test_remind_at_six_weeks_seven_days_english(self):
        tr = text_reminder_test_object("29/5/2017") # 6 weeks, 7 days ago
        self.assertTrue(tr.correct_date_for_reminder(weeks=6, days=7))
        self.assertTrue(tr.should_remind_today())
        self.assertFalse(tr.correct_date_for_reminder(weeks=6, days=1))
        self.assertFalse(tr.correct_date_for_reminder(weeks=10, days=7))
        self.assertFalse(tr.correct_date_for_reminder(months=9, days=7))
        self.assertEqual(tr.get_reminder_msg(),
                         six_week_reminder_seven_days("English").format(name="Roland"))

    @freeze_time(FAKE_NOW)
    def test_remind_at_six_weeks_seven_days_hindi(self):
        tr = text_reminder_test_object("29/5/2017", language="Hindi")
        self.assertTrue(tr.correct_date_for_reminder(weeks=6, days=7))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         six_week_reminder_seven_days('Hindi').format(name=u'\u0906\u0930\u0935'))

    @freeze_time(FAKE_NOW)
    def test_remind_at_six_weeks_seven_days_gujarati(self):
        tr = text_reminder_test_object("29/5/2017", language="Gujarati")
        self.assertTrue(tr.correct_date_for_reminder(weeks=6, days=7))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         six_week_reminder_seven_days("Gujarati").format(name=u'\u0906\u0930\u0935'))


    @freeze_time(FAKE_NOW)
    def test_remind_at_six_weeks_one_day_english(self):
        tr = text_reminder_test_object("4/6/2017") # 6 weeks, 1 day ago
        self.assertTrue(tr.correct_date_for_reminder(weeks=6, days=1))
        self.assertTrue(tr.should_remind_today())
        self.assertFalse(tr.correct_date_for_reminder(weeks=6, days=7))
        self.assertFalse(tr.correct_date_for_reminder(weeks=10, days=7))
        self.assertFalse(tr.correct_date_for_reminder(months=9, days=7))
        self.assertEqual(tr.get_reminder_msg(),
                         six_week_reminder_one_day("English").format(name="Roland"))

    @freeze_time(FAKE_NOW)
    def test_remind_at_six_weeks_one_day_hindi(self):
        tr = text_reminder_test_object("4/6/2017", language="Hindi")
        self.assertTrue(tr.correct_date_for_reminder(weeks=6, days=1))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         six_week_reminder_one_day("Hindi").format(name=u'\u0906\u0930\u0935'))

    @freeze_time(FAKE_NOW)
    def test_remind_at_six_weeks_one_day_gujarati(self):
        tr = text_reminder_test_object("4/6/2017", language="Gujarati")
        self.assertTrue(tr.correct_date_for_reminder(weeks=6, days=1))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         six_week_reminder_one_day("Gujarati").format(name=u'\u0906\u0930\u0935'))


    @freeze_time(FAKE_NOW)
    def test_remind_at_ten_weeks_seven_days_english(self):
        tr = text_reminder_test_object("1/5/2017") # 10 weeks, 7 days ago
        self.assertTrue(tr.correct_date_for_reminder(weeks=10, days=7))
        self.assertTrue(tr.should_remind_today())
        self.assertFalse(tr.correct_date_for_reminder(weeks=10, days=1))
        self.assertFalse(tr.correct_date_for_reminder(weeks=6, days=7))
        self.assertFalse(tr.correct_date_for_reminder(months=9, days=7))
        self.assertEqual(tr.get_reminder_msg(),
                         ten_week_reminder_seven_days("English").format(name="Roland"))

    @freeze_time(FAKE_NOW)
    def test_remind_at_ten_weeks_seven_days_hindi(self):
        tr = text_reminder_test_object("1/5/2017", language="Hindi")
        self.assertTrue(tr.correct_date_for_reminder(weeks=10, days=7))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         ten_week_reminder_seven_days("Hindi").format(name=u'\u0906\u0930\u0935'))

    @freeze_time(FAKE_NOW)
    def test_remind_at_ten_weeks_seven_days_gujarati(self):
        tr = text_reminder_test_object("1/5/2017", language="Gujarati")
        self.assertTrue(tr.correct_date_for_reminder(weeks=10, days=7))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         ten_week_reminder_seven_days("Gujarati").format(name=u'\u0906\u0930\u0935'))


    @freeze_time(FAKE_NOW)
    def test_remind_at_ten_weeks_one_day_english(self):
        tr = text_reminder_test_object("7/5/2017") # 10 weeks, 1 day ago
        self.assertTrue(tr.correct_date_for_reminder(weeks=10, days=1))
        self.assertTrue(tr.should_remind_today())
        self.assertFalse(tr.correct_date_for_reminder(weeks=10, days=7))
        self.assertFalse(tr.correct_date_for_reminder(weeks=6, days=7))
        self.assertFalse(tr.correct_date_for_reminder(months=9, days=7))
        self.assertEqual(tr.get_reminder_msg(),
                         ten_week_reminder_one_day("English").format(name="Roland"))

    @freeze_time(FAKE_NOW)
    def test_remind_at_ten_weeks_one_day_hindi(self):
        tr = text_reminder_test_object("7/5/2017", language="Hindi")
        self.assertTrue(tr.correct_date_for_reminder(weeks=10, days=1))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         ten_week_reminder_one_day("Hindi").format(name=u'\u0906\u0930\u0935'))

    @freeze_time(FAKE_NOW)
    def test_remind_at_ten_weeks_one_day_gujarati(self):
        tr = text_reminder_test_object("7/5/2017", language="Gujarati")
        self.assertTrue(tr.correct_date_for_reminder(weeks=10, days=1))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         ten_week_reminder_one_day("Gujarati").format(name=u'\u0906\u0930\u0935'))


    @freeze_time(FAKE_NOW)
    def test_remind_at_fourteen_weeks_seven_days_english(self):
        tr = text_reminder_test_object("3/4/2017") # 14 weeks, 7 days ago
        self.assertTrue(tr.correct_date_for_reminder(weeks=14, days=7))
        self.assertTrue(tr.should_remind_today())
        self.assertFalse(tr.correct_date_for_reminder(weeks=10, days=1))
        self.assertFalse(tr.correct_date_for_reminder(weeks=6, days=7))
        self.assertFalse(tr.correct_date_for_reminder(months=9, days=7))
        self.assertEqual(tr.get_reminder_msg(),
                         fourteen_week_reminder_seven_days("English").format(name="Roland"))

    @freeze_time(FAKE_NOW)
    def test_remind_at_fourteen_weeks_seven_days_hindi(self):
        tr = text_reminder_test_object("3/4/2017", language="Hindi")
        self.assertTrue(tr.correct_date_for_reminder(weeks=14, days=7))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         fourteen_week_reminder_seven_days("Hindi").format(name=u'\u0906\u0930\u0935'))

    @freeze_time(FAKE_NOW)
    def test_remind_at_fourteen_weeks_seven_days_gujarati(self):
        tr = text_reminder_test_object("3/4/2017", language="Gujarati")
        self.assertTrue(tr.correct_date_for_reminder(weeks=14, days=7))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         fourteen_week_reminder_seven_days("Gujarati").format(name=u'\u0906\u0930\u0935'))


    @freeze_time(FAKE_NOW)
    def test_remind_at_fourteen_weeks_one_day_english(self):
        tr = text_reminder_test_object("9/4/2017") # 14 weeks, 1 day ago
        self.assertTrue(tr.correct_date_for_reminder(weeks=14, days=1))
        self.assertTrue(tr.should_remind_today())
        self.assertFalse(tr.correct_date_for_reminder(weeks=10, days=7))
        self.assertFalse(tr.correct_date_for_reminder(weeks=6, days=7))
        self.assertFalse(tr.correct_date_for_reminder(months=9, days=7))
        self.assertEqual(tr.get_reminder_msg(),
                         fourteen_week_reminder_one_day("English").format(name="Roland"))

    @freeze_time(FAKE_NOW)
    def test_remind_at_fourteen_weeks_one_day_hindi(self):
        tr = text_reminder_test_object("9/4/2017", language="Hindi")
        self.assertTrue(tr.correct_date_for_reminder(weeks=14, days=1))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         fourteen_week_reminder_one_day("Hindi").format(name=u'\u0906\u0930\u0935'))

    @freeze_time(FAKE_NOW)
    def test_remind_at_fourteen_weeks_one_day_gujarati(self):
        tr = text_reminder_test_object("9/4/2017", language="Gujarati")
        self.assertTrue(tr.correct_date_for_reminder(weeks=14, days=1))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         fourteen_week_reminder_one_day("Gujarati").format(name=u'\u0906\u0930\u0935'))


    @freeze_time(FAKE_NOW)
    def test_remind_at_nine_months_seven_days_english(self):
        tr = text_reminder_test_object("10/10/2016") # 9 months, 7 days ago
        self.assertTrue(tr.correct_date_for_reminder(months=9, days=7))
        self.assertTrue(tr.should_remind_today())
        self.assertFalse(tr.correct_date_for_reminder(weeks=10, days=1))
        self.assertFalse(tr.correct_date_for_reminder(weeks=6, days=7))
        self.assertFalse(tr.correct_date_for_reminder(weeks=14, days=7))
        self.assertEqual(tr.get_reminder_msg(),
                         nine_month_reminder_seven_days("English").format(name="Roland"))

    @freeze_time(FAKE_NOW)
    def test_remind_at_nine_months_seven_days_hindi(self):
        tr = text_reminder_test_object("10/10/2016", language="Hindi")
        self.assertTrue(tr.correct_date_for_reminder(months=9, days=7))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         nine_month_reminder_seven_days("Hindi").format(name=u'\u0906\u0930\u0935'))

    @freeze_time(FAKE_NOW)
    def test_remind_at_nine_months_seven_days_gujarati(self):
        tr = text_reminder_test_object("10/10/2016", language="Gujarati")
        self.assertTrue(tr.correct_date_for_reminder(months=9, days=7))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         nine_month_reminder_seven_days("Gujarati").format(name=u'\u0906\u0930\u0935'))


    @freeze_time(FAKE_NOW)
    def test_remind_at_nine_months_one_day_english(self):
        tr = text_reminder_test_object("16/10/2016") # 9 months, 1 day ago
        self.assertTrue(tr.correct_date_for_reminder(months=9, days=1))
        self.assertTrue(tr.should_remind_today())
        self.assertFalse(tr.correct_date_for_reminder(weeks=10, days=1))
        self.assertFalse(tr.correct_date_for_reminder(weeks=6, days=1))
        self.assertFalse(tr.correct_date_for_reminder(months=9, days=7))
        self.assertEqual(tr.get_reminder_msg(),
                         nine_month_reminder_one_day("English").format(name="Roland"))

    @freeze_time(FAKE_NOW)
    def test_remind_at_nine_months_one_day_hindi(self):
        tr = text_reminder_test_object("16/10/2016", language="Hindi")
        self.assertTrue(tr.correct_date_for_reminder(months=9, days=1))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         nine_month_reminder_one_day("Hindi").format(name=u'\u0906\u0930\u0935'))

    @freeze_time(FAKE_NOW)
    def test_remind_at_nine_months_one_day_gujarati(self):
        tr = text_reminder_test_object("16/10/2016", language="Gujarati")
        self.assertTrue(tr.correct_date_for_reminder(months=9, days=1))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         nine_month_reminder_one_day("Gujarati").format(name=u'\u0906\u0930\u0935'))


    @freeze_time(FAKE_NOW)
    def test_remind_at_sixteen_months_seven_days_english(self):
        tr = text_reminder_test_object("10/3/2016") # 16 months, 7 days ago
        self.assertTrue(tr.correct_date_for_reminder(months=16, days=7))
        self.assertTrue(tr.should_remind_today())
        self.assertFalse(tr.correct_date_for_reminder(weeks=10, days=1))
        self.assertFalse(tr.correct_date_for_reminder(weeks=6, days=7))
        self.assertFalse(tr.correct_date_for_reminder(months=16, days=1))
        self.assertEqual(tr.get_reminder_msg(),
                         sixteen_month_reminder_seven_days("English").format(name="Roland"))

    @freeze_time(FAKE_NOW)
    def test_remind_at_sixteen_months_seven_days_hindi(self):
        tr = text_reminder_test_object("10/3/2016", language="Hindi")
        self.assertTrue(tr.correct_date_for_reminder(months=16, days=7))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         sixteen_month_reminder_seven_days("Hindi").format(name=u'\u0906\u0930\u0935'))

    @freeze_time(FAKE_NOW)
    def test_remind_at_sixteen_months_seven_days_gujarati(self):
        tr = text_reminder_test_object("10/3/2016", language="Gujarati")
        self.assertTrue(tr.correct_date_for_reminder(months=16, days=7))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         sixteen_month_reminder_seven_days("Gujarati").format(name=u'\u0906\u0930\u0935'))


    @freeze_time(FAKE_NOW)
    def test_remind_at_sixteen_months_one_day_english(self):
        tr = text_reminder_test_object("16/3/2016") # 16 months, 1 day ago
        self.assertTrue(tr.correct_date_for_reminder(months=16, days=1))
        self.assertTrue(tr.should_remind_today())
        self.assertFalse(tr.correct_date_for_reminder(weeks=10, days=7))
        self.assertFalse(tr.correct_date_for_reminder(weeks=6, days=7))
        self.assertFalse(tr.correct_date_for_reminder(months=16, days=7))
        self.assertEqual(tr.get_reminder_msg(),
                         sixteen_month_reminder_one_day("English").format(name="Roland"))

    @freeze_time(FAKE_NOW)
    def test_remind_at_sixteen_months_one_day_hindi(self):
        tr = text_reminder_test_object("16/3/2016", language="Hindi")
        self.assertTrue(tr.correct_date_for_reminder(months=16, days=1))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         sixteen_month_reminder_one_day("Hindi").format(name=u'\u0906\u0930\u0935'))

    @freeze_time(FAKE_NOW)
    def test_remind_at_sixteen_months_one_day_gujarati(self):
        tr = text_reminder_test_object("16/3/2016", language="Gujarati")
        self.assertTrue(tr.correct_date_for_reminder(months=16, days=1))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         sixteen_month_reminder_one_day("Gujarati").format(name=u'\u0906\u0930\u0935'))


    @freeze_time(FAKE_NOW)
    def test_remind_at_five_years_seven_days_english(self):
        tr = text_reminder_test_object("10/7/2012") # 5 years, 7 days ago
        self.assertTrue(tr.correct_date_for_reminder(years=5, days=7))
        self.assertTrue(tr.should_remind_today())
        self.assertFalse(tr.correct_date_for_reminder(weeks=10, days=1))
        self.assertFalse(tr.correct_date_for_reminder(weeks=6, days=7))
        self.assertFalse(tr.correct_date_for_reminder(years=5, days=1))
        self.assertEqual(tr.get_reminder_msg(),
                         five_year_reminder_seven_days("English").format(name="Roland"))

    @freeze_time(FAKE_NOW)
    def test_remind_at_five_years_seven_days_hindi(self):
        tr = text_reminder_test_object("10/7/2012", language="Hindi")
        self.assertTrue(tr.correct_date_for_reminder(years=5, days=7))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         five_year_reminder_seven_days("Hindi").format(name=u'\u0906\u0930\u0935'))

    @freeze_time(FAKE_NOW)
    def test_remind_at_five_years_seven_days_gujarati(self):
        tr = text_reminder_test_object("10/7/2012", language="Gujarati")
        self.assertTrue(tr.correct_date_for_reminder(years=5, days=7))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         five_year_reminder_seven_days("Gujarati").format(name=u'\u0906\u0930\u0935'))


    @freeze_time(FAKE_NOW)
    def test_remind_at_five_years_one_day_english(self):
        tr = text_reminder_test_object("16/7/2012") # 5 years, 1 day ago
        self.assertTrue(tr.correct_date_for_reminder(years=5, days=1))
        self.assertTrue(tr.should_remind_today())
        self.assertFalse(tr.correct_date_for_reminder(weeks=10, days=7))
        self.assertFalse(tr.correct_date_for_reminder(weeks=6, days=7))
        self.assertFalse(tr.correct_date_for_reminder(years=5, days=7))
        self.assertEqual(tr.get_reminder_msg(),
                         five_year_reminder_one_day("English").format(name="Roland"))

    @freeze_time(FAKE_NOW)
    def test_remind_at_five_years_one_day_hindi(self):
        tr = text_reminder_test_object("16/7/2012", language="Hindi")
        self.assertTrue(tr.correct_date_for_reminder(years=5, days=1))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         five_year_reminder_one_day("Hindi").format(name=u'\u0906\u0930\u0935'))

    @freeze_time(FAKE_NOW)
    def test_remind_at_five_years_one_day_gujarati(self):
        tr = text_reminder_test_object("16/7/2012", language="Gujarati")
        self.assertTrue(tr.correct_date_for_reminder(years=5, days=1))
        self.assertTrue(tr.should_remind_today())
        self.assertEqual(tr.get_reminder_msg(),
                         five_year_reminder_one_day("Gujarati").format(name=u'\u0906\u0930\u0935'))


    @freeze_time(FAKE_NOW)
    @patch("modules.text_reminder.send_text")
    def test_send_text_when_eligible(self, mocked_send_text):
        tr = text_reminder_test_object("29/5/2017") # 6 weeks, 7 days ago
        self.assertTrue(tr.should_remind_today())
        tr.remind()
        mocked_send_text.assert_called_once_with(message=tr.get_reminder_msg(),
                                                 phone_number="1-111-1111")

    @freeze_time(FAKE_NOW)
    @patch("modules.text_reminder.send_text")
    def test_do_not_send_text_when_not_eligible(self, mocked_send_text):
        tr = text_reminder_test_object("10/7/2017") # 7 days ago
        self.assertFalse(tr.should_remind_today())
        tr.remind()
        self.assertFalse(mocked_send_text.called)

    @freeze_time(FAKE_NOW)
    @patch("modules.text_reminder.send_text")
    @patch("modules.text_processor.send_text")
    def test_remind_when_good_dont_remind_when_cancelled(self, r_mocked_send_text, t_mocked_send_text):
        tr = text_reminder_test_object("29/5/2017") # 6 weeks, 7 days ago
        self.assertTrue(tr.should_remind_today())
        tp = TextProcessor(phone_number=tr.phone_number)
        tp.process("STOP")
        self.assertFalse(tr.should_remind_today())
