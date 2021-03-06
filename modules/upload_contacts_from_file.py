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

def csv_upload(filepath, source):
    with open(filepath) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            new_dict = make_contact_dict(row, source)
            if phone_number_is_valid(new_dict["phone_number"]):
                new_contact, created = Contact.objects.update_or_create(name=new_dict["name"],
                    phone_number=new_dict["phone_number"], defaults=new_dict)

                assign_groups_to_contact(new_contact, row.get("Groups"))
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
    new_dict["preg_signup"] = assign_preg_signup(row=row, headers=headers["preg_signup"])
    new_dict["date_of_birth"] = determine_date_of_birth(row=row, dob_headers=headers["date_of_birth"],
        month_headers=headers["month_of_pregnancy"], date_of_signup=new_dict["date_of_sign_up"],
        preg_signup=new_dict["preg_signup"], source=source)
    new_dict["functional_date_of_birth"] = parse_or_create_functional_dob(row=row, headers=headers["functional_date_of_birth"],
        source=source, date_of_birth=new_dict["date_of_birth"], delay=new_dict["delay_in_days"])

    # Personal Info
    new_dict["gender"] = entry_or_empty_string(row=row, headers=headers["gender"])
    new_dict["mother_tongue"] = determine_mother_tongue(row=row, headers=headers["mother_tongue"])
    new_dict["religion"] = entry_or_empty_string(row=row, headers=headers["religion"])
    new_dict["state"] = entry_or_empty_string(row=row, headers=headers["state"])
    new_dict["division"] = entry_or_empty_string(row=row, headers=headers["division"])
    new_dict["district"] = entry_or_empty_string(row=row, headers=headers["district"])
    new_dict["city"] = entry_or_empty_string(row=row, headers=headers["city"])
    new_dict["monthly_income_rupees"] = monthly_income(row=row, headers=headers["monthly_income_rupees"])
    new_dict["children_previously_vaccinated"] = previous_vaccination(row=row, headers=headers["children_previously_vaccinated"])
    new_dict["not_vaccinated_why"] = entry_or_empty_string(row=row, headers=headers["not_vaccinated_why"])
    new_dict["mother_first_name"] = entry_or_empty_string(row=row, headers=headers["mother_first_name"])
    new_dict["mother_last_name"] = entry_or_empty_string(row=row, headers=headers["mother_last_name"])

    # Type of Sign Up
    new_dict["method_of_sign_up"] = assign_method_of_signup(row=row, headers=headers["method_of_sign_up"], source=source)
    new_dict["org_sign_up"] = assign_org_signup(row=row, headers=headers["org_sign_up"], source=source)
    new_dict["hospital_name"] = assign_hospital_name(row=row, headers=headers["hospital_name"],
        method_of_signup=new_dict["method_of_sign_up"], org_signup=new_dict["org_sign_up"])
    new_dict["doctor_name"] = entry_or_empty_string(row=row, headers=headers["doctor_name"])

    # System Identification
    new_dict["telerivet_contact_id"] = entry_or_empty_string(row=row, headers=headers["telerivet_contact_id"])
    new_dict["trial_id"] = entry_or_empty_string(row=row, headers=headers["trial_id"])
    new_dict["trial_group"] = entry_or_empty_string(row=row, headers=headers["trial_group"])

    # Message References
    new_dict["preferred_time"] = entry_or_empty_string(row=row, headers=headers["preferred_time"])
    new_dict["script_selection"] = entry_or_empty_string(row=row, headers=headers["script_selection"])
    new_dict["telerivet_sender_phone"] = entry_or_empty_string(row=row, headers=headers["telerivet_sender_phone"])
    new_dict["last_heard_from"] = time_reference_or_none(row=row, headers=headers["last_heard_from"])
    new_dict["last_contacted"] = time_reference_or_none(row=row, headers=headers["last_contacted"])
    new_dict["time_created"] = parse_contact_time_references(row=row, headers=headers["time_created"])
    return new_dict

