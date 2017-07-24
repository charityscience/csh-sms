#TODO: Verify Hindi and Gujarati language.

def msg_subscribe(language):
    if language == "English":
        return "{name} has been subscribed to CSH health reminders. Text STOP to unsubscribe."
    elif language == "Hindi":
        return u'{name} \u0938\u0940 \u090f\u0938 \u090f\u091a \u0939\u0947\u0932\u094d\u0925 \u0905\u0928\u0941\u0938\u094d\u092e\u0930\u0928 \u0915\u0947 \u0938\u0926\u0938\u094d\u092f \u0939\u0948\u0902. \u0938\u0926\u0938\u094d\u092f\u0924\u093e \u0930\u0926\u094d\u0926 \u0915\u0930\u0928\u0947 \u0915\u0947 \u0932\u093f\u090f STOP \u0932\u093f\u0916\u0947\u0902.'


def msg_unsubscribe(language):
    if language == "English":
        return "You have been unsubscribed from CSH health reminders."
    elif language == "Hindi":
        return u'\u0906\u092a\u0915\u0940 \u0938\u0926\u0938\u094d\u092f\u0924\u093e \u0938\u092e\u093e\u092a\u094d\u0924 \u0915\u0930 \u0926\u0940 \u0917\u092f\u0940 \u0939\u0948.'


def msg_placeholder_child(language):
    if language == "English":
        return "Your child"
    elif language == "Hindi":
        return u'\u0906\u092a\u0915\u093e \u0936\u093f\u0936\u0941'
    elif language == "Gujarati":
        return u'\u0aa4\u0aae\u0abe\u0ab0\u0ac1\u0a82 \u0aac\u0abe\u0ab3\u0a95'


def msg_failure(language):
    if language == "English":
        return "Sorry, we didn't understand that message. Text STOP to unsubscribe."
    elif language == "Hindi":
        return u'\u0915\u094d\u0937\u092e\u093e \u0915\u0930\u0947\u0902, \u0939\u092e\u0928\u0947 \u0909\u0938 \u0938\u0902\u0926\u0947\u0936 \u0915\u094b \u0928\u0939\u0940\u0902 \u0938\u092e\u091d\u093e.'


def msg_failed_date(language):
    if language == "English":
        return "Sorry, the date format was incorrect. An example message is 'Remind Sai 14-01-17' where 'Sai' is your child's first name and '14-01-17'' is their birthday."
    elif language == "Hindi":
        return u'\u0915\u094d\u0937\u092e\u093e \u0915\u0940\u091c\u093f\u092f\u0947, \u0924\u093e\u0930\u0940\u0916 \u0915\u093e \u092a\u094d\u0930\u093e\u0930\u0942\u092a \u0917\u0932\u0924 \u0939\u0948.'


def hindi_remind():
    return u'\u0938\u094d\u092e\u0930\u0923'

def hindi_information():
    return u'\u0907\u0924\u094d\u0924\u093f\u0932\u093e'

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
    elif language == "Hindi":
        return u'7 \u0926\u093f\u0928\u094b\u0902 \u092e\u0947\u0902 {name} \u0915\u093e \u091f\u0940\u0915\u093e\u0915\u0930\u0923 \u0915\u0930\u0935\u093e\u090f\u0901 \u090f\u0935\u0902 \u0916\u093c\u0924\u0930\u0928\u093e\u0915 \u092c\u0940\u092e\u093e\u0930\u093f\u0913\u0902 \u0938\u0947 \u092c\u091a\u093e\u090f\u0901.'
    elif language == "Gujarati":
        return u'{name} \u0aa8 \u0ac1\u0a82\u0aed \u0aa6\u0abf\u0ab5\u0ab8 \u0aae \u0ac1\u0aa8 \u0ac1\u0a82\u0aed \u0aa6\u0abf\u0ab5\u0ab8 \u0aae \u0ac1\u0a82\u0ab0\u0ab8\u0ac0\u0a95\u0ab0\u0aa3 \u0ab8 \u0aa6\u0aa8\u0aa6\u0abf\u0aa4 \u0a9b\u0ac7. \u0a86 \u0ab0\u0ab8\u0ac0\u0a95\u0ab0\u0aa3 \u0ab5\u0a97\u0ab0 \u0aa4\u0aae \u0ab0\u0ac1\u0a82 \u0aac \u0ab3\u0a95 \u0a9c\u0ac0\u0ab5\u0ab2\u0ac7\u0aa3 \u0ab0\u0acb\u0a97\u0acb \u0aae \u0a9f\u0ac7\u0ab8\u0ac1\u0a82\u0ab5\u0ac7\u0abf\u0aa8\u0ab6\u0ac0\u0ab2 \u0ab0\u0ab9\u0ac7\u0ab6\u0ac7.'


