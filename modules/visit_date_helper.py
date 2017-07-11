from dateutil.relativedelta import relativedelta

def add_or_subtract_days(date_of_birth, num_of_days):
	return date_of_birth + relativedelta(days=num_of_days)

def add_or_subtract_weeks(date_of_birth, num_of_weeks):
	return date_of_birth + relativedelta(weeks=num_of_weeks)

def add_or_subtract_months(date_of_birth, num_of_months):
	return date_of_birth + relativedelta(months=num_of_months)

def add_or_subtract_years(date_of_birth, num_of_years):
	return date_of_birth + relativedelta(years=num_of_years)

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
