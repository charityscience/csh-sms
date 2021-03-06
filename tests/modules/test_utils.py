from datetime import datetime
from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time
from mock import patch

from modules.utils import quote, phone_number_is_valid, remove_nondigit_characters, \
                                add_country_code_to_phone_number, prepare_phone_number, \
                                keywords_without_word, is_not_ascii
from modules.date_helper import date_string_to_date, date_is_valid, \
                                date_to_date_string, date_string_dmy_to_date, \
                                date_string_mdy_to_date, date_string_ymd_to_date, \
                                try_parsing_partner_date, try_parsing_gen_date, \
                                datetime_string_mdy_to_datetime, datetime_string_ymd_to_datetime
from modules.i18n import hindi_information, hindi_remind, hindi_born, \
                            subscribe_keywords, six_week_reminder_seven_days, \
                            six_week_reminder_one_day, ten_week_reminder_seven_days, \
                            ten_week_reminder_one_day, fourteen_week_reminder_seven_days, \
                            fourteen_week_reminder_one_day, nine_month_reminder_seven_days, \
                            nine_month_reminder_one_day, sixteen_month_reminder_seven_days, \
                            sixteen_month_reminder_one_day, five_year_reminder_seven_days, \
                            five_year_reminder_one_day, verify_pregnant_signup_birthdate, \
                            msg_subscribe, msg_unsubscribe, msg_already_sub, msg_failure, \
                            msg_failed_date
from six import u

FAKE_NOW = datetime(2017, 12, 1, 15, 10, 3)

class QuoteTests(TestCase):
    def test_quote(self):
        self.assertEqual(quote("text"), "`text`")

    def test_quote_with_a_float(self):
        self.assertEqual(quote(2.0), "`2.0`")


class DateIsValidTests(TestCase):
    def test_normal_date(self):
        self.assertTrue(date_is_valid("25/11/2015"))
        self.assertTrue(date_is_valid("11/12/2012"))
        self.assertTrue(date_is_valid("09/02/2001"))

    def test_short_year_date(self):
        self.assertTrue(date_is_valid("25/11/15"))
        self.assertTrue(date_is_valid("11/12/12"))
        self.assertTrue(date_is_valid("09/02/01"))

    def test_hypen_separated_date(self):
        self.assertTrue(date_is_valid("25-11-2015"))
        self.assertTrue(date_is_valid("11-12-2012"))
        self.assertTrue(date_is_valid("09-02-2001"))

    def test_one_digit_date(self):
        self.assertTrue(date_is_valid("05-05-2015"))
        self.assertTrue(date_is_valid("09-02-2001"))
        self.assertTrue(date_is_valid("05-5-2015"))
        self.assertTrue(date_is_valid("09-2-2001"))
        self.assertTrue(date_is_valid("5-05-2015"))
        self.assertTrue(date_is_valid("5-05-2015"))
        self.assertTrue(date_is_valid("9-2-2001"))
        self.assertTrue(date_is_valid("9-2-2001"))
        
    def test_leap_year_dates(self):
        self.assertTrue(date_is_valid("29/02/2012"))
        self.assertFalse(date_is_valid("29/02/2013"))
        self.assertTrue(date_is_valid("29/02/2016"))
        self.assertFalse(date_is_valid("29/02/2017"))

    def test_reject_bogus_dates(self):
        self.assertFalse(date_is_valid("Bogus"))
        self.assertFalse(date_is_valid("00/00/00"))
        self.assertFalse(date_is_valid("31/02/2015"))
        self.assertFalse(date_is_valid("43/11/2015"))

    def test_reject_mm_dd_dates(self):
        self.assertFalse(date_is_valid("11-25-2015"))
        self.assertFalse(date_is_valid("31/06/2017"))
        self.assertFalse(date_is_valid("29/02/2017"))
        self.assertFalse(date_is_valid("15/15/2015"))
    
    def test_reject_too_far_in_future(self):
        self.assertFalse(date_is_valid("25/11/2133"))
    
    def test_reject_too_far_in_past(self):
        self.assertFalse(date_is_valid("11/12/1991"))


