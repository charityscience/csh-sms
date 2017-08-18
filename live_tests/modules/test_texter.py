import time

from django.test import TestCase
from freezegun import freeze_time

from cshsms.settings import TEXTLOCAL_PHONENUMBER
from modules.texter import Texter
from modules.text_reminder import TextReminder


class TexterGetInboxesTests(TestCase):
	def test_read_inbox(self):
		inbox_dict = Texter().read_inbox()
		self.assertIsInstance(inbox_dict, dict)


	def test_send(self):
		time.sleep(120)
        t = Texter()
		send_status = t.send(message="Testing example message in Texter.",
                             phone_number=TEXTLOCAL_PHONENUMBER)
		time.sleep(120)
		new_message_dict = t.read_inbox()
		self.assertTrue("Testing example message in Texter." in new_message_dict[0])


    @patch("logging.info")
	def test_full_e2e(self, logging_mock):
		time.sleep(120)
        t = Texter()
		send_status = t.send(message="JOIN TestPerson 30/1/2017",
                             phone_number=TEXTLOCAL_PHONENUMBER)
		time.sleep(120)
		new_messages = TEXTER.read_inbox()[0]
        p = TextProcessor(TEXTLOCAL_PHONENUMBER)
        processed = False
        for phone_number, texts in new_messages.items():
            for text in texts:
                if text == "JOIN TestPerson 30/1/2017":
                    processed = True
                    p.process(text)

        # Check processing worked
        self.assertTrue(processed)

        # Check person got a subscribed text
        # TODO

        # Check contact object is created
        self.assertTrue(Contact.objects.filter(name="TestPerson",
                                               phone_number=TEXTLOCAL_PHONENUMBER).exists())
        self.assertTrue(p.get_contacts().exists())

        # Check groups are created
        contact = p.get_contacts().first()
        actual_groups = [str(g) for g in contact.group_set.all()]
        expected_groups = ['Everyone - English', 'Text Sign Ups', 'Text Sign Ups - English']
        self.assertEqual(actual_groups, expected_groups)

        # Check person can be reminded
        r = TextReminder(contact)
        with freeze_time("2017-02-1"): # Two days after...
            self.assertFalse(r.remind())  # ...cannot be reminded
            self.assertEqual(r.why_not_remind_reasons(),
                             ["Contact has no reminders for today's date."])
            # TODO: Check no messages went out
        with freeze_time("2017-02-1"): # Six weeks, one day after...
            self.assertTrue(r.remind())  # ...can be reminded
            # TODO: Check that a reminder message went out
        with freeze_time("2017-02-1"): # Six weeks, seven days after...
            self.assertTrue(r.remind())  # ...can be reminded
            # TODO: Check that a reminder message went out

        # Person cancels
        # TODO: Write cancel text

        # Person can no longer be reminded
        # TODO: Write code

        # Clean up
        # TODO: Delete customer and associated objects from database
