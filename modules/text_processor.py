import logging
import string

from django.utils import timezone
from django.core.exceptions import MultipleObjectsReturned

from management.models import Contact, Group, Message
from modules.texter import Texter
from modules.utils import quote, add_contact_to_group
from modules.date_helper import date_is_valid, date_string_to_date
from modules.i18n import msg_subscribe, msg_unsubscribe, msg_placeholder_child, msg_failure, \
                         msg_failed_date, subscribe_keywords, msg_already_sub, hindi_born

class TextProcessor(object):
    def __init__(self, phone_number):
        self.phone_number = phone_number
        self.get_contacts()
        if self.contacts.exists():
            self.language = self.contacts.first().language_preference
        else:
            self.language = None

    # self.get_contacts() is preferred to self.contact due to triggering a Django DB reload.
    def get_contacts(self):
        self.contacts = Contact.objects.filter(phone_number=self.phone_number)
        return self.contacts


    def create_contact(self, child_name, phone_number, date_of_birth, language, preg_update=False):
        if self.contacts.exists():
            contact = Contact.objects.filter(name=child_name, phone_number=self.phone_number)
            if contact.exists():
                contact = contact.first()
                if contact.cancelled or preg_update:
                    # Update and resubscribe
                    contact.cancelled = False
                    contact.language_preference = language
                    contact.date_of_birth = date_of_birth
                    contact.functional_date_of_birth = date_of_birth
                    contact.preg_update = preg_update
                    contact.save()
                    return True
                else:
                    # Already exists (error)
                    logging.error("Contact for {name} at {phone} was subscribed but already exists!".format(name=child_name, phone=self.phone_number))
                    return False 
        # Otherwise, create
        contact = Contact.objects.create(name=child_name,
                                         phone_number=phone_number,
                                         delay_in_days=0,
                                         language_preference=language,
                                         date_of_birth=date_of_birth,
                                         functional_date_of_birth=date_of_birth,
                                         method_of_sign_up="Text")
        for group_name in ["Text Sign Ups",
                           "Text Sign Ups - " + language.title(),
                           "Everyone - " + language.title()]:
            add_contact_to_group(contact, group_name)
        self.get_contacts()
        return True


    def cancel_contacts(self):
        for contact in self.contacts:
            contact.cancelled = True
            contact.save()
        return True


    def process_subscribe(self, child_name, date_of_birth, preg_update):
        if self.create_contact(child_name=child_name,
                               phone_number=self.phone_number,
                               date_of_birth=date_of_birth,
                               language=self.language,
                               preg_update=preg_update):
            return msg_subscribe(self.language).format(name=child_name)
        else:
            return msg_already_sub(self.language)


    def process_unsubscribe(self, child_name, date_of_birth, preg_update=False):
        if self.contacts.exists():
            self.cancel_contacts()
            return msg_unsubscribe(self.language)
        else:
            logging.error(quote(self.phone_number) + " asked to be unsubscribed but does not exist.")
            return msg_unsubscribe("English")


    def process_failure(self, child_name, date_of_birth, preg_update=False):
        return msg_failure(self.language)


    def process_failed_date(self, child_name, date_of_birth, preg_update=False):
        return msg_failed_date(self.language)


    def get_data_from_message(self, message):
        """Get the keyword, child name, and the date from the message.
            A text will look like `<KEYWORD> <CHILD> <DATE OF BIRTH>`, like
            `REMIND NATHAN 25/11/2015`. Sometimes the child name is omitted."""
        message = message.lower().split(" ")
        if len(message) == 1:
            keyword = message[0]
            date = None
            child_name = None
        elif len(message) == 2:
            keyword, date = message
            child_name = None
        else:
            keyword, child_name, date = message[0:3]
        date = date_string_to_date(date) if date and date_is_valid(date) else None
        return (keyword, child_name, date)


    def process(self, message):
        """This is the main function that is run on an incoming text message to process it."""
        keyword, child_name, date = self.get_data_from_message(message)
        preg_update = False
        if keyword in subscribe_keywords("English"):
            self.language = "English"
            if keyword == "born":
                preg_update = True
            action = self.process_subscribe
        elif keyword in subscribe_keywords("Hindi"):
            self.language = "Hindi"
            if keyword == hindi_born():
                preg_update = True
            action = self.process_subscribe
        elif keyword == "end":
            action = self.process_unsubscribe
        else:
            logging.error("Keyword " + quote(keyword) + " in message " + quote(message) +
                          " was not understood by the system.")
            self.language = "Hindi" if keyword and keyword[0] not in string.ascii_lowercase else "English"
            action = self.process_failure

        if action == self.process_subscribe:
            if child_name is None:
                # If a child name is not found, we call them "your child".
                child_name = msg_placeholder_child(self.language)
            else:
                child_name = child_name.title()

            if len(child_name) > 50:
                action = self.process_failure

            if date is None:
                logging.error("Date in message " + quote(message) + " is invalid.")
                action = self.process_failed_date

        if action == self.process_subscribe:
            logging.info("Subscribing " + quote(message) + "...")
        elif action == self.process_unsubscribe:
            logging.info("Unsubscribing " + quote(self.phone_number) + "...")

        response_text_message = action(child_name=child_name,
                                       date_of_birth=date, preg_update=preg_update)
        self.create_message_object(child_name=child_name, phone_number=self.phone_number,
                                    language=self.language, body=response_text_message,
                                    direction="Outgoing")
        Texter().send(message=response_text_message,
                        phone_number=self.phone_number)
        return response_text_message

    def create_message_object(self, child_name, phone_number, language, body, direction):
        if not child_name or len(child_name) > 50:
            if not language:
                language = "English"   
            child_name = msg_placeholder_child(language)
        try:
            contact, _ = Contact.objects.get_or_create(phone_number=phone_number)
        except MultipleObjectsReturned:
            contact = Contact.objects.get(name=child_name, phone_number=phone_number)

        Message.objects.create(contact=contact, direction=direction, body=body)
        return True