def assign_groups_to_contact(contact, groups_string):
    if not groups_string:
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

def previous_vaccination(row, headers):
    row_entry = check_all_headers(row=row, headers=headers)
    if row_entry is None or row_entry == "":
        return None
    
    if "y" == row_entry[0].lower():
        return True
    elif "n" == row_entry[0].lower():
        return False
    elif "y" in row_entry.lower():
        return True
    elif "n" in row_entry.lower():
        return False
    else:
        return None

def monthly_income(row, headers):
    row_entry = check_all_headers(row=row, headers=headers)
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

def parse_contact_time_references(row, headers):
    row_entry = check_all_headers(row=row, headers=headers)
    return datetime_string_mdy_to_datetime(row_entry) if row_entry else datetime.datetime.now().replace(tzinfo=timezone.get_default_timezone())

def time_reference_or_none(row, headers):
    row_entry = check_all_headers(row=row, headers=headers)
    return datetime_string_mdy_to_datetime(row_entry) if row_entry else None

def assign_preg_signup(row, headers):
    row_entry = entry_or_empty_string(row=row, headers=headers).lower()
    if not row_entry:
        return False
    elif "pregnant" in row_entry:
        return True
    elif row_entry[0] == "1" or row_entry[0] == "t":
        return True
    else:
        return False

def determine_date_of_birth(row, dob_headers, month_headers, date_of_signup, preg_signup, source):
    date_of_birth_entry = entry_or_empty_string(row=row, headers=dob_headers)

    if preg_signup and not date_of_birth_entry:
        month_of_pregnancy = filter_pregnancy_month(row=row, headers=month_headers)
        return estimate_date_of_birth(month_of_pregnancy=month_of_pregnancy, date_of_sign_up=date_of_signup)

    return entered_date_string_to_date(row=row, headers=dob_headers, source=source)

def estimate_date_of_birth(month_of_pregnancy, date_of_sign_up):
    duration_of_pregnancy = 280 # mean number of days of a pregnancy
    if month_of_pregnancy is None or type(month_of_pregnancy) != int:
        return None

    conception_date = add_or_subtract_months(date=date_of_sign_up, num_of_months=-month_of_pregnancy)
    estimated_dob = add_or_subtract_days(date=conception_date, num_of_days=duration_of_pregnancy)
    return estimated_dob

def filter_pregnancy_month(row, headers):
    month_of_pregnancy = entry_or_empty_string(row=row, headers=headers)
    if not month_of_pregnancy:
        return None
    elif month_of_pregnancy == "0":
        return 0
    month_of_pregnancy = re.sub("\D|0", "", str(month_of_pregnancy))
    return int(month_of_pregnancy[0]) if month_of_pregnancy else None

def determine_language(row, headers):
    language_entry = check_all_headers(row=row, headers=headers)
    return language_selector(language_input=language_entry, options=["Hindi", "English", "Gujarati"],
        default_option="Hindi", none_option="Hindi")

def determine_mother_tongue(row, headers):
    mother_tongue = check_all_headers(row=row, headers=headers)
    return language_selector(language_input=mother_tongue, options=["Hindi", "English", "Other"],
        default_option="", none_option="")

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
        name_entry = entry_or_empty_string(row=row, headers=headers)
        return replace_blank_name(name_entry.encode("utf-8").decode('unicode-escape'), language)
    else:
        return nickname.encode("utf-8").decode('unicode-escape')

def assign_org_signup(row, headers, source):
    return source.upper() if source.upper() != "TR" else entry_or_empty_string(row=row, headers=headers)

def assign_method_of_signup(row, headers, source):
    if source.lower() in ["maps", "hansa"]:
        return "Door to Door"
    elif source.lower() in ["wardha"]:
        return "Hospital"
    else:
        return entry_or_empty_string(row=row, headers=headers)

def assign_hospital_name(row, headers, method_of_signup, org_signup):
    return org_signup.capitalize() if method_of_signup == "Hospital" else entry_or_empty_string(row=row, headers=headers)