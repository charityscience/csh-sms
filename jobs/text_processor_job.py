import logging
from modules.texter import Texter
from modules.text_processor import TextProcessor

def check_and_process_registrations():
    logging.info("Checking and processing registrations...")
    messages = Texter.read_inbox()
    num_numbers = len(messages)
    num_messages = sum(list(map(lambda i: len(i[1]), messages.items())))
    logging.info("...Processing {} messages from {} numbers".format(num_messages, num_numbers))
    for phone_number, texts in messages.items():
        t = TextProcessor(phone_number)
        for text in texts:
            t.process(text)
    logging.info("...Completed.")

if __name__ == "__main__":
    check_and_process_registrations()
