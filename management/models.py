from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
import datetime
from django.utils.encoding import python_2_unicode_compatible

@python_2_unicode_compatible
class Contact(models.Model):
    # Vitals
    name = models.CharField(max_length=50)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+9199999999'. Up to 15 digits allowed.")
    phone_number = models.CharField(validators=[phone_regex], blank=False,
        max_length=20, default="012345") # validators should be a list
    alt_phone_number = models.CharField(validators=[phone_regex], blank=False,
        max_length=20, default="012345")
    date_of_birth = models.DateField(auto_now=False, auto_now_add=False,
        default=datetime.date.today)
    date_of_sign_up = models.DateField(auto_now=False, auto_now_add=False,
        default=datetime.date.today)
    delay_in_days = models.SmallIntegerField(default=0, blank=True)
    functional_date_of_birth = models.DateField(blank=True,auto_now=False,
        auto_now_add=False, default=datetime.date.today)
    cancelled = models.BooleanField(default=False, blank=False)

    # Personal Info
    gender = models.CharField(max_length=6, blank=True)
    mother_tongue = models.CharField(max_length=50, blank=True)
    state = models.CharField(max_length=50, blank=True)
    division = models.CharField(max_length=50, blank=True)
    district = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=50, blank=True)
    monthly_income_rupees = models.IntegerField(blank=True, default=999999)
    religion = models.CharField(max_length=50, blank=True)
    children_previously_vaccinated = models.NullBooleanField()
    not_vaccinated_why = models.CharField(max_length=500, blank=True)
    mother_first_name = models.CharField(max_length=30, blank=True)
    mother_last_name = models.CharField(max_length=30, blank=True)
    
    # Type of Sign Up
    method_of_sign_up = models.CharField(max_length=50, blank=True)
    org_sign_up = models.CharField(max_length=40, blank=True)
    hospital_name = models.CharField(max_length=50, blank=True)
    doctor_name = models.CharField(max_length=30, blank=True)

    def has_been_born(self):
        today = datetime.date.today()
        diff = today - self.date_of_birth
        return  diff >= datetime.timedelta(0)


    # System Identification
    telerivet_contact_id = models.CharField(max_length=50, blank=True)
    trial_id = models.CharField(max_length=20, blank=True)
    trial_group = models.CharField(max_length=20, blank=True)    


    language_preference = models.CharField(max_length=20,
        default="English", blank=False, null=False)

    # Message References
    preferred_time = models.CharField(max_length=50, blank=True)
    script_selection = models.CharField(max_length=20, blank=True)
    telerivet_sender_phone = models.CharField(max_length=100, blank=True)
    time_created = models.DateField(auto_now=False, auto_now_add=False,
        default=datetime.date.today)
    last_heard_from = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True,
        null=True, default=timezone.now)
    last_contacted = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True,
        null=True, default=timezone.now)

    def __str__(self):
        return "%s, %s, %s" % (self.name, self.phone_number, self.date_of_birth)

    class Meta:
        ordering = ('name',)


class Group(models.Model):
    """
    List of Pre-existing groups in Telerivet
    -----------------------
    Telerivet Blocked
    Cancelled Contacts
    Cancelled Contacts - English
    Cancelled Contacts - Hindi
    Cancelled Contacts - Text Sign Ups
    Cancelled Contacts - Text Sign Ups - English
    Cancelled Contacts - Text Sign Ups - Hindi
    Cancelled Contacts - Text Sign Ups - undefined
    Cancelled Contacts - undefined
    Everyone - English
    Everyone - Gujarati    Everyone - Hindi
    Everyone - Online Form
    Everyone - Text Default Time
    One Time Sign Up Message 06-02-17
    Online Form
    Online Form - English
    Online Form - English - ENG
    Online Form - English - ENG - Text Default Time
    Online Form - Gujarati
    Online Form - Gujarati - GUJ
    Online Form - Gujarati - GUJ - Text Default Time
    Online Form - Hindi
    Online Form - Hindi - HND
    Online Form - Hindi - HND - Text Default Time
    Sample Contacts
    Text Sign Ups
    Text Sign Ups - English
    Text Sign Ups - English - ENG
    Text Sign Ups - English - ENG - Text Default Time
    Text Sign Ups - Hindi
    """
    name = models.CharField(max_length=100, unique=True)
    contacts = models.ManyToManyField(Contact)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name',)

@python_2_unicode_compatible
class Message(models.Model):
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, null=True)
    body = models.CharField(max_length=300)

    # Message direction is Incoming or Outgoing
    direction = models.CharField(max_length=10)

    def __str__(self):
        return self.body
