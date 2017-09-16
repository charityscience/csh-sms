from datetime import datetime
from django.test import TestCase

from modules.utils import quote, phone_number_is_valid, remove_nondigit_characters, \
                                add_country_code_to_phone_number, prepare_phone_number
from modules.date_helper import date_string_to_date, date_is_valid, \
                                date_to_date_string
from six import u

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