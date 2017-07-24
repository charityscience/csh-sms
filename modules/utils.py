from datetime import datetime
from django.utils import timezone 
from management.models import Group

def quote(word):
    return "`" + word + "`"


def add_contact_to_group(contact, group_name):
    group, _ = Group.objects.get_or_create(name=group_name)
    group.contacts.add(contact)
    group.save()
    return group


def date_string_to_date(date_string):
    sep = "-" if "-" in date_string else "/"
    if len(date_string.split(sep)) < 3:
        raise ValueError()
    year = "%Y" if len(date_string.split(sep)[2]) == 4 else "%y"
    pattern = "%d" + sep + "%m" + sep + year
    return datetime.strptime(date_string, pattern).date()

def date_is_valid(date_string):
    try:
        date = date_string_to_date(date_string)
        too_old = date.year < datetime.now().year - 18
        too_young = date.year > datetime.now().year + 2
        return (not too_old and not too_young)
    except ValueError:
        return False

def date_string_ymd_to_date(date_string):
	return  datetime_from_date_string(date_string, "%Y-%m-%d").date()

def date_string_mdy_to_date(date_string):
	return  datetime_from_date_string(date_string, "%m-%d-%Y").date()

def datetime_string_mdy_to_datetime(date_string):
	return  datetime_from_date_string(date_string, "%m/%d/%Y %I:%M:%S %p").replace(tzinfo=timezone.get_default_timezone())

def datetime_from_date_string(date_string, date_format):
	return datetime.strptime(date_string.strip(), date_format)
