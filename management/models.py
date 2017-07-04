from django.db import models

# Create your models here.
class Contact(models.Model):
	name = models.CharField(max_length=50)
	# phone_number = FIX ME
	# alt_phone_number = FIX ME
	date_of_birth = models.DateField()
	date_of_sign_up = models.DateField()
	delay_in_days = models.SmallIntegerField()
	functional_date_of_birth = models.DateField()
	mother_tongue = models.CharField(max_length=50)
	gender = models.CharField(max_length=2)
	contact_id = models.CharField(max_length=20)
	telerivet_contact_id = models.CharField(max_length=50)
	trial_id = models.CharField(max_length=20)
	trial_group = models.CharField(max_length=20)
	state = models.CharField(max_length=20)
	division = models.CharField(max_length=20)
	district = models.CharField(max_length=20)
	city = models.CharField(max_length=20)
	monthly_income_rupees = models.IntegerField()
	religion = models.CharField(max_length=20)
	children_previously_vaccinated = models.NullBooleanField()
	not_vaccinated_why = models.CharField(max_length=100)
	method_of_sign_up = models.CharField(max_length=20)
	org_sign_up = models.CharField(max_length=20)
	hospital_name = models.CharField(max_length=30)
	mother_first_name = models.CharField(max_length=30)
	mother_last_name = models.CharField(max_length=30)
	doctor_name = models.CharField(max_length=30)
	url_information = models.URLField(max_length=200)
	telerivet_sender_phone = models.CharField(max_length=100)


	# def languages_allowed():
		
	# 	all_lang = []
	# 	english = "English"
	# 	hindi = "Hindi"
	# 	gujarati = "Gujarati"


	def __str__(self):
		return self.name

	class Meta:
		ordering = ('name',)

"""
List of variables Contacts should have
---------------


Language Preference
Script Selection

Preferred Time

Last Heard From
Last Contacted
Time Created


URL information
Groups

Incoming Messages
Outgoing Messages

Standard 6 weeks
Standard 9 months
Standard 10 weeks
Standard 14 weeks
Standard 16 months
Standard 5 years
Functional 6 weeks
Functional 10 weeks
Functional 14 weeks
Functional 9 months
Functional 16 months
Functional 5 years
"""

class Group(models.Model):
	name = models.CharField(max_length=50)
	contacts = models.ManyToManyField(Contact)


	def __str__(self):
		return self.name

	class Meta:
		ordering = ('name',)


"""
List of Pre-existing groups in Telerivet
Telerivet Blocked	Cancelled Contacts	Cancelled Contacts - English	Cancelled Contacts - Hindi	Cancelled Contacts - Text Sign Ups	Cancelled Contacts - Text Sign Ups - English	Cancelled Contacts - Text Sign Ups - Hindi	Cancelled Contacts - Text Sign Ups - undefined	Cancelled Contacts - undefined	Everyone - English	Everyone - Gujarati	Everyone - Hindi	Everyone - Online Form	Everyone - Text Default Time	One Time Sign Up Message 06-02-17	Online Form	Online Form - English	Online Form - English - ENG	Online Form - English - ENG - Text Default Time	Online Form - Gujarati	Online Form - Gujarati - GUJ	Online Form - Gujarati - GUJ - Text Default Time	Online Form - Hindi	Online Form - Hindi - HND	Online Form - Hindi - HND - Text Default Time	Sample Contacts	Text Sign Ups	Text Sign Ups - English	Text Sign Ups - English - ENG	Text Sign Ups - English - ENG - Text Default Time	Text Sign Ups - Hindi
"""