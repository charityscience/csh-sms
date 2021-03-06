import json
import re
import string

from six import unichr, u
from six.moves.urllib import request, parse
from datetime import timedelta, datetime
from django.utils import timezone

from cshsms.settings import TEXTLOCAL_API, TEXTLOCAL_PRIMARY_ID, TEXTLOCAL_SENDERNAME
from modules.date_helper import datetime_string_ymd_to_datetime
from modules.utils import is_not_ascii


class TextLocal(object):
    def __init__(self, apikey, primary_id, sendername):
        self.apikey = apikey
        self.primary_id = primary_id
        self.sendername = sendername


    def get_all_inboxes(self):
        params = {'apikey': self.apikey}
        inboxes_url = 'https://api.textlocal.in/get_inboxes/?'
        return self.get_url_response(request_url=inboxes_url, params=params)


    def get_primary_inbox(self):
        params = {'apikey': self.apikey, 'inbox_id': self.primary_id}
        messages_url = 'https://api.textlocal.in/get_messages/?'
        return self.get_url_response(request_url=messages_url, params=params)

    def get_api_send_history(self):
        params = {'apikey': self.apikey}
        api_send_history_url = 'https://api.textlocal.in/get_history_api/?'
        return self.get_url_response(request_url=api_send_history_url, params=params)


    def get_url_response(self, request_url, params):
        f = request.urlopen(request_url + parse.urlencode(params))
        return json.loads(f.read().decode('latin1'))


    def get_primary_inbox_messages(self):
        return self.get_primary_inbox()['messages']

    def get_api_send_history_messages(self):
        return self.get_api_send_history()['messages']

    def correct_unicode(self, messages, key_name):
        for message in messages:
            message[key_name] = self.correct_corrupted_unicode_matches(message[key_name])
        return messages

    def correct_corrupted_unicode_matches(self, message):
        fixed_message = []
        for message_part in message.split(' '):
            if all(c in string.hexdigits for c in message_part) and '09' in message_part and len(message_part) >= 4:
                fixed_message.append(''.join([unichr(int(message_part[i:i + 4], 16)) for i in range(0, len(message_part), 4)]))
            else:
                fixed_message.append(message_part)
        return ' '.join(fixed_message)

    def response_unicode_encoder(self, message):
        removed_at = message.replace("@U", "\\u")
        front_substring = removed_at[:6] + "\\u"
        back_substring = removed_at[6:]
        back_substring = "\\u".join(re.findall("....", back_substring))
        return (front_substring + back_substring).encode("utf-8").decode("unicode-escape")
         

    def is_message_new(self, message, date_key_name):
        date_of_message = datetime_string_ymd_to_datetime(message[date_key_name])
        margin = timedelta(hours=24)
        return True if datetime.now().replace(tzinfo=timezone.get_default_timezone()) - margin <= date_of_message else False

    def add_to_num_message_dict(self, num_message_dict, message, message_key_name, date_key_name):
        date_of_message = datetime_string_ymd_to_datetime(message[date_key_name])
        num_message_dict.setdefault(str(message['number']), []).append((message[message_key_name], date_of_message))
        return num_message_dict

    def new_messages_by_number(self):
        all_messages = self.get_primary_inbox_messages()
        corrected_messages = self.correct_unicode(messages=all_messages, key_name="message")
        num_message_dict = {}
        for message in corrected_messages:
            if self.is_message_new(message=message, date_key_name="date"):
                num_message_dict = self.add_to_num_message_dict(num_message_dict=num_message_dict,
                                                                message=message,
                                                                message_key_name="message",
                                                                date_key_name="date")
        return num_message_dict

    def new_api_send_messages_by_number(self):
        all_messages = self.get_api_send_history_messages()
        corrected_messages = self.correct_unicode(messages=all_messages, key_name="content")
        num_message_dict = {}
        for message in corrected_messages:
            if self.is_message_new(message=message, date_key_name="datetime"):
                num_message_dict = self.add_to_num_message_dict(num_message_dict=num_message_dict,
                                                                message=message,
                                                                message_key_name="content",
                                                                date_key_name="datetime")
        return num_message_dict

    def send_message(self, message, phone_numbers):
        send_url = "https://api.textlocal.in/send/?"
        unicode_used = 'false'
        if not isinstance(message, str):
            message = message.encode('utf-8')
        if is_not_ascii(message):
            unicode_used = 'true'
        data = parse.urlencode({'numbers': phone_numbers,
                                'message': message,
                                'sender': self.sendername,
                                'apikey': self.apikey,
                                'unicode': unicode_used})
        data = data.encode('utf-8')
        # Avoid triggering bot errors by setting a user agent
        user_agent = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36'}
        requester = request.Request(send_url, headers=user_agent)
        f = request.urlopen(requester, data)
        return json.loads(f.read().decode('latin1'))