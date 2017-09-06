import json
import re
import string

from six import unichr
from six.moves.urllib import request, parse
from datetime import timedelta

from cshsms.settings import TEXTLOCAL_API, TEXTLOCAL_PRIMARY_ID
from modules.date_helper import datetime_from_date_string


class TextLocal(object):
    def __init__(self, apikey, primary_id):
        self.apikey = apikey
        self.primary_id = primary_id


    def get_all_inboxes(self):
        params = {'apikey': self.apikey}
        inboxes_url = 'https://api.textlocal.in/get_inboxes/?'
        return self.get_url_response(request_url=inboxes_url, params=params)


    def get_primary_inbox(self):
        params = {'apikey': self.apikey, 'inbox_id': self.primary_id}
        messages_url = 'https://api.textlocal.in/get_messages/?'
        return self.get_url_response(request_url=messages_url, params=params)


    def get_url_response(self, request_url, params):
        f = request.urlopen(request_url + parse.urlencode(params))
        return json.loads(f.read().decode('latin1'))


    def get_primary_inbox_messages(self):
        return self.get_primary_inbox()['messages']


    def combine_messages(self, messages):
        # TextLocal will split messages that are too long into multiple messages.
        # This can (hopefully) be detected by looking for messages sent less than ten
        # seconds apart where the first message in the pair has a length of >250 chars.
        # ...Also, of course, the order of the message can't be guaranteed... :(
        # TODO: This is a very terrible loop :(
        combined_messages = []
        i = 0
        while i < len(messages):
            if i == len(messages) - 1:
                combined_messages.append(messages[i])
                i += 1
            elif messages[i]['number'] == messages[i + 1]['number']:
                first_message_date = datetime_from_date_string(messages[i]['date'], "%Y-%m-%d %H:%M:%S")
                second_message_date = datetime_from_date_string(messages[i + 1]['date'], "%Y-%m-%d %H:%M:%S")
                ten_seconds = timedelta(0, 10)
                if second_message_date - first_message_date < ten_seconds:
                    if len(messages[i]['message']) > 250:
                        message = messages[i]['message'] + messages[i + 1]['message']
                        combined_messages.append({'id': messages[i + 1]['id'],
                                                  'number': messages[i]['number'],
                                                  'message': message,
                                                  'date': messages[i + 1]['date'],
                                                  'isNew': messages[i]['isNew'] or messages[i + 1]['isNew'],
                                                  'status': messages[i + 1]['status']})
                        i += 2
                    elif len(messages[i + 1]['message']) > 250:
                        message = messages[i + 1]['message'] + messages[i]['message']
                        combined_messages.append({'id': messages[i + 1]['id'],
                                                  'number': messages[i]['number'],
                                                  'message': message,
                                                  'date': messages[i + 1]['date'],
                                                  'isNew': messages[i]['isNew'] or messages[i + 1]['isNew'],
                                                  'status': messages[i + 1]['status']})
                        i += 2
                    else:
                        combined_messages.append(messages[i])
                        i += 1
                else:
                    combined_messages.append(messages[i])
                    i += 1
            else:
                combined_messages.append(messages[i])
                i += 1
        return combined_messages


    def correct_unicode(self, messages):
        for message in messages:
            if '09' in message['message']:
                message['message'] = self.correct_corrupted_unicode_matches(message['message'])
        return messages

    def correct_corrupted_unicode_matches(self, message):
        fixed_message = []
        for message_part in message.split(' '):
            if all(c in string.hexdigits for c in message_part) and '0' in message_part and len(message_part) >= 4:
                fixed_message.append(''.join([unichr(int(message_part[i:i + 4], 16)) for i in range(0, len(message_part), 4)]))
            else:
                fixed_message.append(message_part)
        return ' '.join(fixed_message)
         

    def is_message_new(self, message):
        return True if message['isNew'] == True else False

    def new_messages_by_number(self):
        all_messages = self.get_primary_inbox_messages()
        combined_messages = self.combine_messages(all_messages)
        corrected_messages = self.correct_unicode(combined_messages)
        num_message_dict = {}
        for message in corrected_messages:
            if self.is_message_new(message):
                num_message_dict.setdefault(message['number'], []).append(message['message'])
        return num_message_dict
