from __future__ import unicode_literals
import os
import csv
import tempfile
from django.test import TestCase

from mock import patch
from freezegun import freeze_time
from datetime import datetime
from django.utils import timezone
from management.models import Contact, Group
from modules.utils import phone_number_is_valid
from modules.upload_contacts_from_file import csv_upload, make_contact_dict, assign_groups_to_contact, \
                                              previous_vaccination, monthly_income, parse_or_create_delay_num, \
                                              entered_date_string_to_date, parse_or_create_functional_dob, \
                                              parse_contact_time_references, parse_preg_signup, assign_preg_signup, \
                                              estimate_date_of_birth, filter_pregnancy_month, determine_language, \
                                              determine_mother_tongue, language_selector, replace_blank_name, \
                                              determine_name, check_permutations
from modules.date_helper import add_or_subtract_days, add_or_subtract_months
from modules.i18n import hindi_placeholder_name, gujarati_placeholder_name
from dateutil.relativedelta import relativedelta
from six import u

def create_sample_contact(name="Aaarsh"):
    contact, created = Contact.objects.get_or_create(name=name, phone_number="911234567890",
        date_of_birth=datetime(2011, 5, 10, 0,0).date())
    return contact

def create_sample_group(name="TestMe"):
    group, created = Group.objects.get_or_create(name=name)
    return group


class UploadContactsFileTests(TestCase):
    def test_nonexistent_file_csv(self):
        with self.assertRaises(IOError):
            csv_upload(filepath="none.csv", source="TR")

    def test_non_csv_file(self):
        fake_txt_path = os.path.join(tempfile.gettempdir(), "fake.txt")
        with self.assertRaises(IOError):
            csv_upload(filepath=fake_txt_path, source="TR")

    @patch("logging.error")
    def test_processes_csv(self, logging_mock):
        csv_path = "tests/data/example.csv" 
        csv_upload(filepath=csv_path, source="TR")


class UploadContactsContactFieldsTests(TestCase):
    def upload_file(self):
        csv_path = "tests/data/example.csv" 
        csv_upload(filepath=csv_path, source="TR")        

    @patch("logging.error")
    def test_existing_contacts_are_updated(self, logging_mock):
        old_contact = create_sample_contact()

        self.upload_file()
        updated_contact = Contact.objects.get(name=old_contact.name, phone_number=old_contact.phone_number)
        self.assertNotEqual(old_contact.date_of_birth, updated_contact.date_of_birth)

    @patch("logging.error")
    def test_new_contacts_are_created(self, logging_mock):
        old_all_contacts = Contact.objects.all()
        old_contacts_count = Contact.objects.count()
        self.upload_file()
        new_all_contacts = Contact.objects.all()
        new_contacts_count = Contact.objects.count()
        self.assertNotEqual(old_all_contacts, new_all_contacts)
        self.assertNotEqual(old_contacts_count, new_contacts_count)

    @patch("logging.error")
    def test_only_contacts_with_valid_numbers_created(self, logging_mock):
    	"""tests/data/example.csv file being tested contains
    	   a contact with name: FakestNumber and phone number: 511234567890"""
    	self.upload_file()
    	self.assertFalse(Contact.objects.filter(name="FakestNumber").exists())
    	logging_mock.assert_called_with("Entry: FakestNumber - 2016-09-14 has invalid phone number: 123456")

    @patch("logging.error")
    def test_hindi_names_are_preserved(self, logging_mock):
        """tests/data/example.csv file being tested contains
           a contact with name: \u0906\u0930\u0935 and phone number: 912222277777"""
        hindi_name = u'\\u0906\\u0930\\u0935'
        self.upload_file()
        hin_contact = Contact.objects.get(phone_number="912222277777")
        self.assertNotEqual(hindi_name, hin_contact.name)
        self.assertTrue("\\" not in hin_contact.name)
        self.assertEqual(hindi_name.encode("utf-8").decode('unicode-escape'), hin_contact.name)

    @patch("logging.error")
    def test_gujarati_names_are_preserved(self, logging_mock):
        """tests/data/example.csv file being tested contains
           a contact with name: \u0A90\u0AC5\u0A94 and phone number: 915555511111"""
        guj_name = u'\\u0A90\\u0AC5\\u0A94'
        self.upload_file()
        guj_contact = Contact.objects.get(phone_number="915555511111")
        self.assertNotEqual(guj_name, guj_contact.name)
        self.assertTrue("\\" not in guj_contact.name)
        self.assertEqual(guj_name.encode("utf-8").decode('unicode-escape'), guj_contact.name)

    @patch("logging.error")
    def test_unicode_literal_names_are_encoded(self, logging_mock):
        self.upload_file()
        self.assertFalse(Contact.objects.filter(name__startswith="\\"))

