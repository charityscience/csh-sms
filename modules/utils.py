import re
from management.models import Group

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
    return re.match(pattern, phone_number)