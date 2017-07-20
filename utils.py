from datetime import datetime
from django.utils import timezone 

def quote(word):
    return "`" + str(word) + "`"

def date_string_to_date(date_string):
    return datetime.strptime(date_string, "%d/%m/%y")

def date_is_valid(date_string):
    try:
        date_string_to_date(date_string)
        return True
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