class UploadContactsRelationshipTests(TestCase):
    def test_groups_are_assigned_to_contact(self):
        contact = create_sample_contact()
        group_string = "TestMe"
        multi_group_string = "TestMe, Again"
        group = create_sample_group(name=group_string)
        try:
            before_add = contact.group_set.get(id=group.id)
        except Group.DoesNotExist:
            before_add = None
        assign_groups_to_contact(contact, group_string)
        after_add = contact.group_set.get(id=group.id)
        assign_groups_to_contact(contact, multi_group_string)
        after_second_add = contact.group_set.get(name__exact="Again")

        self.assertNotEqual(before_add, after_add)
        self.assertTrue(after_add)
        self.assertEqual(after_add.name, group_string)
        self.assertEqual(after_second_add.name, "Again")

    def test_existing_groups_are_updated_with_new_contacts(self):
        group_string = "TestMe"
        group = create_sample_group(name=group_string)
        contact = create_sample_contact()

        with self.assertRaises(Contact.DoesNotExist):
            group.contacts.get(id=contact.id)

        assign_groups_to_contact(contact, group_string)
        self.assertTrue(group.contacts.get(id=contact.id))

    def test_empty_group_strings(self):
        group_string = ""
        contact = create_sample_contact()
        assign_groups_to_contact(contact, group_string)

        with self.assertRaises(Group.DoesNotExist):
            contact.group_set.get(name__exact=group_string)


