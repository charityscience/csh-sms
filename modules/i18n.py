#TODO: Verify Hindi and Gujarati language.

def msg_subscribe(language):
    if language == "English":
        return "{name} has been subscribed to CSH health reminders. Text STOP to unsubscribe."
    else:
        return "{name} \xe0\xa4\x95\xe0\xa5\x8d\xe0\xa4\xb7\xe0\xa4\xae\xe0\xa4\xbe \xe0\xa4\x95\xe0\xa4\xb0\xe0\xa5\x87\xe0\xa4\x82, \xe0\xa4\xb9\xe0\xa4\xae\xe0\xa4\xa8\xe0\xa5\x87 \xe0\xa4\x89\xe0\xa4\xb8 \xe0\xa4\xb8\xe0\xa4\x82\xe0\xa4\xa6\xe0\xa5\x87\xe0\xa4\xb6 \xe0\xa4\x95\xe0\xa5\x8b \xe0\xa4\xa8\xe0\xa4\xb9\xe0\xa5\x80\xe0\xa4\x82 \xe0\xa4\xb8\xe0\xa4\xae\xe0\xa4\x9d\xe0\xa4\xbe \xe0\xa4\xb9\xe0\xa5\x88\xe0\xa4\x82. \xe0\xa4\xb8\xe0\xa4\xa6\xe0\xa4\xb8\xe0\xa5\x8d\xe0\xa4\xaf\xe0\xa4\xa4\xe0\xa4\xbe \xe0\xa4\xb0\xe0\xa4\xa6\xe0\xa5\x8d\xe0\xa4\xa6 \xe0\xa4\x95\xe0\xa4\xb0\xe0\xa4\xa8\xe0\xa5\x87 \xe0\xa4\x95\xe0\xa5\x87 \xe0\xa4\xb2\xe0\xa4\xbf\xe0\xa4\x8f STOP \xe0\xa4\xb2\xe0\xa4\xbf\xe0\xa4\x96\xe0\xa5\x87\xe0\xa4\x82."


def msg_unsubscribe(language):
    if language == "English":
        return "You have been unsubscribed from CSH health reminders."
    else:
        return "\xe0\xa4\x86\xe0\xa4\xaa\xe0\xa4\x95\xe0\xa5\x80 \xe0\xa4\xb8\xe0\xa4\xa6\xe0\xa4\xb8\xe0\xa5\x8d\xe0\xa4\xaf\xe0\xa4\xa4\xe0\xa4\xbe \xe0\xa4\xb8\xe0\xa4\xae\xe0\xa4\xbe\xe0\xa4\xaa\xe0\xa5\x8d\xe0\xa4\xa4 \xe0\xa4\x95\xe0\xa4\xb0 \xe0\xa4\xa6\xe0\xa5\x80 \xe0\xa4\x97\xe0\xa4\xaf\xe0\xa5\x80 \xe0\xa4\xb9\xe0\xa5\x88."


def msg_placeholder_child(language):
    if language == "English":
        return "Your child"
    if language == "Hindi":
        return "\xe0\xa4\x86\xe0\xa4\xaa\xe0\xa4\x95\xe0\xa4\xbe \xe0\xa4\xb6\xe0\xa4\xbf\xe0\xa4\xb6\xe0\xa5\x81"
    if language == "Gujarati":
        return "\xe0\xaa\xa4\xe0\xaa\xae\xe0\xaa\xbe\xe0\xaa\xb0\xe0\xab\x81\xe0\xaa\x82 \xe0\xaa\xac\xe0\xaa\xbe\xe0\xaa\xb3\xe0\xaa\x95"


