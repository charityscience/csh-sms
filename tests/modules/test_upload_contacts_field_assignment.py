from __future__ import unicode_literals
import csv
from django.test import TestCase

from mock import patch
from freezegun import freeze_time
from datetime import datetime
from django.utils import timezone
from management.models import Contact, Group
from modules.upload_contacts_from_file import csv_upload
from modules.i18n import hindi_placeholder_name, gujarati_placeholder_name
from dateutil.relativedelta import relativedelta

def create_sample_contact(name, phone_number, date_of_birth):
    contact, created = Contact.objects.get_or_create(name=name, phone_number=phone_number,
        date_of_birth=date_of_birth)
    return contact


class UploadContactsContactFieldsTests(TestCase):
    def upload_file(self, filepath, source):
        csv_upload(filepath=filepath, source=source)        

    @patch("logging.error")
    def test_existing_contacts_are_updated_telerivet(self, logging_mock):
        """A contact with name Aaarsh, phone number 911234567890,
            and date of birth: November 12, 2012 exists in the example-m.csv file
        """
        old_contact = create_sample_contact(name="Aaarsh", phone_number="911234567890",
                                            date_of_birth=datetime(2011, 5, 10, 0,0).date())

        self.upload_file(filepath="tests/data/example.csv", source="TR")
        updated_contact = Contact.objects.get(name=old_contact.name, phone_number=old_contact.phone_number)
        self.assertNotEqual(old_contact.date_of_birth, updated_contact.date_of_birth)

        self.assertEqual(old_contact.id, updated_contact.id)

    @patch("logging.error")
    def test_existing_contacts_are_updated_maps(self, logging_mock):
        """A contact with name DEVANSH, nick name ANSHIKA, phone number 8888800184,
            and date of birth: September 22, 2016 exists in the example-m.csv file
        """
        old_contact = create_sample_contact(name="ANSHIKA", phone_number="918888800184",
                                            date_of_birth=datetime(2011, 5, 10, 0,0).date())

        self.upload_file(filepath="tests/data/example-m.csv", source="MAPS")
        updated_contact = Contact.objects.get(name=old_contact.name, phone_number=old_contact.phone_number)
        self.assertNotEqual(old_contact.date_of_birth, updated_contact.date_of_birth)
        self.assertEqual(old_contact.id, updated_contact.id)

    @patch("logging.error")
    def test_existing_contacts_are_updated_hansa(self, logging_mock):
        """A contact with name Aaliyah, phone number 910123456886, and date of birth: August, 25, 2017
            exists in the example-h.csv file
        """
        old_contact = create_sample_contact(name="Aaliyah", phone_number="910123456886",
                                            date_of_birth=datetime(2011, 5, 10, 0,0).date())

        self.upload_file(filepath="tests/data/example-h.csv", source="HANSA")
        updated_contact = Contact.objects.get(name=old_contact.name, phone_number=old_contact.phone_number)
        self.assertNotEqual(old_contact.date_of_birth, updated_contact.date_of_birth)
        self.assertEqual(old_contact.id, updated_contact.id)

    @patch("logging.error")
    def test_new_contacts_are_created_telerivet(self, logging_mock):
        old_all_contacts = Contact.objects.all()
        old_contacts_count = Contact.objects.count()
        self.upload_file(filepath="tests/data/example.csv", source="TR")
        new_all_contacts = Contact.objects.all()
        new_contacts_count = Contact.objects.count()
        self.assertNotEqual(old_all_contacts, new_all_contacts)
        self.assertNotEqual(old_contacts_count, new_contacts_count)

    @patch("logging.error")
    def test_new_contacts_are_created_maps(self, logging_mock):
        old_all_contacts = Contact.objects.all()
        old_contacts_count = Contact.objects.count()
        self.upload_file(filepath="tests/data/example-m.csv", source="MAPS")
        new_all_contacts = Contact.objects.all()
        new_contacts_count = Contact.objects.count()
        self.assertNotEqual(old_all_contacts, new_all_contacts)
        self.assertNotEqual(old_contacts_count, new_contacts_count)

    @patch("logging.error")
    def test_new_contacts_are_created_hansa(self, logging_mock):
        old_all_contacts = Contact.objects.all()
        old_contacts_count = Contact.objects.count()
        self.upload_file(filepath="tests/data/example-h.csv", source="HANSA")
        new_all_contacts = Contact.objects.all()
        new_contacts_count = Contact.objects.count()
        self.assertNotEqual(old_all_contacts, new_all_contacts)
        self.assertNotEqual(old_contacts_count, new_contacts_count)

    @patch("logging.error")
    def test_only_contacts_with_valid_numbers_created(self, logging_mock):
    	"""tests/data/example.csv file being tested contains
    	   a contact with name: FakestNumber and phone number: 511234567890"""
    	self.upload_file(filepath="tests/data/example.csv", source="TR")
    	self.assertFalse(Contact.objects.filter(name="FakestNumber").exists())
    	logging_mock.assert_called_with("Entry: FakestNumber - 2016-09-14 has invalid phone number: 123456")

    @patch("logging.error")
    def test_hindi_names_are_preserved(self, logging_mock):
        """tests/data/example.csv file being tested contains
           a contact with name: \u0906\u0930\u0935 and phone number: 912222277777"""
        hindi_name = u'\\u0906\\u0930\\u0935'
        self.upload_file(filepath="tests/data/example.csv", source="TR")
        hin_contact = Contact.objects.get(phone_number="912222277777")
        self.assertNotEqual(hindi_name, hin_contact.name)
        self.assertTrue("\\" not in hin_contact.name)
        self.assertEqual(hindi_name.encode("utf-8").decode('unicode-escape'), hin_contact.name)

    @patch("logging.error")
    def test_gujarati_names_are_preserved(self, logging_mock):
        """tests/data/example.csv file being tested contains
           a contact with name: \u0A90\u0AC5\u0A94 and phone number: 915555511111"""
        guj_name = u'\\u0A90\\u0AC5\\u0A94'
        self.upload_file(filepath="tests/data/example.csv", source="TR")
        guj_contact = Contact.objects.get(phone_number="915555511111")
        self.assertNotEqual(guj_name, guj_contact.name)
        self.assertTrue("\\" not in guj_contact.name)
        self.assertEqual(guj_name.encode("utf-8").decode('unicode-escape'), guj_contact.name)

    @patch("logging.error")
    def test_unicode_literal_names_are_encoded(self, logging_mock):
        self.upload_file(filepath="tests/data/example.csv", source="TR")
        self.assertFalse(Contact.objects.filter(name__startswith="\\"))

    @patch("logging.error")
    def test_contact_pregnant_signup_correctly_assigned_telerivet(self, logging_mock):
        """A contact with name: "Aadya", phone number 911234567890,
            and date of birth: September 3, 2017 exists in the example.csv file
            NOT a pregnant signup
        """
        self.upload_file(filepath="tests/data/example.csv", source="TR")
        non_preg_contact = Contact.objects.get(name="Aakriti", phone_number="911234567893")
        self.assertFalse(non_preg_contact.preg_signup)
        """A contact with name: "Aakriti", phone number: 911234567890, date of birth: ""
            exists in the example.csv file
            IS a pregnant signup
        """
        preg_contact = Contact.objects.get(name="Aadya", phone_number="911234567892")
        self.assertTrue(preg_contact.preg_signup)

    @patch("logging.error")
    def test_contact_pregnant_signup_correctly_assigned_maps(self, logging_mock):
        """A contact with name DEVANSH, nick name ANSHIKA, phone number 8888800184,
            and date of birth: September 22, 2016 exists in the example-m.csv file
            NOT a pregnant signup
        """
        self.upload_file(filepath="tests/data/example-m.csv", source="MAPS")
        non_preg_contact = Contact.objects.get(name="ANSHIKA", phone_number="918888800184")
        self.assertFalse(non_preg_contact.preg_signup)
        """A contact with name: "", phone number: 8888800494, date of birth: "", language: "1" (for Hindi)
            exists in the example-m.csv file
            IS a pregnant signup
        """
        preg_contact = Contact.objects.get(name=hindi_placeholder_name(), phone_number="918888800494")
        self.assertTrue(preg_contact.preg_signup)

    @patch("logging.error")
    def test_contact_pregnant_signup_correctly_assigned_hansa(self, logging_mock):
        """A contact with name Aaliyah, phone number 910123456886, and date of birth: August, 25, 2017
            exists in the example-h.csv file
            NOT a pregnant signup
        """
        self.upload_file(filepath="tests/data/example-h.csv", source="HANSA")
        non_preg_contact = Contact.objects.get(name="Aaliyah", phone_number="910123456886")
        self.assertFalse(non_preg_contact.preg_signup)
        """A contact with name: "", phone number: 912345678901, date of birth: "", language: Hindi
            exists in the example-h.csv file
            IS a pregnant signup
        """
        preg_contact = Contact.objects.get(name=hindi_placeholder_name(), phone_number="912345678901")
        self.assertTrue(preg_contact.preg_signup)

    @patch("logging.error")
    def test_contact_vital_info_correctly_assigned_telerivet(self, logging_mock):
        """A contact with name: Aaarsh, phone number: 911234567890, alt_phone_number: "",
            date of birth: "2012-11-12", date of sign up: "2017-06-25", delay in days: "0",
            month of pregnancy: DOESNT EXIST, language: Hindi, preg_signup: "FALSE" exists in the example.csv file
        """
        self.upload_file(filepath="tests/data/example.csv", source="TR")
        non_preg_contact = Contact.objects.get(name="Aaarsh", phone_number="911234567890",
            alt_phone_number="", date_of_birth=datetime(2012, 11, 12).date(), date_of_sign_up=datetime(2017, 6, 25).date(),
            language_preference="Hindi", delay_in_days=0, functional_date_of_birth=datetime(2012, 11, 12).date(),
            preg_signup=False)
        self.assertFalse(non_preg_contact.preg_signup)

        """A contact with name: Aakriti, phone number: 911234567893, alt_phone_number: "910000011118",
            date of birth: "2015-10-15", date of sign up: "2017-06-29", delay in days: "",
            month of pregnancy: DOESNT EXIST, language: English, preg_signup: "0" exists in the example.csv file
        """
        alt_phone_contact = Contact.objects.get(name="Aakriti", phone_number="911234567893",
            alt_phone_number="", date_of_birth=datetime(2015, 10, 15).date(), date_of_sign_up=datetime(2017, 6, 29).date(),
            language_preference="English", delay_in_days=0, functional_date_of_birth=datetime(2015, 10, 15).date(),
            preg_signup=False)
        self.assertEqual("", alt_phone_contact.alt_phone_number)

        """A contact with name: "Aadya", phone number: 911234567892, alt_phone_number: "",
            date of birth: "2017-09-03",  date_of_sign_up: "2017-06-16", delay in days: "5",
            month of pregnancy: DOESNT EXIST, language: English, preg_signup: "TRUE" exists in the example.csv file
        """
        preg_contact = Contact.objects.get(name="Aadya", phone_number="911234567892",
            alt_phone_number="", date_of_birth=datetime(2017, 9, 3).date(), date_of_sign_up=datetime(2017, 6, 16).date(),
            language_preference="English", delay_in_days=5, functional_date_of_birth=datetime(2017, 9, 8).date(),
            preg_signup=True)
        self.assertTrue(preg_contact.preg_signup)

    @patch("logging.error")
    def test_contact_vital_info_correctly_assigned_maps(self, logging_mock):
        """A contact with name: RAJNEEL, nickname: "RABI", phone number: 8888800099, alt_phone_number: "7777700124",
            date of birth: 25/08/2016, date of sign up: "25/07/2017", delay in days: DOESNT EXIST,
            month of pregnancy: "", language: 1 (for Hindi), pregnant: "2" (for no) exists in the example-m.csv file
        """
        self.upload_file(filepath="tests/data/example-m.csv", source="MAPS")
        non_preg_contact = Contact.objects.get(name="RABI", phone_number="918888800099",
            alt_phone_number="917777700124", date_of_birth=datetime(2016, 8, 25).date(), date_of_sign_up=datetime(2017, 7, 25).date(),
            language_preference="Hindi", delay_in_days=0, functional_date_of_birth=datetime(2016, 8, 25).date(),
            preg_signup=False)
        self.assertFalse(non_preg_contact.preg_signup)

        """A contact with name: RAJ, nickname: "PRAYASH", phone number: 8888800199, alt_phone_number: "0",
            date of birth: "07/11/2016", date of sign up: "28/07/2017", delay in days: DOESNT EXIST,
            month of pregnancy: "", language: 1 (for Hindi), pregnant: "2" (for no) exists in the example-m.csv file
        """
        alt_phone_contact = Contact.objects.get(name="PRAYASH", phone_number="918888800199",
            alt_phone_number="", date_of_birth=datetime(2016, 11, 7).date(), date_of_sign_up=datetime(2017, 7, 28).date(),
            language_preference="Hindi", delay_in_days=0, functional_date_of_birth=datetime(2016, 11, 7).date(),
            preg_signup=False)
        self.assertEqual("", alt_phone_contact.alt_phone_number)

        """A contact with name: "", phone number: 8888800288, alt_phone_number: "7777700246",
            date of birth: "",  date_of_sign_up: "25/07/2017", delay in days: DOESNT EXIST,
            month of pregnancy: "7", language: 1 (for Hindi), pregnant: "1" (for yes) exists in the example-m.csv file
            IS a pregnant signup
        """
        seven_months = datetime(2017, 7, 25).date() + relativedelta(months=-7) + relativedelta(days=280)
        preg_contact = Contact.objects.get(name=hindi_placeholder_name(), phone_number="918888800288",
            alt_phone_number="917777700246", date_of_birth=seven_months, date_of_sign_up=datetime(2017, 7, 25).date(),
            language_preference="Hindi", delay_in_days=0, functional_date_of_birth=seven_months,
            preg_signup=True)
        self.assertTrue(preg_contact.preg_signup)

    @patch("logging.error")
    def test_contact_vital_info_correctly_assigned_hansa(self, logging_mock):
        """A contact with name: Aaliyah, phone number: 910123456886, alt_phone_number: "",
            date of birth: August, 25, 2017, date of sign up: "03/09/2017", delay in days: DOESNT EXIST,
            month of pregnancy: "", language: Hindi, exists in the example-h.csv file
            NOT a pregnant signup
        """
        self.upload_file(filepath="tests/data/example-h.csv", source="HANSA")
        non_preg_contact = Contact.objects.get(name="Aaliyah", phone_number="910123456886",
            alt_phone_number="", date_of_birth=datetime(2017, 8, 25).date(), date_of_sign_up=datetime(2017, 9, 3).date(),
            language_preference="Hindi", delay_in_days=0, functional_date_of_birth=datetime(2017, 8, 25).date())
        self.assertFalse(non_preg_contact.preg_signup)

        """A contact with name: Sofia, phone number: 910123456855, alt_phone_number: "910000011118",
            date of birth: "17/07/2017", date of sign up: "30/08/2017", delay in days: DOESNT EXIST,
            month of pregnancy: "", language: Hindi, exists in the example-h.csv file
            NOT a pregnant signup
        """
        alt_phone_contact = Contact.objects.get(name="Sofia", phone_number="910123456855",
            alt_phone_number="910000011118", date_of_birth=datetime(2017, 7, 17).date(), date_of_sign_up=datetime(2017, 8, 30).date(),
            language_preference="Hindi", delay_in_days=0, functional_date_of_birth=datetime(2017, 7, 17).date())
        self.assertEqual("910000011118", alt_phone_contact.alt_phone_number)

        """A contact with name: "", phone number: 912345678901, alt_phone_number: "",
            date of birth: "",  date_of_sign_up: "25/08/2017", delay in days: DOESNT EXIST,
            month of pregnancy: "4", language: Hindi, exists in the example-h.csv file
            IS a pregnant signup
        """
        four_months = datetime(2017, 8, 25).date() + relativedelta(months=-4) + relativedelta(days=280)
        preg_contact = Contact.objects.get(name=hindi_placeholder_name(), phone_number="912345678901",
            alt_phone_number="", date_of_birth=four_months, date_of_sign_up=datetime(2017, 8, 25).date(),
            language_preference="Hindi", delay_in_days=0, functional_date_of_birth=four_months)
        self.assertTrue(preg_contact.preg_signup)

    @patch("logging.error")
    def test_contact_personal_info_correctly_assigned_hansa(self, logging_mock):
        """A contact with name: Aaliyah, phone number: 910123456886, alt_phone_number: "",
            gender: "Male", mother_tongue: "", religion: DOESNT EXIST, state: "Madhya Pradesh", division: "Indore",
            district: "Indore", city: "Indore", monthly_income_rupees: DOESNT EXIST, children_previously_vaccinated: DOESNT EXIST,
            not_vaccinated_why: DOESNT EXIST, mother_first_name: "mom", mother_last_name: DOESNT EXIST,
            exists in the example-h.csv file
            NOT a pregnant signup
        """
        self.upload_file(filepath="tests/data/example-h.csv", source="HANSA")
        non_preg_contact = Contact.objects.get(name="Aaliyah", phone_number="910123456886",
            gender="Male", mother_tongue="", religion="", state="Madhya Pradesh", division="Indore",
            district="Indore", city="Indore", monthly_income_rupees=999999, children_previously_vaccinated=None,
            not_vaccinated_why="", mother_first_name="mom", mother_last_name="")
        self.assertFalse(non_preg_contact.preg_signup)

        """A contact with name: Sofia, phone number: 910123456855, alt_phone_number: "910000011118",
            gender: "Female", mother_tongue: "", religion: DOESNT EXIST, state: "Madhya Pradesh", division: "Indore",
            district: "Indore", city: "Indore", monthly_income_rupees: DOESNT EXIST, children_previously_vaccinated: DOESNT EXIST,
            not_vaccinated_why: DOESNT EXIST, mother_first_name: "mom", mother_last_name: DOESNT EXIST,
            exists in the example-h.csv file
            NOT a pregnant signup
        """
        alt_phone_contact = Contact.objects.get(name="Sofia", phone_number="910123456855",
            gender="Female", mother_tongue="", religion="", state="Madhya Pradesh", division="Indore",
            district="Indore", city="Indore", monthly_income_rupees=999999, children_previously_vaccinated=None,
            not_vaccinated_why="", mother_first_name="mom", mother_last_name="")
        self.assertEqual("910000011118", alt_phone_contact.alt_phone_number)

        """A contact with name: "", phone number: 912345678901, alt_phone_number: "",
            gender: "", mother_tongue: "", religion: DOESNT EXIST, state: "Madhya Pradesh", division: "Indore",
            district: "Indore", city: "Indore", monthly_income_rupees: DOESNT EXIST, children_previously_vaccinated: DOESNT EXIST,
            not_vaccinated_why: DOESNT EXIST, mother_first_name: "s", mother_last_name: DOESNT EXIST,
            exists in the example-h.csv file
            IS a pregnant signup
        """
        four_months = datetime(2017, 8, 25).date() + relativedelta(months=-4) + relativedelta(days=280)
        preg_contact = Contact.objects.get(name=hindi_placeholder_name(), phone_number="912345678901",
            gender="", mother_tongue="", religion="", state="Madhya Pradesh", division="Indore",
            district="Indore", city="Indore", monthly_income_rupees=999999, children_previously_vaccinated=None,
            not_vaccinated_why="", mother_first_name="", mother_last_name="")
        self.assertTrue(preg_contact.preg_signup)

    @patch("logging.error")
    def test_contact_signup_info_correctly_assigned_hansa(self, logging_mock):
        """A contact with name: Aaliyah, phone number: 910123456886, alt_phone_number: "",
            hospital_name: DOESNT EXIST, doctor_name: DOESNT EXIST,
            exists in the example-h.csv file
            NOT a pregnant signup
        """
        self.upload_file(filepath="tests/data/example-h.csv", source="HANSA")
        non_preg_contact = Contact.objects.get(name="Aaliyah", phone_number="910123456886",
            method_of_sign_up="Door to Door", org_sign_up="HANSA", hospital_name="", doctor_name="")
        self.assertFalse(non_preg_contact.preg_signup)

        """A contact with name: Sofia, phone number: 910123456855, alt_phone_number: "910000011118",
            hospital_name: DOESNT EXIST, doctor_name: DOESNT EXIST,
            exists in the example-h.csv file
            NOT a pregnant signup
        """
        alt_phone_contact = Contact.objects.get(name="Sofia", phone_number="910123456855",
            method_of_sign_up="Door to Door", org_sign_up="HANSA", hospital_name="", doctor_name="")
        self.assertEqual("910000011118", alt_phone_contact.alt_phone_number)

        """A contact with name: "", phone number: 912345678901, alt_phone_number: "",
            hospital_name: DOESNT EXIST, doctor_name: DOESNT EXIST,
            exists in the example-h.csv file
            IS a pregnant signup
        """
        four_months = datetime(2017, 8, 25).date() + relativedelta(months=-4) + relativedelta(days=280)
        preg_contact = Contact.objects.get(name=hindi_placeholder_name(), phone_number="912345678901",
            method_of_sign_up="Door to Door", org_sign_up="HANSA", hospital_name="", doctor_name="")
        self.assertTrue(preg_contact.preg_signup)

    @patch("logging.error")
    def test_contact_system_info_correctly_assigned_hansa(self, logging_mock):
        """A contact with name: Aaliyah, phone number: 910123456886, alt_phone_number: "",
            telerivet_contact_id: DOESNT EXIST, trial_id: DOESNT EXIST, trial_group: DOESNT EXIST,
            exists in the example-h.csv file
            NOT a pregnant signup
        """
        self.upload_file(filepath="tests/data/example-h.csv", source="HANSA")
        non_preg_contact = Contact.objects.get(name="Aaliyah", phone_number="910123456886",
            telerivet_contact_id="", trial_id="", trial_group="")
        self.assertFalse(non_preg_contact.preg_signup)

        """A contact with name: Sofia, phone number: 910123456855, alt_phone_number: "910000011118",
            telerivet_contact_id: DOESNT EXIST, trial_id: DOESNT EXIST, trial_group: DOESNT EXIST,
            exists in the example-h.csv file
            NOT a pregnant signup
        """
        alt_phone_contact = Contact.objects.get(name="Sofia", phone_number="910123456855",
            telerivet_contact_id="", trial_id="", trial_group="")
        self.assertEqual("910000011118", alt_phone_contact.alt_phone_number)

        """A contact with name: "", phone number: 912345678901, alt_phone_number: "",
            telerivet_contact_id: DOESNT EXIST, trial_id: DOESNT EXIST, trial_group: DOESNT EXIST,
            exists in the example-h.csv file
            IS a pregnant signup
        """
        four_months = datetime(2017, 8, 25).date() + relativedelta(months=-4) + relativedelta(days=280)
        preg_contact = Contact.objects.get(name=hindi_placeholder_name(), phone_number="912345678901",
            preferred_time="", script_selection="", telerivet_sender_phone="")
        self.assertTrue(preg_contact.preg_signup)

    @freeze_time(datetime(2017, 7, 21, 0, 0).replace(tzinfo=timezone.get_default_timezone()))
    @patch("logging.error")
    def test_contact_message_references_correctly_assigned_hansa(self, logging_mock):
        frozen_time = datetime.now()
        """A contact with name: Aaliyah, phone number: 910123456886, alt_phone_number: "",
            preferred_time: DOESNT EXIST, script_selection: DOESNT EXIST, telerivet_sender_phone: DOESNT EXIST
            last_heard_from: DOESNT EXIST, last_contacted: DOESNT EXIST, time_created: DOESNT EXIST,
            exists in the example-h.csv file
            NOT a pregnant signup
        """
        self.upload_file(filepath="tests/data/example-h.csv", source="HANSA")
        non_preg_contact = Contact.objects.get(name="Aaliyah", phone_number="910123456886",
            preferred_time="", script_selection="", telerivet_sender_phone="", last_heard_from=None,
            last_contacted=None, time_created=frozen_time)
        self.assertFalse(non_preg_contact.preg_signup)

        """A contact with name: Sofia, phone number: 910123456855, alt_phone_number: "910000011118",
            preferred_time: DOESNT EXIST, script_selection: DOESNT EXIST, telerivet_sender_phone: DOESNT EXIST
            last_heard_from: DOESNT EXIST, last_contacted: DOESNT EXIST, time_created: DOESNT EXIST,
            exists in the example-h.csv file
            NOT a pregnant signup
        """
        alt_phone_contact = Contact.objects.get(name="Sofia", phone_number="910123456855",
            preferred_time="", script_selection="", telerivet_sender_phone="", last_heard_from=None,
            last_contacted=None, time_created=frozen_time)
        self.assertEqual("910000011118", alt_phone_contact.alt_phone_number)

        """A contact with name: "", phone number: 912345678901, alt_phone_number: "",
            preferred_time: DOESNT EXIST, script_selection: DOESNT EXIST, telerivet_sender_phone: DOESNT EXIST
            last_heard_from: DOESNT EXIST, last_contacted: DOESNT EXIST, time_created: DOESNT EXIST,
            exists in the example-h.csv file
            IS a pregnant signup
        """
        four_months = datetime(2017, 8, 25).date() + relativedelta(months=-4) + relativedelta(days=280)
        preg_contact = Contact.objects.get(name=hindi_placeholder_name(), phone_number="912345678901",
            preferred_time="", script_selection="", telerivet_sender_phone="", last_heard_from=None,
            last_contacted=None, time_created=frozen_time)
        self.assertTrue(preg_contact.preg_signup)