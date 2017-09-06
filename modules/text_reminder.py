from datetime import datetime
from dateutil.relativedelta import relativedelta

from modules.texter import Texter
from modules.i18n import six_week_reminder_seven_days, six_week_reminder_one_day, \
                         ten_week_reminder_seven_days, ten_week_reminder_one_day, \
                         fourteen_week_reminder_seven_days, fourteen_week_reminder_one_day, \
                         nine_month_reminder_seven_days, nine_month_reminder_one_day, \
                         sixteen_month_reminder_seven_days, sixteen_month_reminder_one_day, \
                         five_year_reminder_seven_days, five_year_reminder_one_day, \
                         verify_pregnant_signup_birthdate

class TextReminder(object):
    def __init__(self, contact):
        self.contact = contact
        self.child_name = contact.name
        self.date_of_birth = contact.date_of_birth
        self.phone_number = contact.phone_number
        self.language = contact.language_preference
        self.preg_signup = contact.preg_signup
        self.preg_update = contact.preg_update

    # self.get_contact() is preferred to self.contact due to triggering a Django DB refresh.
    def get_contact(self):
        if self.contact:
            self.contact.refresh_from_db()
        return self.contact

    def correct_date_for_reminder(self, years_after_birth=0, months_after_birth=0,
                                  weeks_after_birth=0, days_before_appointment=0):
        time_after_dob = relativedelta(years=years_after_birth,
                                       months=months_after_birth,
                                       weeks=weeks_after_birth)
        time_before_appointment = relativedelta(days=days_before_appointment)
        target_date = (datetime.now() - time_after_dob + time_before_appointment).date()
        return self.date_of_birth == target_date

    def get_reminder_msg(self):
        if self.preg_signup_check():
            if self.correct_date_for_reminder(weeks_after_birth=2, days_before_appointment=0):
                reminder = verify_pregnant_signup_birthdate
            elif self.correct_date_for_reminder(weeks_after_birth=4, days_before_appointment=0):
                reminder = verify_pregnant_signup_birthdate
        elif self.correct_date_for_reminder(weeks_after_birth=6, days_before_appointment=7):
            reminder = six_week_reminder_seven_days
        elif self.correct_date_for_reminder(weeks_after_birth=6, days_before_appointment=1):
            reminder = six_week_reminder_one_day
        elif self.correct_date_for_reminder(weeks_after_birth=10, days_before_appointment=7):
            reminder = ten_week_reminder_seven_days
        elif self.correct_date_for_reminder(weeks_after_birth=10, days_before_appointment=1):
            reminder = ten_week_reminder_one_day
        elif self.correct_date_for_reminder(weeks_after_birth=14, days_before_appointment=7):
            reminder = fourteen_week_reminder_seven_days
        elif self.correct_date_for_reminder(weeks_after_birth=14, days_before_appointment=1):
            reminder = fourteen_week_reminder_one_day
        elif self.correct_date_for_reminder(months_after_birth=9, days_before_appointment=7):
            reminder = nine_month_reminder_seven_days
        elif self.correct_date_for_reminder(months_after_birth=9, days_before_appointment=1):
            reminder = nine_month_reminder_one_day
        elif self.correct_date_for_reminder(months_after_birth=16, days_before_appointment=7):
            reminder = sixteen_month_reminder_seven_days
        elif self.correct_date_for_reminder(months_after_birth=16, days_before_appointment=1):
            reminder = sixteen_month_reminder_one_day
        elif self.correct_date_for_reminder(years_after_birth=5, days_before_appointment=7):
            reminder = five_year_reminder_seven_days
        elif self.correct_date_for_reminder(years_after_birth=5, days_before_appointment=1):
            reminder = five_year_reminder_one_day
        else:
            reminder = None
        return reminder(self.language).format(name=self.child_name) if reminder else None

    def why_not_remind_reasons(self):
        reasons = []
        if self.get_contact().cancelled:
            reasons.append("Contact is cancelled.")
        if self.get_reminder_msg() is None:
            reasons.append("Contact has no reminders for today's date.")
        return reasons
        
    def should_remind_today(self):
        return len(self.why_not_remind_reasons()) == 0

    def remind(self):
        if self.should_remind_today():
            Texter().send(message=self.get_reminder_msg(),
                          phone_number=self.phone_number)
            return True
        else:
            return False

    def preg_signup_check(self):
        return True if self.preg_signup and not self.preg_update else False