def msg_failure(language):
    if language == "English":
        return "Sorry, we didn't understand that message. Text STOP to unsubscribe."
    else:
        return "\xe0\xa4\x95\xe0\xa5\x8d\xe0\xa4\xb7\xe0\xa4\xae\xe0\xa4\xbe \xe0\xa4\x95\xe0\xa4\xb0\xe0\xa5\x87\xe0\xa4\x82, \xe0\xa4\xb9\xe0\xa4\xae\xe0\xa4\xa8\xe0\xa5\x87 \xe0\xa4\x89\xe0\xa4\xb8 \xe0\xa4\xb8\xe0\xa4\x82\xe0\xa4\xa6\xe0\xa5\x87\xe0\xa4\xb6 \xe0\xa4\x95\xe0\xa5\x8b \xe0\xa4\xa8\xe0\xa4\xb9\xe0\xa5\x80\xe0\xa4\x82 \xe0\xa4\xb8\xe0\xa4\xae"


def msg_failed_date(language):
    if language == "English":
        return "Sorry, the date format was incorrect. An example message is 'Remind Sai 14-01-17' where 'Sai' is your child's first name and '14-01-17'' is their birthday."
    else:
        return "\xe0\xa4\x95\xe0\xa5\x8d\xe0\xa4\xb7\xe0\xa4\xae\xe0\xa4\xbe \xe0\xa4\x95\xe0\xa5\x80\xe0\xa4\x9c\xe0\xa4\xbf\xe0\xa4\xaf\xe0\xa5\x87, \xe0\xa4\xa4\xe0\xa4\xbe\xe0\xa4\xb0\xe0\xa5\x80\xe0\xa4\x96 \xe0\xa4\x95\xe0\xa4\xbe \xe0\xa4\xaa\xe0\xa5\x8d\xe0\xa4\xb0\xe0\xa4\xbe\xe0\xa4\xb0\xe0\xa5\x82\xe0\xa4\xaa \xe0\xa4\x97\xe0\xa4\xb2\xe0\xa4\xa4 \xe0\xa4\xb9\xe0\xa5\x88."


def hindi_remind():
    return "\xe0\xa4\xb8\xe0\xa5\x8d\xe0\xa4\xae\xe0\xa4\xb0\xe0\xa4\xa3"

def hindi_information():
    return "\xe0\xa4\x87\xe0\xa4\xa4\xe0\xa5\x8d\xe0\xa4\xa4\xe0\xa4\xbf\xe0\xa4\xb2\xe0\xa4\xbe"

def subscribe_keywords(language):
    if language == "English":
        return ["remind", "join"]
    elif language == "Hindi":
        return [hindi_remind(), hindi_information()]
    else:
        return []


def six_week_reminder_seven_days(language):
    if language == "English":
        return "{name} has their scheduled vaccination in 7 days. Without this vaccination your child will be vulnerable to deadly diseases."
    # TODO: add other languages

def six_week_reminder_one_day(language):
    if language == "English":
        return "{name} is due for their important vaccinations in tomorrow. Please do so then."

def ten_week_reminder_seven_days(language):
    if language == "English":
        return "{name} is eligible for a free vaccination in 7 days. Without this vaccination your child will be vulnerable to deadly diseases."

def ten_week_reminder_one_day(language):
    if language == "English":
        return "{name} is due for their important vaccinations tomorrow. Please do so then."

def fourteen_week_reminder_seven_days(language):
    if language == "English":
        return "Thank you for being a responsible mother. {name} is due for their important vaccinations in 7 days. Please do so then."

def fourteen_week_reminder_one_day(language):
    if language == "English":
        return "Your child is eligible to receive a free course of vaccines. {name} has their scheduled vaccination tomorrow."

def nine_month_reminder_seven_days(language):
    return six_week_reminder_seven_days(language)

def nine_month_reminder_one_day(language):
    return six_week_reminder_one_day(language)

def sixteen_month_reminder_seven_days(language):
    return ten_week_reminder_seven_days(language)

def sixteen_month_reminder_one_day(language):
    return ten_week_reminder_one_day(language)

def five_year_reminder_seven_days(language):
    return fourteen_week_reminder_seven_days(language)

def five_year_reminder_one_day(language):
    return fourteen_week_reminder_one_day(language)