def six_week_reminder_one_day(language):
    if language == "English":
        return "{name} is due for their important vaccinations tomorrow. Please do so then."
    elif language == "Hindi":
        return u'\u0905\u0917\u0932\u0947 1 \u0926\u093f\u0928 \u092e\u0947\u0902 {name} \u0915\u0940 \u091c\u093c\u0930\u0942\u0930\u0940 \u091f\u0940\u0915\u093e\u0915\u0930\u0923 \u0905\u0935\u0936\u094d\u092f \u0915\u0930\u0935\u093e\u090f\u0901.'
    elif language == "Gujarati":
        return u'{name} \u0aa8 \u0ac1\u0a82\u0ae7 \u0aa6\u0abf\u0ab5\u0ab8\u0aae \u0ac1\u0a82\u0aae\u0ab9\u0aa4\u0acd\u0ab5\u0aaa\u0ac2\u0aa3\u0aa3\u0ab0\u0ab8\u0ac0\u0a95\u0ab0\u0aa3 \u0aa6\u0aa8\u0aaf\u0aa4 \u0a9b\u0ac7. \u0aa4\u0acb \u0a95\u0ac3\u0aaa \u0a95\u0ab0\u0ac0\u0ac1\u0a82\u0aa8\u0ac7\u0aaa\u0a9b\u0ac0 \u0a8f \u0a95\u0ab0\u0a9c\u0acb.'


def ten_week_reminder_seven_days(language):
    if language == "English":
        return "{name} is eligible for a free vaccination in 7 days. Without this vaccination your child will be vulnerable to deadly diseases."
    elif language == "Hindi":
        return u'7 \u0926\u093f\u0928\u094b\u0902 \u092e\u0947\u0902 {name} \u0915\u0940 \u0928\u093f\u0903\u0936\u0941\u0932\u094d\u0915 \u091f\u0940\u0915\u093e\u0915\u0930\u0923 \u0915\u0930\u0935\u093e\u090f\u0901 \u090f\u0935\u0902 \u0916\u093c\u0924\u0930\u0928\u093e\u0915 \u092c\u0940\u092e\u093e\u0930\u093f\u0913\u0902 \u0938\u0947 \u092c\u091a\u093e\u090f\u0901.'
    elif language == "Gujarati":
        return u'{name} \u0aed \u0aa6\u0abf\u0ab5\u0ab8\u0aae \u0ac1\u0a82\u0aae\u0aab\u0aa4 \u0ab0\u0ab8\u0ac0\u0a95\u0ab0\u0aa3 \u0aae \u0a9f\u0ac7\u0aaa \u0aa4\u0acd\u0ab0 \u0a9b\u0ac7. \u0a86 \u0ab0\u0ab8\u0ac0\u0a95\u0ab0\u0aa3 \u0ab5\u0a97\u0ab0 \u0aa4\u0aae \u0ab0\u0ac2 \u0aac \u0ab3\u0a95 \u0a9c\u0ac0\u0ab5\u0ab2\u0ac7\u0aa3 \u0ab0\u0acb\u0a97\u0acb \u0aae \u0a9f\u0ac7\u0ab8\u0ac1\u0a82\u0ab5\u0ac7\u0abf\u0aa8\u0ab6\u0ac0\u0ab2 \u0ab0\u0ab9\u0ac7\u0ab6\u0ac7.'


