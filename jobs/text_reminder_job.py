from management.models import Contact
from modules.text_reminder import TextReminder

def remind_all():
    for contact in Contact.objects.all():
        TextReminder(contact).remind()

if __name__ == "__main__":
    remind_all()