class DateStringToDateTests(TestCase):
    def test_date_strings_get_converted_to_dates(self):
        self.assertEqual(date_string_to_date("25/11/2015"), datetime(2015, 11, 25, 0, 0).date())
        self.assertEqual(date_string_to_date("11/12/2012"), datetime(2012, 12, 11, 0, 0).date())
        self.assertEqual(date_string_to_date("9-2-01"), datetime(2001, 2, 9, 0, 0).date())

    def test_nonworking_dates_for_date_string_dmy_to_date(self):
        with self.assertRaises(ValueError):
            date_string_dmy_to_date("")
        with self.assertRaises(ValueError):
            date_string_dmy_to_date(" ")
        with self.assertRaises(ValueError):
            date_string_dmy_to_date("12")
        with self.assertRaises(ValueError):
            date_string_dmy_to_date("1212")
        with self.assertRaises(ValueError):
            date_string_dmy_to_date("12-12")
        with self.assertRaises(ValueError):
            date_string_dmy_to_date("12/12")
        with self.assertRaises(ValueError):
            date_string_dmy_to_date("40-15-2015")
        with self.assertRaises(ValueError):
            date_string_dmy_to_date("10-15-2015")
        with self.assertRaises(ValueError):
            date_string_dmy_to_date("30-15-2015")
        with self.assertRaises(ValueError):
            date_string_dmy_to_date("30/15/2015")
        with self.assertRaises(ValueError):
            date_string_dmy_to_date("2014-20-15")
        with self.assertRaises(ValueError):
            date_string_dmy_to_date("12-00-2015")
        with self.assertRaises(ValueError):
            date_string_dmy_to_date("0000-20-15")
        with self.assertRaises(ValueError):
            date_string_dmy_to_date("2014-35-00")
        with self.assertRaises(ValueError):
            date_string_dmy_to_date("2016-12-40")
        with self.assertRaises(ValueError):
            date_string_dmy_to_date("2017-02-02")
        with self.assertRaises(ValueError):
            date_string_dmy_to_date("2017-10-10")
        with self.assertRaises(ValueError):
            date_string_dmy_to_date("10-20-201")
        with self.assertRaises(ValueError):
            date_string_dmy_to_date("2017-02-29")
        with self.assertRaises(ValueError):
            date_string_dmy_to_date("30-15-2015")
        with self.assertRaises(ValueError):
            date_string_dmy_to_date("12-35-2015")
        with self.assertRaises(ValueError):
            date_string_dmy_to_date("0000-20-15")
        with self.assertRaises(ValueError):
            date_string_dmy_to_date("2014-20-15")
        with self.assertRaises(ValueError):
            date_string_dmy_to_date("29-02-2017")
        with self.assertRaises(ValueError):
            date_string_dmy_to_date("25-11-15")
        with self.assertRaises(ValueError):
            date_string_dmy_to_date("25/11/15")
        with self.assertRaises(ValueError):
            date_string_dmy_to_date("11-25-15")
        with self.assertRaises(ValueError):
            date_string_dmy_to_date("11/25/15")
        with self.assertRaises(ValueError):
            date_string_dmy_to_date("02-29-2017")
        with self.assertRaises(ValueError):
            date_string_dmy_to_date("29/05/2016/")

    def test_date_string_dmy_to_date(self):
        self.assertEqual(datetime(2015, 11, 25, 0, 0).date(), date_string_dmy_to_date("25-11-2015"))
        self.assertEqual(datetime(2015, 11, 25, 0, 0).date(), date_string_dmy_to_date("25/11/2015"))
        self.assertEqual(datetime(2015, 1, 11, 0, 0).date(), date_string_dmy_to_date("11-01-2015"))
        self.assertEqual(datetime(2015, 1, 11, 0, 0).date(), date_string_dmy_to_date("11/01/2015"))
        self.assertEqual(datetime(2015, 1, 1, 0, 0).date(), date_string_dmy_to_date("01-01-2015"))
        self.assertEqual(datetime(2016, 2, 29, 0, 0).date(), date_string_dmy_to_date("29-02-2016"))
        self.assertEqual(datetime(2017, 2, 28, 0, 0).date(), date_string_dmy_to_date("28-02-2017"))
        self.assertEqual(datetime(2020, 2, 28, 0, 0).date(), date_string_dmy_to_date("28-02-2020"))
        self.assertEqual(datetime(2009, 7, 10, 0, 0).date(), date_string_dmy_to_date("10-07-2009"))
        self.assertEqual(datetime(2009, 12, 12, 0, 0).date(), date_string_dmy_to_date("12-12-2009"))
        self.assertEqual(datetime(2009, 8, 12, 0, 0).date(), date_string_dmy_to_date("12-08-2009"))
        self.assertEqual(datetime(2014, 12, 8, 0, 0).date(), date_string_dmy_to_date("08-12-2014"))
        self.assertEqual(datetime(2014, 2, 8, 0, 0).date(), date_string_dmy_to_date("8-02-2014"))
        self.assertEqual(datetime(2014, 2, 8, 0, 0).date(), date_string_dmy_to_date("8/02/2014"))
        self.assertEqual(datetime(2014, 2, 8, 0, 0).date(), date_string_dmy_to_date("08-2-2014"))
        self.assertEqual(datetime(2014, 2, 8, 0, 0).date(), date_string_dmy_to_date("08/2/2014"))
        self.assertEqual(datetime(2014, 2, 8, 0, 0).date(), date_string_dmy_to_date("8-2-2014"))
        self.assertEqual(datetime(2014, 2, 8, 0, 0).date(), date_string_dmy_to_date("8/2/2014"))

    def test_nonworking_dates_for_date_string_mdy_to_date(self):
        with self.assertRaises(ValueError):
            date_string_mdy_to_date("")
        with self.assertRaises(ValueError):
            date_string_mdy_to_date(" ")
        with self.assertRaises(ValueError):
            date_string_mdy_to_date("12")
        with self.assertRaises(ValueError):
            date_string_mdy_to_date("1212")
        with self.assertRaises(ValueError):
            date_string_mdy_to_date("12-12")
        with self.assertRaises(ValueError):
            date_string_mdy_to_date("12/12")
        with self.assertRaises(ValueError):
            date_string_mdy_to_date("40-15-2015")
        with self.assertRaises(ValueError):
            date_string_mdy_to_date("30-15-2015")
        with self.assertRaises(ValueError):
            date_string_mdy_to_date("30/15/2015")
        with self.assertRaises(ValueError):
            date_string_mdy_to_date("2014-20-15")
        with self.assertRaises(ValueError):
            date_string_mdy_to_date("12-00-2015")
        with self.assertRaises(ValueError):
            date_string_mdy_to_date("0000-20-15")
        with self.assertRaises(ValueError):
            date_string_mdy_to_date("2014-35-00")
        with self.assertRaises(ValueError):
            date_string_mdy_to_date("2016-12-40")
        with self.assertRaises(ValueError):
            date_string_mdy_to_date("2017-02-02")
        with self.assertRaises(ValueError):
            date_string_mdy_to_date("2017-10-10")
        with self.assertRaises(ValueError):
            date_string_mdy_to_date("17-10-2016")
        with self.assertRaises(ValueError):
            date_string_mdy_to_date("17-05-2016")
        with self.assertRaises(ValueError):
            date_string_mdy_to_date("2017-02-29")
        with self.assertRaises(ValueError):
            date_string_mdy_to_date("12-35-2015")
        with self.assertRaises(ValueError):
            date_string_mdy_to_date("0000-20-15")
        with self.assertRaises(ValueError):
            date_string_mdy_to_date("29-02-2017")
        with self.assertRaises(ValueError):
            date_string_mdy_to_date("25-11-15")
        with self.assertRaises(ValueError):
            date_string_mdy_to_date("25/11/15")
        with self.assertRaises(ValueError):
            date_string_mdy_to_date("11-25-15")
        with self.assertRaises(ValueError):
            date_string_mdy_to_date("11/25/15")
        with self.assertRaises(ValueError):
            date_string_mdy_to_date("02-29-2017")
        with self.assertRaises(ValueError):
            date_string_mdy_to_date("02-05-2016-")
        with self.assertRaises(ValueError):
            date_string_mdy_to_date("05/29/2016/")

    def test_date_string_mdy_to_date(self):
        self.assertEqual(datetime(2015, 11, 25, 0, 0).date(), date_string_mdy_to_date("11-25-2015"))
        self.assertEqual(datetime(2015, 11, 25, 0, 0).date(), date_string_mdy_to_date("11/25/2015"))
        self.assertEqual(datetime(2015, 1, 11, 0, 0).date(), date_string_mdy_to_date("01-11-2015"))
        self.assertEqual(datetime(2015, 1, 11, 0, 0).date(), date_string_mdy_to_date("01/11/2015"))
        self.assertEqual(datetime(2015, 1, 1, 0, 0).date(), date_string_mdy_to_date("01-01-2015"))
        self.assertEqual(datetime(2016, 2, 29, 0, 0).date(), date_string_mdy_to_date("02-29-2016"))
        self.assertEqual(datetime(2017, 2, 28, 0, 0).date(), date_string_mdy_to_date("02-28-2017"))
        self.assertEqual(datetime(2020, 2, 28, 0, 0).date(), date_string_mdy_to_date("02-28-2020"))
        self.assertEqual(datetime(2009, 7, 10, 0, 0).date(), date_string_mdy_to_date("07-10-2009"))
        self.assertEqual(datetime(2009, 12, 12, 0, 0).date(), date_string_mdy_to_date("12-12-2009"))
        self.assertEqual(datetime(2009, 8, 12, 0, 0).date(), date_string_mdy_to_date("08-12-2009"))
        self.assertEqual(datetime(2014, 12, 8, 0, 0).date(), date_string_mdy_to_date("12-08-2014"))
        self.assertEqual(datetime(2014, 8, 2, 0, 0).date(), date_string_mdy_to_date("8-02-2014"))
        self.assertEqual(datetime(2014, 8, 2, 0, 0).date(), date_string_mdy_to_date("8/02/2014"))
        self.assertEqual(datetime(2014, 8, 2, 0, 0).date(), date_string_mdy_to_date("08-2-2014"))
        self.assertEqual(datetime(2014, 8, 2, 0, 0).date(), date_string_mdy_to_date("08/2/2014"))
        self.assertEqual(datetime(2014, 8, 2, 0, 0).date(), date_string_mdy_to_date("8-2-2014"))
        self.assertEqual(datetime(2014, 8, 2, 0, 0).date(), date_string_mdy_to_date("8/2/2014"))

    def test_nonworking_dates_for_date_string_ymd_to_date(self):
        with self.assertRaises(ValueError):
            date_string_ymd_to_date("")
        with self.assertRaises(ValueError):
            date_string_ymd_to_date(" ")
        with self.assertRaises(ValueError):
            date_string_ymd_to_date("12")
        with self.assertRaises(ValueError):
            date_string_ymd_to_date("1212")
        with self.assertRaises(ValueError):
            date_string_ymd_to_date("12-12")
        with self.assertRaises(ValueError):
            date_string_ymd_to_date("12/12")
        with self.assertRaises(ValueError):
            date_string_ymd_to_date("40-15-2015")
        with self.assertRaises(ValueError):
            date_string_ymd_to_date("30-15-2015")
        with self.assertRaises(ValueError):
            date_string_ymd_to_date("30/15/2015")
        with self.assertRaises(ValueError):
            date_string_ymd_to_date("2014-20-15")
        with self.assertRaises(ValueError):
            date_string_ymd_to_date("12-00-2015")
        with self.assertRaises(ValueError):
            date_string_ymd_to_date("0000-20-15")
        with self.assertRaises(ValueError):
            date_string_ymd_to_date("2014-35-00")
        with self.assertRaises(ValueError):
            date_string_ymd_to_date("2016-12-40")
        with self.assertRaises(ValueError):
            date_string_ymd_to_date("02-02-2017")
        with self.assertRaises(ValueError):
            date_string_ymd_to_date("10-10-2017")
        with self.assertRaises(ValueError):
            date_string_ymd_to_date("2017-02-29")
        with self.assertRaises(ValueError):
            date_string_ymd_to_date("12-35-2015")
        with self.assertRaises(ValueError):
            date_string_ymd_to_date("0000-20-15")
        with self.assertRaises(ValueError):
            date_string_ymd_to_date("29-02-2017")
        with self.assertRaises(ValueError):
            date_string_ymd_to_date("25-11-15")
        with self.assertRaises(ValueError):
            date_string_ymd_to_date("25/11/15")
        with self.assertRaises(ValueError):
            date_string_ymd_to_date("11-25-15")
        with self.assertRaises(ValueError):
            date_string_ymd_to_date("11/25/15")
        with self.assertRaises(ValueError):
            date_string_ymd_to_date("02-29-2017")
        with self.assertRaises(ValueError):
            date_string_ymd_to_date("2017-02-29")
        with self.assertRaises(ValueError):
            date_string_ymd_to_date("2016-05-29-")
        with self.assertRaises(ValueError):
            date_string_ymd_to_date("2016-05-29--")
        with self.assertRaises(ValueError):
            date_string_ymd_to_date("2016/05/29/")

    def test_date_string_ymd_to_date(self):
        self.assertEqual(datetime(2015, 11, 25, 0, 0).date(), date_string_ymd_to_date("2015-11-25"))
        self.assertEqual(datetime(2015, 11, 25, 0, 0).date(), date_string_ymd_to_date("2015/11/25"))
        self.assertEqual(datetime(2015, 1, 11, 0, 0).date(), date_string_ymd_to_date("2015-01-11"))
        self.assertEqual(datetime(2015, 1, 11, 0, 0).date(), date_string_ymd_to_date("2015/01/11"))
        self.assertEqual(datetime(2015, 1, 1, 0, 0).date(), date_string_ymd_to_date("2015-01-01"))
        self.assertEqual(datetime(2016, 2, 29, 0, 0).date(), date_string_ymd_to_date("2016-02-29"))
        self.assertEqual(datetime(2017, 2, 28, 0, 0).date(), date_string_ymd_to_date("2017-02-28"))
        self.assertEqual(datetime(2020, 2, 28, 0, 0).date(), date_string_ymd_to_date("2020-02-28"))
        self.assertEqual(datetime(2009, 7, 10, 0, 0).date(), date_string_ymd_to_date("2009-07-10"))
        self.assertEqual(datetime(2009, 12, 12, 0, 0).date(), date_string_ymd_to_date("2009-12-12"))
        self.assertEqual(datetime(2009, 8, 12, 0, 0).date(), date_string_ymd_to_date("2009-08-12"))
        self.assertEqual(datetime(2014, 12, 8, 0, 0).date(), date_string_ymd_to_date("2014-12-08"))
        self.assertEqual(datetime(2014, 8, 2, 0, 0).date(), date_string_ymd_to_date("2014-8-02"))
        self.assertEqual(datetime(2014, 8, 2, 0, 0).date(), date_string_ymd_to_date("2014/8/02"))
        self.assertEqual(datetime(2014, 8, 2, 0, 0).date(), date_string_ymd_to_date("2014-08-2"))
        self.assertEqual(datetime(2014, 8, 2, 0, 0).date(), date_string_ymd_to_date("2014/08/2"))
        self.assertEqual(datetime(2014, 8, 2, 0, 0).date(), date_string_ymd_to_date("2014-8-2"))
        self.assertEqual(datetime(2014, 8, 2, 0, 0).date(), date_string_ymd_to_date("2014/8/2"))


    def test_nonworking_dates_for_try_parsing_partner_date(self):
        with self.assertRaises(ValueError):
            try_parsing_partner_date("")
        with self.assertRaises(ValueError):
            try_parsing_partner_date(" ")
        with self.assertRaises(ValueError):
            try_parsing_partner_date("12")
        with self.assertRaises(ValueError):
            try_parsing_partner_date("1212")
        with self.assertRaises(ValueError):
            try_parsing_partner_date("12-12")
        with self.assertRaises(ValueError):
            try_parsing_partner_date("12/12")
        with self.assertRaises(ValueError):
            try_parsing_partner_date("40-15-2015")
        with self.assertRaises(ValueError):
            try_parsing_partner_date("10-15-2015")
        with self.assertRaises(ValueError):
            try_parsing_partner_date("30-15-2015")
        with self.assertRaises(ValueError):
            try_parsing_partner_date("30/15/2015")
        with self.assertRaises(ValueError):
            try_parsing_partner_date("2014-20-15")
        with self.assertRaises(ValueError):
            try_parsing_partner_date("12-00-2015")
        with self.assertRaises(ValueError):
            try_parsing_partner_date("0000-20-15")
        with self.assertRaises(ValueError):
            try_parsing_partner_date("2014-35-00")
        with self.assertRaises(ValueError):
            try_parsing_partner_date("2016-12-40")
        with self.assertRaises(ValueError):
            try_parsing_partner_date("2017-02-29")
        with self.assertRaises(ValueError):
            try_parsing_partner_date("30-15-2015")
        with self.assertRaises(ValueError):
            try_parsing_partner_date("12-35-2015")
        with self.assertRaises(ValueError):
            try_parsing_partner_date("0000-20-15")
        with self.assertRaises(ValueError):
            try_parsing_partner_date("2014-20-15")
        with self.assertRaises(ValueError):
            try_parsing_partner_date("29-02-2017")
        with self.assertRaises(ValueError):
            try_parsing_partner_date("25-11-15")
        with self.assertRaises(ValueError):
            try_parsing_partner_date("25/11/15")
        with self.assertRaises(ValueError):
            try_parsing_partner_date("11-25-15")
        with self.assertRaises(ValueError):
            try_parsing_partner_date("11/25/15")
        with self.assertRaises(ValueError):
            try_parsing_partner_date("02-29-2017")
        with self.assertRaises(ValueError):
            try_parsing_partner_date("29/05/2016/")
        with self.assertRaises(ValueError):
            try_parsing_partner_date("2016-05-29-")
        with self.assertRaises(ValueError):
            try_parsing_partner_date("2016-05-29--")
        with self.assertRaises(ValueError):
            try_parsing_partner_date("2016/05/29/")

    def test_try_parsing_partner_date(self):
        self.assertEqual(datetime(2015, 11, 25, 0, 0).date(), try_parsing_partner_date("25-11-2015"))
        self.assertEqual(datetime(2015, 11, 25, 0, 0).date(), try_parsing_partner_date("25/11/2015"))
        self.assertEqual(datetime(2015, 1, 11, 0, 0).date(), try_parsing_partner_date("11-01-2015"))
        self.assertEqual(datetime(2015, 1, 11, 0, 0).date(), try_parsing_partner_date("11/01/2015"))
        self.assertEqual(datetime(2015, 1, 1, 0, 0).date(), try_parsing_partner_date("01-01-2015"))
        self.assertEqual(datetime(2016, 2, 29, 0, 0).date(), try_parsing_partner_date("29-02-2016"))
        self.assertEqual(datetime(2017, 2, 28, 0, 0).date(), try_parsing_partner_date("28-02-2017"))
        self.assertEqual(datetime(2020, 2, 28, 0, 0).date(), try_parsing_partner_date("28-02-2020"))
        self.assertEqual(datetime(2009, 7, 10, 0, 0).date(), try_parsing_partner_date("10-07-2009"))
        self.assertEqual(datetime(2009, 12, 12, 0, 0).date(), try_parsing_partner_date("12-12-2009"))
        self.assertEqual(datetime(2009, 8, 12, 0, 0).date(), try_parsing_partner_date("12-08-2009"))
        self.assertEqual(datetime(2014, 12, 8, 0, 0).date(), try_parsing_partner_date("08-12-2014"))
        self.assertEqual(datetime(2015, 11, 25, 0, 0).date(), try_parsing_partner_date("2015-11-25"))
        self.assertEqual(datetime(2015, 11, 25, 0, 0).date(), try_parsing_partner_date("2015/11/25"))
        self.assertEqual(datetime(2015, 1, 11, 0, 0).date(), try_parsing_partner_date("2015-01-11"))
        self.assertEqual(datetime(2015, 1, 11, 0, 0).date(), try_parsing_partner_date("2015/01/11"))
        self.assertEqual(datetime(2015, 1, 1, 0, 0).date(), try_parsing_partner_date("2015-01-01"))
        self.assertEqual(datetime(2016, 2, 29, 0, 0).date(), try_parsing_partner_date("2016-02-29"))
        self.assertEqual(datetime(2017, 2, 28, 0, 0).date(), try_parsing_partner_date("2017-02-28"))
        self.assertEqual(datetime(2020, 2, 28, 0, 0).date(), try_parsing_partner_date("2020-02-28"))
        self.assertEqual(datetime(2009, 7, 10, 0, 0).date(), try_parsing_partner_date("2009-07-10"))
        self.assertEqual(datetime(2009, 12, 12, 0, 0).date(), try_parsing_partner_date("2009-12-12"))
        self.assertEqual(datetime(2009, 8, 12, 0, 0).date(), try_parsing_partner_date("2009-08-12"))
        self.assertEqual(datetime(2014, 12, 8, 0, 0).date(), try_parsing_partner_date("2014-12-08"))
        self.assertEqual(datetime(2014, 8, 2, 0, 0).date(), try_parsing_partner_date("2014-8-02"))
        self.assertEqual(datetime(2014, 8, 2, 0, 0).date(), try_parsing_partner_date("2014/8/02"))
        self.assertEqual(datetime(2014, 8, 2, 0, 0).date(), try_parsing_partner_date("2014-08-2"))
        self.assertEqual(datetime(2014, 8, 2, 0, 0).date(), try_parsing_partner_date("2014/08/2"))
        self.assertEqual(datetime(2014, 8, 2, 0, 0).date(), try_parsing_partner_date("2014-8-2"))
        self.assertEqual(datetime(2014, 8, 2, 0, 0).date(), try_parsing_partner_date("2014/8/2"))
        self.assertEqual(datetime(2014, 2, 8, 0, 0).date(), try_parsing_partner_date("8-02-2014"))
        self.assertEqual(datetime(2014, 2, 8, 0, 0).date(), try_parsing_partner_date("8/02/2014"))
        self.assertEqual(datetime(2014, 2, 8, 0, 0).date(), try_parsing_partner_date("08-2-2014"))
        self.assertEqual(datetime(2014, 2, 8, 0, 0).date(), try_parsing_partner_date("08/2/2014"))
        self.assertEqual(datetime(2014, 2, 8, 0, 0).date(), try_parsing_partner_date("8-2-2014"))
        self.assertEqual(datetime(2014, 2, 8, 0, 0).date(), try_parsing_partner_date("8/2/2014"))
    
    def test_nonworking_dates_for_try_parsing_gen_date(self):
        with self.assertRaises(ValueError):
            try_parsing_gen_date("")
        with self.assertRaises(ValueError):
            try_parsing_gen_date(" ")
        with self.assertRaises(ValueError):
            try_parsing_gen_date("12")
        with self.assertRaises(ValueError):
            try_parsing_gen_date("1212")
        with self.assertRaises(ValueError):
            try_parsing_gen_date("12-12")
        with self.assertRaises(ValueError):
            try_parsing_gen_date("12/12")
        with self.assertRaises(ValueError):
            try_parsing_gen_date("40-15-2015")
        with self.assertRaises(ValueError):
            try_parsing_gen_date("30-15-2015")
        with self.assertRaises(ValueError):
            try_parsing_gen_date("30/15/2015")
        with self.assertRaises(ValueError):
            try_parsing_gen_date("2014-20-15")
        with self.assertRaises(ValueError):
            try_parsing_gen_date("12-00-2015")
        with self.assertRaises(ValueError):
            try_parsing_gen_date("0000-20-15")
        with self.assertRaises(ValueError):
            try_parsing_gen_date("2014-35-00")
        with self.assertRaises(ValueError):
            try_parsing_gen_date("2016-12-40")
        with self.assertRaises(ValueError):
            try_parsing_gen_date("17-10-2016")
        with self.assertRaises(ValueError):
            try_parsing_gen_date("17-05-2016")
        with self.assertRaises(ValueError):
            try_parsing_gen_date("2017-02-29")
        with self.assertRaises(ValueError):
            try_parsing_gen_date("12-35-2015")
        with self.assertRaises(ValueError):
            try_parsing_gen_date("0000-20-15")
        with self.assertRaises(ValueError):
            try_parsing_gen_date("29-02-2017")
        with self.assertRaises(ValueError):
            try_parsing_gen_date("25-11-15")
        with self.assertRaises(ValueError):
            try_parsing_gen_date("25/11/15")
        with self.assertRaises(ValueError):
            try_parsing_gen_date("11-25-15")
        with self.assertRaises(ValueError):
            try_parsing_gen_date("11/25/15")
        with self.assertRaises(ValueError):
            try_parsing_gen_date("02-29-2017")
        with self.assertRaises(ValueError):
            try_parsing_gen_date("02-05-2016-")
        with self.assertRaises(ValueError):
            try_parsing_gen_date("05/29/2016/")
        with self.assertRaises(ValueError):
            try_parsing_gen_date("2016-05-29-")
        with self.assertRaises(ValueError):
            try_parsing_gen_date("2016-05-29--")
        with self.assertRaises(ValueError):
            try_parsing_gen_date("2016/05/29/")

    def test_try_parsing_gen_date(self):
        self.assertEqual(datetime(2015, 11, 25, 0, 0).date(), try_parsing_gen_date("11-25-2015"))
        self.assertEqual(datetime(2015, 11, 25, 0, 0).date(), try_parsing_gen_date("11/25/2015"))
        self.assertEqual(datetime(2015, 1, 11, 0, 0).date(), try_parsing_gen_date("01-11-2015"))
        self.assertEqual(datetime(2015, 1, 11, 0, 0).date(), try_parsing_gen_date("01/11/2015"))
        self.assertEqual(datetime(2015, 1, 1, 0, 0).date(), try_parsing_gen_date("01-01-2015"))
        self.assertEqual(datetime(2016, 2, 29, 0, 0).date(), try_parsing_gen_date("02-29-2016"))
        self.assertEqual(datetime(2017, 2, 28, 0, 0).date(), try_parsing_gen_date("02-28-2017"))
        self.assertEqual(datetime(2020, 2, 28, 0, 0).date(), try_parsing_gen_date("02-28-2020"))
        self.assertEqual(datetime(2009, 7, 10, 0, 0).date(), try_parsing_gen_date("07-10-2009"))
        self.assertEqual(datetime(2009, 12, 12, 0, 0).date(), try_parsing_gen_date("12-12-2009"))
        self.assertEqual(datetime(2009, 8, 12, 0, 0).date(), try_parsing_gen_date("08-12-2009"))
        self.assertEqual(datetime(2014, 12, 8, 0, 0).date(), try_parsing_gen_date("12-08-2014"))
        self.assertEqual(datetime(2015, 11, 25, 0, 0).date(), try_parsing_gen_date("2015-11-25"))
        self.assertEqual(datetime(2015, 11, 25, 0, 0).date(), try_parsing_gen_date("2015/11/25"))
        self.assertEqual(datetime(2015, 1, 11, 0, 0).date(), try_parsing_gen_date("2015-01-11"))
        self.assertEqual(datetime(2015, 1, 11, 0, 0).date(), try_parsing_gen_date("2015/01/11"))
        self.assertEqual(datetime(2015, 1, 1, 0, 0).date(), try_parsing_gen_date("2015-01-01"))
        self.assertEqual(datetime(2016, 2, 29, 0, 0).date(), try_parsing_gen_date("2016-02-29"))
        self.assertEqual(datetime(2017, 2, 28, 0, 0).date(), try_parsing_gen_date("2017-02-28"))
        self.assertEqual(datetime(2020, 2, 28, 0, 0).date(), try_parsing_gen_date("2020-02-28"))
        self.assertEqual(datetime(2009, 7, 10, 0, 0).date(), try_parsing_gen_date("2009-07-10"))
        self.assertEqual(datetime(2009, 12, 12, 0, 0).date(), try_parsing_gen_date("2009-12-12"))
        self.assertEqual(datetime(2009, 8, 12, 0, 0).date(), try_parsing_gen_date("2009-08-12"))
        self.assertEqual(datetime(2014, 12, 8, 0, 0).date(), try_parsing_gen_date("2014-12-08"))
        self.assertEqual(datetime(2014, 8, 2, 0, 0).date(), try_parsing_gen_date("8-02-2014"))
        self.assertEqual(datetime(2014, 8, 2, 0, 0).date(), try_parsing_gen_date("8/02/2014"))
        self.assertEqual(datetime(2014, 8, 2, 0, 0).date(), try_parsing_gen_date("08-2-2014"))
        self.assertEqual(datetime(2014, 8, 2, 0, 0).date(), try_parsing_gen_date("08/2/2014"))
        self.assertEqual(datetime(2014, 8, 2, 0, 0).date(), try_parsing_gen_date("8-2-2014"))
        self.assertEqual(datetime(2014, 8, 2, 0, 0).date(), try_parsing_gen_date("8/2/2014"))
        self.assertEqual(datetime(2014, 8, 2, 0, 0).date(), try_parsing_gen_date("2014-8-02"))
        self.assertEqual(datetime(2014, 8, 2, 0, 0).date(), try_parsing_gen_date("2014/8/02"))
        self.assertEqual(datetime(2014, 8, 2, 0, 0).date(), try_parsing_gen_date("2014-08-2"))
        self.assertEqual(datetime(2014, 8, 2, 0, 0).date(), try_parsing_gen_date("2014/08/2"))
        self.assertEqual(datetime(2014, 8, 2, 0, 0).date(), try_parsing_gen_date("2014-8-2"))
        self.assertEqual(datetime(2014, 8, 2, 0, 0).date(), try_parsing_gen_date("2014/8/2"))

