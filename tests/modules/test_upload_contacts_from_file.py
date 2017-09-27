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
                                              parse_contact_time_references, assign_preg_signup, assign_preg_signup, \
                                              estimate_date_of_birth, filter_pregnancy_month, determine_language, \
                                              determine_mother_tongue, language_selector, replace_blank_name, \
                                              determine_name, matching_permutation, check_all_headers, \
                                              assign_org_signup, assign_method_of_signup, assign_hospital_name, \
                                              entry_or_empty_string, determine_date_of_birth, time_reference_or_none 
from modules.date_helper import add_or_subtract_days, add_or_subtract_months
from modules.i18n import hindi_placeholder_name, gujarati_placeholder_name
from dateutil.relativedelta import relativedelta
from six import u

def create_sample_contact(name, phone_number, date_of_birth):
    contact, created = Contact.objects.get_or_create(name=name, phone_number=phone_number,
        date_of_birth=date_of_birth)
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

class UploadContactsRelationshipTests(TestCase):
    def test_groups_are_assigned_to_contact(self):
        contact = create_sample_contact(name="Aaarsh", phone_number="911234567890",
                                        date_of_birth=datetime(2011, 5, 10, 0,0).date())
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
        contact = create_sample_contact(name="Aaarsh", phone_number="911234567890",
                                        date_of_birth=datetime(2011, 5, 10, 0,0).date())

        with self.assertRaises(Contact.DoesNotExist):
            group.contacts.get(id=contact.id)

        assign_groups_to_contact(contact, group_string)
        self.assertTrue(group.contacts.get(id=contact.id))

    def test_empty_group_strings(self):
        group_string = ""
        contact = create_sample_contact(name="Aaarsh", phone_number="911234567890",
                                        date_of_birth=datetime(2011, 5, 10, 0,0).date())
        assign_groups_to_contact(contact, group_string)

        with self.assertRaises(Group.DoesNotExist):
            contact.group_set.get(name__exact=group_string)


