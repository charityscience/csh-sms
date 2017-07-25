import time
from modules.texter import Texter
from modules.text_processor import TextProcessor

def check_and_process_registrations():
    for phone_number, messages in Texter.read_inbox().items():
        t = TextProcessor(phone_number)
        for message in messages:
            t.process(message)

if __name__ == "__main__":
    check_and_process_registrations()