class DatetimeStringToDatetimeTests(TestCase):
    def test_datetime_string_mdy_to_datetime(self):
        self.assertEqual(datetime(2017, 6, 20, 18, 50, 20).replace(tzinfo=timezone.get_default_timezone()), datetime_string_mdy_to_datetime("6/20/2017 6:50:20 PM"))
        self.assertEqual(datetime(2017, 6, 20, 6, 50, 20).replace(tzinfo=timezone.get_default_timezone()), datetime_string_mdy_to_datetime("6/20/2017 6:50:20 AM"))
        self.assertEqual(datetime(2015, 12, 19, 0, 10, 20).replace(tzinfo=timezone.get_default_timezone()), datetime_string_mdy_to_datetime("12/19/2015 12:10:20 AM"))
        self.assertEqual(datetime(2015, 12, 19, 12, 10, 20).replace(tzinfo=timezone.get_default_timezone()), datetime_string_mdy_to_datetime("12/19/2015 12:10:20 PM"))
        self.assertEqual(datetime(2015, 12, 19, 11, 10, 20).replace(tzinfo=timezone.get_default_timezone()), datetime_string_mdy_to_datetime("12/19/2015 11:10:20 AM"))
        self.assertEqual(datetime(2015, 12, 19, 23, 10, 20).replace(tzinfo=timezone.get_default_timezone()), datetime_string_mdy_to_datetime("12/19/2015 11:10:20 PM"))
        self.assertEqual(datetime(2020, 12, 19, 23, 10, 20).replace(tzinfo=timezone.get_default_timezone()), datetime_string_mdy_to_datetime("12/19/2020 11:10:20 PM"))
        self.assertEqual(datetime(2016, 1, 10, 16, 5, 7).replace(tzinfo=timezone.get_default_timezone()), datetime_string_mdy_to_datetime("01/10/2016 4:05:07 PM"))
        self.assertEqual(datetime(2016, 1, 10, 16, 5, 7).replace(tzinfo=timezone.get_default_timezone()), datetime_string_mdy_to_datetime("01/10/2016 4:05:07 PM"))
        self.assertEqual(datetime(2016, 2, 29, 16, 5, 7).replace(tzinfo=timezone.get_default_timezone()), datetime_string_mdy_to_datetime("02/29/2016 4:05:07 PM"))
        self.assertEqual(datetime(2020, 2, 29, 16, 5, 7).replace(tzinfo=timezone.get_default_timezone()), datetime_string_mdy_to_datetime("02/29/2020 4:05:07 PM"))
    
    def test_fake_datetimes_for_datetime_string_mdy_to_datetime(self):
        with self.assertRaises(ValueError):
            self.assertEqual(datetime_string_mdy_to_datetime("16/20/2017 6:50:20 AM"))
        with self.assertRaises(ValueError):
            self.assertEqual(datetime_string_mdy_to_datetime("6/35/2017 6:50:20 AM"))
        with self.assertRaises(ValueError):
            self.assertEqual(datetime_string_mdy_to_datetime("16/20/20217 6:50:20 AM"))
        with self.assertRaises(ValueError):
            self.assertEqual(datetime_string_mdy_to_datetime("12/20/2017 16:50:20 AM"))
        with self.assertRaises(ValueError):
            self.assertEqual(datetime_string_mdy_to_datetime("6/20/2017 6:70:20 AM"))
        with self.assertRaises(ValueError):
            self.assertEqual(datetime_string_mdy_to_datetime("6/20/2017 6:50:80 AM"))
        with self.assertRaises(ValueError):
            self.assertEqual(datetime_string_mdy_to_datetime("6/20/2017 6:50:510 AM"))
        with self.assertRaises(ValueError):
            self.assertEqual(datetime_string_mdy_to_datetime("6/20/2017 6:150:10 AM"))
        with self.assertRaises(ValueError):
            self.assertEqual(datetime_string_mdy_to_datetime("6/20/2017 6:50:10 A"))
        with self.assertRaises(ValueError):
            self.assertEqual(datetime_string_mdy_to_datetime("6/20/2017 6:50:10"))
        with self.assertRaises(ValueError):
            self.assertEqual(datetime_string_mdy_to_datetime("6/20/2017 6:50:10 PMt"))
        with self.assertRaises(ValueError):
            self.assertEqual(datetime_string_mdy_to_datetime("2/29/2017 6:50:10 PM"))

    def test_datetime_string_ymd_to_datetime(self):
        self.assertEqual(datetime(2017, 11, 30, 23, 45, 45).replace(tzinfo=timezone.get_default_timezone()),
                            datetime_string_ymd_to_datetime("2017-11-30 23:45:45"))
        self.assertEqual(datetime(2016, 11, 30, 23, 45, 45).replace(tzinfo=timezone.get_default_timezone()),
                            datetime_string_ymd_to_datetime("2016-11-30 23:45:45"))
        self.assertEqual(datetime(2018, 11, 30, 23, 45, 45).replace(tzinfo=timezone.get_default_timezone()),
                            datetime_string_ymd_to_datetime("2018-11-30 23:45:45"))
        self.assertEqual(datetime(2017, 9, 30, 23, 45, 45).replace(tzinfo=timezone.get_default_timezone()),
                            datetime_string_ymd_to_datetime("2017-09-30 23:45:45"))
        self.assertEqual(datetime(2017, 11, 8, 23, 45, 45).replace(tzinfo=timezone.get_default_timezone()),
                            datetime_string_ymd_to_datetime("2017-11-08 23:45:45"))
        self.assertEqual(datetime(2017, 10, 10, 23, 45, 45).replace(tzinfo=timezone.get_default_timezone()),
                            datetime_string_ymd_to_datetime("2017-10-10 23:45:45"))
        self.assertEqual(datetime(2017, 9, 9, 23, 45, 45).replace(tzinfo=timezone.get_default_timezone()),
                            datetime_string_ymd_to_datetime("2017-09-09 23:45:45"))
        self.assertEqual(datetime(2017, 11, 30, 11, 45, 45).replace(tzinfo=timezone.get_default_timezone()),
                            datetime_string_ymd_to_datetime("2017-11-30 11:45:45"))
        self.assertEqual(datetime(2017, 11, 30, 23, 4, 45).replace(tzinfo=timezone.get_default_timezone()),
                            datetime_string_ymd_to_datetime("2017-11-30 23:04:45"))
        self.assertEqual(datetime(2017, 11, 30, 23, 45, 4).replace(tzinfo=timezone.get_default_timezone()),
                            datetime_string_ymd_to_datetime("2017-11-30 23:45:04"))
        self.assertEqual(datetime(2017, 11, 30, 23, 5, 4).replace(tzinfo=timezone.get_default_timezone()),
                            datetime_string_ymd_to_datetime("2017-11-30 23:05:04"))
        self.assertEqual(datetime(2017, 11, 30, 5, 5, 4).replace(tzinfo=timezone.get_default_timezone()),
                            datetime_string_ymd_to_datetime("2017-11-30 05:05:04"))
        self.assertEqual(datetime(2017, 11, 30, 5, 5, 4).replace(tzinfo=timezone.get_default_timezone()),
                            datetime_string_ymd_to_datetime("2017-11-30 05:05:04 "))
        self.assertEqual(datetime(2017, 11, 30, 5, 5, 4).replace(tzinfo=timezone.get_default_timezone()),
                            datetime_string_ymd_to_datetime("  2017-11-30 05:05:04  "))
        self.assertEqual(datetime(2025, 11, 30, 23, 5, 4).replace(tzinfo=timezone.get_default_timezone()),
                            datetime_string_ymd_to_datetime("2025-11-30 23:05:04"))
        self.assertEqual(datetime(2016, 2, 29, 12, 5, 4).replace(tzinfo=timezone.get_default_timezone()),
                            datetime_string_ymd_to_datetime("2016-02-29 12:05:04"))

    @freeze_time(FAKE_NOW)
    @patch("logging.error")
    def test_invalid_datetimes_for_datetime_string_ymd_to_datetime(self, logging_error_mock):
        self.assertEqual(FAKE_NOW.replace(tzinfo=timezone.get_default_timezone()),
                        datetime_string_ymd_to_datetime("2017/11-30 23:45:45"))
        logging_error_mock.assert_called_with("Invalid datetime entry for message: " + quote("2017/11-30 23:45:45"))
        self.assertEqual(FAKE_NOW.replace(tzinfo=timezone.get_default_timezone()),
                        datetime_string_ymd_to_datetime("2016-11/30 23:45:45"))
        self.assertEqual(FAKE_NOW.replace(tzinfo=timezone.get_default_timezone()), 
                        datetime_string_ymd_to_datetime("2018-11-3023:45:45"))
        self.assertEqual(FAKE_NOW.replace(tzinfo=timezone.get_default_timezone()),
                        datetime_string_ymd_to_datetime("2017-09-30 23-45:45"))
        self.assertEqual(FAKE_NOW.replace(tzinfo=timezone.get_default_timezone()),
                        datetime_string_ymd_to_datetime("2017-11-08 23:45-45"))
        self.assertEqual(FAKE_NOW.replace(tzinfo=timezone.get_default_timezone()),
                        datetime_string_ymd_to_datetime("2017-10-10 23/45:45"))
        self.assertEqual(FAKE_NOW.replace(tzinfo=timezone.get_default_timezone()),
                        datetime_string_ymd_to_datetime("2017-09-09 23:45:45pm"))
        self.assertEqual(FAKE_NOW.replace(tzinfo=timezone.get_default_timezone()),
                        datetime_string_ymd_to_datetime("2017-11-30 11:45:45 pm"))
        self.assertEqual(FAKE_NOW.replace(tzinfo=timezone.get_default_timezone()),
                        datetime_string_ymd_to_datetime("2017-41-30 23:04:45"))
        self.assertEqual(FAKE_NOW.replace(tzinfo=timezone.get_default_timezone()),
                        datetime_string_ymd_to_datetime("2017-11-36 23:45:04"))
        self.assertEqual(FAKE_NOW.replace(tzinfo=timezone.get_default_timezone()),
                        datetime_string_ymd_to_datetime("2017-11-30 25:05:04"))
        self.assertEqual(FAKE_NOW.replace(tzinfo=timezone.get_default_timezone()),
                        datetime_string_ymd_to_datetime("2017-11-30 05:95:04"))
        self.assertEqual(FAKE_NOW.replace(tzinfo=timezone.get_default_timezone()),
                        datetime_string_ymd_to_datetime("2025-11-30 23:05:94"))
        self.assertEqual(FAKE_NOW.replace(tzinfo=timezone.get_default_timezone()),
                        datetime_string_ymd_to_datetime("20E5-11-30 23:05:94"))
        self.assertEqual(FAKE_NOW.replace(tzinfo=timezone.get_default_timezone()),
                        datetime_string_ymd_to_datetime(""))
        self.assertEqual(FAKE_NOW.replace(tzinfo=timezone.get_default_timezone()),
                        datetime_string_ymd_to_datetime("   "))
        self.assertEqual(FAKE_NOW.replace(tzinfo=timezone.get_default_timezone()),
                        datetime_string_ymd_to_datetime("2017-02-29 12:05:04"))
        self.assertEqual(17, logging_error_mock.call_count)

