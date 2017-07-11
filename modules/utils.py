from datetime import datetime

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
