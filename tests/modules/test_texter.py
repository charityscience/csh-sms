from django.test import TestCase
from modules.texter import Texter

class TexterGetInboxesTests(TestCase):
	def create_texter(self):
		return Texter()


	def test_read_inbox(self):
		texter = Texter()
		inbox_dict = texter.read_inbox()

		self.assertIsInstance(inbox_dict, dict)