class DateToDateStringTests(TestCase):
    def test_dates_get_converted_to_date_strings(self):
        self.assertEqual(date_to_date_string(datetime(2015, 11, 25, 0, 0).date()), "25/11/2015")
        self.assertEqual(date_to_date_string(datetime(2012, 12, 11, 0, 0).date()), "11/12/2012")

class NumberHandlingTests(TestCase):
    def test_remove_nondigit_characters(self):
        self.assertEqual("910123456789", remove_nondigit_characters("+910123456789"))
        self.assertEqual("910123456789", remove_nondigit_characters("^910123456789"))
        self.assertEqual("910123456789", remove_nondigit_characters("^+910123456789"))
        self.assertEqual("910123456789", remove_nondigit_characters("+^910123456789"))
        self.assertEqual("910123456789", remove_nondigit_characters(" 910123456789"))
        self.assertEqual("910123456789", remove_nondigit_characters("_910123456789"))
        self.assertEqual("910123456789", remove_nondigit_characters(" 910123456789"))
        self.assertEqual("910123456789", remove_nondigit_characters("910123456789 "))
        self.assertEqual("910123456789", remove_nondigit_characters("910123456789 +"))
        self.assertEqual("1000", remove_nondigit_characters("1000 adfassfd!"))
        self.assertEqual("1000", remove_nondigit_characters("$1000"))
        self.assertEqual("1000", remove_nondigit_characters(u"\u20B91000")) #Rupee symbol is u20B9
        self.assertEqual("1000", remove_nondigit_characters("+_income1000 adfassfd!"))
        self.assertEqual("1000", remove_nondigit_characters("[1000]"))
        self.assertEqual("1000", remove_nondigit_characters("/1000] /-_-%&*()~?><;:'\"|\\@$#"))
        self.assertEqual("", remove_nondigit_characters(""))

    def test_valid_phone_numbers(self):
        self.assertTrue(phone_number_is_valid("91123456s7890"))
        self.assertTrue(phone_number_is_valid("91123456 7890"))
        self.assertTrue(phone_number_is_valid(" 911234567890"))
        self.assertTrue(phone_number_is_valid("91 12345 67890"))
        self.assertTrue(phone_number_is_valid("123456789012"))
        self.assertTrue(phone_number_is_valid("1234567890"))
        self.assertTrue(phone_number_is_valid("0123456789"))
        self.assertTrue(phone_number_is_valid("123-456-8901"))
        self.assertTrue(phone_number_is_valid("123 456 8901"))
        self.assertTrue(phone_number_is_valid("+911234567890"))
        self.assertTrue(phone_number_is_valid("+91123456789012345"))
        self.assertTrue(phone_number_is_valid("91123456789012345"))
        self.assertTrue(phone_number_is_valid("123456789012345"))
        self.assertTrue(phone_number_is_valid("911234567890"))
        self.assertTrue(phone_number_is_valid("910987654321"))
        self.assertTrue(phone_number_is_valid("9109876543210"))

    def test_invalid_phone_numbers(self):
        self.assertFalse(phone_number_is_valid("9112345678901234567890"))
        self.assertFalse(phone_number_is_valid("911234567890123456"))
        self.assertFalse(phone_number_is_valid("911234567890 1234567890"))
        self.assertFalse(phone_number_is_valid("123456"))
        self.assertFalse(phone_number_is_valid("9123456"))
        self.assertFalse(phone_number_is_valid("912345679"))
        self.assertFalse(phone_number_is_valid("12345678"))
        self.assertFalse(phone_number_is_valid("123456789"))
        self.assertFalse(phone_number_is_valid("1234567890123456"))
        self.assertFalse(phone_number_is_valid(""))
        self.assertFalse(phone_number_is_valid(" "))
        self.assertFalse(phone_number_is_valid("         "))

    def test_add_country_code_to_phone_number(self):
        self.assertEqual("9109876543210", add_country_code_to_phone_number("9109876543210"))
        self.assertEqual("9109876543210", add_country_code_to_phone_number("09876543210"))
        self.assertEqual("911234567890", add_country_code_to_phone_number("1234567890"))
        self.assertEqual("912345678", add_country_code_to_phone_number("912345678"))
        self.assertEqual("910000000000", add_country_code_to_phone_number("910000000000"))
        self.assertEqual("9100000000", add_country_code_to_phone_number("9100000000"))
        self.assertEqual("919876543210", add_country_code_to_phone_number("9876543210"))
        self.assertEqual("910987654321", add_country_code_to_phone_number("0987654321"))
        self.assertEqual("", add_country_code_to_phone_number(""))

    def test_prepare_phone_number(self):
        self.assertEqual("9112345678901234567890", prepare_phone_number("9112345678901234567890"))
        self.assertEqual("911234567890123456", prepare_phone_number("911234567890123456"))
        self.assertEqual("9112345678901234567890", prepare_phone_number("911234567890 1234567890"))
        self.assertEqual("911234567890", prepare_phone_number("91123456s7890"))
        self.assertEqual("911234567890", prepare_phone_number("91123456 7890"))
        self.assertEqual("911234567890", prepare_phone_number(" 911234567890"))
        self.assertEqual("911234567890", prepare_phone_number("91 12345 67890"))
        self.assertEqual("91123456789012", prepare_phone_number("123456789012"))
        self.assertEqual("911234568901", prepare_phone_number("123-456-8901"))
        self.assertEqual("911234568901", prepare_phone_number("123 456 8901"))
        self.assertEqual("911234567890", prepare_phone_number("+911234567890"))
        self.assertEqual("91123456789012345", prepare_phone_number("+91123456789012345"))
        self.assertEqual("911234567890", prepare_phone_number("911234567890"))
        self.assertEqual("910987654321", prepare_phone_number("910987654321"))
        self.assertEqual("9109876543210", prepare_phone_number("9109876543210"))
        self.assertEqual("123456", prepare_phone_number("123456"))
        self.assertEqual("12345678", prepare_phone_number("12345678"))
        self.assertEqual("", prepare_phone_number(""))
        self.assertEqual("", prepare_phone_number("0"))
        self.assertEqual("", prepare_phone_number(" "))
        self.assertEqual("", prepare_phone_number("   "))
        self.assertEqual("", prepare_phone_number("  0 "))



