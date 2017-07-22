import csv
import re
import datetime
from django.utils import timezone
from modules.utils import date_string_ymd_to_date, date_string_mdy_to_date, datetime_string_mdy_to_datetime
from modules.visit_date_helper import add_or_subtract_days
from management.models import Contact, Group

def csv_upload(filepath):
	with open(filepath) as csvfile:
		reader = csv.DictReader(csvfile)
		
		for row in reader:
			new_dict = make_contact_dict(row)
			
			new_contact, created = Contact.objects.update_or_create(name=new_dict["name"],
				phone_number=new_dict["phone_number"],defaults=new_dict)
			
			assign_groups_to_contact(new_contact, row["Groups"])
			assign_visit_dates_to_contact(new_contact)


def make_contact_dict(row):
	new_dict = {}
	new_dict["name"] = row["Name"]
	new_dict["phone_number"] = row["Phone Number"]
	new_dict["alt_phone_number"] = row["Alternative Phone"]
	new_dict["delay_in_days"] = parse_or_create_delay_num(row["Delay in days"])
	new_dict["language_preference"] = row["Language Preference"]
	
	new_dict["date_of_birth"] = entered_date_string_to_date(row["Date of Birth"])
	new_dict["date_of_sign_up"] = entered_date_string_to_date(row["Date of Sign Up"])
	new_dict["functional_date_of_birth"] = parse_or_create_functional_dob(row["Functional DoB"], new_dict["date_of_birth"], new_dict["delay_in_days"])

	# Personal Info
	new_dict["gender"] = row["Gender"]
	new_dict["mother_tongue"] = row["Mother Tongue"]
	new_dict["language_preference"] = row["Language Preference"]
	new_dict["religion"] = row["Religion"]
	new_dict["state"] = row["State"]
	new_dict["division"] = row["Division"]
	new_dict["district"] = row["District"]
	new_dict["city"] = row["City"]
	new_dict["monthly_income_rupees"] = monthly_income(row["Monthly Income"])
	new_dict["children_previously_vaccinated"] = previous_vaccination(row["Previously had children vaccinated"].lower())
	new_dict["not_vaccinated_why"] = row["If not vaccinated why"]
	new_dict["mother_first_name"] = row["Mother's First"]
	new_dict["mother_last_name"] = row["Mother's Last"]


	# Type of Sign Up
	new_dict["method_of_sign_up"] = row["Method of Sign Up"]
	new_dict["org_sign_up"] = row["Org Sign Up"]
	new_dict["hospital_name"] = row["Hospital Name"]
	new_dict["doctor_name"] = row["Doctor Name"]
	new_dict["url_information"] = row["URL information"]

	# System Identification
	new_dict["telerivet_contact_id"] = row["Telerivet Contact ID"]
	new_dict["trial_id"] = row["Trial ID"]
	new_dict["trial_group"] = row["Trial Group"]

	# Message References
	new_dict["preferred_time"] = row["Preferred Time"]
	new_dict["script_selection"] = row["Script Selection"]
	new_dict["telerivet_sender_phone"] = row["Sender Phone"]
	new_dict["last_heard_from"] = parse_contact_time_references(row["Last Heard From"])
	new_dict["last_contacted"] = parse_contact_time_references(row["Last Contacted"])
	new_dict["time_created"] = parse_contact_time_references(row["Time Created"])

	return new_dict

def assign_groups_to_contact(contact, groups_string):
	if groups_string == "":
		return None

	for group_name in groups_string.split(", "):
		new_or_old_group, created = Group.objects.get_or_create(name=group_name)
		new_or_old_group.contacts.add(contact)
		new_or_old_group.save()

def assign_visit_dates_to_contact(contact):
	standards, functionals = contact.set_visit_dates()

	visit_dict_parse(contact, standards, "standard_")
	visit_dict_parse(contact, functionals, "functional_")
	contact.save()

def visit_dict_parse(contact, visit_dict, name_preface):

	for key, value in visit_dict.items():
		contact.visitdate_set.create(name=name_preface+str(key), date=value)


def previous_vaccination(row_entry):
	if "y" in row_entry:
		return True
	elif "n" in row_entry:
		return False
	else:
		return None

def monthly_income(row_entry):
	return int(row_entry) if row_entry and not re.search("\D+", row_entry) else 999999

def parse_or_create_delay_num(row_entry):
	return int(row_entry) if row_entry and not re.search("\D+", row_entry) else 0

def entered_date_string_to_date(row_entry):
	try:
		return date_string_ymd_to_date(row_entry)
	except ValueError:
		return date_string_mdy_to_date(row_entry)

def parse_or_create_functional_dob(row_entry, date_of_birth, delay):
	return entered_date_string_to_date(row_entry) if row_entry else add_or_subtract_days(date_of_birth, delay)

def parse_contact_time_references(row_entry):
	return datetime_string_mdy_to_datetime(row_entry) if row_entry else datetime.datetime.now().replace(tzinfo=timezone.get_default_timezone())