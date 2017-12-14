from cshsms.settings import TEXTLOCAL_API, TEXTLOCAL_PRIMARY_ID, HSPSMS_API, HSPSMS_USERNAME, HSPSMS_SENDERNAME, TEXTLOCAL_SENDERNAME
from modules.textlocalwrapper import TextLocal
from modules.hspsmswrapper import Hspsms

class Texter(object):
    def read_inbox(self):
        textlocal = TextLocal(apikey=TEXTLOCAL_API, primary_id=TEXTLOCAL_PRIMARY_ID, sendername=TEXTLOCAL_SENDERNAME)
        num_message_dict = textlocal.new_messages_by_number()
        return num_message_dict

    def send(self, message, phone_number):
        textlocal = TextLocal(apikey=TEXTLOCAL_API,
                        primary_id=TEXTLOCAL_PRIMARY_ID,
                        sendername=TEXTLOCAL_SENDERNAME)
        send_status = textlocal.send_message(message=message,
                                            phone_numbers=phone_number)
        return send_status

    def read_api_outbox(self):
        textlocal = TextLocal(apikey=TEXTLOCAL_API, primary_id=TEXTLOCAL_PRIMARY_ID, sendername=TEXTLOCAL_SENDERNAME)
        num_message_dict = textlocal.new_api_send_messages_by_number()
        return num_message_dict