def ten_week_reminder_one_day(language):
    if language == "English":
        return "{name} is due for their important vaccinations tomorrow. Please do so then."
    elif language == "Hindi":
        return u'\u091c\u093c\u093f\u092e\u094d\u092e\u0947\u0926\u093e\u0930 \u092e\u093e\u0924\u093e \u0939\u094b\u0928\u0947 \u0915\u0947 \u0932\u093f\u090f \u0906\u092a\u0915\u094b \u092c\u0927\u093e\u0908. 1 \u0926\u093f\u0928 \u092e\u0947\u0902 {name} \u0915\u0947 \u091c\u093c\u0930\u0942\u0930\u0940 \u091f\u0940\u0915\u093e\u0915\u0930\u0923 \u0915\u0947 \u0932\u093f\u090f \u0906\u092a \u0938\u0947 \u092e\u0941\u0932\u093e\u0915\u093c\u093e\u0924 \u0939\u094b\u0917\u0940.'
    elif language == "Gujarati":
        return u'{name} \u0aa8 \u0ac1\u0a82\u0ae7 \u0aa6\u0abf\u0ab5\u0ab8\u0aae \u0ac1\u0a82\u0aae\u0ab9\u0aa4\u0acd\u0ab5\u0aaa\u0ac2\u0aa3\u0aa3\u0ab0\u0ab8\u0ac0\u0a95\u0ab0\u0aa3 \u0aa6\u0aa8\u0aaf\u0aa4 \u0a9b\u0ac7. \u0aa4\u0acb \u0a95\u0ac3\u0aaa \u0a95\u0ab0\u0ac0\u0ac1\u0a82\u0aa8\u0ac7\u0aaa\u0a9b\u0ac0 \u0a8f \u0a95\u0ab0\u0a9c\u0acb.'

def fourteen_week_reminder_seven_days(language):
    if language == "English":
        return "Thank you for being a responsible mother. {name} is due for their important vaccinations in 7 days. Please do so then."
    elif language == "Hindi":
        return u'{name} \u0915\u0947 \u091f\u0940\u0915\u093e\u0915\u0930\u0923 7 \u0926\u093f\u0928\u094b\u0902 \u092e\u0947\u0902 \u0905\u0935\u0936\u094d\u092f \u0915\u0930\u0935\u093e\u090f\u0901.'
    elif language == "Gujarati":
        return u'\u0a8f\u0a95 \u0a9c\u0ab5 \u0aac\u0abf \u0ab0 \u0aae \u0aa4 \u0ab9\u0acb\u0ab5 \u0aac\u0abf\u0ab2 \u0aa7\u0aa8\u0acd\u0aaf\u0ab5 \u0abf. {name} \u0aa8 \u0ac1\u0a82\u0aed \u0aa6\u0abf\u0ab5\u0ab8\u0aae \u0ac1\u0a82\u0aae\u0ab9\u0aa4\u0acd\u0ab5\u0aaa\u0ac2\u0aa3\u0aa3\u0ab0\u0ab8\u0ac0\u0a95\u0ab0\u0aa3 \u0aa6\u0aa8\u0aaf\u0aa4 \u0a9b\u0ac7. \u0aa4\u0acb \u0a95\u0ac3\u0aaa \u0a95\u0ab0\u0ac0\u0ac1\u0a82\u0aa8\u0ac7\u0aaa\u0a9b\u0ac0 \u0a8f \u0a95\u0ab0\u0a9c\u0acb.'


def fourteen_week_reminder_one_day(language):
    if language == "English":
        return "Your child is eligible to receive a free course of vaccines. {name} has their scheduled vaccination tomorrow."
    elif language == "Hindi":
        return u'1 \u0926\u093f\u0928 \u092e\u0947\u0902 {name} \u0915\u0940 \u091f\u0940\u0915\u093e\u0915\u0930\u0923 \u0915\u0930\u0935\u093e\u090f\u0901 \u090f\u0935\u0902 \u0916\u093c\u0924\u0930\u0928\u093e\u0915 \u092c\u0940\u092e\u093e\u0930\u093f\u0913\u0902 \u0938\u0947 \u092c\u091a\u093e\u090f\u0901.'
    elif language == "Gujarati":
        return u'\u0aa1\u0ac9\u0a95\u0acd\u0a9f\u0ab0\u0ac9 \u0a8f \u0ae7 \u0aa6\u0abf\u0ab5\u0ab8\u0aae\u0abe\u0a82  {name} \u0aa8\u0ac7 \u0ab0\u0ab8\u0ac0\u0a95\u0ab0\u0aa3 \u0aae\u0abe\u0a9f\u0ac7 \u0ab8\u0ac2\u0a9a\u0ab5\u0acd\u0aaf\u0ac1 \u0a9b\u0ac7.'


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
