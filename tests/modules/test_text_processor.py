from django.test import TestCase
from modules.text_processor import TextProcessor
from modules.i18n import hindi_remind, hindi_information

class TextProcessorGetDataTests(TestCase):
    def test_all_caps(self):
        t = TextProcessor()
        keyword, child_name, date = t.get_data_from_message("REMIND NATHAN 25/11/2015")
        self.assertEqual(keyword, "remind")
        self.assertEqual(child_name, "nathan")
        self.assertEqual(date, "25/11/2015")

    def test_all_lowercase(self):
        t = TextProcessor()
        keyword, child_name, date = t.get_data_from_message("remind nathan 25/11/2015")
        self.assertEqual(keyword, "remind")
        self.assertEqual(child_name, "nathan")
        self.assertEqual(date, "25/11/2015")

    def test_normalcase(self):
        t = TextProcessor()
        keyword, child_name, date = t.get_data_from_message("Remind Nathan 25/11/2015")
        self.assertEqual(keyword, "remind")
        self.assertEqual(child_name, "nathan")
        self.assertEqual(date, "25/11/2015")

    def test_join_keyword(self):
        t = TextProcessor()
        keyword, child_name, date = t.get_data_from_message("Join Charles 19/12/2012")
        self.assertEqual(keyword, "join")
        self.assertEqual(child_name, "charles")
        self.assertEqual(date, "19/12/2012")

    def test_hindi_remind(self):
        t = TextProcessor()
        keyword, child_name, date = t.get_data_from_message(hindi_remind() + " Sai 11/09/2013")
        self.assertEqual(keyword, hindi_remind())
        self.assertEqual(child_name, "sai")
        self.assertEqual(date, "11/09/2013")

    def test_hindi_information(self):
        t = TextProcessor()
        keyword, child_name, date = t.get_data_from_message(hindi_information() + " Sai 11/09/2013")
        self.assertEqual(keyword, hindi_information())
        self.assertEqual(child_name, "sai")
        self.assertEqual(date, "11/09/2013")

    def test_no_child_name(self):
        t = TextProcessor()
        keyword, child_name, date = t.get_data_from_message("Remind 25/11/2015")
        self.assertEqual(keyword, "remind")
        self.assertEqual(child_name, None)
        self.assertEqual(date, "25/11/2015")

