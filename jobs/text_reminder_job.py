import logging
from management.models import Contact
from modules.text_reminder import TextReminder

def remind_all():
    logging.info("Checking {} contacts for reminders...".format(Contact.objects.count()))
    reminds = 0
    for contact in Contact.objects.all():
        reminds += TextReminder(contact).remind()
    logging.info("...Completed. Send {} reminders.".format(reminds))
