from django.db import models

# Create your models here.
class Contact(models.Model):
	name = models.CharField(max_length=50)

	def __str__(self):
		return self.name

	class Meta:
		ordering = ('name',)

"""
List of variables Contacts should have

Name	Telerivet Contact ID	Phone Number	Alternative Phone	Date of Birth	Date of Sign Up	Delay in days	Functional DoB	Mother Tongue	Language Preference	Script Selection	Gender	Preferred Time	Contact ID	Trial ID	Trial Group	State	Division	District	City	Monthly Income	Religion	Previously had children vaccinated	If not vaccinated why	Method of Sign Up	Org Sign Up	Hospital Name	Mother's First	Mother's Last	Doctor Name	URL information	Phone Number	Groups	Sender Phone	Incoming Messages	Outgoing Messages	Last Heard From	Last Contacted	Time Created	Standard 6 weeks	Standard 9 months	Standard 10 weeks	Standard 14 weeks	Standard 16 months	Standard 5 years	Functional 6 weeks	Functional 10 weeks	Functional 14 weeks	Functional 9 months	Functional 16 months	Functional 5 years	Telerivet Blocked	Cancelled Contacts	Cancelled Contacts - English	Cancelled Contacts - Hindi	Cancelled Contacts - Text Sign Ups	Cancelled Contacts - Text Sign Ups - English	Cancelled Contacts - Text Sign Ups - Hindi	Cancelled Contacts - Text Sign Ups - undefined	Cancelled Contacts - undefined	Everyone - English	Everyone - Gujarati	Everyone - Hindi	Everyone - Online Form	Everyone - Text Default Time	One Time Sign Up Message 06-02-17	Online Form	Online Form - English	Online Form - English - ENG	Online Form - English - ENG - Text Default Time	Online Form - Gujarati	Online Form - Gujarati - GUJ	Online Form - Gujarati - GUJ - Text Default Time	Online Form - Hindi	Online Form - Hindi - HND	Online Form - Hindi - HND - Text Default Time	Sample Contacts	Text Sign Ups	Text Sign Ups - English	Text Sign Ups - English - ENG	Text Sign Ups - English - ENG - Text Default Time	Text Sign Ups - Hindi
"""

class Group(models.Model):
	name = models.CharField(max_length=50)
	contacts = models.ManyToManyField(Contact)


	def __str__(self):
		return self.name

	class Meta:
		ordering = ('name',)