class KeywordTests(TestCase):
    def test_removes_english_words(self):
        no_join_list = keywords_without_word(language="English", word="join")
        list_comp_minus_join = [key for key in subscribe_keywords("English") if key not in ["join"]]
        self.assertEqual(list_comp_minus_join, no_join_list)
        no_remind_list = keywords_without_word(language="English", word="remind")
        list_comp_minus_remind = [key for key in subscribe_keywords("English") if key not in ["remind"]]
        self.assertEqual(list_comp_minus_remind, no_remind_list)
        no_born_list = keywords_without_word(language="English", word="born")
        list_comp_minus_born = [key for key in subscribe_keywords("English") if key not in ["born"]]
        self.assertEqual(list_comp_minus_born, no_born_list)

    def test_removes_hindi_words(self):
        no_info_list = keywords_without_word(language="Hindi", word=hindi_information())
        list_comp_minus_info = [key for key in subscribe_keywords("Hindi") if key not in [hindi_information()]]
        self.assertEqual(list_comp_minus_info, no_info_list)
        no_remind_list = keywords_without_word(language="Hindi", word=hindi_remind())
        list_comp_minus_remind = [key for key in subscribe_keywords("Hindi") if key not in [hindi_remind()]]
        self.assertEqual(list_comp_minus_remind, no_remind_list)
        no_born_list = keywords_without_word(language="Hindi", word=hindi_born())
        list_comp_minus_born = [key for key in subscribe_keywords("Hindi") if key not in [hindi_born()]]
        self.assertEqual(list_comp_minus_born, no_born_list)

    def test_only_removes_words_in_set_english(self):
        no_laugh_list = keywords_without_word(language="English", word="hahahaha")
        self.assertEqual(subscribe_keywords("English"), no_laugh_list)
        no_capital_born_list = keywords_without_word(language="English", word="Born")
        self.assertEqual(subscribe_keywords("English"), no_capital_born_list)
        no_partial_born_list = keywords_without_word(language="English", word="bor")
        self.assertEqual(subscribe_keywords("English"), no_partial_born_list)
        no_hyphen_list = keywords_without_word(language="English", word="---")
        self.assertEqual(subscribe_keywords("English"), no_hyphen_list)
        no_speical_character_list = keywords_without_word(language="English", word="!*^%$")
        self.assertEqual(subscribe_keywords("English"), no_speical_character_list)
        no_empty_list = keywords_without_word(language="English", word="")
        self.assertEqual(subscribe_keywords("English"), no_empty_list)
        no_blank_list = keywords_without_word(language="English", word=" ")
        self.assertEqual(subscribe_keywords("English"), no_blank_list)
        no_triple_blank_list = keywords_without_word(language="English", word="   ")
        self.assertEqual(subscribe_keywords("English"), no_triple_blank_list)
        no_int_list = keywords_without_word(language="English", word=10)
        self.assertEqual(subscribe_keywords("English"), no_int_list)
        no_digit_list = keywords_without_word(language="English", word="100")
        self.assertEqual(subscribe_keywords("English"), no_digit_list)
        no_hindi_remind_list = keywords_without_word(language="English", word=hindi_remind())
        self.assertEqual(subscribe_keywords("English"), no_hindi_remind_list)
        no_hindi_information_list = keywords_without_word(language="English", word=hindi_information())
        self.assertEqual(subscribe_keywords("English"), no_hindi_information_list)
        no_hindi_born_list = keywords_without_word(language="English", word=hindi_born())
        self.assertEqual(subscribe_keywords("English"), no_hindi_born_list)

    def test_only_removes_words_in_set_hindi(self):
        no_random_char_list1 = keywords_without_word(language="Hindi", word=u"\u092e\u0947\u0902")
        self.assertEqual(subscribe_keywords("Hindi"), no_random_char_list1)
        no_random_char_list2 = keywords_without_word(language="Hindi", word=u"\u0917\u0932\u0947")
        self.assertEqual(subscribe_keywords("Hindi"), no_random_char_list2)
        no_partial_born_list = keywords_without_word(language="Hindi", word=u"\u091c\u0928\u094d")
        self.assertEqual(subscribe_keywords("Hindi"), no_partial_born_list)
        no_hyphen_list = keywords_without_word(language="Hindi", word="---")
        self.assertEqual(subscribe_keywords("Hindi"), no_hyphen_list)
        no_speical_character_list = keywords_without_word(language="Hindi", word="!*^%$")
        self.assertEqual(subscribe_keywords("Hindi"), no_speical_character_list)
        no_empty_list = keywords_without_word(language="Hindi", word="")
        self.assertEqual(subscribe_keywords("Hindi"), no_empty_list)
        no_blank_list = keywords_without_word(language="Hindi", word=" ")
        self.assertEqual(subscribe_keywords("Hindi"), no_blank_list)
        no_triple_blank_list = keywords_without_word(language="Hindi", word="   ")
        self.assertEqual(subscribe_keywords("Hindi"), no_triple_blank_list)
        no_int_list = keywords_without_word(language="Hindi", word=10)
        self.assertEqual(subscribe_keywords("Hindi"), no_int_list)
        no_digit_list = keywords_without_word(language="Hindi", word="100")
        self.assertEqual(subscribe_keywords("Hindi"), no_digit_list)
        no_english_remind_list = keywords_without_word(language="Hindi", word="remind")
        self.assertEqual(subscribe_keywords("Hindi"), no_english_remind_list)
        no_english_join_list = keywords_without_word(language="Hindi", word="join")
        self.assertEqual(subscribe_keywords("Hindi"), no_english_join_list)
        no_english_born_list = keywords_without_word(language="Hindi", word="born")
        self.assertEqual(subscribe_keywords("Hindi"), no_english_born_list)

