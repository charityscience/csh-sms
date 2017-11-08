import re
from management.models import Group
from modules.i18n import subscribe_keywords

def quote(word):
    return "`" + word + "`"


def add_contact_to_group(contact, group_name):
    group, _ = Group.objects.get_or_create(name=group_name)
    group.contacts.add(contact)
    group.save()
    return group


def phone_number_is_valid(phone_number):
    """Match any number starting with 91 or +91 that has another
        9 to 15 digits"""
    pattern = '^\+?91?\d{9,15}$'
    prepared_phone_number = prepare_phone_number(phone_number)
    return re.match(pattern, prepared_phone_number)

def remove_nondigit_characters(phone_number):
	return re.sub("[^0-9]", "", phone_number)

def add_country_code_to_phone_number(phone_number):
	if not phone_number:
		return phone_number

	begins_with_nine_one = re.match("^91", phone_number)
		
	if not begins_with_nine_one:
		phone_number = "91" + phone_number

	return phone_number

def prepare_phone_number(phone_number):
	if phone_number == None:
		return ""
	stripped_phone_number = remove_nondigit_characters(phone_number)
	if stripped_phone_number == "0" * len(stripped_phone_number):
		return ""
	elif len(stripped_phone_number) < 10:
		return phone_number
	return add_country_code_to_phone_number(stripped_phone_number)

def keywords_without_word(language, word):
	new_keys = subscribe_keywords(language)
	if word in new_keys:
		new_keys.remove(word)
	return new_keys