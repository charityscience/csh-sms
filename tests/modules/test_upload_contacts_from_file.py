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
                                              determine_name, matching_permutation, check_all_headers, \
                                              assign_org_signup, assign_method_of_signup, assign_hospital_name 
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

    @patch("modules.upload_contacts_from_file.check_all_headers")
    def test_delay_normal_inputs(self, headers_mock):
        headers = ["Delay in days"]
        row = {"Delay in days:" "WONT BE READ"}
        headers_mock.return_value = "1000"
        self.assertEqual(1000, parse_or_create_delay_num(row=row, headers=headers))
        headers_mock.return_value = "100"
        self.assertEqual(100, parse_or_create_delay_num(row=row, headers=headers))
        headers_mock.return_value = "1003"
        self.assertEqual(1003, parse_or_create_delay_num(row=row, headers=headers))
        headers_mock.return_value = "4500"
        self.assertEqual(4500, parse_or_create_delay_num(row=row, headers=headers))
        headers_mock.return_value = "5"
        self.assertEqual(5, parse_or_create_delay_num(row=row, headers=headers))
        headers_mock.return_value = "10"
        self.assertEqual(10, parse_or_create_delay_num(row=row, headers=headers))
        headers_mock.return_value = "800"
        self.assertEqual(800, parse_or_create_delay_num(row=row, headers=headers))

    @patch("modules.upload_contacts_from_file.check_all_headers")
    def test_nondigits_in_delay(self, headers_mock):
        headers = ["Delay in days"]
        row = {"Delay in days:" "WONT BE READ"}
        headers_mock.return_value = ""
        self.assertEqual(0, parse_or_create_delay_num(row=row, headers=headers))
        headers_mock.return_value = None
        self.assertEqual(0, parse_or_create_delay_num(row=row, headers=headers))
        headers_mock.return_value = "1892ff8"
        self.assertEqual(0, parse_or_create_delay_num(row=row, headers=headers))
        headers_mock.return_value = "ghg18928"
        self.assertEqual(0, parse_or_create_delay_num(row=row, headers=headers))
        headers_mock.return_value = "18928-"
        self.assertEqual(0, parse_or_create_delay_num(row=row, headers=headers))
        headers_mock.return_value = "-18928"
        self.assertEqual(0, parse_or_create_delay_num(row=row, headers=headers))
        headers_mock.return_value = "8+928"
        self.assertEqual(0, parse_or_create_delay_num(row=row, headers=headers))
        headers_mock.return_value = "18 928"
        self.assertEqual(0, parse_or_create_delay_num(row=row, headers=headers))
        headers_mock.return_value = "1,928"
        self.assertEqual(1928, parse_or_create_delay_num(row=row, headers=headers))

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


    @patch("modules.upload_contacts_from_file.check_all_headers")
    def test_string_dob_for_parse_or_create_functional_dob(self, headers_mock):
        headers = ["Functional DoB"]
        no_diff_row = {'Name': 'FakestNumber', 'Phone Number': '123456', 'Date of Birth': '2016-09-14',
                "Functional DoB": '2016-09-14', "Delay in days": "0"}

        headers_mock.return_value = ""
        with self.assertRaises(TypeError):
            parse_or_create_functional_dob(row=no_diff_row, headers=headers, source="TR", date_of_birth="10-10-2015", delay=0)
        with self.assertRaises(TypeError):
            parse_or_create_functional_dob(row=no_diff_row, headers=headers, source="TR", date_of_birth="01-01-2017", delay=0)
        with self.assertRaises(TypeError):
            parse_or_create_functional_dob(row=no_diff_row, headers=headers, source="TR", date_of_birth="2017-01-01", delay=0)
        with self.assertRaises(TypeError):
            parse_or_create_functional_dob(row=no_diff_row, headers=headers, source="TR", date_of_birth="40-15-2015", delay=0)

        headers_mock.return_value = "40-15-2015"
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob(row=no_diff_row, headers=headers, source="TR", date_of_birth="40-15-2015", delay=0)


    @patch("modules.upload_contacts_from_file.check_all_headers")
    def test_fake_dates_for_parse_or_create_functional_dob(self, headers_mock):
        headers = ["Functional DoB"]
        no_diff_row = {'Name': 'FakestNumber', 'Phone Number': '123456', 'Date of Birth': '2016-09-14',
                "Functional DoB": '2016-09-14', "Delay in days": "0"}

        headers_mock.return_value = "40-15-2015"
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob(row=no_diff_row, headers=headers, source="TR", date_of_birth=datetime(2015, 15, 40, 0, 0).date(), delay=0)
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob(row=no_diff_row, headers=headers, source="TR", date_of_birth=datetime(2015, 12, 10, 0, 0).date(), delay=0)
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob(row=no_diff_row, headers=headers, source="TR", date_of_birth=datetime(2015, 12, 10, 0, 0).date(), delay=5)
        headers_mock.return_value = "30-15-2015"
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob(row=no_diff_row, headers=headers, source="TR", date_of_birth=datetime(2015, 15, 30, 0, 0), delay=0)
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob(row=no_diff_row, headers=headers, source="TR", date_of_birth=datetime(2015, 1, 10, 0, 0), delay=0)
        headers_mock.return_value = "12-35-2015"
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob(row=no_diff_row, headers=headers, source="TR", date_of_birth=datetime(2015, 1, 10, 0, 0), delay=0)
        headers_mock.return_value = "2014-20-15"
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob(row=no_diff_row, headers=headers, source="TR", date_of_birth=datetime(2015, 1, 10, 0, 0), delay=0)
        headers_mock.return_value = "12-00-2015"
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob(row=no_diff_row, headers=headers, source="TR", date_of_birth=datetime(2015, 1, 10, 0, 0), delay=0)
        headers_mock.return_value = "20000-20-15"
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob(row=no_diff_row, headers=headers, source="TR", date_of_birth=datetime(2015, 1, 10, 0, 0), delay=0)
        headers_mock.return_value = "2014-35-00"
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob(row=no_diff_row, headers=headers, source="TR", date_of_birth=datetime(2015, 1, 10, 0, 0), delay=0)
        headers_mock.return_value = "2016-12-40"
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob(row=no_diff_row, headers=headers, source="TR", date_of_birth=datetime(2015, 1, 10, 0, 0), delay=0)
        headers_mock.return_value = "2017-02-40"
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob(row=no_diff_row, headers=headers, source="TR", date_of_birth=datetime(2015, 1, 10, 0, 0), delay=0)
        headers_mock.return_value = "29-02-2017"
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob(row=no_diff_row, headers=headers, source="TR", date_of_birth=datetime(2015, 1, 10, 0, 0), delay=0)
        headers_mock.return_value = "40-15-2015"
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob(row=no_diff_row, headers=headers, source="MPS", date_of_birth=datetime(2015, 1, 10, 0, 0), delay=0)
        headers_mock.return_value = "30-15-2015"
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob(row=no_diff_row, headers=headers, source="MPS", date_of_birth=datetime(2015, 1, 10, 0, 0), delay=0)
        headers_mock.return_value = "2017-02-29"
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob(row=no_diff_row, headers=headers, source="TR", date_of_birth="2017-02-40", delay=0)
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob(row=no_diff_row, headers=headers, source="PRNT", date_of_birth="2017-02-40", delay=0)
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob(row=no_diff_row, headers=headers, source="PRNT", date_of_birth="2017-02-40", delay=5)

    @freeze_time(datetime(2017, 7, 21, 0, 0).replace(tzinfo=timezone.get_default_timezone()))
    @patch("modules.upload_contacts_from_file.check_all_headers")
    def test_nonexistent_dates_for_parse_or_create_functional_dob(self, headers_mock):
        headers = ["Functional DoB"]
        no_diff_row = {'Name': 'FakestNumber', 'Phone Number': '123456', 'Date of Birth': '2016-09-14',
                "Functional DoB": '2016-09-14', "Delay in days": "0"}

        headers_mock.return_value = ""
        with self.assertRaises(TypeError):
            parse_or_create_functional_dob(row=no_diff_row, headers=headers, source="TR", date_of_birth="", delay=0)

        parsed_func_dob = parse_or_create_functional_dob(row=no_diff_row, headers=headers, source="TR", date_of_birth=datetime(2015, 10, 15, 0, 0).date(), delay=0)
        parsed_func_dob_diff_source = parse_or_create_functional_dob(row=no_diff_row, headers=headers, source="PRNT", date_of_birth=datetime(2015, 10, 15, 0, 0).date(), delay=0)
        parsed_func_dob2 = parse_or_create_functional_dob(row=no_diff_row, headers=headers, source="TR", date_of_birth=datetime(2015, 10, 15, 0, 0).date(), delay=5)
        month_roll = parse_or_create_functional_dob(row=no_diff_row, headers=headers, source="TR", date_of_birth=datetime(2016, 6, 3, 0, 0).date(), delay=30)
        year_roll = parse_or_create_functional_dob(row=no_diff_row, headers=headers, source="TR", date_of_birth=datetime(2015, 12, 31, 0, 0).date(), delay=5)
        large_delay = parse_or_create_functional_dob(row=no_diff_row, headers=headers, source="TR", date_of_birth=datetime(2016, 6, 30, 0, 0).date(), delay=50)
        past_to_future = parse_or_create_functional_dob(row=no_diff_row, headers=headers, source="TR", date_of_birth=datetime(2017, 7, 11, 0, 0).date(), delay=20)
        future_to_future = parse_or_create_functional_dob(row=no_diff_row, headers=headers, source="TR", date_of_birth=datetime(2017, 8, 11, 0, 0).date(), delay=20)
        
        self.assertEqual(parsed_func_dob, datetime(2015, 10, 15).date())
        self.assertEqual(parsed_func_dob_diff_source, datetime(2015, 10, 15).date())
        self.assertEqual(parsed_func_dob2, datetime(2015, 10, 20).date())
        self.assertEqual(month_roll, datetime(2016, 7, 3).date())
        self.assertEqual(year_roll, datetime(2016, 1, 5).date())
        self.assertEqual(large_delay, datetime(2016, 8, 19).date())
        self.assertEqual(past_to_future, datetime(2017, 7, 31).date())
        self.assertEqual(future_to_future, datetime(2017, 8, 31).date())

    @patch("modules.upload_contacts_from_file.check_all_headers")
    def test_real_dates_for_parse_or_create_functional_dob(self, headers_mock):
        headers = ["Functional DoB"]
        no_diff_row = {'Name': 'FakestNumber', 'Phone Number': '123456', 'Date of Birth': '2016-09-14',
                "Functional DoB": '2016-09-14', "Delay in days": "0"}

        headers_mock.return_value = "10-15-2015"
        parsed_func_dob1 = parse_or_create_functional_dob(row=no_diff_row, headers=headers, source="TR",
          date_of_birth=datetime(2015, 10, 15,0,0).date(), delay=0)
        self.assertEqual(parsed_func_dob1, datetime(2015, 10, 15).date())
        headers_mock.return_value = "10-18-2015"
        parsed_func_dob2 = parse_or_create_functional_dob(row=no_diff_row, headers=headers, source="TR",
          date_of_birth=datetime(2015, 10, 15,0,0).date(), delay=3)
        self.assertEqual(parsed_func_dob2, datetime(2015, 10, 18).date())
        headers_mock.return_value = "15-10-2015"
        parsed_func_dob3 = parse_or_create_functional_dob(row=no_diff_row, headers=headers, source="PRNT",
            date_of_birth=datetime(2015, 10, 15,0,0).date(), delay=0)
        self.assertEqual(parsed_func_dob3, datetime(2015, 10, 15).date())
        headers_mock.return_value = "18-10-2015"
        parsed_func_dob4 = parse_or_create_functional_dob(row=no_diff_row, headers=headers, source="PRNT",
            date_of_birth=datetime(2015, 10, 15,0,0).date(), delay=3)
        self.assertEqual(parsed_func_dob4, datetime(2015, 10, 18).date())
        

    @patch("modules.upload_contacts_from_file.check_all_headers")
    def test_nonexistent_dates_for_entered_date_string_to_date(self, headers_mock):
        date_of_birth_headers = ["Date of Birth", "Date Of Birth Of The Child",
                        "Date of Birth of Child (dd/mm/yyyy)", "Date of Birth of Child"]
        date_of_birth_row = {'Name': 'FakestNumber', 'Phone Number': '123456',
                                'Date of Birth': '2016-09-14'}
        headers_mock.return_value = ""
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="TR")
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="NOT TR")
        headers_mock.return_value = " "
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="TR")
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="NOT TR")
        headers_mock.return_value = "    "
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="TR")
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="NOT TR")

    @patch("modules.upload_contacts_from_file.check_all_headers")
    def test_fake_dates_for_entered_date_string_to_date(self, headers_mock):
        date_of_birth_headers = ["Date of Birth", "Date Of Birth Of The Child",
                        "Date of Birth of Child (dd/mm/yyyy)", "Date of Birth of Child"]
        date_of_signup_headers = ["Date of Sign Up", "Date of Survey (dd/mm/yy)", "Date of Survey"]
        date_of_birth_row = {'Name': 'FakestNumber', 'Phone Number': '123456',
                                'Date of Birth': '2016-09-14'}
        date_of_signup_row = {'Name': 'FakestNumber', 'Phone Number': '123456',
                                'Date of Sign Up': '2016-09-14'}

        headers_mock.return_value = "40-15-2015"
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="TR")
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row=date_of_signup_row, headers=date_of_signup_headers, source="TR")
        headers_mock.return_value = "30-15-2015"
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="TR")
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row=date_of_signup_row, headers=date_of_signup_headers, source="TR")
        headers_mock.return_value = "12-35-2015"
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="TR")
        headers_mock.return_value = "2014-20-15"
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="TR")
        headers_mock.return_value = "12-00-2015"
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="TR")
        headers_mock.return_value = "0000-20-15"
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="TR")
        headers_mock.return_value = "2014-35-00"
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="TR")
        headers_mock.return_value = "2016-12-40"
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="TR")
        headers_mock.return_value = "2017-02-29"
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="TR")
        headers_mock.return_value = "0000-20-15"
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="MPS")
        headers_mock.return_value = "2014-35-00"
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="MPS")
        headers_mock.return_value = "2016-12-40"
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="PRNT")
        headers_mock.return_value = "2017-02-29"
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="PRNT")
        headers_mock.return_value = "30-15-2015"
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="PRNT")
        headers_mock.return_value = "12-35-2015"
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="PRNT")
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row=date_of_signup_row, headers=date_of_signup_headers, source="PRNT")
        headers_mock.return_value = "2014-20-15"
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="PRNT")
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row=date_of_signup_row, headers=date_of_signup_headers, source="PRNT")
        headers_mock.return_value = "2017-02-29"
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="PRNT")
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row=date_of_signup_row, headers=date_of_signup_headers, source="PRNT")
        headers_mock.return_value = "02-29-2017"
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="MPS")
        headers_mock.return_value = "29-02-2017"
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="Tr")

    @patch("modules.upload_contacts_from_file.check_all_headers")
    def test_real_dates_for_entered_date_that_should_fail(self, headers_mock):
        date_of_birth_headers = ["Date of Birth", "Date Of Birth Of The Child",
                        "Date of Birth of Child (dd/mm/yyyy)", "Date of Birth of Child"]
        date_of_signup_headers = ["Date of Sign Up", "Date of Survey (dd/mm/yy)", "Date of Survey"]
        date_of_birth_row = {'Name': 'FakestNumber', 'Phone Number': '123456',
                                'Date of Birth': '2016-09-14'}
        date_of_signup_row = {'Name': 'FakestNumber', 'Phone Number': '123456',
                                'Date of Sign Up': '2016-09-14'}

        headers_mock.return_value = "20-10-2017"
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="TR")
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row=date_of_signup_row, headers=date_of_signup_headers, source="TR")
        headers_mock.return_value = "28-03-2015"
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="TR")
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row=date_of_signup_row, headers=date_of_signup_headers, source="TR")
        headers_mock.return_value = "05-15-2015"
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="MPS")
        headers_mock.return_value = "03-28-2015"
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="PRNT")
        with self.assertRaises(ValueError):
            entered_date_string_to_date(row=date_of_signup_row, headers=date_of_signup_headers, source="PRNT")

    @patch("modules.upload_contacts_from_file.check_all_headers")
    def test_real_dates_for_entered_date_string_to_date(self, headers_mock):
        date_of_birth_headers = ["Date of Birth", "Date Of Birth Of The Child",
                        "Date of Birth of Child (dd/mm/yyyy)", "Date of Birth of Child"]
        date_of_signup_headers = ["Date of Sign Up", "Date of Survey (dd/mm/yy)", "Date of Survey"]
        date_of_birth_row = {'Name': 'FakestNumber', 'Phone Number': '123456',
                                'Date of Birth': '2016-09-14'}
        date_of_signup_row = {'Name': 'FakestNumber', 'Phone Number': '123456',
                                'Date of Sign Up': '2016-09-14'}

        headers_mock.return_value = "2014-12-20"
        self.assertEqual(entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="TR"), datetime(2014, 12, 20, 0,0 ).date())
        self.assertEqual(entered_date_string_to_date(row=date_of_signup_row, headers=date_of_signup_headers, source="TR"), datetime(2014, 12, 20, 0,0 ).date())
        headers_mock.return_value = "2017-01-20"
        self.assertEqual(entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="TR"), datetime(2017, 1, 20, 0,0 ).date())
        headers_mock.return_value = "2017-01-07"
        self.assertEqual(entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="TR"), datetime(2017, 1, 7, 0,0 ).date())
        headers_mock.return_value = "01-15-2017"
        self.assertEqual(entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="TR"), datetime(2017, 1, 15, 0,0 ).date())
        headers_mock.return_value = "02-28-2017"
        self.assertEqual(entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="TR"), datetime(2017, 2, 28, 0,0 ).date())
        headers_mock.return_value = "02-29-2016"
        self.assertEqual(entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="TR"), datetime(2016, 2, 29, 0,0 ).date())
        headers_mock.return_value = "2014-12-20"
        self.assertEqual(entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="MPS"), datetime(2014, 12, 20, 0,0 ).date())
        headers_mock.return_value = "2017-01-20"
        self.assertEqual(entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="MPS"), datetime(2017, 1, 20, 0,0 ).date())
        headers_mock.return_value = "2017-01-07"
        self.assertEqual(entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="MPS"), datetime(2017, 1, 7, 0,0 ).date())
        headers_mock.return_value = "15-01-2017"
        self.assertEqual(entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="MPS"), datetime(2017, 1, 15, 0,0 ).date())
        headers_mock.return_value = "28-02-2017"
        self.assertEqual(entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="MPS"), datetime(2017, 2, 28, 0,0 ).date())
        headers_mock.return_value = "29-02-2016"
        self.assertEqual(entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="MPS"), datetime(2016, 2, 29, 0,0 ).date())
        headers_mock.return_value = "2017-01-07"
        self.assertEqual(entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="PRNT"), datetime(2017, 1, 7, 0,0 ).date())
        headers_mock.return_value = "28-02-2017"
        self.assertEqual(entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="PRNT"), datetime(2017, 2, 28, 0,0 ).date())
        headers_mock.return_value = "15-01-2017"
        self.assertEqual(entered_date_string_to_date(row=date_of_birth_row, headers=date_of_birth_headers, source="PRNT"), datetime(2017, 1, 15, 0,0 ).date())
        self.assertEqual(entered_date_string_to_date(row=date_of_signup_row, headers=date_of_signup_headers, source="PRNT"), datetime(2017, 1, 15, 0,0 ).date())

    
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

    @patch("modules.upload_contacts_from_file.check_all_headers")
    def test_determine_language(self, headers_mock):
        lan_pref = ["Language Preference", "preferred Language Of Participant",
                        "Prefer Language for SMS 1.Hindi, 2.English, 3.Gujarati", "Prefer Language for SMS"]
        lan_row = {'Language Preference': 'NONSENSE', 'Name': 'FakestNumber',
                        'Phone Number': '123456', 'Date of Birth': '2016-09-14'}

        headers_mock.return_value = "English"
        self.assertEqual("English", determine_language(row=lan_row, headers=lan_pref))
        headers_mock.return_value = "English--"
        self.assertEqual("English", determine_language(row=lan_row, headers=lan_pref))
        headers_mock.return_value = "Hindi"
        self.assertEqual("Hindi", determine_language(row=lan_row, headers=lan_pref))
        headers_mock.return_value = "  Hindi"
        self.assertEqual("Hindi", determine_language(row=lan_row, headers=lan_pref))
        headers_mock.return_value = "Gujarati"
        self.assertEqual("Gujarati", determine_language(row=lan_row, headers=lan_pref))
        headers_mock.return_value = "Gujarati "
        self.assertEqual("Gujarati", determine_language(row=lan_row, headers=lan_pref))
        headers_mock.return_value = "Other"
        self.assertEqual("Hindi", determine_language(row=lan_row, headers=lan_pref))
        headers_mock.return_value = "1"
        self.assertEqual("Hindi", determine_language(row=lan_row, headers=lan_pref))
        headers_mock.return_value = "10"
        self.assertEqual("Hindi", determine_language(row=lan_row, headers=lan_pref))
        headers_mock.return_value = 1
        self.assertEqual("Hindi", determine_language(row=lan_row, headers=lan_pref))
        headers_mock.return_value = 200
        self.assertEqual("English", determine_language(row=lan_row, headers=lan_pref))
        headers_mock.return_value = 300
        self.assertEqual("Gujarati", determine_language(row=lan_row, headers=lan_pref))
        headers_mock.return_value = "2"
        self.assertEqual("English", determine_language(row=lan_row, headers=lan_pref))
        headers_mock.return_value = "3"
        self.assertEqual("Gujarati", determine_language(row=lan_row, headers=lan_pref))
        headers_mock.return_value = "30"
        self.assertEqual("Gujarati", determine_language(row=lan_row, headers=lan_pref))
        headers_mock.return_value = "4"
        self.assertEqual("Hindi", determine_language(row=lan_row, headers=lan_pref))
        headers_mock.return_value = "7"
        self.assertEqual("Hindi", determine_language(row=lan_row, headers=lan_pref))
        headers_mock.return_value = "None"
        self.assertEqual("Hindi", determine_language(row=lan_row, headers=lan_pref))
        headers_mock.return_value = ""
        self.assertEqual("Hindi", determine_language(row=lan_row, headers=lan_pref))
        headers_mock.return_value = " "
        self.assertEqual("Hindi", determine_language(row=lan_row, headers=lan_pref))
        headers_mock.return_value = u"\\u0923\\u09a1"
        self.assertEqual("Hindi", determine_language(row=lan_row, headers=lan_pref))

    @patch("modules.upload_contacts_from_file.check_all_headers")
    def test_determine_mother_tongue(self, headers_mock):
        mother_options = ["Mother Tongue", "Mother Tongue Of Participant",
                            "Mother/Father Tongue 1.(Hindi, 2.English, 3.Other ", "Mother/Father Tongue"]
        mother_tongue_row = {'Mother Tongue': 'NONSENSE', 'Name': 'FakestNumber',
                        'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        headers_mock.return_value = "English"
        self.assertEqual("English", determine_mother_tongue(row=mother_tongue_row, headers=mother_options))
        headers_mock.return_value = "English--"
        self.assertEqual("English", determine_mother_tongue(row=mother_tongue_row, headers=mother_options))
        headers_mock.return_value = "Hindi"
        self.assertEqual("Hindi", determine_mother_tongue(row=mother_tongue_row, headers=mother_options))
        headers_mock.return_value = " Hindi"
        self.assertEqual("Hindi", determine_mother_tongue(row=mother_tongue_row, headers=mother_options))
        headers_mock.return_value = "Other"
        self.assertEqual("Other", determine_mother_tongue(row=mother_tongue_row, headers=mother_options))
        headers_mock.return_value = "Other "
        self.assertEqual("Other", determine_mother_tongue(row=mother_tongue_row, headers=mother_options))
        headers_mock.return_value = "1"
        self.assertEqual("Hindi", determine_mother_tongue(row=mother_tongue_row, headers=mother_options))
        headers_mock.return_value = 1
        self.assertEqual("Hindi", determine_mother_tongue(row=mother_tongue_row, headers=mother_options))
        headers_mock.return_value = 200
        self.assertEqual("English", determine_mother_tongue(row=mother_tongue_row, headers=mother_options))
        headers_mock.return_value = 300
        self.assertEqual("Other", determine_mother_tongue(row=mother_tongue_row, headers=mother_options))
        headers_mock.return_value = "2"
        self.assertEqual("English", determine_mother_tongue(row=mother_tongue_row, headers=mother_options))
        headers_mock.return_value = "20"
        self.assertEqual("English", determine_mother_tongue(row=mother_tongue_row, headers=mother_options))
        headers_mock.return_value = "3"
        self.assertEqual("Other", determine_mother_tongue(row=mother_tongue_row, headers=mother_options))
        headers_mock.return_value = "30"
        self.assertEqual("Other", determine_mother_tongue(row=mother_tongue_row, headers=mother_options))
        headers_mock.return_value = "4"
        self.assertEqual("Other", determine_mother_tongue(row=mother_tongue_row, headers=mother_options))
        headers_mock.return_value = "7"
        self.assertEqual("Other", determine_mother_tongue(row=mother_tongue_row, headers=mother_options))
        headers_mock.return_value = "None"
        self.assertEqual("Other", determine_mother_tongue(row=mother_tongue_row, headers=mother_options))
        headers_mock.return_value = ""
        self.assertIsNone(determine_mother_tongue(row=mother_tongue_row, headers=mother_options))
        headers_mock.return_value = " "
        self.assertIsNone(determine_mother_tongue(row=mother_tongue_row, headers=mother_options))
        headers_mock.return_value = u"\\u0923\\u09a1"
        self.assertEqual("Other", determine_mother_tongue(row=mother_tongue_row, headers=mother_options))

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

    @patch("modules.upload_contacts_from_file.check_all_headers")
    def test_determine_name(self, headers_mock):
        name_headers = ["Name", "First Name Of Child To Be Vaccinated", "Name of Child"]
        fake_row = {'Name': 'FAKE ENTRY', 'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        fake_row2 = {'Name': 'NONSENSE', "Nick Name of Child": "Fakest NickName", 'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        fake_row3 = {'Name': 'Replace blank nickname', "Nick Name of Child": "", 'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        ufake_row = {'Name': u"\\u0936\\u093f\\u0936\\u0941", 'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        ufake_row2 = {'Name': 'FakestNumber', "Nick Name of Child": u"\\u0936\\u093f\\u0936\\u0941", 'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        guj_fake_row2 = {'Name': 'FakestNumber', "Nick Name of Child": u"\\u0aa4\\u0aae\\u0abe\\u0ab0\\u0ac1\\u0a82", 'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        ufake_row3 = {'Name': u"\\u0936\\u093f\\u0936\\u0941", "Nick Name of Child": "", 'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        headers_mock.return_value = "FakestNumber"
        self.assertEqual("FakestNumber", determine_name(row=fake_row, headers=name_headers, language="English"))
        headers_mock.return_value = u"\\u0936\\u093f\\u0936\\u0941"
        self.assertEqual(u"\u0936\u093f\u0936\u0941", determine_name(row=ufake_row, headers=name_headers, language="Gujarati"))
        headers_mock.return_value = "Shouldn't matter"
        self.assertEqual("Fakest NickName", determine_name(row=fake_row2, headers=name_headers, language="English"))
        headers_mock.return_value = u"\\u0936\\u093f\\u0936\\u0941"
        self.assertEqual(u"\u0936\u093f\u0936\u0941", determine_name(row=ufake_row2, headers=name_headers, language="Hindi"))
        headers_mock.return_value = u"\\u0aa4\\u0aae\\u0abe\\u0ab0\\u0ac1\\u0a82"
        self.assertEqual(u"\u0aa4\u0aae\u0abe\u0ab0\u0ac1\u0a82", determine_name(row=guj_fake_row2, headers=name_headers, language="Hindi"))
        headers_mock.return_value = "Replace blank nickname"
        self.assertEqual("Replace blank nickname", determine_name(row=fake_row3, headers=name_headers, language="English"))
        headers_mock.return_value = u"\\u0936\\u093f\\u0936\\u0941"
        self.assertEqual(u"\u0936\u093f\u0936\u0941", determine_name(row=ufake_row3, headers=name_headers, language="English"))

    def test_determine_name_reads_multiple_columns(self):
        name_headers = ["Name", "First Name Of Child To Be Vaccinated", "Name of Child"]
        name_row = {'Name': 'FakestNumber', 'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        name_of_child_row = {'Name of Child': 'FakestNumber', 'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        first_name_of_child_row = {'First Name Of Child To Be Vaccinated': 'FakestNumber', 'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        other_name_column_row = {'Name of Respondent': 'first last', 'Name of The Mother': 'mom', 'First Name Of Child To Be Vaccinated': 'FakestNumber',
                                    'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        other_name_column_row2 = {'Name of State': 'MADHYA PRADESH', 'Name of Child': 'FakestNumber', 'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        other_name_column_row3 = {'Name of State': 'MADHYA PRADESH', 'Name of Child': 'FakestNumber', 'Nick Name of Child': 'Good nickname',
                                    'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        self.assertEqual("FakestNumber", determine_name(row=name_row, headers=name_headers, language="English"))
        self.assertEqual("FakestNumber", determine_name(row=name_of_child_row, headers=name_headers, language="English"))
        self.assertEqual("FakestNumber", determine_name(row=other_name_column_row, headers=name_headers, language="English"))
        self.assertEqual("FakestNumber", determine_name(row=other_name_column_row2, headers=name_headers, language="English"))
        self.assertEqual("Good nickname", determine_name(row=other_name_column_row3, headers=name_headers, language="English"))

    def test_matching_permutation(self):
        name_header = "Name"
        name_of_child_header = "Name of Child"

        name_row = {'Name of Respondent': 'first last', 'Name of The Mother': 'mom', 'Name': 'FakestNumber',
                        'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        lowercase = {'Name of Respondent': 'first last', 'Name of The Mother': 'mom', 'name': 'FakestNumber',
                        'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        with_period = {'Name of Respondent': 'first last', 'Name of The Mother': 'mom', 'Name.': 'FakestNumber',
                        'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        with_comma = {'Name of Respondent': 'first last', 'Name of The Mother': 'mom', 'Name,': 'FakestNumber',
                        'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        with_space = {'Name of Respondent': 'first last', 'Name of The Mother': 'mom', 'Name ': 'FakestNumber',
                        'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        with_spaces = {'Name of Respondent': 'first last', 'Name of The Mother': 'mom', ' Name ': 'FakestNumber',
                        'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        with_the_lower = {'Name of Respondent': 'first last', 'Name of The Mother': 'mom', 'the name': 'FakestNumber',
                        'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        with_cap_the = {'Name of Respondent': 'first last', 'Name of The Mother': 'mom', 'The Name': 'FakestNumber',
                        'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        self.assertTrue(matching_permutation(row=name_row, header=name_header))
        self.assertTrue(matching_permutation(row=lowercase, header=name_header))
        self.assertTrue(matching_permutation(row=with_period, header=name_header))
        self.assertTrue(matching_permutation(row=with_comma, header=name_header))
        self.assertTrue(matching_permutation(row=with_space, header=name_header))
        self.assertTrue(matching_permutation(row=with_spaces, header=name_header))
        self.assertTrue(matching_permutation(row=with_the_lower, header=name_header))
        self.assertTrue(matching_permutation(row=with_cap_the, header=name_header))

        name_of_child = {'Name of Respondent': 'first last', 'Name of The Mother': 'mom', 'Name of Child': 'FakestNumber',
                            'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        title_noc = {'Name of Respondent': 'first last', 'Name of The Mother': 'mom', 'NAME OF CHILD': 'FakestNumber',
                            'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        upper_noc = {'Name of Respondent': 'first last', 'Name of The Mother': 'mom', 'Name Of Child': 'FakestNumber',
                            'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        self.assertTrue(matching_permutation(row=name_of_child, header=name_of_child_header))
        self.assertTrue(matching_permutation(row=title_noc, header=name_of_child_header))
        self.assertTrue(matching_permutation(row=upper_noc, header=name_of_child_header))

        language_preference = "preferred Language Of Participant"
        lang_pref = {'preferred Language Of Participant': 'Hindi', 'Name of The Mother': 'mom', 'Name of Child': 'FakestNumber',
                        'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        cap_lang_pref = {'Preferred Language Of Participant': 'Hindi', 'Name of The Mother': 'mom', 'Name of Child': 'FakestNumber',
                        'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        self.assertTrue(matching_permutation(row=lang_pref, header=language_preference))
        self.assertTrue(matching_permutation(row=cap_lang_pref, header=language_preference))

        alt_num = "Alternate Mobile No."
        end_typo_alt_num_row = {'Name Of The Child': 'James', 'Phone Number': '123456', 'Alternate Mobile No': '0987654321'}
        begin_typo_alt_num_row = {'Name Of The Child': 'James', 'Phone Number': '123456', 'lternate Mobile No.': '0987654321'}
        self.assertEqual("Alternate Mobile No", matching_permutation(row=end_typo_alt_num_row, header=alt_num))
        self.assertEqual("lternate Mobile No.", matching_permutation(row=begin_typo_alt_num_row, header=alt_num))

    def test_matching_permutation_returns_none_when_no_match(self):
        name_of_child_header = "Name of Child"
        extra_the = {'Name of Respondent': 'first last', 'Name of The Mother': 'mom', 'Name Of the Child': 'FakestNumber',
                            'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        cap_extra_the = {'Name of Respondent': 'first last', 'Name of The Mother': 'mom', 'Name Of The Child': 'FakestNumber',
                            'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        self.assertIsNone(matching_permutation(row=extra_the, header=name_of_child_header))
        self.assertIsNone(matching_permutation(row=cap_extra_the, header=name_of_child_header))
        
        name_header = "Name"
        spaced_cap_the = {'Name of Respondent': 'first last', 'Name of The Mother': 'mom', '  The   Name': 'FakestNumber',
                        'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        self.assertIsNone(matching_permutation(row=spaced_cap_the, header=name_header))

    def test_check_all_headers(self):
        name = ["Name", "First Name Of Child To Be Vaccinated", "Name of Child"]
        phone_number = ["Phone Number", "Mobile No of  Pregnant/ Mother/ Father",
                    "Mobile Number of Respondent Capture At End", "Mobile Number of Respondent"]
        alt_phone_number = ["Alternative Phone", "Alternate Mobile Number", "Alternate Mobile No."]
        delay_in_days = ["Delay in days"]
        first_name_row = {'Name of Respondent': 'first last', 'Name of The Mother': 'mom', 'First Name Of Child To Be Vaccinated': 'FakestNumber',
                            'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        name_of_child_row = {'Name of Respondent': 'first last', 'Name of The Mother': 'mom', 'Name of Child': 'FakestNumber',
                                'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        name_row = {'Name of Respondent': 'first last', 'Name of The Mother': 'mom', 'Name': 'FakestNumber',
                            'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        lowercase = {'Name of Respondent': 'first last', 'Name of The Mother': 'mom', 'name': 'FakestNumber',
                            'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        with_period = {'Name of Respondent': 'first last', 'Name of The Mother': 'mom', 'Name.': 'FakestNumber',
                            'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        with_comma = {'Name of Respondent': 'first last', 'Name of The Mother': 'mom', 'Name,': 'FakestNumber',
                            'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        with_space = {'Name of Respondent': 'first last', 'Name of The Mother': 'mom', 'Name ': 'FakestNumber',
                            'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        with_spaces = {'Name of Respondent': 'first last', 'Name of The Mother': 'mom', ' Name ': 'FakestNumber',
                                'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        with_the_lower = {'Name of Respondent': 'first last', 'Name of The Mother': 'mom', 'the name': 'FakestNumber',
                            'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        with_cap_the = {'Name of Respondent': 'first last', 'Name of The Mother': 'mom', 'The Name': 'FakestNumber',
                            'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        spaced_cap_the = {'Name of Respondent': 'first last', 'Name of The Mother': 'mom', '  The   Name': 'FakestNumber',
                            'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        
        name_of_child = {'Name of Respondent': 'first last', 'Name of The Mother': 'mom', 'Name of Child': 'James',
                            'Phone Number': '123456', 'Date of Birth': '2016-09-14', 'Delay in days': '1'}
        title_noc = {'Name of Respondent': 'first last', 'Name of The Mother': 'mom', 'Name Of Child': 'James',
                        'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        upper_noc = {'Name of Respondent': 'first last', 'Name of The Mother': 'mom', 'NAME OF CHILD': 'James',
                        'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        lower_noc = {'Name of Respondent': 'first last', 'Name of The Mother': 'mom', 'name of child': 'James',
                        'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        self.assertEqual("FakestNumber", check_all_headers(row=first_name_row, headers=name))
        self.assertEqual("FakestNumber", check_all_headers(row=name_of_child_row, headers=name))
        self.assertEqual("FakestNumber", check_all_headers(row=name_row, headers=name))
        self.assertEqual("FakestNumber", check_all_headers(row=lowercase, headers=name))
        self.assertEqual("FakestNumber", check_all_headers(row=with_period, headers=name))
        self.assertEqual("FakestNumber", check_all_headers(row=with_comma, headers=name))
        self.assertEqual("FakestNumber", check_all_headers(row=with_space, headers=name))
        self.assertEqual("FakestNumber", check_all_headers(row=with_spaces, headers=name))
        self.assertEqual("FakestNumber", check_all_headers(row=with_the_lower, headers=name))
        self.assertEqual("FakestNumber", check_all_headers(row=with_cap_the, headers=name))
        self.assertEqual("James", check_all_headers(row=name_of_child, headers=name))
        self.assertEqual("James", check_all_headers(row=title_noc, headers=name))
        self.assertEqual("James", check_all_headers(row=upper_noc, headers=name))
        self.assertEqual("James", check_all_headers(row=lower_noc, headers=name))
        self.assertEqual("123456", check_all_headers(row=name_of_child, headers=phone_number))
        self.assertEqual("1", check_all_headers(row=name_of_child, headers=delay_in_days))
        
        end_typo_alt_num_row = {'Name Of The Child': 'James', 'Phone Number': '123456', 'Alternate Mobile No': '0987654321'}
        begin_typo_alt_num_row = {'Name Of The Child': 'James', 'Phone Number': '123456', 'lternate Mobile No.': '0987654321'}
        self.assertEqual("0987654321", check_all_headers(row=end_typo_alt_num_row, headers=alt_phone_number))
        self.assertEqual("0987654321", check_all_headers(row=begin_typo_alt_num_row, headers=alt_phone_number))        

    def test_check_all_headers_returns_none_if_no_key_exists(self):
        name = ["Name", "First Name Of Child To Be Vaccinated", "Name of Child"]
        spaced_cap_the = {'Name of Respondent': 'first last', 'Name of The Mother': 'mom', '  The   Name': 'FakestNumber',
                            'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        extra_the = {'Name of Respondent': 'first last', 'Name of The Mother': 'mom', 'Name Of the Child': 'James',
                            'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        cap_extra_the = {'Name of Respondent': 'first last', 'Name of The Mother': 'mom', 'Name Of The Child': 'James',
                            'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        no_name_row = {'Name of Respondent': 'first last', 'Name of The Mother': 'mom', 'Phone Number': '123456', 'Date of Birth': '2016-09-14'}
        no_name_one_item_row = {'Phone Number': '123456'}
        self.assertIsNone(check_all_headers(row=spaced_cap_the, headers=name))
        self.assertIsNone(check_all_headers(row=extra_the, headers=name))
        self.assertIsNone(check_all_headers(row=cap_extra_the, headers=name))
        self.assertIsNone(check_all_headers(row=no_name_row, headers=name))
        self.assertIsNone(check_all_headers(row=no_name_one_item_row, headers=name))

    def test_check_all_headers_preserves_unicode_literals(self):
        name = ["Name", "First Name Of Child To Be Vaccinated", "Name of Child"]
        hin_unicode = {'Name of Respondent': 'first last', 'Name of The Mother': 'mom', 'Name': u'\\u0936\\u093f\\u0936\\u0941'}
        guj_unicode = {'Name of Respondent': 'first last', 'Name of The Mother': 'mom', 'Name': u'\\u0aa4\\u0aae\\u0abe\\u0ab0\\u0ac1\\u0a82'}
        unicode_with_space = {'Name of Respondent': 'first last', 'Name of The Mother': 'mom', 'Name': u'  \\u0aa4\\u0aae\\u0abe\\u0ab0\\u0ac1\\u0a82  '}
        self.assertEqual(u'\\u0936\\u093f\\u0936\\u0941', check_all_headers(row=hin_unicode, headers=name))
        self.assertEqual(u'\\u0aa4\\u0aae\\u0abe\\u0ab0\\u0ac1\\u0a82', check_all_headers(row=guj_unicode, headers=name))
        self.assertEqual(u'  \\u0aa4\\u0aae\\u0abe\\u0ab0\\u0ac1\\u0a82  ', check_all_headers(row=unicode_with_space, headers=name))

    def test_assign_org_signup(self):
        org_row = {'Org Sign Up': 'Parker', 'Name of The Mother': 'mom', 'Name': 'Kendra'}
        no_org_row = {'Name of The Mother': 'mom', 'Name': 'Kendra'}
        org_empty_row = {'Org Sign Up': '','Name of The Mother': 'mom', 'Name': 'Kendra'}
        self.assertEqual("Parker", assign_org_signup(row=org_row, source="TR"))
        self.assertFalse(assign_org_signup(row=no_org_row, source="TR"))
        self.assertEqual("TA", assign_org_signup(row=org_row, source="TA"))
        self.assertEqual("TA", assign_org_signup(row=no_org_row, source="TA"))
        self.assertEqual("Parker", assign_org_signup(row=org_row, source="tr"))
        self.assertEqual("Other".upper(), assign_org_signup(row=org_row, source="Other"))
        self.assertEqual("OTHER", assign_org_signup(row=org_row, source="OTHER"))
        self.assertEqual("other".upper(), assign_org_signup(row=org_row, source="other"))
        self.assertEqual("MPS", assign_org_signup(row=org_row, source="MPS"))
        self.assertEqual("MPS", assign_org_signup(row=org_empty_row, source="MPS"))
        self.assertFalse(assign_org_signup(row=org_empty_row, source="TR"))

    def test_assign_method_of_signup(self):
        maps = "Maps"
        maps_cap = "MAPS"
        maps_lower = "maps"
        maps_typo = "mps"
        hansa = "Hansa"
        wardha = "Wardha"
        other = "Other"
        another = "Another"
        door_method = {'Method of Sign Up': 'Door to Door', 'Name of The Mother': 'mom', 'Name': 'Kendra'}
        hospital = {'Method of Sign Up': 'Hospital', 'Name of The Mother': 'mom', 'Name': 'Kendra'}
        text_in = {'Method of Sign Up': 'Text', 'Name of The Mother': 'mom', 'Name': 'Kendra'}
        method_empty = {'Method of Sign Up': '', 'Name of The Mother': 'mom', 'Name': 'Kendra'}
        no_method_row = {'Name of The Mother': 'mom', 'Name': 'Kendra'}
        self.assertEqual("Door to Door", assign_method_of_signup(row=door_method, source=maps))
        self.assertEqual("Door to Door", assign_method_of_signup(row=method_empty, source=maps))
        self.assertEqual("Door to Door", assign_method_of_signup(row=method_empty, source=maps_cap))
        self.assertEqual("Door to Door", assign_method_of_signup(row=method_empty, source=maps_lower))
        self.assertEqual("Door to Door", assign_method_of_signup(row=method_empty, source=hansa))
        self.assertEqual("Door to Door", assign_method_of_signup(row=method_empty, source=hansa))
        self.assertFalse(assign_method_of_signup(row=method_empty, source=maps_typo))
        self.assertEqual("Door to Door", assign_method_of_signup(row=door_method, source=maps_typo))
        self.assertEqual("Hospital", assign_method_of_signup(row=method_empty, source=wardha))
        self.assertEqual("Hospital", assign_method_of_signup(row=door_method, source=wardha))
        self.assertEqual("Hospital", assign_method_of_signup(row=text_in, source=wardha))
        self.assertEqual("Hospital", assign_method_of_signup(row=no_method_row, source=wardha))
        self.assertFalse(assign_method_of_signup(row=no_method_row, source=other))
        self.assertFalse(assign_method_of_signup(row=no_method_row, source=another))
        self.assertEqual("Text", assign_method_of_signup(row=text_in, source=other))

    def test_assign_hospital_name(self):
        large = {'Hospital Name': 'Large', 'Name of The Mother': 'mom', 'Name': 'Kendra'}
        different = {'Hospital Name': 'Diff From Large', 'Name of The Mother': 'mom', 'Name': 'Kendra'}
        no_hospital_row = {'Name of The Mother': 'mom', 'Name': 'Kendra'}
        hospital_empty = {'Hospital Name': '', 'Name of The Mother': 'mom', 'Name': 'Kendra'}

        self.assertEqual("Wardha", assign_hospital_name(row=large, method_of_signup="Hospital", org_signup="Wardha"))
        self.assertEqual("Wardha".capitalize(), assign_hospital_name(row=large, method_of_signup="Hospital", org_signup="Wardha"))
        self.assertEqual("second".capitalize(), assign_hospital_name(row=large, method_of_signup="Hospital", org_signup="second"))
        self.assertEqual(large["Hospital Name"], assign_hospital_name(row=large, method_of_signup="Door to Door", org_signup="Wardha"))
        self.assertEqual(large["Hospital Name"], assign_hospital_name(row=large, method_of_signup="Door to Door", org_signup="second"))
        self.assertEqual(different["Hospital Name"], assign_hospital_name(row=different, method_of_signup="Door to Door", org_signup="second"))
        self.assertFalse(assign_hospital_name(row=hospital_empty, method_of_signup="Door to Door", org_signup="Wardha"))
        self.assertFalse(assign_hospital_name(row=no_hospital_row, method_of_signup="Door to Door", org_signup="Wardha"))
        self.assertFalse(assign_hospital_name(row=no_hospital_row, method_of_signup="Door to Door", org_signup="second"))

