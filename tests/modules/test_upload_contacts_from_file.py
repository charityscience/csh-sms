import os
import csv
import tempfile
from django.test import TestCase

from datetime import datetime
from django.utils import timezone
from management.models import Contact, Group
from modules.upload_contacts_from_file import csv_upload, make_contact_dict, assign_groups_to_contact, \
											  assign_visit_dates_to_contact, visit_dict_parse, previous_vaccination, \
											  monthly_income, parse_or_create_delay_num, entered_date_string_to_date, \
											  parse_or_create_functional_dob, parse_contact_time_references




def create_sample_contact(*args):
	contact, created = Contact.objects.get_or_create(name="Aarav", phone_number="911234567890",
		date_of_birth=datetime(2011, 5, 10, 0,0).date())
	return contact

def create_sample_group(name="TestMe"):
	group, created = Group.objects.get_or_create(name=name)
	return group

class UploadContactsFileTests(TestCase):

	def test_nonexistent_file_csv(self):
		with self.assertRaises(FileNotFoundError):
			csv_upload("none.csv")

	def test_non_csv_file(self):
		fake_txt_path = os.path.join(tempfile.gettempdir(), "fake.txt")
		with self.assertRaises(FileNotFoundError):
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

class UploadContactsRelationshipTests(TestCase):

	def test_groups_are_assigned_to_contact(self):
		contact = create_sample_contact()
		group_string = "TestMe"
		multi_group_string = "TestMe, Again"
		group = create_sample_group(name=group_string)
		try:
			before_add = contact.group_set.get(id=group.id)
		except Group.DoesNotExist:
			before_add = False
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
		self.assertEqual(monthly_income("1892ff8"),999999)
		self.assertEqual(monthly_income("ghg18928"),999999)
		self.assertEqual(monthly_income("18928ff"),999999)
		self.assertEqual(monthly_income("18928-"),999999)
		self.assertEqual(monthly_income("-18928"),999999)
		self.assertEqual(monthly_income("+18928"),999999)
		self.assertEqual(monthly_income("18+928"),999999)
		self.assertEqual(monthly_income("18 928"),999999)
		self.assertEqual(monthly_income("18,928"),999999)

	def test_empty_income(self):
		self.assertEqual(monthly_income(''),999999)
		self.assertEqual(monthly_income(None),999999)

	def test_empty_delay(self):
		self.assertEqual(parse_or_create_delay_num(''),0)
		self.assertEqual(parse_or_create_delay_num(None),0)

	def test_nondigits_in_delay(self):
		self.assertEqual(parse_or_create_delay_num("1892ff8"),0)
		self.assertEqual(parse_or_create_delay_num("ghg18928"),0)
		self.assertEqual(parse_or_create_delay_num("18928ff"),0)
		self.assertEqual(parse_or_create_delay_num("18928-"),0)
		self.assertEqual(parse_or_create_delay_num("-18928"),0)
		self.assertEqual(parse_or_create_delay_num("+18928"),0)
		self.assertEqual(parse_or_create_delay_num("18+928"),0)
		self.assertEqual(parse_or_create_delay_num("18 928"),0)
		self.assertEqual(parse_or_create_delay_num("18,928"),0)

	def test_empty_previous_vaccination(self):
		self.assertEqual(previous_vaccination(''), None)

	def test_previous_vaccination_positive(self):
		self.assertEqual(previous_vaccination("y"),True)
		self.assertEqual(previous_vaccination("yes"),True)
		self.assertEqual(previous_vaccination("yes  "),True)
		self.assertEqual(previous_vaccination("yes asdfasfasf "),True)

	def test_previous_vaccination_negative(self):
		self.assertEqual(previous_vaccination("n"),False)
		self.assertEqual(previous_vaccination("no"),False)
		self.assertEqual(previous_vaccination("no  "),False)
		self.assertEqual(previous_vaccination("no asdfasfasf "),False)


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
			parse_or_create_functional_dob("", "", 0)

		delay1 = 0
		delay2 = 5
		dob1 = entered_date_string_to_date("10-15-2015")
		parsed_func_dob = parse_or_create_functional_dob("", dob1, delay1)
		parsed_func_dob2 = parse_or_create_functional_dob("", dob1, delay2)
		
		self.assertEqual(parsed_func_dob, datetime(2015, 10, 15).date())
		self.assertEqual(parsed_func_dob2, datetime(2015, 10, 20).date())

	def test_real_dates_for_parse_or_create_functional_dob(self):
		funct_dob1 = "10-15-2015"
		funct_dob2 = "10-18-2015"
		dob1 = entered_date_string_to_date("10-15-2015")
		delay1 = 0
		delay2 = 3
		parsed_func_dob1 = parse_or_create_functional_dob(funct_dob1, dob1, delay1)
		parsed_func_dob2 = parse_or_create_functional_dob(funct_dob2, dob1, delay2)
		
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
		date_string1 = "2014-12-20"
		date_string2 = "2017-01-20"
		date_string3 = "2017-01-07"
		date_string4 = "01-15-2017"
		date_string5 = "02-28-2017"

		self.assertEqual(entered_date_string_to_date(date_string1),datetime(2014, 12, 20, 0,0 ).date())
		self.assertEqual(entered_date_string_to_date(date_string2),datetime(2017, 1, 20, 0,0 ).date())
		self.assertEqual(entered_date_string_to_date(date_string3),datetime(2017, 1, 7, 0,0 ).date())
		self.assertEqual(entered_date_string_to_date(date_string4),datetime(2017, 1, 15, 0,0 ).date())
		self.assertEqual(entered_date_string_to_date(date_string5),datetime(2017, 2, 28, 0,0 ).date())
	
	def test_parse_contact_time_references_real_datetimes(self):
		time1 = "6/12/2017 4:00:03 PM"
		time2 = "6/16/2017 6:51:28 PM"

		self.assertEqual(datetime(2017, 6, 12, 16, 0, 3, tzinfo=timezone.get_default_timezone()),
			parse_contact_time_references(time1))
		self.assertEqual(datetime(2017, 6, 16, 18, 51, 28, tzinfo=timezone.get_default_timezone()),
			parse_contact_time_references(time2))