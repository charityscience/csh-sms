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


    def correct_unicode(self, messages):
        for message in messages:
            message['message'] = self.correct_corrupted_unicode_matches(message['message'])
        return messages

    def correct_corrupted_unicode_matches(self, message):
        fixed_message = []
        for message_part in message.split(' '):
            if all(c in string.hexdigits for c in message_part) and '09' in message_part and len(message_part) >= 4:
                fixed_message.append(''.join([unichr(int(message_part[i:i + 4], 16)) for i in range(0, len(message_part), 4)]))
            else:
                fixed_message.append(message_part)
        return ' '.join(fixed_message)
         

    def is_message_new(self, message):
        return True if message['isNew'] == True else False

    def new_messages_by_number(self):
        all_messages = self.get_primary_inbox_messages()
        corrected_messages = self.correct_unicode(all_messages)
        num_message_dict = {}
        for message in corrected_messages:
            if self.is_message_new(message):
                num_message_dict.setdefault(message['number'], []).append(message['message'])
        return num_message_dict