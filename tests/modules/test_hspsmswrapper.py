import json
import mock
from mock import patch

from django.test import TestCase

from modules.hspsmswrapper import Hspsms
from modules.i18n import hindi_remind


class HspsmsSendingTests(TestCase):
    def test_create_objects(self):
        hspsms = Hspsms(apikey='mock_key',
                        username='mock_user',
                        sendername='mock_sendername')
        self.assertIsInstance(hspsms, Hspsms)


    @patch("modules.hspsmswrapper.request")
    def test_send_transactional_message(self, mock_request):
        class MockResponse():
            def read(self):
                return json.dumps({'message': 'yay'}).encode('latin1')
        mock_request.urlopen.return_value = MockResponse()
        hspsms = Hspsms(apikey='mock_key',
                        username='mock_user',
                        sendername='mock_sendername')
        response = hspsms.send_transactional_message(message='Test', phone_number='0000000')
        self.assertEqual(response['message'], 'yay')

    @patch("modules.hspsmswrapper.request")
    def test_send_transactional_message_hindi(self, mock_request):
        class MockResponse():
            def read(self):
                return json.dumps({'message': hindi_remind()}).encode('latin1')
        mock_request.urlopen.return_value = MockResponse()
        hspsms = Hspsms(apikey='mock_key',
                        username='mock_user',
                        sendername='mock_sendername')
        response = hspsms.send_transactional_message(message='Test', phone_number='0000000')
        self.assertEqual(response['message'], hindi_remind())
