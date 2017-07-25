from management.models import Group

def quote(word):
    return "`" + word + "`"

def add_contact_to_group(contact, group_name):
    group, _ = Group.objects.get_or_create(name=group_name)
    group.contacts.add(contact)
    group.save()
    return group
