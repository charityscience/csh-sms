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
        self.set_language(default=None)

    def set_language(self, default):
        if self.get_contacts().exists():
            self.language = self.contacts.first().language_preference or default
        else:
            self.language = None

    # self.get_contacts() is preferred to self.contact due to triggering a Django DB reload.
    def get_contacts(self):
        self.contacts = Contact.objects.filter(phone_number=self.phone_number)
        return self.contacts


    def create_contact(self, child_name, phone_number, date_of_birth, language, preg_update=False):
        contact = Contact.objects.filter(name=child_name, phone_number=self.phone_number).first()
        if contact:
            if contact.cancelled or preg_update:
                # Update and resubscribe
                contact.cancelled = False
                contact.language_preference = language
                contact.date_of_birth = date_of_birth
                contact.functional_date_of_birth = date_of_birth
                contact.preg_update = preg_update
                contact.save()
                return True
            elif Message.objects.filter(contact=contact,
                                        direction="Outgoing",
                                        body=msg_subscribe(language).format(name=contact.name)).exists():
                # Already exists (error)
                logging.error("Contact for {name} at {phone} was subscribed but already exists!".format(name=child_name, phone=self.phone_number))
                return False

        # Otherwise, create
        update_dict = {"delay_in_days": 0,
                       "language_preference": self.language,
                       "date_of_birth": date_of_birth,
                       "functional_date_of_birth": date_of_birth,
                       "method_of_sign_up": "Text"}
        contact, _ = Contact.objects.update_or_create(name=child_name,
                                                      phone_number=phone_number,
                                                      defaults=update_dict)
        for group_name in ["Text Sign Ups",
                           "Text Sign Ups - " + self.language.title(),
                           "Everyone - " + self.language.title()]:
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
            if child_name is None or date_of_birth is None or self.language is None:
                logging.error(quote(self.phone_number) + " asked to be unsubscribed but some data is missing on the existing contact object.")
            self.cancel_contacts()
        else:
            logging.error(quote(self.phone_number) + " asked to be unsubscribed but does not exist.")
        return msg_unsubscribe(self.language or "English")


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

    def write_to_database(self, message):
        keyword, child_name, date = self.get_data_from_message(message)
        inferred_language = "Hindi" if keyword and keyword[0] not in string.ascii_lowercase else "English"
        language = self.language or inferred_language

        if not child_name and self.get_contacts():
            contact = self.get_contacts().first()
            child_name = contact.name

        if child_name:
            child_name = child_name.title()

        incoming = self.create_message_object(child_name=child_name,
                                              phone_number=self.phone_number,
                                              language=language,
                                              body=message,
                                              direction="Incoming")

        contact = Contact.objects.get(pk=incoming.contact.id)
        contact.last_heard_from = incoming.time
        contact.save()
        self.get_contacts()
        return incoming

    def process(self, message):
        """This is the main function that is run on an message to process it."""
        contact = Contact.objects.get(pk=message.contact.id)
        keyword, child_name, date = self.get_data_from_message(message.body)
        preg_update = False
        if keyword in subscribe_keywords("English"):
            self.set_language(default="English")
            if keyword == "born":
                preg_update = True
            action = self.process_subscribe
        elif keyword in subscribe_keywords("Hindi"):
            self.set_language(default="Hindi")
            if keyword == hindi_born():
                preg_update = True
            action = self.process_subscribe
        elif keyword == "end":
            self.set_language(default="English")
            action = self.process_unsubscribe
        else:
            self.set_language(default="English")
            logging.error("Keyword " + quote(keyword) + " in message " + quote(message.body) +
                          " was not understood by the system.")
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
                logging.error("Date in message " + quote(message.body) + " is invalid.")
                action = self.process_failed_date

        if action == self.process_subscribe:
            logging.info("Subscribing " + quote(message.body) + "...")
        elif action == self.process_unsubscribe:
            logging.info("Unsubscribing " + quote(contact.phone_number) + "...")

        response_text_message = action(child_name=child_name,
                                       date_of_birth=date,
                                       preg_update=preg_update)

        outgoing = self.create_message_object(child_name=contact.name,
                                              phone_number=contact.phone_number,
                                              language=self.language,
                                              body=response_text_message,
                                              direction="Outgoing")
        contact = Contact.objects.get(pk=outgoing.contact.id)
        contact.last_contacted = outgoing.time
        contact.save()
        self.get_contacts()
        Texter().send(message=response_text_message,
                      phone_number=self.phone_number)
        outgoing.is_processed = True
        outgoing.save()
        message.is_processed = True
        message.save()
        return response_text_message

    def create_message_object(self, child_name, phone_number, language, body, direction):
        if not child_name or len(child_name) > 50:
            if not language:
                language = "English"
            child_name = msg_placeholder_child(language)
        try:
            contact, _ = Contact.objects.get_or_create(name=child_name,
                                                       phone_number=phone_number,
                                                       language_preference=language)
        except MultipleObjectsReturned:
            contact = Contact.objects.filter(name=child_name,
                                             phone_number=phone_number,
                                             language_preference=language).first()

        return Message.objects.create(contact=contact, direction=direction, body=body)
        
