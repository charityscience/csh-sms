from django.test import TestCase
from django.utils import timezone
import datetime

from .models import Contact

# Create your tests here.
class ContactModelTests(TestCase):
	def test_has_been_born_with_future_birth(self):
		"""
		has_been_born() returns False for contacts whose date_of_birth
		is in the future
		"""

		future_date = datetime.date.today() + datetime.timedelta(40)
		future_contact = Contact(date_of_birth=future_date)
		self.assertIs(future_contact.has_been_born(), False)


	def test_has_been_born_with_today_birth(self):
		"""
		has_been_born() returns True for contacts whose date_of_birth
		is today
		"""

		today = datetime.date.today()
		today_contact = Contact(date_of_birth=today)
		self.assertIs(today_contact.has_been_born(), True)

	def test_has_been_born_with_past_birth(self):
		"""
		has_been_born() returns True for contacts whose date_of_birth
		is before today's date
		"""

		past_date = datetime.date.today() - datetime.timedelta(40)
		past_contact = Contact(date_of_birth=past_date)
		self.assertIs(past_contact.has_been_born(), True)