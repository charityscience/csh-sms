import json
from cshsms.settings import HSPSMS_API, HSPSMS_USERNAME, HSPSMS_SENDERNAME
from six.moves.urllib import request, parse

class Hspsms(object):
    def __init__(self, apikey, username, sendername):
        self.apikey = apikey
        self.username = username
        self.sendername = sendername

    def send_transactional_message(self, message, phone_number):
        send_url = 'http://sms.hspsms.com/sendSMS?'
        if not isinstance(message, str):
            message = message.encode('utf-8')
        data = parse.urlencode({'username': self.username,
                                'message': message,
                                'sendername': self.sendername,
                                'smstype': 'TRANS',
                                'numbers': phone_number,
                                'apikey': self.apikey})
        data = data.encode('utf-8')
        # Avoid triggering bot errors by setting a user agent
        user_agent = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36'}
        requester = request.Request(send_url, headers=user_agent)
        f = request.urlopen(requester, data)
        return json.loads(f.read().decode('latin1'))
