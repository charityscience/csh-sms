# TODO test after the library is ready
from django.test import TestCase
from modules.texter import Texter
from modules.textlocalwrapper import TextLocal

class TexterGetInboxesTests(TestCase):
	def create_texter(self):
		return Texter()


	def test_get_inboxes(self):
		# TODO: Implement for real
		pass
