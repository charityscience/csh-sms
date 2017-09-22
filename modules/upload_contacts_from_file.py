import csv
import re
import datetime
import logging
from django.utils import timezone
from modules.utils import add_contact_to_group, phone_number_is_valid, prepare_phone_number
from modules.date_helper import try_parsing_partner_date, try_parsing_gen_date, datetime_string_mdy_to_datetime, \
                                add_or_subtract_days, add_or_subtract_months
from modules.i18n import hindi_placeholder_name, gujarati_placeholder_name
from modules.csv_columns import column_headers
from management.models import Contact
from six import u

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
    headers = column_headers()
    new_dict["language_preference"] = determine_language(row=row, headers=headers["language_preference"])
    new_dict["name"] = determine_name(row=row, headers=headers["name"], language=new_dict["language_preference"]) 
    new_dict["phone_number"] = prepare_phone_number(check_all_headers(row=row, headers=headers["phone_number"]))
    new_dict["alt_phone_number"] = prepare_phone_number(check_all_headers(row=row, headers=headers["alt_phone_number"]))
    new_dict["delay_in_days"] = parse_or_create_delay_num(row=row, headers=headers["delay_in_days"])
    new_dict["date_of_sign_up"] = entered_date_string_to_date(row=row, headers=headers["date_of_sign_up"], source=source)
    new_dict["date_of_birth"] = entered_date_string_to_date(row=row, headers=headers["date_of_birth"], source=source)
    new_dict["functional_date_of_birth"] = parse_or_create_functional_dob(row=row, headers=headers["functional_date_of_birth"],
        source=source, date_of_birth=new_dict["date_of_birth"], delay=new_dict["delay_in_days"])

    # Personal Info
    new_dict["gender"] = row.get("Gender")
    new_dict["mother_tongue"] = determine_mother_tongue(row=row, headers=headers["mother_tongue"])
    new_dict["religion"] = row.get("Religion")
    new_dict["state"] = row.get("State")
    new_dict["division"] = row.get("Division")
    new_dict["district"] = row.get("District")
    new_dict["city"] = row.get("City")
    new_dict["monthly_income_rupees"] = monthly_income(row.get("Monthly Income"))
    new_dict["children_previously_vaccinated"] = previous_vaccination(row.get("Previously had children vaccinated").lower())
    new_dict["not_vaccinated_why"] = row.get("If not vaccinated why")
    new_dict["mother_first_name"] = row.get("Mother's First")
    new_dict["mother_last_name"] = row.get("Mother's Last")

    # Type of Sign Up
    new_dict["method_of_sign_up"] = row.get("Method of Sign Up")
    new_dict["org_sign_up"] = row.get("Org Sign Up")
    new_dict["hospital_name"] = row.get("Hospital Name")
    new_dict["doctor_name"] = row.get("Doctor Name")
    new_dict["preg_signup"] = parse_preg_signup(row.get("Pregnant Signup"))

    # System Identification
    new_dict["telerivet_contact_id"] = row.get("Telerivet Contact ID")
    new_dict["trial_id"] = row.get("Trial ID")
    new_dict["trial_group"] = row.get("Trial Group")

    # Message References
    new_dict["preferred_time"] = row.get("Preferred Time")
    new_dict["script_selection"] = row.get("Script Selection")
    new_dict["telerivet_sender_phone"] = row.get("Sender Phone")
    new_dict["last_heard_from"] = parse_contact_time_references(row.get("Last Heard From"))
    new_dict["last_contacted"] = parse_contact_time_references(row.get("Last Contacted"))
    new_dict["time_created"] = parse_contact_time_references(row.get("Time Created"))
    return new_dict

def assign_groups_to_contact(contact, groups_string):
    if groups_string == "":
        return None
    for group_name in groups_string.split(", "):
        add_contact_to_group(contact, group_name)

def matching_permutation(row, header):
    permutations = [header, header + " ", " " + header + " ",
                    header + ",", header + ".", "The " + header,
                    header[0:-1], header[1:]]

    for perm in permutations:
        if row.get(perm):
            return perm
        elif row.get(perm.capitalize()):
            return perm.capitalize()
        elif row.get(perm.title()):
            return perm.title()
        elif row.get(perm.upper()):
            return perm.upper()
        elif row.get(perm.lower()):
            return perm.lower()
    
    return None

def check_all_headers(row, headers):
    for header in headers:
        if row.get(header):
            return row.get(header)
        
    for header in headers:
        matching_key = matching_permutation(row=row, header=header)
        if matching_key:
            return row.get(matching_key)

    return None

def entry_or_empty_string(row, headers):
    row_entry = check_all_headers(row=row, headers=headers)
    return "" if row_entry is None else row_entry 

def previous_vaccination(row_entry):
    if "y" in row_entry:
        return True
    elif "n" in row_entry:
        return False
    else:
        return None

def monthly_income(row_entry):
    return int(row_entry) if row_entry and not re.search("\D+", row_entry) else 999999

def parse_or_create_delay_num(row, headers):
    delay_input = check_all_headers(row=row, headers=headers)
    if delay_input is None:
        return 0
    else:
        delay_input = delay_input.replace(",", "")
    return int(delay_input) if delay_input and not re.search("\D+", delay_input) else 0

def entered_date_string_to_date(row, headers, source):
    row_entry = check_all_headers(row=row, headers=headers)
    return try_parsing_gen_date(row_entry) if source == "TR" else try_parsing_partner_date(row_entry)

def parse_or_create_functional_dob(row, headers, source, date_of_birth, delay):
    row_entry = check_all_headers(row=row, headers=headers)
    return entered_date_string_to_date(row=row, headers=headers, source=source) if row_entry else add_or_subtract_days(date_of_birth, delay)

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

def determine_language(row, headers):
    language_entry = check_all_headers(row=row, headers=headers)
    return language_selector(language_input=language_entry, options=["Hindi", "English", "Gujarati"],
        default_option="Hindi", none_option="Hindi")

def determine_mother_tongue(row, headers):
    mother_tongue = check_all_headers(row=row, headers=headers)
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

def replace_blank_name(name, language):
    if not name or name == len(name) * " ":
        if language == "English":
            return "Your child"
        elif language == "Hindi":
            return hindi_placeholder_name()
        elif language == "Gujarati":
            return gujarati_placeholder_name()
    else:
        return name

def determine_name(row, headers, language):
    nickname = row.get("Nick Name of Child")
    if not nickname or nickname == len(nickname) * " ":
        name_entry = check_all_headers(row=row, headers=headers)
        return replace_blank_name(u(name_entry.encode("utf-8").decode('unicode-escape')), language)
    else:
        return nickname.encode("utf-8").decode('unicode-escape')

def assign_org_signup(row, source):
    return source.upper() if source.upper() != "TR" else row.get("Org Sign Up")

def assign_method_of_signup(row, source):
    if source.lower() in ["maps", "hansa"]:
        return "Door to Door"
    elif source.lower() in ["wardha"]:
        return "Hospital"
    else:
        return row.get("Method of Sign Up")

def assign_hospital_name(row, method_of_signup, org_signup):
    return org_signup.capitalize() if method_of_signup == "Hospital" else row.get("Hospital Name")