class UploadContactsInputParserTests(TestCase):
    def test_nondigits_in_income(self):
        self.assertEqual(monthly_income("1892ff8"), 999999)
        self.assertEqual(monthly_income("ghg18928"), 999999)
        self.assertEqual(monthly_income("18928ff"), 999999)
        self.assertEqual(monthly_income("18928-"), 999999)
        self.assertEqual(monthly_income("-18928"), 999999)
        self.assertEqual(monthly_income("+18928"), 999999)
        self.assertEqual(monthly_income("18+928"), 999999)
        self.assertEqual(monthly_income("18 928"), 999999)
        self.assertEqual(monthly_income("18,928"), 999999)

    def test_empty_income(self):
        self.assertEqual(monthly_income(''), 999999)
        self.assertEqual(monthly_income(None), 999999)

    def test_empty_delay(self):
        self.assertEqual(parse_or_create_delay_num(''), 0)
        self.assertEqual(parse_or_create_delay_num(None), 0)

    def test_nondigits_in_delay(self):
        self.assertEqual(parse_or_create_delay_num("1892ff8"), 0)
        self.assertEqual(parse_or_create_delay_num("ghg18928"), 0)
        self.assertEqual(parse_or_create_delay_num("18928ff"), 0)
        self.assertEqual(parse_or_create_delay_num("18928-"), 0)
        self.assertEqual(parse_or_create_delay_num("-18928"), 0)
        self.assertEqual(parse_or_create_delay_num("+18928"), 0)
        self.assertEqual(parse_or_create_delay_num("18+928"), 0)
        self.assertEqual(parse_or_create_delay_num("18 928"), 0)
        self.assertEqual(parse_or_create_delay_num("18,928"), 0)

    def test_empty_previous_vaccination(self):
        self.assertEqual(previous_vaccination(''), None)

    def test_previous_vaccination_positive(self):
        self.assertEqual(previous_vaccination("y"), True)
        self.assertEqual(previous_vaccination("yes"), True)
        self.assertEqual(previous_vaccination("yes  "), True)
        self.assertEqual(previous_vaccination("yes asdfasfasf "), True)

    def test_previous_vaccination_negative(self):
        self.assertEqual(previous_vaccination("n"), False)
        self.assertEqual(previous_vaccination("no"), False)
        self.assertEqual(previous_vaccination("no  "), False)
        self.assertEqual(previous_vaccination("no asdfasfasf "), False)


    def test_fake_dates_for_parse_or_create_functional_dob(self):
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob(row_entry="40-15-2015", source="TR", date_of_birth="40-15-2015", delay=0)
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob(row_entry="30-15-2015", source="TR", date_of_birth="30-15-2015", delay=0)
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob(row_entry="12-35-2015", source="TR", date_of_birth="12-35-2015", delay=0)
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob(row_entry="2014-20-15", source="TR", date_of_birth="2014-20-15", delay=0)
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob(row_entry="12-00-2015", source="TR", date_of_birth="12-00-2015", delay=0)
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob(row_entry="20000-20-15", source="TR", date_of_birth="0000-20-15", delay=0)
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob(row_entry="2014-35-00", source="TR", date_of_birth="2014-35-00", delay=0)
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob(row_entry="2016-12-40", source="TR", date_of_birth="2016-12-40", delay=0)
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob(row_entry="2017-02-40", source="TR", date_of_birth="2017-02-40", delay=0)
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob(row_entry="40-15-2015", source="MPS", date_of_birth="40-15-2015", delay=0)
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob(row_entry="30-15-2015", source="MPS", date_of_birth="30-15-2015", delay=0)
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob(row_entry="12-35-2015", source="MPS", date_of_birth="12-35-2015", delay=0)
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob(row_entry="2014-20-15", source="PRNT", date_of_birth="2014-20-15", delay=0)
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob(row_entry="12-00-2015", source="PRNT", date_of_birth="12-00-2015", delay=0)
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob(row_entry="20000-20-15", source="PRNT", date_of_birth="0000-20-15", delay=0)
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob(row_entry="2014-35-00", source="PRNT", date_of_birth="2014-35-00", delay=0)
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob(row_entry="2016-12-40", source="PRNT", date_of_birth="2016-12-40", delay=0)
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob(row_entry="2017-02-40", source="PRNT", date_of_birth="2017-02-40", delay=0)


    def test_nonexistent_dates_for_parse_or_create_functional_dob(self):
        with self.assertRaises(TypeError):
            parse_or_create_functional_dob(row_entry="", source="TR", date_of_birth="", delay=0)

        parsed_func_dob = parse_or_create_functional_dob(row_entry="", source="TR", date_of_birth=datetime(2015, 10, 15,0,0).date(), delay=0)
        parsed_func_dob = parse_or_create_functional_dob(row_entry="", source="PRNT", date_of_birth=datetime(2015, 10, 15,0,0).date(), delay=0)
        parsed_func_dob2 = parse_or_create_functional_dob(row_entry="", source="TR", date_of_birth=datetime(2015, 10, 15,0,0).date(), delay=5)
        parsed_func_dob2 = parse_or_create_functional_dob(row_entry="", source="PRNT", date_of_birth=datetime(2015, 10, 15,0,0).date(), delay=5)
        
        self.assertEqual(parsed_func_dob, datetime(2015, 10, 15).date())
        self.assertEqual(parsed_func_dob2, datetime(2015, 10, 20).date())

    def test_real_dates_for_parse_or_create_functional_dob(self):
        parsed_func_dob1 = parse_or_create_functional_dob(row_entry="10-15-2015", source="TR",
        	date_of_birth=datetime(2015, 10, 15,0,0).date(), delay=0)
        parsed_func_dob2 = parse_or_create_functional_dob(row_entry="10-18-2015", source="TR",
        	date_of_birth=datetime(2015, 10, 15,0,0).date(), delay=3)

        parsed_func_dob3 = parse_or_create_functional_dob(row_entry="15-10-2015", source="PRNT",
            date_of_birth=datetime(2015, 10, 15,0,0).date(), delay=0)
        parsed_func_dob4 = parse_or_create_functional_dob(row_entry="18-10-2015", source="PRNT",
            date_of_birth=datetime(2015, 10, 15,0,0).date(), delay=3)
        
        self.assertEqual(parsed_func_dob1, datetime(2015, 10, 15).date())
        self.assertEqual(parsed_func_dob2, datetime(2015, 10, 18).date())
        self.assertEqual(parsed_func_dob3, datetime(2015, 10, 15).date())
        self.assertEqual(parsed_func_dob4, datetime(2015, 10, 18).date())

    def test_nonexistent_dates_for_entered_date_string_to_date(self):
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row_entry="", source="TR")

    def test_fake_dates_for_entered_date_string_to_date(self):
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row_entry="40-15-2015", source="TR")
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row_entry="30-15-2015", source="TR")
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row_entry="12-35-2015", source="TR")
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row_entry="2014-20-15", source="TR")
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row_entry="12-00-2015", source="TR")
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row_entry="0000-20-15", source="TR")
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row_entry="2014-35-00", source="TR")
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row_entry="2016-12-40", source="TR")
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row_entry="2017-02-29", source="TR")
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row_entry="0000-20-15", source="MPS")
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row_entry="2014-35-00", source="MPS")
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row_entry="2016-12-40", source="PRNT")
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row_entry="2017-02-29", source="PRNT")
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row_entry="30-15-2015", source="PRNT")
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row_entry="12-35-2015", source="PRNT")
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row_entry="2014-20-15", source="PRNT")

    def test_real_dates_for_entered_date_that_should_fail(self):
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row_entry="28-03-2015", source="TR")
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row_entry="15-05-2015", source="TR")
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row_entry="03-28-2015", source="MPS")
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row_entry="05-15-2015", source="MPS")
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row_entry="03-28-2015", source="PRNT")
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row_entry="05-15-2015", source="PRNT")


    def test_real_dates_for_entered_date_string_to_date(self):
        self.assertEqual(entered_date_string_to_date(row_entry="2014-12-20", source="TR"), datetime(2014, 12, 20, 0,0 ).date())
        self.assertEqual(entered_date_string_to_date(row_entry="2017-01-20", source="TR"), datetime(2017, 1, 20, 0,0 ).date())
        self.assertEqual(entered_date_string_to_date(row_entry="2017-01-07", source="TR"), datetime(2017, 1, 7, 0,0 ).date())
        self.assertEqual(entered_date_string_to_date(row_entry="01-15-2017", source="TR"), datetime(2017, 1, 15, 0,0 ).date())
        self.assertEqual(entered_date_string_to_date(row_entry="02-28-2017", source="TR"), datetime(2017, 2, 28, 0,0 ).date())
        self.assertEqual(entered_date_string_to_date(row_entry="2014-12-20", source="MPS"), datetime(2014, 12, 20, 0,0 ).date())
        self.assertEqual(entered_date_string_to_date(row_entry="2017-01-20", source="MPS"), datetime(2017, 1, 20, 0,0 ).date())
        self.assertEqual(entered_date_string_to_date(row_entry="2017-01-07", source="MPS"), datetime(2017, 1, 7, 0,0 ).date())
        self.assertEqual(entered_date_string_to_date(row_entry="15-01-2017", source="MPS"), datetime(2017, 1, 15, 0,0 ).date())
        self.assertEqual(entered_date_string_to_date(row_entry="28-02-2017", source="MPS"), datetime(2017, 2, 28, 0,0 ).date())
        self.assertEqual(entered_date_string_to_date(row_entry="2017-01-07", source="PRNT"), datetime(2017, 1, 7, 0,0 ).date())
        self.assertEqual(entered_date_string_to_date(row_entry="28-02-2017", source="PRNT"), datetime(2017, 2, 28, 0,0 ).date())
        self.assertEqual(entered_date_string_to_date(row_entry="15-01-2017", source="PRNT"), datetime(2017, 1, 15, 0,0 ).date())
    
    def test_parse_contact_time_references_real_datetimes(self):
        self.assertEqual(datetime(2017, 6, 12, 16, 0, 3, tzinfo=timezone.get_default_timezone()),
            parse_contact_time_references("6/12/2017 4:00:03 PM"))
        self.assertEqual(datetime(2017, 6, 16, 18, 51, 28, tzinfo=timezone.get_default_timezone()),
            parse_contact_time_references("6/16/2017 6:51:28 PM"))

    def test_parse_contact_time_references_fake_datetimes(self):
        with self.assertRaises(ValueError):
            parse_contact_time_references("6/12/2017 25:00:03 PM")
        with self.assertRaises(ValueError):
            parse_contact_time_references("6/30/2017 16:51:28 PM")

    @freeze_time(datetime(2017, 7, 21, 0, 0).replace(tzinfo=timezone.get_default_timezone()))
    def test_parse_contact_time_references_empty_times(self):
        self.assertEqual(datetime.now().replace(tzinfo=timezone.get_default_timezone()),
            parse_contact_time_references(""))

    def test_parse_preg_signup(self):
        self.assertTrue(parse_preg_signup("True"))
        self.assertTrue(parse_preg_signup("TRUE"))
        self.assertTrue(parse_preg_signup("T"))
        self.assertTrue(parse_preg_signup("t"))
        self.assertTrue(parse_preg_signup("to"))
        self.assertFalse(parse_preg_signup("False"))
        self.assertFalse(parse_preg_signup("FALSE"))
        self.assertFalse(parse_preg_signup("false"))
        self.assertFalse(parse_preg_signup("F"))
        self.assertFalse(parse_preg_signup("f"))
        self.assertFalse(parse_preg_signup("fo"))
        self.assertFalse(parse_preg_signup("0"))
        self.assertTrue(parse_preg_signup("1"))
        self.assertFalse(parse_preg_signup(0))
        self.assertTrue(parse_preg_signup(1))
        self.assertFalse(parse_preg_signup(""))

    @freeze_time(datetime(2017, 7, 21, 0, 0).replace(tzinfo=timezone.get_default_timezone()))
    def test_assign_preg_signup(self):
        true_contact = create_sample_contact()
        true_contact.preg_signup = True
        self.assertEqual(assign_preg_signup(true_contact), True)
        false_contact = create_sample_contact()
        false_contact.preg_signup = False
        self.assertEqual(assign_preg_signup(false_contact), False)
        none_contact = create_sample_contact()
        none_contact.preg_signup = None
        self.assertEqual(assign_preg_signup(none_contact), False)
        
        # Contact with birthdate in the future relative to frozen time, but preg_signup assigned by csv as False
        future_contact = create_sample_contact()
        future_contact.date_of_birth = datetime(2017, 7, 28, 0, 0).date()
        future_contact.preg_signup = False
        self.assertEqual(assign_preg_signup(future_contact), True)

    @freeze_time(datetime(2017, 7, 21, 0, 0))
    def test_estimate_date_of_birth(self):
        freeze_time_date = datetime.now().date()
        five_months_ago = add_or_subtract_months(date=freeze_time_date, num_of_months=-5)
        five_months_plus_preg_time = add_or_subtract_days(date=five_months_ago, num_of_days=280)
        one_month = freeze_time_date + relativedelta(months=-1) + relativedelta(days=280)
        two_months = freeze_time_date + relativedelta(months=-2) + relativedelta(days=280)
        three_months = freeze_time_date + relativedelta(months=-3) + relativedelta(days=280)
        four_months = freeze_time_date + relativedelta(months=-4) + relativedelta(days=280)
        five_months = freeze_time_date + relativedelta(months=-5) + relativedelta(days=280)
        six_months = freeze_time_date + relativedelta(months=-6) + relativedelta(days=280)
        seven_months = freeze_time_date + relativedelta(months=-7) + relativedelta(days=280)
        eight_months = freeze_time_date + relativedelta(months=-8) + relativedelta(days=280)
        nine_months = freeze_time_date + relativedelta(months=-9) + relativedelta(days=280)
        self.assertEqual(one_month, estimate_date_of_birth(month_of_pregnancy="1", date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(two_months, estimate_date_of_birth(month_of_pregnancy="2", date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(three_months, estimate_date_of_birth(month_of_pregnancy="3", date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(four_months, estimate_date_of_birth(month_of_pregnancy="4", date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(five_months, estimate_date_of_birth(month_of_pregnancy="5", date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(six_months, estimate_date_of_birth(month_of_pregnancy="6", date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(seven_months, estimate_date_of_birth(month_of_pregnancy="7", date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(eight_months, estimate_date_of_birth(month_of_pregnancy="8", date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(eight_months, estimate_date_of_birth(month_of_pregnancy="8m", date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(eight_months, estimate_date_of_birth(month_of_pregnancy="8_", date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(nine_months, estimate_date_of_birth(month_of_pregnancy="9", date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(nine_months, estimate_date_of_birth(month_of_pregnancy="9 ", date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(nine_months, estimate_date_of_birth(month_of_pregnancy=" 9", date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(nine_months, estimate_date_of_birth(month_of_pregnancy=" 9 ", date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(five_months_plus_preg_time, estimate_date_of_birth(month_of_pregnancy="5", date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(five_months_plus_preg_time, estimate_date_of_birth(month_of_pregnancy=5, date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(None, estimate_date_of_birth(month_of_pregnancy="0", date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(None, estimate_date_of_birth(month_of_pregnancy="00", date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))

    @freeze_time(datetime(2017, 7, 21, 0, 0))
    def test_estimate_date_of_birth_handles_month_typos(self):
        freeze_time_date = datetime.now().date()
        one_month = freeze_time_date + relativedelta(months=-1) + relativedelta(days=280)
        two_months = freeze_time_date + relativedelta(months=-2) + relativedelta(days=280)
        nine_months = freeze_time_date + relativedelta(months=-9) + relativedelta(days=280)
        self.assertEqual(one_month, estimate_date_of_birth(month_of_pregnancy="10", date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(one_month, estimate_date_of_birth(month_of_pregnancy="11", date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(two_months, estimate_date_of_birth(month_of_pregnancy="22", date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(nine_months, estimate_date_of_birth(month_of_pregnancy="99", date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(two_months, estimate_date_of_birth(month_of_pregnancy="-2", date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(two_months, estimate_date_of_birth(month_of_pregnancy="-22", date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(two_months, estimate_date_of_birth(month_of_pregnancy="0020", date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(two_months, estimate_date_of_birth(month_of_pregnancy="200", date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(two_months, estimate_date_of_birth(month_of_pregnancy="002", date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(two_months, estimate_date_of_birth(month_of_pregnancy="2adgasdfasdf", date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))

    def test_estimate_date_of_birth_rejects_nonnumbers(self):
        self.assertEqual(None, estimate_date_of_birth(month_of_pregnancy="Five", date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(None, estimate_date_of_birth(month_of_pregnancy="Ten", date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(None, estimate_date_of_birth(month_of_pregnancy="", date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(None, estimate_date_of_birth(month_of_pregnancy=" ", date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(None, estimate_date_of_birth(month_of_pregnancy="_!", date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))

    def test_filter_pregnancy_month(self):
        self.assertEqual(None, filter_pregnancy_month(month_of_pregnancy="Five"))
        self.assertEqual(None, filter_pregnancy_month(month_of_pregnancy="Ten"))
        self.assertEqual(None, filter_pregnancy_month(month_of_pregnancy=" "))
        self.assertEqual(None, filter_pregnancy_month(month_of_pregnancy=""))
        self.assertEqual(None, filter_pregnancy_month(month_of_pregnancy="_ *"))
        self.assertEqual(None, filter_pregnancy_month(month_of_pregnancy="Let'em see"))
        self.assertEqual(1, filter_pregnancy_month(month_of_pregnancy="1"))
        self.assertEqual(1, filter_pregnancy_month(month_of_pregnancy="11"))
        self.assertEqual(2, filter_pregnancy_month(month_of_pregnancy="22"))
        self.assertEqual(2, filter_pregnancy_month(month_of_pregnancy="2 "))
        self.assertEqual(2, filter_pregnancy_month(month_of_pregnancy="2s"))
        self.assertEqual(3, filter_pregnancy_month(month_of_pregnancy="300"))
        self.assertEqual(4, filter_pregnancy_month(month_of_pregnancy="004"))
        self.assertEqual(4, filter_pregnancy_month(month_of_pregnancy="0040"))

    def test_determine_language(self):
        self.assertEqual("English", determine_language("English"))
        self.assertEqual("English", determine_language("English--"))
        self.assertEqual("Hindi", determine_language("Hindi"))
        self.assertEqual("Hindi", determine_language(" Hindi"))
        self.assertEqual("Gujarati", determine_language("Gujarati"))
        self.assertEqual("Gujarati", determine_language("Gujarati "))
        self.assertEqual("Hindi", determine_language("Other"))
        self.assertEqual("Hindi", determine_language("1"))
        self.assertEqual("Hindi", determine_language("10"))
        self.assertEqual("Hindi", determine_language(1))
        self.assertEqual("English", determine_language(200))
        self.assertEqual("Gujarati", determine_language(300))
        self.assertEqual("English", determine_language("2"))
        self.assertEqual("Gujarati", determine_language("3"))
        self.assertEqual("Gujarati", determine_language("30"))
        self.assertEqual("Hindi", determine_language("4"))
        self.assertEqual("Hindi", determine_language("7"))
        self.assertEqual("Hindi", determine_language("None"))
        self.assertEqual("Hindi", determine_language(""))
        self.assertEqual("Hindi", determine_language(" "))
        self.assertEqual("Hindi", determine_language(u"\u0923\u09a1"))

    def test_determine_mother_tongue(self):
        self.assertEqual("English", determine_mother_tongue("English"))
        self.assertEqual("English", determine_mother_tongue("English--"))
        self.assertEqual("Hindi", determine_mother_tongue("Hindi"))
        self.assertEqual("Hindi", determine_mother_tongue(" Hindi"))
        self.assertEqual("Other", determine_mother_tongue("Other"))
        self.assertEqual("Other", determine_mother_tongue("Other "))
        self.assertEqual("Hindi", determine_mother_tongue("1"))
        self.assertEqual("Hindi", determine_mother_tongue(1))
        self.assertEqual("English", determine_mother_tongue(200))
        self.assertEqual("Other", determine_mother_tongue(300))
        self.assertEqual("English", determine_mother_tongue("2"))
        self.assertEqual("English", determine_mother_tongue("20"))
        self.assertEqual("Other", determine_mother_tongue("3"))
        self.assertEqual("Other", determine_mother_tongue("30"))
        self.assertEqual("Other", determine_mother_tongue("4"))
        self.assertEqual("Other", determine_mother_tongue("7"))
        self.assertEqual("Other", determine_mother_tongue("None"))
        self.assertEqual(None, determine_mother_tongue(""))
        self.assertEqual(None, determine_mother_tongue(" "))
        self.assertEqual("Other", determine_mother_tongue(u"\u0923\u09a1"))

    def test_language_selector(self):
        self.assertIsNone(language_selector(language_input="", options=["Hindi", "English", "Other"],
                            default_option="Other", none_option=None))
        self.assertIsNone(language_selector(language_input=" ", options=["Hindi", "English", "Gujarati"],
                            default_option="Other", none_option=None))
        self.assertEqual("Hindi", language_selector(language_input=" ", options=["Hindi", "English", "Other"],
                            default_option="Other", none_option="Hindi"))
        self.assertEqual("Hindi", language_selector(language_input="", options=["Hindi", "English", "Other"],
                            default_option="Other", none_option="Hindi"))
        options_one = ["Hindi", "English", "Other"]
        options_two = ["Hindi", "English", "Gujarati"]
        options_three = ["Tiger", "Lion", "Cobra"]
        self.assertEqual(options_one[0], language_selector(language_input=options_one[0], options=options_one,
                            default_option="Other", none_option="Hindi"))
        self.assertEqual(options_one[1], language_selector(language_input=options_one[1], options=options_one,
                            default_option="Other", none_option="Hindi"))
        self.assertEqual(options_one[2], language_selector(language_input=options_one[2], options=options_one,
                            default_option="Other", none_option="Hindi"))
        self.assertEqual(options_two[2], language_selector(language_input=options_two[2], options=options_two,
                            default_option="Other", none_option="Hindi"))
        self.assertEqual(options_three[2], language_selector(language_input=options_three[2], options=options_three,
                            default_option="Other", none_option="Hindi"))
        self.assertEqual(options_one[2], language_selector(language_input=" " + options_one[2] + " ", options=options_one,
                            default_option="Other", none_option="Hindi"))
        self.assertEqual(options_two[0], language_selector(language_input="1", options=options_two,
                            default_option="Other", none_option="Hindi"))
        self.assertEqual(options_two[1], language_selector(language_input="2", options=options_two,
                            default_option="Other", none_option="Hindi"))
        self.assertEqual(options_two[1], language_selector(language_input="20", options=options_two,
                            default_option="Other", none_option="Hindi"))
        self.assertEqual(options_two[2], language_selector(language_input="3", options=options_two,
                            default_option="Other", none_option="Hindi"))
        self.assertEqual(options_two[2], language_selector(language_input=3, options=options_two,
                            default_option="Other", none_option="Hindi"))
        self.assertEqual(options_two[1], language_selector(language_input=20, options=options_two,
                            default_option="Other", none_option="Hindi"))
        self.assertEqual("Stuff", language_selector(language_input="7", options=options_two,
                            default_option="Stuff", none_option="Hindi"))
        self.assertEqual("Stuff", language_selector(language_input="dfsadfasdfp", options=options_two,
                            default_option="Stuff", none_option="Hindi"))
        self.assertEqual("More stuff", language_selector(language_input=u"\u0923\u09a1", options=options_two,
                            default_option="More stuff", none_option="Hindi"))

    def test_replace_blank_name(self):
        self.assertEqual("Your child", replace_blank_name(name="", language="English"))
        self.assertEqual("Your child", replace_blank_name(name=" ", language="English"))
        self.assertEqual("Your child", replace_blank_name(name="     ", language="English"))
        self.assertEqual("Harvey", replace_blank_name(name="Harvey", language="English"))
        self.assertEqual(u"\u0906\u092a\u0915\u093e", replace_blank_name(name=u"\u0906\u092a\u0915\u093e", language="English"))
        self.assertEqual(hindi_placeholder_name(), replace_blank_name(name=" ", language="Hindi"))
        self.assertEqual(hindi_placeholder_name(), replace_blank_name(name=" ", language="Hindi"))
        self.assertEqual(hindi_placeholder_name(), replace_blank_name(name="    ", language="Hindi"))
        self.assertEqual(u"\u0906\u092a\u0915\u093e", replace_blank_name(name=u"\u0906\u092a\u0915\u093e", language="Hindi"))
        self.assertEqual(u"\u0936\u093f\u0936\u0941", replace_blank_name(name=u"\u0936\u093f\u0936\u0941", language="Hindi"))
        self.assertEqual("Aarav", replace_blank_name(name="Aarav", language="Hindi"))
        self.assertEqual("Aditya", replace_blank_name(name="Aditya", language="Hindi"))
        self.assertEqual(gujarati_placeholder_name(), replace_blank_name(name="", language="Gujarati"))
        self.assertEqual(gujarati_placeholder_name(), replace_blank_name(name=" ", language="Gujarati"))
        self.assertEqual(gujarati_placeholder_name(), replace_blank_name(name="    ", language="Gujarati"))
        self.assertEqual(u"\u0aac\u0abe\u0ab3\u0a95", replace_blank_name(name=u"\u0aac\u0abe\u0ab3\u0a95", language="Gujarati"))
        self.assertEqual(u"\u0aa4\u0aae\u0abe\u0ab0\u0ac1\u0a82", replace_blank_name(name=u"\u0aa4\u0aae\u0abe\u0ab0\u0ac1\u0a82", language="Gujarati"))
        self.assertEqual(u"\u0aac\u0abe\u0ab3\u0a95", replace_blank_name(name=u"\u0aac\u0abe\u0ab3\u0a95", language="Gujarati"))
        self.assertEqual("Shuham", replace_blank_name(name="Shuham", language="Gujarati"))
        self.assertEqual("Vashvika", replace_blank_name(name="Vashvika", language="Gujarati"))

    def test_determine_name(self):
        fake_row = {'Name': 'FakestNumber', 'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        fake_row2 = {'Name': 'FakestNumber', "Nick Name of Child": "Fakest NickName", 'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        fake_row3 = {'Name': 'FakestNumber', "Nick Name of Child": "", 'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        ufake_row = {'Name': u"\\u0936\\u093f\\u0936\\u0941", 'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        ufake_row2 = {'Name': 'FakestNumber', "Nick Name of Child": u"\\u0936\\u093f\\u0936\\u0941", 'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        guj_fake_row2 = {'Name': 'FakestNumber', "Nick Name of Child": u"\\u0aa4\\u0aae\\u0abe\\u0ab0\\u0ac1\\u0a82", 'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        ufake_row3 = {'Name': u"\\u0936\\u093f\\u0936\\u0941", "Nick Name of Child": "", 'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        self.assertEqual("FakestNumber", determine_name(language="English", row=fake_row))
        self.assertEqual(u"\u0936\u093f\u0936\u0941", determine_name(language="Gujarati", row=ufake_row))
        self.assertEqual("Fakest NickName", determine_name(language="English", row=fake_row2))
        self.assertEqual(u"\u0936\u093f\u0936\u0941", determine_name(language="Hindi", row=ufake_row2))
        self.assertEqual(u"\u0aa4\u0aae\u0abe\u0ab0\u0ac1\u0a82", determine_name(language="Hindi", row=guj_fake_row2))
        self.assertEqual("FakestNumber", determine_name(language="English", row=fake_row3))
        self.assertEqual(u"\u0936\u093f\u0936\u0941", determine_name(language="Hindi", row=ufake_row3))

    def test_determine_name_reads_multiple_columns(self):
        name_row = {'Name': 'FakestNumber', 'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        name_of_child_row = {'Name of Child': 'FakestNumber', 'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        first_name_of_child_row = {'First Name Of Child To Be Vaccinated': 'FakestNumber', 'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        other_name_column_row = {'Name of Respondent': 'first last', 'Name of The Mother': 'mom', 'First Name Of Child To Be Vaccinated': 'FakestNumber', 'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        other_name_column_row2 = {'Name of State': 'MADHYA PRADESH', 'Name of Child': 'FakestNumber', 'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        other_name_column_row3 = {'Name of State': 'MADHYA PRADESH', 'Name of Child': 'FakestNumber', 'Nick Name of Child': 'Good nickname', 'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        self.assertEqual("FakestNumber", determine_name(language="English", row=name_row))
        self.assertEqual("FakestNumber", determine_name(language="English", row=name_of_child_row))
        self.assertEqual("FakestNumber", determine_name(language="English", row=other_name_column_row))
        self.assertEqual("FakestNumber", determine_name(language="English", row=other_name_column_row2))
        self.assertEqual("Good nickname", determine_name(language="English", row=other_name_column_row3))


    def test_check_permutations(self):
        name_row = {'Name of Respondent': 'first last', 'Name of The Mother': 'mom', 'Name': 'FakestNumber', 'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        name_of_child_row = {'Name of State': 'MADHYA PRADESH', 'Name of Child': 'FakestNumber', 'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        name_match = "Name"
        lowercase = "name"
        with_period = "Name."
        with_comma = "Name,"
        with_space = " Name"
        with_spaces = " Name "
        with_the = "the Name"
        with_cap_the = "The Name"
        spaced_cap_the = "  The  Name"
        self.assertTrue(check_permutations(row=name_row, header=name_match))
        self.assertTrue(check_permutations(row=name_row, header=lowercase))
        self.assertTrue(check_permutations(row=name_row, header=with_period))
        self.assertTrue(check_permutations(row=name_row, header=with_comma))
        self.assertTrue(check_permutations(row=name_row, header=with_space))
        self.assertTrue(check_permutations(row=name_row, header=with_spaces))
        self.assertTrue(check_permutations(row=name_row, header=with_the))
        self.assertTrue(check_permutations(row=name_row, header=with_cap_the))
        self.assertTrue(check_permutations(row=name_row, header=spaced_cap_the))

        name_of_child = "Name of Child"
        title_noc = "Name Of Child"
        extra_the = "Name of the Child"
        cap_extra_the = "Name of The Child"
        self.assertTrue(check_permutations(row=name_of_child_row, header=name_of_child))
        self.assertTrue(check_permutations(row=name_of_child_row, header=title_noc))
        self.assertTrue(check_permutations(row=name_of_child_row, header=extra_the))
        self.assertTrue(check_permutations(row=name_of_child_row, header=cap_extra_the))

