from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
import datetime
from dateutil.relativedelta import relativedelta

from management.models import Contact

def create_contact(name, days):
	"""
	Create a contact with the given `name` and born the
	given number of `days` offset to now (negative for birthdates
	in the past, positive for contacts yet to be born).
	"""
	day = datetime.date.today() + datetime.timedelta(days=days)
	return Contact.objects.create(name=name, date_of_birth=day)


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


class ContactIndexViewTests(TestCase):
    def test_no_contacts(self):
        """
        If no contacts exist, an appropriate message is displayed.
        """
        response = self.client.get(reverse('management:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No contacts are available.")
        self.assertQuerysetEqual(response.context['latest_contact_list'], [])

    def test_one_contact_that_has_been_born(self):
        """
        A contact that has been born is displayed on the
        index page.
        """
        create_contact(name="Namey is born", days=-20)
        response = self.client.get(reverse('management:index'))
        self.assertQuerysetEqual(
            response.context['latest_contact_list'],
            ['<Contact: Namey is born>']
        )

    def test_two_contacts_that_have_been_born(self):
        """
        Two contacts that has been born are displayed on the
        index page.
        """
        create_contact(name="Namey is born", days=-20)
        create_contact(name="Other is born", days=-10)
        response = self.client.get(reverse('management:index'))
        self.assertQuerysetEqual(
            response.context['latest_contact_list'],
            ['<Contact: Namey is born>', '<Contact: Other is born>']
        )


class ContactDetailViewTests(TestCase):
    def test_one_contact_that_has_been_born(self):
        """
        The detail view of a Contact with a date_of_birth in the past
        displays the Contact's name.
        """
        contact_that_has_been_born = create_contact(name='Namey', days=-5)
        url = reverse('management:detail', args=(contact_that_has_been_born.id,))
        response = self.client.get(url)
        self.assertContains(response, contact_that_has_been_born.name)
