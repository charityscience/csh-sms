from datetime import datetime, timedelta

from texter import send_text
from i18n import six_week_reminder_seven_days, six_week_reminder_one_day, \
                 ten_week_reminder_seven_days, ten_week_reminder_one_day, \
                 fourteen_week_reminder_seven_days, fourteen_week_reminder_one_day, \
                 nine_month_reminder_seven_days, nine_month_reminder_one_day, \
                 sixteen_month_reminder_seven_days, sixteen_month_reminder_one_day, \
                 five_year_reminder_seven_days, five_year_reminder_one_day

class TextReminder(object):
    # TODO: Run once per day to process reminders

    def __init__(self, child_name, date_of_birth, phone_number, language):
        self.child_name = child_name
        self.date_of_birth = date_of_birth
        self.phone_number = phone_number
        self.language = language

    def is_eligible_for_reminder(years=0, months=0, weeks=0, days=0):
        self.date_of_birth == (datetime.now() - timedelta(years=years,
                                                          months=months,
                                                          weeks=weeks,
                                                          days=days)).date()

	def get_reminder_msg(self):
        if is_eligible_for_reminder(weeks=6, days=7):
            reminder = six_week_reminder_seven_days
        elif is_eligible_for_reminder(weeks=6, days=1):
            reminder = six_week_reminder_one_day
        elif is_eligible_for_reminder(weeks=10, days=7):
            reminder = ten_week_reminder_seven_days
        elif is_eligible_for_reminder(weeks=10, days=1):
            reminder = ten_week_reminder_one_day
        elif is_eligible_for_reminder(weeks=14, days=7):
            reminder = fourteen_week_reminder_seven_days
        elif is_eligible_for_reminder(weeks=14, days=1):
            reminder = fourteen_week_reminder_one_day
        elif is_eligible_for_reminder(months=9, days=7):
            reminder = nine_month_reminder_seven_days
        elif is_eligible_for_reminder(months=9, days=1):
            reminder = nine_month_reminder_one_day
        elif is_eligible_for_reminder(months=16, days=7):
            reminder = sixteen_month_reminder_seven_days
        elif is_eligible_for_reminder(months=16, days=1):
            reminder = sixteen_month_reminder_one_day
        elif is_eligible_for_reminder(years=5, days=7):
            reminder = five_year_reminder_seven_days
        elif is_eligible_for_reminder(years=5, days=1):
            reminder = five_year_reminder_one_day
        else:
            reminder = None
        return reminder(self.language).format(child=self.child_name) if reminder else None

    def should_remind_today(self):
        return self.get_reminder_msg() is not None

    def remind(self):
        if self.should_remind_today():
            send_text(self.get_reminder_msg())
