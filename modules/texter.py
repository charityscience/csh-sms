from cshsms.settings import TEXTLOCAL_API, TEXTLOCAL_PRIMARY_ID
from modules.textlocalwrapper import TextLocal

class Texter(object):
	def get_all_inboxes(self, apikey):
		# TODO: Get every inbox an API returns
		return inboxes

	def read_inbox(self):
	    # TODO: Implement for real
	    # TODO: Get all messages in the inbox.
	    textlocal = TextLocal(apikey=TEXTLOCAL_API, primary_id=TEXTLOCAL_PRIMARY_ID)
	    messages = textlocal.get_primary_inbox_messages()
	    num_message_dict = textlocal.new_messages_by_number(messages)
	    return num_message_dict

	def send(self, message, phone_number):
		#TODO: Implement for real
		print("I SENT THIS TEXT: '" + message + "`.")
		return None