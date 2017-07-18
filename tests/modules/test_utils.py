from django.test import TestCase

from modules.utils import quote, date_string_to_date, date_is_valid

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
        
    def test_reject_bogus_dates(self):
        self.assertFalse(date_is_valid("Bogus"))
        self.assertFalse(date_is_valid("00/00/00"))

    def test_reject_mm_dd_dates(self):
        self.assertFalse(date_is_valid("11-25-2015"))
    
    def test_reject_too_far_in_future(self):
        self.assertFalse(date_is_valid("25/11/2133"))
    
    def test_reject_too_far_in_past(self):
        self.assertFalse(date_is_valid("11/12/1991"))
