import logging
from modules.texter import Texter
from modules.text_processor import TextProcessor
from management.models import Message

def check_and_process_registrations():
    logging.info("Checking and processing registrations...")
    messages = Texter().read_inbox()
    num_numbers = len(messages)
    num_messages = sum(list(map(lambda i: len(i[1]), messages.items())))
    logging.info("...Writing {} messages from {} numbers to the database".format(num_messages, num_numbers))
    for phone_number, texts in messages.items():
        t = TextProcessor(phone_number)
        for text in texts:
            t.write_to_database(text)
    
    unprocessed_messages = Message.objects.filter(direction="Incoming", is_processed=False)
    num_unprocessed = unprocessed_messages.count()
    logging.info("...Processing {} messages from database".format(num_unprocessed))
    for message in unprocessed_messages:
        print("Message is: ", message)
        t.process(message)
    logging.info("...Completed.")
