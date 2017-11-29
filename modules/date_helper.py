from datetime import datetime
from django.utils import timezone 
from dateutil.relativedelta import relativedelta
import logging
from modules.utils import quote

def date_string_to_date(date_string):
    sep = "-" if "-" in date_string else "/"
    if len(date_string.split(sep)) < 3:
        raise ValueError()
    year = "%Y" if len(date_string.split(sep)[2]) == 4 else "%y"
    pattern = "%d" + sep + "%m" + sep + year
    return datetime.strptime(date_string, pattern).date()

def date_to_date_string(date):
    return '{d}/{m}/{y}'.format(d = date.day,
                                m = date.month,
                                y = date.year)

def date_is_valid(date_string):
    try:
        date = date_string_to_date(date_string)
        too_old = date.year < datetime.now().year - 18
        too_young = date.year > datetime.now().year + 2
        return (not too_old and not too_young)
    except ValueError:
        return False

def date_string_dmy_to_date(date_string):
	for fmt in ["%d-%m-%Y", "%d/%m/%Y"]:
		try:
			return  datetime_from_date_string(date_string, fmt).date()
		except ValueError:
			pass
	raise ValueError("No valid day-month-year date format")

def date_string_ymd_to_date(date_string):
	for fmt in ["%Y-%m-%d", "%Y/%m/%d"]:
		try:
			return datetime_from_date_string(date_string, fmt).date()
		except ValueError:
			pass
	raise ValueError("No valid year-month-day date format")

def date_string_mdy_to_date(date_string):
	for fmt in ["%m-%d-%Y", "%m/%d/%Y"]:
		try:
			return  datetime_from_date_string(date_string, fmt).date()
		except ValueError:
			pass
	raise ValueError("No valid month-day-year date format")

def try_parsing_partner_date(date_string):
	try:
		return date_string_dmy_to_date(date_string)
	except ValueError:
		return date_string_ymd_to_date(date_string)

def try_parsing_gen_date(date_string):
	try:
	    return date_string_ymd_to_date(date_string)
	except ValueError:
		return date_string_mdy_to_date(date_string)

def datetime_string_mdy_to_datetime(date_string):
	return  datetime_from_date_string(date_string, "%m/%d/%Y %I:%M:%S %p").replace(tzinfo=timezone.get_default_timezone())

def datetime_string_ymd_to_datetime(date_string):
		try:
			return datetime_from_date_string(date_string, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.get_default_timezone())
		except ValueError:
			logging.error("Invalid datetime entry for message: " + quote(date_string))
			return datetime.now().replace(tzinfo=timezone.get_default_timezone())

def datetime_from_date_string(date_string, date_format):
	return datetime.strptime(date_string.strip(), date_format)

def add_or_subtract_days(date, num_of_days):
	return date + relativedelta(days=num_of_days)

def add_or_subtract_weeks(date, num_of_weeks):
	return date + relativedelta(weeks=num_of_weeks)

def add_or_subtract_months(date, num_of_months):
	return date + relativedelta(months=num_of_months)

def add_or_subtract_years(date, num_of_years):
	return date + relativedelta(years=num_of_years)

def get_modified_dates(date_of_birth):
	six_weeks = add_or_subtract_weeks(date_of_birth, 6)
	ten_weeks = add_or_subtract_weeks(date_of_birth, 10)
	fourteen_weeks = add_or_subtract_weeks(date_of_birth, 14)
	nine_months = add_or_subtract_months(date_of_birth, 9)
	sixteen_months = add_or_subtract_months(date_of_birth, 16)
	five_years = add_or_subtract_years(date_of_birth, 5)
	modified_dates = {"six_weeks": six_weeks,
					  "ten_weeks": ten_weeks,
					  "fourteen_weeks": fourteen_weeks,
					  "nine_months": nine_months,
					  "sixteen_months": sixteen_months,
					  "five_years": five_years}
	return modified_dates

