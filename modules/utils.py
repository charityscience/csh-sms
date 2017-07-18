from datetime import datetime

def quote(word):
    return "`" + str(word) + "`"

def date_string_to_date(date_string):
    sep = "-" if "-" in date_string else "/"
    if len(date_string.split(sep)) < 3:
        raise ValueError()
    year = "%Y" if len(date_string.split(sep)[2]) == 4 else "%y"
    pattern = "%d" + sep + "%m" + sep + year
    return datetime.strptime(date_string, pattern)

def date_is_valid(date_string):
    try:
        date = date_string_to_date(date_string)
        too_old = date.year < datetime.now().year - 18
        too_young = date.year > datetime.now().year + 2
        return (not too_old and not too_young)
    except ValueError:
        return False
