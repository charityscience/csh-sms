from __future__ import absolute_import # I don't know why this is necessary to get these imports to work in Python 2 (only in this file!!!), but it is. :(
from management.models import Contact
from modules.text_reminder import TextReminder
from modules.date_helper import date_string_to_date

def contact_object(name=None, phone_number="1-111-1111", date_of_birth=None, language="English"):
    if name is None:
        name = 'Roland' if language == 'English' else u'\u0906\u0930\u0935'
    if date_of_birth is None:
        date_of_birth = datetime.now().date()
    if isinstance(date_of_birth, str):
        date_of_birth = date_string_to_date(date_of_birth)
    return Contact.objects.create(name=name,
                                  phone_number=phone_number,
                                  delay_in_days=0,
                                  language_preference=language,
                                  date_of_birth=date_of_birth,
                                  functional_date_of_birth=date_of_birth,
                                  method_of_sign_up="text")

def text_reminder_object(date_of_birth, language="English"):
    return TextReminder(contact_object(date_of_birth=date_of_birth, language=language))
