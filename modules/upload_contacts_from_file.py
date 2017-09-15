import csv
import re
import datetime
import logging
from django.utils import timezone
from modules.utils import add_contact_to_group, phone_number_is_valid, prepare_phone_number
from modules.date_helper import date_string_ymd_to_date, date_string_mdy_to_date, datetime_string_mdy_to_datetime, \
                                add_or_subtract_days, add_or_subtract_months, date_string_dmy_to_date
from management.models import Contact

def csv_upload(filepath, source):
    with open(filepath) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            new_dict = make_contact_dict(row, source)
            if phone_number_is_valid(new_dict["phone_number"]):
                new_contact, created = Contact.objects.update_or_create(name=new_dict["name"],
                    phone_number=new_dict["phone_number"], defaults=new_dict)

                assign_groups_to_contact(new_contact, row["Groups"])
                new_contact.preg_signup = assign_preg_signup(new_contact)
            else:
                logging.error("Entry: {name} - {date_of_birth} has invalid phone number: {phone}".format(
                    name=new_dict["name"], phone=new_dict["phone_number"], date_of_birth=new_dict["date_of_birth"]))

def make_contact_dict(row, source):
    new_dict = {}
    new_dict["name"] = row["Name"].encode("utf-8").decode('unicode-escape')
    new_dict["phone_number"] = prepare_phone_number(row["Phone Number"])
    new_dict["alt_phone_number"] = row["Alternative Phone"]
    new_dict["delay_in_days"] = parse_or_create_delay_num(row["Delay in days"])
    new_dict["language_preference"] = row["Language Preference"]
    new_dict["date_of_sign_up"] = entered_date_string_to_date(row["Date of Sign Up"])
    new_dict["date_of_birth"] = entered_date_string_to_date(row["Date of Birth"])
    new_dict["functional_date_of_birth"] = parse_or_create_functional_dob(row["Functional DoB"], new_dict["date_of_birth"], new_dict["delay_in_days"])

    # Personal Info
    new_dict["gender"] = row["Gender"]
    new_dict["mother_tongue"] = row["Mother Tongue"]
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
    new_dict["preg_signup"] = parse_preg_signup(row["Pregnant Signup"])

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
        add_contact_to_group(contact, group_name)

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

def parse_preg_signup(row_entry):
    row_entry = str(row_entry).lower()
    if not row_entry:
        return False
    elif row_entry[0] == "f" or row_entry == "0":
        return False
    else:
        return True

def assign_preg_signup(contact):
    return True if contact.preg_signup or not contact.has_been_born() else False

def estimate_date_of_birth(month_of_pregnancy, date_of_sign_up):
    duration_of_pregnancy = 280 # mean number of days of a pregnancy
    month_of_pregnancy = filter_pregnancy_month(month_of_pregnancy)
    if month_of_pregnancy is None:
        return None

    conception_date = add_or_subtract_months(date=date_of_sign_up, num_of_months=-month_of_pregnancy)
    estimated_dob = add_or_subtract_days(date=conception_date, num_of_days=duration_of_pregnancy)
    return estimated_dob

def filter_pregnancy_month(month_of_pregnancy):
    month_of_pregnancy = re.sub("\D|0", "", str(month_of_pregnancy))
    return int(month_of_pregnancy[0]) if month_of_pregnancy else None

def determine_language(language_entry):
    return language_selector(language_input=language_entry, options=["Hindi", "English", "Gujarati"],
        default_option="Hindi", none_option="Hindi")

def determine_mother_tongue(mother_tongue):
    return language_selector(language_input=mother_tongue, options=["Hindi", "English", "Other"],
        default_option="Other", none_option=None)

def language_selector(language_input, options, default_option, none_option):
    language_input = re.sub("\W", "", str(language_input))
    if not language_input:
        return none_option

    if language_input in options:
        return language_input
    elif language_input[0] == "1":
        return "Hindi"
    elif language_input[0] == "2":
        return "English"
    elif language_input[0] == "3":
        return options[2]
    else:
        return default_option
