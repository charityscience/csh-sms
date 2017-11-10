import logging
from modules.texter import Texter
from modules.text_processor import TextProcessor
from management.models import Message

def check_and_process_registrations():
    logging.info("Checking and processing registrations...")
    messages = Texter().read_inbox()
    num_numbers = len(messages)
    num_messages = sum(list(map(lambda i: len(i[1]), messages.items())))
    logging.info("...Processing {} messages from {} numbers.".format(num_messages, num_numbers))

    for phone_number, texts in messages.items():
        t = TextProcessor(phone_number)
        for text in texts:
            message = t.write_to_database(message=text[0], date=text[1])
            if not message.is_processed:
                t.process(message)

    logging.info("...Completed.")
