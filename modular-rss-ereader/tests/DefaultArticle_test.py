import unittest

from ArticleMetadata_mocks import MOCK_ARTICLE_METADATA_DO_NOT_FETCH
from default_modules.DefaultArticle import DefaultArticle
from DefaultArticle_mocks import DEFAULT_ARTICLE_HTML_STRING

class TestDefaultArticle(unittest.TestCase):

    def test_time_to_read_in_minutes(self):
        a = DefaultArticle(MOCK_ARTICLE_METADATA_DO_NOT_FETCH, wpm=0)
        a.word_count = 100000000
        # 0 wpm
        self.assertEqual(a.time_to_read_in_minutes(), 0)

        # 200 wpm
        a._wpm = 200

        # 1600 word_count
        a.word_count = 1600
        self.assertEqual(a.time_to_read_in_minutes(), 8)

        # 350 word_count
        a.word_count = 350
        self.assertEqual(a.time_to_read_in_minutes(), 1)

        # 1 word_count
        a.word_count = 1
        self.assertEqual(a.time_to_read_in_minutes(), 0)

        # 22 word_count
        a.word_count = 22
        self.assertEqual(a.time_to_read_in_minutes(), 0)

    def test_time_to_read_str(self):
        a = DefaultArticle(MOCK_ARTICLE_METADATA_DO_NOT_FETCH)
        # converts hours with remainder correctly
        a.word_count = 14500
        self.assertEqual(a.time_to_read_str(),'1 hr 12 min')
        # converts hours without remainder correctly
        a.word_count = 12000
        self.assertEqual(a.time_to_read_str(),'1 hr 0 min')
        # converts minutes correctly
        a.word_count = 1600
        self.assertEqual(a.time_to_read_str(),'8 min')
        # converts days correctly
        a.word_count = 289000
        self.assertEqual(a.time_to_read_str(),'24 hr 5 min')
        

    def test_to_html_string(self):
        s = """
            had not long to wait before making further acquaintance with my pretty midnight visitor.  Our second meeting took place within a few hours of the police call and on the same day.  I had been out for a long walk across the hills and was tramping steadily along the high road towards Stone Hollow, when I saw, gleaming through the darkness—it was already dark though only late afternoon—at probably the loneliest and most desolate spot in the Dale, the headlights of a motor-car evidently at a standstill.

            “It's a weird place for a halt and worse if it's a breakdown,” I murmured, and involuntarily quickened my steps.

            But as I approached the car I saw a moving light and then the shadow of a woman walking towards me, carrying, apparently, a small electric torch.  Evidently she had heard my approach and had set out to meet me.  As she stepped momentarily into the light of the car p. 35I recognised her.  It was the girl of the midnight visit.

            “Who is it, Kitty?” demanded a quick, imperious voice somewhere in the darkness.  “Tell him to come here.  Do you know him?”

            “Lady Clevedon is in the car,” the girl said a little hurriedly.  “Will you come and speak to her?”

            “Is it a breakdown?” I queried.

            “No,” the girl responded, “it is Hartrey.  We have lost him.”

            But I had no immediate opportunity of questioning her as to the missing Hartrey, or the manner of his going, for “Kitty,” as the old lady had addressed her, had run to the door of the car and pulled it open, to reveal old Lady Clevedon, white of hair, very erect of figure, rather stern of face and with keen, searching eyes that just now were full of wrath.

            “Is there anything I can do?” I began.

            “You can find Hartrey,” her ladyship responded, not exactly snappily, but quite ungently; she was evidently used to giving orders, and it never occurred to her, apparently, that I would do any other than obey.

            “Who is Hartrey?” I demanded.

            “He is the chauffeur,” the girl explained. p. 36“We sent him with a message to Lepley's farm—it is over there.”

            She pointed vaguely into the darkness, and I followed her gesture with my eyes.  But I could see no sign of house or light or living creature—only the darkness and, in the fore-ground, the blurred outlines of masses of rock."""
        self.maxDiff = None
        a = DefaultArticle(MOCK_ARTICLE_METADATA_DO_NOT_FETCH,"DISPLAY_TITLE",s,"next_id")
        # supports reading time if WPM exists
        # supports top link
        # supports ids for items
        # supports 'Fetched content' if appropriate
        # supports display content
        self.assertEqual(a.to_html_string(),DEFAULT_ARTICLE_HTML_STRING)

        s = """        <a href="#top">[← top]</a>
        <h1 id="12345"><a href="https://www.google.com">DISPLAY_TITLE</a></h1>
        <a href="#next_id">[skip →]</a>
        <h2>FEED TITLE</h2>
        <h3>(1 words)</h3>
        CONTENTS"""
        # supports no reading time if WPM does not exist
        # supports reading time if WPM exists
        # supports top link
        # supports ids for items
        # supports 'Fetched content' if appropriate
        # supports display content
        a = DefaultArticle(MOCK_ARTICLE_METADATA_DO_NOT_FETCH,"DISPLAY_TITLE",next_id="next_id",wpm=-1)
        self.assertEqual(a.to_html_string(),s)
