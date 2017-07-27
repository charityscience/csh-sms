from __future__ import unicode_literals
import os
import csv
import tempfile
from django.test import TestCase

from freezegun import freeze_time
from datetime import datetime
from django.utils import timezone
from management.models import Contact, Group
from modules.utils import phone_number_is_valid
from modules.upload_contacts_from_file import csv_upload, make_contact_dict, assign_groups_to_contact, \
                                              previous_vaccination, monthly_income, parse_or_create_delay_num, \
                                              entered_date_string_to_date, parse_or_create_functional_dob, \
                                              parse_contact_time_references

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
            csv_upload("none.csv")

    def test_non_csv_file(self):
        fake_txt_path = os.path.join(tempfile.gettempdir(), "fake.txt")
        with self.assertRaises(IOError):
            csv_upload(fake_txt_path)

    def test_processes_csv(self):
        csv_path = "tests/data/example.csv" 
        csv_upload(csv_path)


class UploadContactsContactFieldsTests(TestCase):
    def upload_file(self):
        csv_path = "tests/data/example.csv" 
        csv_upload(csv_path)        

    def test_existing_contacts_are_updated(self):
        old_contact = create_sample_contact()

        self.upload_file()
        updated_contact = Contact.objects.get(name=old_contact.name, phone_number=old_contact.phone_number)
        self.assertNotEqual(old_contact.date_of_birth, updated_contact.date_of_birth)

    def test_new_contacts_are_created(self):
        old_all_contacts = Contact.objects.all()
        old_contacts_count = Contact.objects.count()
        self.upload_file()
        new_all_contacts = Contact.objects.all()
        new_contacts_count = Contact.objects.count()
        self.assertNotEqual(old_all_contacts, new_all_contacts)
        self.assertNotEqual(old_contacts_count, new_contacts_count)

    def test_only_contacts_with_valid_numbers_created(self):
    	"""tests/data/example.csv file being tested contains
    	   a contact with name: FakestNumber and phone number: 511234567890"""
    	self.upload_file()
    	with self.assertRaises(Contact.DoesNotExist):
    		Contact.objects.get(name="FakestNumber")

    def test_hindi_names_are_preserved(self):
        """tests/data/example.csv file being tested contains
           a contact with name: \u0906\u0930\u0935 and phone number: 912222277777"""
        hindi_name = u'\\u0906\\u0930\\u0935'
        self.upload_file()
        hin_contact = Contact.objects.get(phone_number="912222277777")
        self.assertNotEqual(hindi_name, hin_contact.name)
        self.assertTrue("\\" not in hin_contact.name)
        self.assertEqual(hindi_name.encode("utf-8").decode('unicode-escape'), hin_contact.name)

    def test_gujarati_names_are_preserved(self):
        """tests/data/example.csv file being tested contains
           a contact with name: \u0A90\u0AC5\u0A94 and phone number: 915555511111"""
        guj_name = u'\\u0A90\\u0AC5\\u0A94'
        self.upload_file()
        guj_contact = Contact.objects.get(phone_number="915555511111")
        self.assertNotEqual(guj_name, guj_contact.name)
        self.assertTrue("\\" not in guj_contact.name)
        self.assertEqual(guj_name.encode("utf-8").decode('unicode-escape'), guj_contact.name)

    def test_unicode_literal_names_are_encoded(self):
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
            parse_or_create_functional_dob("40-15-2015", "40-15-2015", 0)
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob("30-15-2015", "30-15-2015", 0)
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob("12-35-2015", "12-35-2015", 0)
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob("2014-20-15", "2014-20-15", 0)
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob("12-00-2015", "12-00-2015", 0)
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob("20000-20-15", "0000-20-15", 0)
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob("2014-35-00", "2014-35-00", 0)
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob("2016-12-40", "2016-12-40", 0)
        with self.assertRaises(ValueError):
            parse_or_create_functional_dob("2017-02-40", "2017-02-40", 0)

    def test_nonexistent_dates_for_parse_or_create_functional_dob(self):
        with self.assertRaises(TypeError):
            parse_or_create_functional_dob(row_entry="", date_of_birth="", delay=0)

        parsed_func_dob = parse_or_create_functional_dob(row_entry="", date_of_birth=datetime(2015, 10, 15,0,0).date(), delay=0)
        parsed_func_dob2 = parse_or_create_functional_dob(row_entry="", date_of_birth=datetime(2015, 10, 15,0,0).date(), delay=5)
        
        self.assertEqual(parsed_func_dob, datetime(2015, 10, 15).date())
        self.assertEqual(parsed_func_dob2, datetime(2015, 10, 20).date())

    def test_real_dates_for_parse_or_create_functional_dob(self):
        parsed_func_dob1 = parse_or_create_functional_dob(row_entry="10-15-2015",
        	date_of_birth=datetime(2015, 10, 15,0,0).date(), delay=0)
        parsed_func_dob2 = parse_or_create_functional_dob(row_entry="10-18-2015",
        	date_of_birth=datetime(2015, 10, 15,0,0).date(), delay=3)
        
        self.assertEqual(parsed_func_dob1, datetime(2015, 10, 15).date())
        self.assertEqual(parsed_func_dob2, datetime(2015, 10, 18).date())

    def test_nonexistent_dates_for_entered_date_string_to_date(self):
        with self.assertRaises(ValueError):
            entered_date_string_to_date("")

    def test_fake_dates_for_entered_date_string_to_date(self):
        with self.assertRaises(ValueError):
            entered_date_string_to_date("40-15-2015")
        with self.assertRaises(ValueError):
            entered_date_string_to_date("30-15-2015")
        with self.assertRaises(ValueError):
            entered_date_string_to_date("12-35-2015")
        with self.assertRaises(ValueError):
            entered_date_string_to_date("2014-20-15")
        with self.assertRaises(ValueError):
            entered_date_string_to_date("12-00-2015")
        with self.assertRaises(ValueError):
            entered_date_string_to_date("0000-20-15")
        with self.assertRaises(ValueError):
            entered_date_string_to_date("2014-35-00")
        with self.assertRaises(ValueError):
            entered_date_string_to_date("2016-12-40")
        with self.assertRaises(ValueError):
            entered_date_string_to_date("2017-02-29")

    def test_real_dates_for_entered_date_string_to_date(self):
        self.assertEqual(entered_date_string_to_date("2014-12-20"), datetime(2014, 12, 20, 0,0 ).date())
        self.assertEqual(entered_date_string_to_date("2017-01-20"), datetime(2017, 1, 20, 0,0 ).date())
        self.assertEqual(entered_date_string_to_date("2017-01-07"), datetime(2017, 1, 7, 0,0 ).date())
        self.assertEqual(entered_date_string_to_date("01-15-2017"), datetime(2017, 1, 15, 0,0 ).date())
        self.assertEqual(entered_date_string_to_date("02-28-2017"), datetime(2017, 2, 28, 0,0 ).date())
    
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