class UploadContactsInputParserTests(TestCase):
    @patch("modules.upload_contacts_from_file.check_all_headers")
    def test_nondigits_in_income(self, headers_mock):
        headers = ["Monthly Income"]
        row = {"Monthly Income": "WONT BE READ"}
        headers_mock.return_value = "1892ff8"
        self.assertEqual(monthly_income(row=row, headers=headers), 999999)
        headers_mock.return_value = "ghg18928"
        self.assertEqual(monthly_income(row=row, headers=headers), 999999)
        headers_mock.return_value = "18928ff"
        self.assertEqual(monthly_income(row=row, headers=headers), 999999)
        headers_mock.return_value = "18928-"
        self.assertEqual(monthly_income(row=row, headers=headers), 999999)
        headers_mock.return_value = "-18928"
        self.assertEqual(monthly_income(row=row, headers=headers), 999999)
        headers_mock.return_value = "+18928"
        self.assertEqual(monthly_income(row=row, headers=headers), 999999)
        headers_mock.return_value = "+18928"
        self.assertEqual(monthly_income(row=row, headers=headers), 999999)
        headers_mock.return_value = "18 928"
        self.assertEqual(monthly_income(row=row, headers=headers), 999999)
        headers_mock.return_value = "18,928"
        self.assertEqual(monthly_income(row=row, headers=headers), 999999)

    @patch("modules.upload_contacts_from_file.check_all_headers")
    def test_empty_income(self, headers_mock):
        headers = ["Monthly Income"]
        row = {"Monthly Income": "WONT BE READ"}
        headers_mock.return_value = ""
        self.assertEqual(monthly_income(row=row, headers=headers), 999999)
        headers_mock.return_value = " "
        self.assertEqual(monthly_income(row=row, headers=headers), 999999)
        headers_mock.return_value = None
        self.assertEqual(monthly_income(row=row, headers=headers), 999999)

    @patch("modules.upload_contacts_from_file.check_all_headers")
    def test_delay_normal_inputs(self, headers_mock):
        headers = ["Delay in days"]
        row = {"Delay in days": "WONT BE READ"}
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
        row = {"Delay in days": "WONT BE READ"}
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

    @patch("modules.upload_contacts_from_file.check_all_headers")
    def test_empty_previous_vaccination(self, headers_mock):
        headers = ["Previously had children vaccinated"]
        row = {"Previously had children vaccinated": "WONT BE READ"}
        headers_mock.return_value = None
        headers_mock.return_value = ""
        self.assertIsNone(previous_vaccination(row=row, headers=headers))
        headers_mock.return_value = ""
        self.assertIsNone(previous_vaccination(row=row, headers=headers))
        headers_mock.return_value = " "
        self.assertIsNone(previous_vaccination(row=row, headers=headers))
        headers_mock.return_value = "  "
        self.assertIsNone(previous_vaccination(row=row, headers=headers))

    @patch("modules.upload_contacts_from_file.check_all_headers")
    def test_previous_vaccination_positive(self, headers_mock):
        headers = ["Previously had children vaccinated"]
        row = {"Previously had children vaccinated": "WONT BE READ"}
        headers_mock.return_value = "y"
        self.assertEqual(True, previous_vaccination(row=row, headers=headers))
        headers_mock.return_value = "yes"
        self.assertEqual(True, previous_vaccination(row=row, headers=headers))
        headers_mock.return_value = "yes  "
        self.assertEqual(True, previous_vaccination(row=row, headers=headers))
        headers_mock.return_value = "yes asdfasfasf "
        self.assertEqual(True, previous_vaccination(row=row, headers=headers))
        headers_mock.return_value = "yn"
        self.assertEqual(True, previous_vaccination(row=row, headers=headers))

    @patch("modules.upload_contacts_from_file.check_all_headers")
    def test_previous_vaccination_negative(self, headers_mock):
        headers = ["Previously had children vaccinated"]
        row = {"Previously had children vaccinated": "WONT BE READ"}
        headers_mock.return_value = "n"
        self.assertEqual(False, previous_vaccination(row=row, headers=headers))
        headers_mock.return_value = "no"
        self.assertEqual(False, previous_vaccination(row=row, headers=headers))
        headers_mock.return_value = "no  "
        self.assertEqual(False, previous_vaccination(row=row, headers=headers))
        headers_mock.return_value = "no asdfasfasf "
        self.assertEqual(False, previous_vaccination(row=row, headers=headers))
        headers_mock.return_value = "ny"
        self.assertEqual(False, previous_vaccination(row=row, headers=headers))

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

    
    @patch("modules.upload_contacts_from_file.check_all_headers")
    def test_time_reference_or_none_real_datetimes(self, headers_mock):
        headers = ["Last Contacted"]
        row = {"Last Contacted": "WONT BE READ"}
        headers_mock.return_value = "6/12/2017 4:00:03 PM"
        self.assertEqual(datetime(2017, 6, 12, 16, 0, 3, tzinfo=timezone.get_default_timezone()),
            time_reference_or_none(row=row, headers=headers))
        headers_mock.return_value = "6/16/2017 6:51:28 PM"
        self.assertEqual(datetime(2017, 6, 16, 18, 51, 28, tzinfo=timezone.get_default_timezone()),
            time_reference_or_none(row=row, headers=headers))

    @patch("modules.upload_contacts_from_file.check_all_headers")
    def test_time_reference_or_none_fake_datetimes(self, headers_mock):
        headers = ["Last Contacted"]
        row = {"Last Contacted": "WONT BE READ"}
        headers_mock.return_value = "6/12/2017 25:00:03 PM"
        with self.assertRaises(ValueError):
            time_reference_or_none(row=row, headers=headers)
        headers_mock.return_value = "6/30/2017 16:51:28 PM"
        with self.assertRaises(ValueError):
            time_reference_or_none(row=row, headers=headers)

    @patch("modules.upload_contacts_from_file.check_all_headers")
    @freeze_time(datetime(2017, 7, 21, 0, 0).replace(tzinfo=timezone.get_default_timezone()))
    def test_time_reference_or_none_empty_times(self, headers_mock):
        headers = ["Last Contacted"]
        row = {"Last Contacted": "WONT BE READ"}
        headers_mock.return_value = ""
        self.assertIsNone(time_reference_or_none(row=row, headers=headers))

    @patch("modules.upload_contacts_from_file.check_all_headers")
    def test_parse_contact_time_references_real_datetimes(self, headers_mock):
        headers = ["Time Created"]
        row = {"Time Created": "WONT BE READ"}
        headers_mock.return_value = "6/12/2017 4:00:03 PM"
        self.assertEqual(datetime(2017, 6, 12, 16, 0, 3, tzinfo=timezone.get_default_timezone()),
            parse_contact_time_references(row=row, headers=headers))
        headers_mock.return_value = "6/16/2017 6:51:28 PM"
        self.assertEqual(datetime(2017, 6, 16, 18, 51, 28, tzinfo=timezone.get_default_timezone()),
            parse_contact_time_references(row=row, headers=headers))

    @patch("modules.upload_contacts_from_file.check_all_headers")
    def test_parse_contact_time_references_fake_datetimes(self, headers_mock):
        headers = ["Time Created"]
        row = {"Time Created": "WONT BE READ"}
        headers_mock.return_value = "6/12/2017 25:00:03 PM"
        with self.assertRaises(ValueError):
            parse_contact_time_references(row=row, headers=headers)
        headers_mock.return_value = "6/30/2017 16:51:28 PM"
        with self.assertRaises(ValueError):
            parse_contact_time_references(row=row, headers=headers)

    @patch("modules.upload_contacts_from_file.check_all_headers")
    @freeze_time(datetime(2017, 7, 21, 0, 0).replace(tzinfo=timezone.get_default_timezone()))
    def test_parse_contact_time_references_empty_times(self, headers_mock):
        headers = ["Time Created"]
        row = {"Time Created": "WONT BE READ"}
        headers_mock.return_value = ""
        self.assertEqual(datetime.now().replace(tzinfo=timezone.get_default_timezone()),
            parse_contact_time_references(row=row, headers=headers))

    @freeze_time(datetime(2017, 7, 21, 0, 0).replace(tzinfo=timezone.get_default_timezone()))
    @patch("modules.upload_contacts_from_file.entry_or_empty_string")
    def test_assign_preg_signup(self, headers_mock):
        headers = ["Pregnant Signup", "Pregnant women  Yes=1, No=2", "Segment", "Pregnant women"]
        row = {"Segment": "WONT BE READ"}
        headers_mock.return_value = "True"
        self.assertTrue(assign_preg_signup(row=row, headers=headers))
        headers_mock.return_value = "T"
        self.assertTrue(assign_preg_signup(row=row, headers=headers))
        headers_mock.return_value = "t"
        self.assertTrue(assign_preg_signup(row=row, headers=headers))
        headers_mock.return_value = "to"
        self.assertTrue(assign_preg_signup(row=row, headers=headers))
        headers_mock.return_value = "1"
        self.assertTrue(assign_preg_signup(row=row, headers=headers))
        headers_mock.return_value = "Pregnant women"
        self.assertTrue(assign_preg_signup(row=row, headers=headers))
        headers_mock.return_value = "Pregnant"
        self.assertTrue(assign_preg_signup(row=row, headers=headers))
        headers_mock.return_value = "pregnant"
        self.assertTrue(assign_preg_signup(row=row, headers=headers))
        headers_mock.return_value = "nonsense pregnant adsoifasfd"
        self.assertTrue(assign_preg_signup(row=row, headers=headers))
        headers_mock.return_value = "False"
        self.assertFalse(assign_preg_signup(row=row, headers=headers))
        headers_mock.return_value = "F"
        self.assertFalse(assign_preg_signup(row=row, headers=headers))
        headers_mock.return_value = "f"
        self.assertFalse(assign_preg_signup(row=row, headers=headers))
        headers_mock.return_value = "fo"
        self.assertFalse(assign_preg_signup(row=row, headers=headers))
        headers_mock.return_value = ""
        self.assertFalse(assign_preg_signup(row=row, headers=headers))
        headers_mock.return_value = " "
        self.assertFalse(assign_preg_signup(row=row, headers=headers))
        headers_mock.return_value = "0"
        self.assertFalse(assign_preg_signup(row=row, headers=headers))
        headers_mock.return_value = "2"
        self.assertFalse(assign_preg_signup(row=row, headers=headers))
        headers_mock.return_value = "Below one years child"
        self.assertFalse(assign_preg_signup(row=row, headers=headers))

    @freeze_time(datetime(2017, 7, 21, 0, 0))
    def test_estimate_date_of_birth(self):
        freeze_time_date = datetime.now().date()
        five_months_ago = add_or_subtract_months(date=freeze_time_date, num_of_months=-5)
        five_months_plus_preg_time = add_or_subtract_days(date=five_months_ago, num_of_days=280)
        zero_month = freeze_time_date + relativedelta(months=-0) + relativedelta(days=280)
        one_month = freeze_time_date + relativedelta(months=-1) + relativedelta(days=280)
        two_months = freeze_time_date + relativedelta(months=-2) + relativedelta(days=280)
        three_months = freeze_time_date + relativedelta(months=-3) + relativedelta(days=280)
        four_months = freeze_time_date + relativedelta(months=-4) + relativedelta(days=280)
        five_months = freeze_time_date + relativedelta(months=-5) + relativedelta(days=280)
        six_months = freeze_time_date + relativedelta(months=-6) + relativedelta(days=280)
        seven_months = freeze_time_date + relativedelta(months=-7) + relativedelta(days=280)
        eight_months = freeze_time_date + relativedelta(months=-8) + relativedelta(days=280)
        nine_months = freeze_time_date + relativedelta(months=-9) + relativedelta(days=280)
        self.assertEqual(zero_month, estimate_date_of_birth(month_of_pregnancy=0, date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(one_month, estimate_date_of_birth(month_of_pregnancy=1, date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(two_months, estimate_date_of_birth(month_of_pregnancy=2, date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(three_months, estimate_date_of_birth(month_of_pregnancy=3, date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(four_months, estimate_date_of_birth(month_of_pregnancy=4, date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(five_months, estimate_date_of_birth(month_of_pregnancy=5, date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(six_months, estimate_date_of_birth(month_of_pregnancy=6, date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(seven_months, estimate_date_of_birth(month_of_pregnancy=7, date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(eight_months, estimate_date_of_birth(month_of_pregnancy=8, date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(nine_months, estimate_date_of_birth(month_of_pregnancy=9, date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(five_months_plus_preg_time, estimate_date_of_birth(month_of_pregnancy=5, date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))

    def test_estimate_date_of_birth_rejects_nonnumbers(self):
        self.assertEqual(None, estimate_date_of_birth(month_of_pregnancy=None, date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(None, estimate_date_of_birth(month_of_pregnancy="Five", date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(None, estimate_date_of_birth(month_of_pregnancy="Ten", date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(None, estimate_date_of_birth(month_of_pregnancy="", date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(None, estimate_date_of_birth(month_of_pregnancy=" ", date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))
        self.assertEqual(None, estimate_date_of_birth(month_of_pregnancy="_!", date_of_sign_up=datetime(2017, 7, 21, 0, 0).date()))

    @patch("modules.upload_contacts_from_file.entry_or_empty_string")
    def test_filter_pregnancy_month(self, headers_mock):
        headers = ["Current Month Of Pregnancy", "Month of Pregnancy"]
        row = {"Current Month Of Pregnancy": "DOESNT MATTER"}
        headers_mock.return_value = "Five"
        self.assertEqual(None, filter_pregnancy_month(row=row, headers=headers))
        headers_mock.return_value = "Ten"
        self.assertEqual(None, filter_pregnancy_month(row=row, headers=headers))
        headers_mock.return_value = " "
        self.assertEqual(None, filter_pregnancy_month(row=row, headers=headers))
        headers_mock.return_value = ""
        self.assertEqual(None, filter_pregnancy_month(row=row, headers=headers))
        headers_mock.return_value = "_ *"
        self.assertEqual(None, filter_pregnancy_month(row=row, headers=headers))
        headers_mock.return_value = "Let'em see"
        self.assertEqual(None, filter_pregnancy_month(row=row, headers=headers))
        headers_mock.return_value = "0"
        self.assertEqual(0, filter_pregnancy_month(row=row, headers=headers))
        headers_mock.return_value = "1"
        self.assertEqual(1, filter_pregnancy_month(row=row, headers=headers))
        headers_mock.return_value = "2"
        self.assertEqual(2, filter_pregnancy_month(row=row, headers=headers))
        headers_mock.return_value = "5"
        self.assertEqual(5, filter_pregnancy_month(row=row, headers=headers))
        headers_mock.return_value = "9"
        self.assertEqual(9, filter_pregnancy_month(row=row, headers=headers))

    @patch("modules.upload_contacts_from_file.entry_or_empty_string")
    def test_filter_pregnancy_month_handles_typos(self, headers_mock):
        headers = ["Current Month Of Pregnancy", "Month of Pregnancy"]
        row = {"Current Month Of Pregnancy": "DOESNT MATTER"}
        headers_mock.return_value = "10"
        self.assertEqual(1, filter_pregnancy_month(row=row, headers=headers))
        headers_mock.return_value = "11"
        self.assertEqual(1, filter_pregnancy_month(row=row, headers=headers))
        headers_mock.return_value = "22"
        self.assertEqual(2, filter_pregnancy_month(row=row, headers=headers))
        headers_mock.return_value = "2s"
        self.assertEqual(2, filter_pregnancy_month(row=row, headers=headers))
        headers_mock.return_value = "300"
        self.assertEqual(3, filter_pregnancy_month(row=row, headers=headers))
        headers_mock.return_value = "004"
        self.assertEqual(4, filter_pregnancy_month(row=row, headers=headers))
        headers_mock.return_value = "0040"
        self.assertEqual(4, filter_pregnancy_month(row=row, headers=headers))
        headers_mock.return_value = "99"
        self.assertEqual(9, filter_pregnancy_month(row=row, headers=headers))
        headers_mock.return_value = "-2"
        self.assertEqual(2, filter_pregnancy_month(row=row, headers=headers))
        headers_mock.return_value = "-22"
        self.assertEqual(2, filter_pregnancy_month(row=row, headers=headers))
        headers_mock.return_value = "002"
        self.assertEqual(2, filter_pregnancy_month(row=row, headers=headers))
        headers_mock.return_value = "2adgasdfasdf"
        self.assertEqual(2, filter_pregnancy_month(row=row, headers=headers))
        headers_mock.return_value = "8m"
        self.assertEqual(8, filter_pregnancy_month(row=row, headers=headers))
        headers_mock.return_value = "8_"
        self.assertEqual(8, filter_pregnancy_month(row=row, headers=headers))
        headers_mock.return_value = "9  "
        self.assertEqual(9, filter_pregnancy_month(row=row, headers=headers))
        headers_mock.return_value = "  9"
        self.assertEqual(9, filter_pregnancy_month(row=row, headers=headers))
        headers_mock.return_value = "  9   "
        self.assertEqual(9, filter_pregnancy_month(row=row, headers=headers))

    
    @freeze_time(datetime(2017, 7, 21, 0, 0))
    @patch("modules.upload_contacts_from_file.entry_or_empty_string")
    @patch("modules.upload_contacts_from_file.filter_pregnancy_month")
    def test_determine_date_of_birth_only_estimates_date_of_birth_when_no_dob_entry_and_preg_signup_is_true(self, mock_pregnancy_month, mock_dob_entry):
        frozen_date = datetime.now().date()
        dob_headers = ["Date of Birth", "Date Of Birth Of The Child",
                            "Date of Birth of Child (dd/mm/yyyy)", "Date of Birth of Child"]
        month_headers = ["Current Month Of Pregnancy", "Month of Pregnancy"]
        row = {"Current Month Of Pregnancy": "WONT BE READ", "Date of Birth": "2015-01-01"}
        mock_dob_entry.return_value = "2015-01-01"
        mock_pregnancy_month.return_value = 1
        self.assertEqual(datetime(2015, 1, 1).date(), determine_date_of_birth(row=row, dob_headers=dob_headers, month_headers=month_headers,
            date_of_signup=frozen_date, preg_signup=False, source="TR"))
        mock_pregnancy_month.assert_not_called()
        row = {"Current Month Of Pregnancy": "WONT BE READ", "Date of Birth": "10-20-2015"}
        self.assertEqual(datetime(2015, 10, 20).date(), determine_date_of_birth(row=row, dob_headers=dob_headers, month_headers=month_headers,
            date_of_signup=frozen_date, preg_signup=False, source="TR"))
        mock_pregnancy_month.assert_not_called()

        row = {"Current Month Of Pregnancy": "WONT BE READ", "Date of Birth": ""}
        mock_dob_entry.return_value = ""
        with self.assertRaises(AttributeError):
            determine_date_of_birth(row=row, dob_headers=dob_headers, month_headers=month_headers,
                date_of_signup=frozen_date, preg_signup=False, source="TR")
        mock_pregnancy_month.assert_not_called()

        row = {"Current Month Of Pregnancy": "WONT BE READ", "Date of Birth": "2015-01-01"}
        mock_dob_entry.return_value = "2015-01-01"
        mock_pregnancy_month.return_value = 1
        one_month = frozen_date + relativedelta(months=-1) + relativedelta(days=280)
        self.assertEqual(datetime(2015, 1, 1).date(), determine_date_of_birth(row=row, dob_headers=dob_headers, month_headers=month_headers,
                date_of_signup=frozen_date, preg_signup=True, source="TR"))
        mock_pregnancy_month.assert_not_called()

        row = {"Current Month Of Pregnancy": "WONT BE READ", "Date of Birth": "WONT BE READ"}
        mock_dob_entry.return_value = ""
        mock_pregnancy_month.return_value = 1
        one_month = frozen_date + relativedelta(months=-1) + relativedelta(days=280)
        self.assertEqual(one_month, determine_date_of_birth(row=row, dob_headers=dob_headers, month_headers=month_headers,
                date_of_signup=frozen_date, preg_signup=True, source="TR"))
        mock_pregnancy_month.assert_called_once_with(row=row, headers=month_headers)

    @freeze_time(datetime(2017, 7, 21, 0, 0))
    @patch("modules.upload_contacts_from_file.entered_date_string_to_date")
    @patch("modules.upload_contacts_from_file.entry_or_empty_string")
    @patch("modules.upload_contacts_from_file.filter_pregnancy_month")
    def test_determine_date_of_birth_returns_correct_date_of_birth_when_no_date_of_birth_given(self, mock_pregnancy_month, mock_dob_entry, mock_dob_date):
        frozen_date = datetime.now().date()
        dob_headers = ["Date of Birth", "Date Of Birth Of The Child",
                            "Date of Birth of Child (dd/mm/yyyy)", "Date of Birth of Child"]
        month_headers = ["Current Month Of Pregnancy", "Month of Pregnancy"]
        row = {"Current Month Of Pregnancy": "WONT BE READ", "Date of Birth": "WONT BE READ"}
        mock_dob_entry.return_value = ""
        mock_pregnancy_month.return_value = 1
        one_month = frozen_date + relativedelta(months=-1) + relativedelta(days=280)
        self.assertEqual(one_month, determine_date_of_birth(row=row, dob_headers=dob_headers, month_headers=month_headers,
                date_of_signup=frozen_date, preg_signup=True, source="TR"))
        mock_pregnancy_month.assert_called_once_with(row=row, headers=month_headers)

        mock_pregnancy_month.return_value = 2
        two_months = frozen_date + relativedelta(months=-2) + relativedelta(days=280)
        self.assertEqual(two_months, determine_date_of_birth(row=row, dob_headers=dob_headers, month_headers=month_headers,
                date_of_signup=frozen_date, preg_signup=True, source="TR"))

        mock_pregnancy_month.return_value = 0
        zero_months = frozen_date + relativedelta(months=-0) + relativedelta(days=280)
        self.assertEqual(zero_months, determine_date_of_birth(row=row, dob_headers=dob_headers, month_headers=month_headers,
                date_of_signup=frozen_date, preg_signup=True, source="TR"))

        mock_pregnancy_month.return_value = 5
        five_months = frozen_date + relativedelta(months=-5) + relativedelta(days=280)
        self.assertEqual(five_months, determine_date_of_birth(row=row, dob_headers=dob_headers, month_headers=month_headers,
                date_of_signup=frozen_date, preg_signup=True, source="TR"))

        mock_pregnancy_month.return_value = 8
        eight_months = frozen_date + relativedelta(months=-8) + relativedelta(days=280)
        self.assertEqual(eight_months, determine_date_of_birth(row=row, dob_headers=dob_headers, month_headers=month_headers,
                date_of_signup=frozen_date, preg_signup=True, source="TR"))
        
        mock_pregnancy_month.return_value = 9
        nine_months = frozen_date + relativedelta(months=-9) + relativedelta(days=280)
        self.assertEqual(nine_months, determine_date_of_birth(row=row, dob_headers=dob_headers, month_headers=month_headers,
                date_of_signup=frozen_date, preg_signup=True, source="TR"))

        mock_dob_date.assert_not_called()

    @freeze_time(datetime(2017, 7, 21, 0, 0))
    @patch("modules.upload_contacts_from_file.filter_pregnancy_month")
    def test_determine_date_of_birth_returns_correct_date_of_birth_when_date_of_birth_is_given(self, mock_pregnancy_month):
        frozen_date = datetime.now().date()
        dob_headers = ["Date of Birth", "Date Of Birth Of The Child",
                            "Date of Birth of Child (dd/mm/yyyy)", "Date of Birth of Child"]
        month_headers = ["Current Month Of Pregnancy", "Month of Pregnancy"]
        row = {"Current Month Of Pregnancy": "WONT BE READ", "Date of Birth": "2015-01-01"}
        mock_pregnancy_month.return_value = 0
        self.assertEqual(datetime(2015, 1, 1).date(), determine_date_of_birth(row=row, dob_headers=dob_headers, month_headers=month_headers,
            date_of_signup=frozen_date, preg_signup=False, source="TR"))

        row = {"Current Month Of Pregnancy": "WONT BE READ", "Date of Birth": "2017-10-25"}
        self.assertEqual(datetime(2017, 10, 25).date(), determine_date_of_birth(row=row, dob_headers=dob_headers, month_headers=month_headers,
            date_of_signup=frozen_date, preg_signup=False, source="TR"))
        self.assertEqual(datetime(2017, 10, 25).date(), determine_date_of_birth(row=row, dob_headers=dob_headers, month_headers=month_headers,
            date_of_signup=frozen_date, preg_signup=False, source="MPS"))

        row = {"Current Month Of Pregnancy": "WONT BE READ", "Date of Birth": "10-25-2017"}
        self.assertEqual(datetime(2017, 10, 25).date(), determine_date_of_birth(row=row, dob_headers=dob_headers, month_headers=month_headers,
            date_of_signup=frozen_date, preg_signup=False, source="TR"))

        row = {"Current Month Of Pregnancy": "WONT BE READ", "Date of Birth": "25-10-2017"}
        self.assertEqual(datetime(2017, 10, 25).date(), determine_date_of_birth(row=row, dob_headers=dob_headers, month_headers=month_headers,
            date_of_signup=frozen_date, preg_signup=False, source="MPS"))

        row = {"Current Month Of Pregnancy": "WONT BE READ", "Date of Birth": "14-08-2016"}
        self.assertEqual(datetime(2016, 8, 14).date(), determine_date_of_birth(row=row, dob_headers=dob_headers, month_headers=month_headers,
            date_of_signup=frozen_date, preg_signup=False, source="OTHER"))

        row = {"Current Month Of Pregnancy": "WONT BE READ", "Date of Birth": "30-05-2016"}
        self.assertEqual(datetime(2016, 5, 30).date(), determine_date_of_birth(row=row, dob_headers=dob_headers, month_headers=month_headers,
            date_of_signup=frozen_date, preg_signup=False, source="OTHER"))

        row = {"Current Month Of Pregnancy": "WONT BE READ", "Date of Birth": "30-05-2020"}
        self.assertEqual(datetime(2020, 5, 30).date(), determine_date_of_birth(row=row, dob_headers=dob_headers, month_headers=month_headers,
            date_of_signup=frozen_date, preg_signup=False, source="OTHER"))

        mock_pregnancy_month.assert_not_called()

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
        self.assertEqual("", determine_mother_tongue(row=mother_tongue_row, headers=mother_options))
        headers_mock.return_value = "7"
        self.assertEqual("", determine_mother_tongue(row=mother_tongue_row, headers=mother_options))
        headers_mock.return_value = "None"
        self.assertEqual("", determine_mother_tongue(row=mother_tongue_row, headers=mother_options))
        headers_mock.return_value = ""
        self.assertEqual("", determine_mother_tongue(row=mother_tongue_row, headers=mother_options))
        headers_mock.return_value = " "
        self.assertEqual("", determine_mother_tongue(row=mother_tongue_row, headers=mother_options))
        headers_mock.return_value = u"\\u0923\\u09a1"
        self.assertEqual("", determine_mother_tongue(row=mother_tongue_row, headers=mother_options))

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
        self.assertEqual("More stuff", language_selector(language_input=u"\\u0923\\u09a1", options=options_two,
                            default_option="More stuff", none_option="Hindi"))

    def test_replace_blank_name(self):
        self.assertEqual("Your child", replace_blank_name(name=None, language="English"))
        self.assertEqual("Your child", replace_blank_name(name="", language="English"))
        self.assertEqual("Your child", replace_blank_name(name=" ", language="English"))
        self.assertEqual("Your child", replace_blank_name(name="     ", language="English"))
        self.assertEqual("Harvey", replace_blank_name(name="Harvey", language="English"))
        self.assertEqual(u"\u0906\u092a\u0915\u093e", replace_blank_name(name=u"\u0906\u092a\u0915\u093e", language="English"))
        self.assertEqual(hindi_placeholder_name(), replace_blank_name(name=None, language="Hindi"))
        self.assertEqual(hindi_placeholder_name(), replace_blank_name(name=" ", language="Hindi"))
        self.assertEqual(hindi_placeholder_name(), replace_blank_name(name=" ", language="Hindi"))
        self.assertEqual(hindi_placeholder_name(), replace_blank_name(name="    ", language="Hindi"))
        self.assertEqual(u"\u0906\u092a\u0915\u093e", replace_blank_name(name=u"\u0906\u092a\u0915\u093e", language="Hindi"))
        self.assertEqual(u"\u0936\u093f\u0936\u0941", replace_blank_name(name=u"\u0936\u093f\u0936\u0941", language="Hindi"))
        self.assertEqual("Aarav", replace_blank_name(name="Aarav", language="Hindi"))
        self.assertEqual("Aditya", replace_blank_name(name="Aditya", language="Hindi"))
        self.assertEqual(gujarati_placeholder_name(), replace_blank_name(name=None, language="Gujarati"))
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

    @patch("modules.upload_contacts_from_file.entry_or_empty_string")
    def test_assign_org_signup(self, headers_mock):
        headers = ["Org Sign Up"]
        row = {"Org Sign Up": "WONT BE READ"}
        headers_mock.return_value = "Parker"
        self.assertEqual("Parker", assign_org_signup(row=row, headers=headers, source="TR"))
        self.assertEqual("TA", assign_org_signup(row=row, headers=headers, source="TA"))
        self.assertEqual("TA", assign_org_signup(row=row, headers=headers, source="Ta"))
        headers_mock.return_value = ""
        self.assertEqual("", assign_org_signup(row=row, headers=headers, source="TR"))
        self.assertEqual("TA", assign_org_signup(row=row, headers=headers, source="TA"))
        self.assertEqual("TA", assign_org_signup(row=row, headers=headers, source="Ta"))
        headers_mock.return_value = "Other"
        self.assertEqual("Other", assign_org_signup(row=row, headers=headers, source="TR"))
        self.assertEqual("OTHER", assign_org_signup(row=row, headers=headers, source="Other"))
        self.assertEqual("MPS", assign_org_signup(row=row, headers=headers, source="Mps"))

    @patch("modules.upload_contacts_from_file.entry_or_empty_string")
    def test_assign_method_of_signup(self, headers_mock):
        headers = ["Method of Sign Up"]
        row = {"Method of Sign Up": "WONT BE READ"}
        headers_mock.return_value = "Other"
        self.assertEqual("Door to Door", assign_method_of_signup(row=row, headers=headers, source="Maps"))
        self.assertEqual("Door to Door", assign_method_of_signup(row=row, headers=headers, source="maps"))
        self.assertEqual("Door to Door", assign_method_of_signup(row=row, headers=headers, source="MAPS"))
        self.assertEqual("Door to Door", assign_method_of_signup(row=row, headers=headers, source="HANSA"))
        self.assertEqual("Door to Door", assign_method_of_signup(row=row, headers=headers, source="Hansa"))
        self.assertEqual("Door to Door", assign_method_of_signup(row=row, headers=headers, source="hansa"))
        headers_mock.return_value = ""
        self.assertEqual("Door to Door", assign_method_of_signup(row=row, headers=headers, source="Maps"))
        self.assertEqual("Door to Door", assign_method_of_signup(row=row, headers=headers, source="Hansa"))
        headers_mock.return_value = "Door to Door"
        self.assertEqual("Door to Door", assign_method_of_signup(row=row, headers=headers, source="mps"))
        self.assertEqual("Door to Door", assign_method_of_signup(row=row, headers=headers, source="hnsa"))
        self.assertEqual("Door to Door", assign_method_of_signup(row=row, headers=headers, source="hnsa"))
        headers_mock.return_value = "Other"
        self.assertEqual("Hospital", assign_method_of_signup(row=row, headers=headers, source="Wardha"))
        self.assertEqual("Hospital", assign_method_of_signup(row=row, headers=headers, source="wardha"))
        self.assertEqual("Hospital", assign_method_of_signup(row=row, headers=headers, source="WARDHA"))
        headers_mock.return_value = "Hospital"
        self.assertEqual("Hospital", assign_method_of_signup(row=row, headers=headers, source="TR"))
        self.assertEqual("Hospital", assign_method_of_signup(row=row, headers=headers, source="LARGE"))
        headers_mock.return_value = ""
        self.assertEqual("", assign_method_of_signup(row=row, headers=headers, source="TR"))
        self.assertEqual("", assign_method_of_signup(row=row, headers=headers, source="hnsa"))
        headers_mock.return_value = "Online Form"
        self.assertEqual("Online Form", assign_method_of_signup(row=row, headers=headers, source="TR"))
        self.assertEqual("Online Form", assign_method_of_signup(row=row, headers=headers, source="hnsa"))
        self.assertEqual("Online Form", assign_method_of_signup(row=row, headers=headers, source="mps"))
        self.assertEqual("Online Form", assign_method_of_signup(row=row, headers=headers, source="mps"))
        self.assertEqual("Online Form", assign_method_of_signup(row=row, headers=headers, source="ANOTHER"))
        headers_mock.return_value = "Text"
        self.assertEqual("Text", assign_method_of_signup(row=row, headers=headers, source="TR"))
        self.assertEqual("Text", assign_method_of_signup(row=row, headers=headers, source="hnsa"))
        self.assertEqual("Text", assign_method_of_signup(row=row, headers=headers, source="mps"))
        self.assertEqual("Text", assign_method_of_signup(row=row, headers=headers, source="ANOTHER"))

    @patch("modules.upload_contacts_from_file.entry_or_empty_string")
    def test_assign_hospital_name(self, headers_mock):
        headers = ["Hospital Name"]
        row = {"Hospital Name": "WONT BE READ"}
        headers_mock.return_value = "Other"
        self.assertEqual("Wardha", assign_hospital_name(row=row, headers=headers, method_of_signup="Hospital", org_signup="Wardha"))
        self.assertEqual("Wardha".capitalize(), assign_hospital_name(row=row, headers=headers, method_of_signup="Hospital", org_signup="Wardha"))
        self.assertEqual("second".capitalize(), assign_hospital_name(row=row, headers=headers, method_of_signup="Hospital", org_signup="second"))
        headers_mock.return_value = "Wardha"
        self.assertEqual("Wardha", assign_hospital_name(row=row, headers=headers, method_of_signup="Hospital", org_signup="Wardha"))
        self.assertEqual("Wardha".capitalize(), assign_hospital_name(row=row, headers=headers, method_of_signup="Hospital", org_signup="Wardha"))
        self.assertEqual("second".capitalize(), assign_hospital_name(row=row, headers=headers, method_of_signup="Hospital", org_signup="second"))
        headers_mock.return_value = "Other"
        self.assertEqual("Other", assign_hospital_name(row=row, headers=headers, method_of_signup="Door to Door", org_signup="Wardha"))
        self.assertEqual("Other", assign_hospital_name(row=row, headers=headers, method_of_signup="Door to Door", org_signup="second"))
        self.assertEqual("Other", assign_hospital_name(row=row, headers=headers, method_of_signup="Door to Door", org_signup="second"))
        headers_mock.return_value = ""
        self.assertEqual("", assign_hospital_name(row=row, headers=headers, method_of_signup="Door to Door", org_signup="Wardha"))
        self.assertEqual("", assign_hospital_name(row=row, headers=headers, method_of_signup="Door to Door", org_signup="Wardha"))
        self.assertEqual("", assign_hospital_name(row=row, headers=headers, method_of_signup="Door to Door", org_signup="second"))

    @patch("modules.upload_contacts_from_file.check_all_headers")
    def test_entry_or_empty_string(self, headers_mock):
        headers = ["NONSENSE"]
        row = {'key_one': 'value', 'key_two': 'value_two'}

        headers_mock.return_value = None
        self.assertEqual("", entry_or_empty_string(row=row, headers=headers))
        self.assertIsInstance(entry_or_empty_string(row=row, headers=headers), str)
        headers_mock.return_value = " "
        self.assertEqual(" ", entry_or_empty_string(row=row, headers=headers))
        headers_mock.return_value = 0
        self.assertEqual(0, entry_or_empty_string(row=row, headers=headers))
        headers_mock.return_value = []
        self.assertEqual([], entry_or_empty_string(row=row, headers=headers))
        headers_mock.return_value = {}
        self.assertEqual({}, entry_or_empty_string(row=row, headers=headers))
        headers_mock.return_value = set()
        self.assertEqual(set(), entry_or_empty_string(row=row, headers=headers))
        headers_mock.return_value = False
        self.assertEqual(False, entry_or_empty_string(row=row, headers=headers))
        headers_mock.return_value = True
        self.assertEqual(True, entry_or_empty_string(row=row, headers=headers))
        headers_mock.return_value = "String"
        self.assertEqual("String", entry_or_empty_string(row=row, headers=headers))
        headers_mock.return_value = datetime(2016, 1, 1).date()
        self.assertEqual(datetime(2016, 1, 1).date(), entry_or_empty_string(row=row, headers=headers))
        headers_mock.return_value = datetime(2016, 1, 1)
        self.assertEqual(datetime(2016, 1, 1), entry_or_empty_string(row=row, headers=headers))
        headers_mock.return_value = 10
        self.assertEqual(10, entry_or_empty_string(row=row, headers=headers))