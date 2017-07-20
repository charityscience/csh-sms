import os
import csv
import tempfile
from django.test import TestCase

from datetime import datetime
from management.models import Contact
from modules.upload_contacts_from_file import csv_upload, make_contact_dict, assign_groups_to_contact, \
											  assign_visit_dates_to_contact, visit_dict_parse, previous_vaccination, \
											  monthly_income, parse_or_create_delay_num, entered_date_string_to_date, \
											  parse_or_create_functional_dob, parse_contact_time_references



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

	def create_sample_contact(self):
		contact, created = Contact.objects.get_or_create(name="Aarav", phone_number="911234567890",
			date_of_birth=datetime(2011, 5, 10, 0,0).date())
		return contact

	def test_existing_contacts_are_updated(self):
		old_contact = self.create_sample_contact()
		old_contact_dob = old_contact.date_of_birth

		self.upload_file()
		updated_contact = Contact.objects.get(name=old_contact.name, phone_number=old_contact.phone_number)
		updated_contact_dob = updated_contact.date_of_birth
		self.assertNotEqual(old_contact_dob, updated_contact_dob)

	def test_new_contacts_are_created(self):
		old_all_contacts = Contact.objects.all()
		self.upload_file()
		new_all_contacts = Contact.objects.all()
		self.assertNotEqual(old_all_contacts, new_all_contacts)


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