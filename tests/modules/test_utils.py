from datetime import datetime
from django.test import TestCase

from modules.utils import quote, remove_nondigit_characters
from modules.date_helper import date_string_to_date, date_is_valid, \
                                date_to_date_string

class QuoteTests(TestCase):
    def test_quote(self):
        self.assertEqual(quote("text"), "`text`")


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
        self.assertEqual("1000", remove_nondigit_characters("₹1000"))
        self.assertEqual("1000", remove_nondigit_characters("+_income1000 adfassfd!"))
        self.assertEqual("1000", remove_nondigit_characters("[1000]"))
        self.assertEqual("1000", remove_nondigit_characters("/1000] /-_-%&*()~?><;:'\"|\\@$#"))
        self.assertEqual("", remove_nondigit_characters(""))