class AsciiMessageTests(TestCase):
    def test_is_not_ascii_with_ascii_text(self):
        self.assertFalse(is_not_ascii(" "))
        self.assertFalse(is_not_ascii("   "))
        self.assertFalse(is_not_ascii(""))
        self.assertFalse(is_not_ascii("Ascii string here"))
        self.assertFalse(is_not_ascii("Ascii string here that is really long" * 5))
        self.assertFalse(is_not_ascii("12234567890"))
        self.assertFalse(is_not_ascii("~!@#$%^&*()_+=-`\\{}][\":;'?><,./'"))
        self.assertFalse(is_not_ascii(u'\u0000\u0001\u0002\u0003\u0004'))
        self.assertFalse(is_not_ascii(u'\u005B\u005C\u005D\u005E\u005F\u0060'))
        self.assertFalse(is_not_ascii(u'\u007A\u007B\u007C\u007D\u007E\u007F')) # last characters in ASCII set

    def test_is_not_ascii_with_nonascii_text(self):
        self.assertTrue(is_not_ascii(u'\u04FA'))
        self.assertTrue(is_not_ascii(u'\u0080')) # First character after ASCII set
        self.assertTrue(is_not_ascii(u'Ascii string start \u04FA'))
        self.assertTrue(is_not_ascii(u'\u04FA Ascii string end'))
        self.assertTrue(is_not_ascii(u'\u04FA Ascii string mid \u00BB'))
        self.assertTrue(is_not_ascii(u'\u04FA Ascii string mid one \u00BB Ascii string end'))
        self.assertTrue(is_not_ascii(u'\u04FA Ascii string mid one \u00BB Ascii string mid two \u00BC'))
        self.assertTrue(is_not_ascii(u'\u00BA\u00BB\u00BC\u00BD\u00BE\u00BF')) # First characters after ASCII set
        self.assertTrue(is_not_ascii(u'\u04FA\u04FB\u04FC\u04FD\u04FE\u04FF'))
        self.assertTrue(is_not_ascii(u'\u00BA\u00BB\u00BC\u00BD\u00BE\u00BF' * 5))

    def test_is_not_ascii_with_english_messages(self):
        self.assertFalse(is_not_ascii("join"))
        self.assertFalse(is_not_ascii("remind"))
        self.assertFalse(is_not_ascii("born"))
        self.assertFalse(is_not_ascii(msg_subscribe("English")))
        self.assertFalse(is_not_ascii(msg_unsubscribe("English")))
        self.assertFalse(is_not_ascii(msg_already_sub("English")))
        self.assertFalse(is_not_ascii(msg_failure("English")))
        self.assertFalse(is_not_ascii(msg_failed_date("English")))
        self.assertFalse(is_not_ascii(six_week_reminder_seven_days("English")))
        self.assertFalse(is_not_ascii(six_week_reminder_one_day("English")))
        self.assertFalse(is_not_ascii(ten_week_reminder_seven_days("English")))
        self.assertFalse(is_not_ascii(ten_week_reminder_one_day("English")))
        self.assertFalse(is_not_ascii(fourteen_week_reminder_seven_days("English")))
        self.assertFalse(is_not_ascii(fourteen_week_reminder_one_day("English")))
        self.assertFalse(is_not_ascii(nine_month_reminder_seven_days("English")))
        self.assertFalse(is_not_ascii(nine_month_reminder_one_day("English")))
        self.assertFalse(is_not_ascii(sixteen_month_reminder_seven_days("English")))
        self.assertFalse(is_not_ascii(sixteen_month_reminder_one_day("English")))
        self.assertFalse(is_not_ascii(five_year_reminder_seven_days("English")))
        self.assertFalse(is_not_ascii(five_year_reminder_one_day("English")))
        self.assertFalse(is_not_ascii(verify_pregnant_signup_birthdate("English")))
    
    def test_is_not_ascii_with_hindi_messages(self):
        self.assertTrue(is_not_ascii(hindi_information()))
        self.assertTrue(is_not_ascii(hindi_remind()))
        self.assertTrue(is_not_ascii(hindi_born()))
        self.assertTrue(is_not_ascii(msg_subscribe("Hindi")))
        self.assertTrue(is_not_ascii(msg_unsubscribe("Hindi")))
        self.assertTrue(is_not_ascii(msg_already_sub("Hindi")))
        self.assertTrue(is_not_ascii(msg_failure("Hindi")))
        self.assertTrue(is_not_ascii(msg_failed_date("Hindi")))
        self.assertTrue(is_not_ascii(six_week_reminder_seven_days("Hindi")))
        self.assertTrue(is_not_ascii(six_week_reminder_one_day("Hindi")))
        self.assertTrue(is_not_ascii(ten_week_reminder_seven_days("Hindi")))
        self.assertTrue(is_not_ascii(ten_week_reminder_one_day("Hindi")))
        self.assertTrue(is_not_ascii(fourteen_week_reminder_seven_days("Hindi")))
        self.assertTrue(is_not_ascii(fourteen_week_reminder_one_day("Hindi")))
        self.assertTrue(is_not_ascii(nine_month_reminder_seven_days("Hindi")))
        self.assertTrue(is_not_ascii(nine_month_reminder_one_day("Hindi")))
        self.assertTrue(is_not_ascii(sixteen_month_reminder_seven_days("Hindi")))
        self.assertTrue(is_not_ascii(sixteen_month_reminder_one_day("Hindi")))
        self.assertTrue(is_not_ascii(five_year_reminder_seven_days("Hindi")))
        self.assertTrue(is_not_ascii(five_year_reminder_one_day("Hindi")))
        self.assertTrue(is_not_ascii(verify_pregnant_signup_birthdate("Hindi")))

    def test_is_not_ascii_with_gujarati_messages(self):
        self.assertTrue(is_not_ascii(six_week_reminder_seven_days("Gujarati")))
        self.assertTrue(is_not_ascii(six_week_reminder_one_day("Gujarati")))
        self.assertTrue(is_not_ascii(ten_week_reminder_seven_days("Gujarati")))
        self.assertTrue(is_not_ascii(ten_week_reminder_one_day("Gujarati")))
        self.assertTrue(is_not_ascii(fourteen_week_reminder_seven_days("Gujarati")))
        self.assertTrue(is_not_ascii(fourteen_week_reminder_one_day("Gujarati")))
        self.assertTrue(is_not_ascii(nine_month_reminder_seven_days("Gujarati")))
        self.assertTrue(is_not_ascii(nine_month_reminder_one_day("Gujarati")))
        self.assertTrue(is_not_ascii(sixteen_month_reminder_seven_days("Gujarati")))
        self.assertTrue(is_not_ascii(sixteen_month_reminder_one_day("Gujarati")))
        self.assertTrue(is_not_ascii(five_year_reminder_seven_days("Gujarati")))
        self.assertTrue(is_not_ascii(five_year_reminder_one_day("Gujarati")))
