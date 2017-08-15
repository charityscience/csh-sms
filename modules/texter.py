from cshsms.settings import TEXTLOCAL_API, TEXTLOCAL_PRIMARY_ID, HSPSMS_API, HSPSMS_USERNAME, HSPSMS_SENDERNAME
from modules.textlocalwrapper import TextLocal
from modules.hspsmswrapper import Hspsms

class Texter(object):
	def read_inbox(self):
	    textlocal = TextLocal(apikey=TEXTLOCAL_API, primary_id=TEXTLOCAL_PRIMARY_ID)
	    messages = textlocal.get_primary_inbox_messages()
	    num_message_dict = textlocal.new_messages_by_number(messages)
	    return num_message_dict

	def send(self, message, phone_number):
		hspsms = Hspsms(apikey=HSPSMS_API, username=HSPSMS_USERNAME, sendername=HSPSMS_SENDERNAME)
		send_status = hspsms.send_transactional_message(message=message, phone_number=phone_number)
		return send_status