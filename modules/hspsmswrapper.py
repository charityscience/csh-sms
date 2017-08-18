import json
from cshsms.settings import HSPSMS_API, HSPSMS_USERNAME, HSPSMS_SENDERNAME
from six import u
from six.moves.urllib import request, parse

class Hspsms(object):
    def __init__(self, apikey, username, sendername):
        self.apikey = apikey
        self.username = username
        self.sendername = sendername

    def send_transactional_message(self, message, phone_number):
        send_url = 'http://sms.hspsms.com/sendSMS?'
        data = parse.urlencode({'username': self.username,
                                'message': message,
                                'sendername': self.sendername,
                                'smstype': 'TRANS',
                                'numbers': phone_number,
                                'apikey': self.apikey})
        data = data.encode('utf-8')
        requester = request.Request(send_url)
        f = request.urlopen(requester, data)
        return u(json.loads(f.read().decode('latin1')))
