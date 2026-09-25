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
        

    def test_time_to_read_str_under_a_minute(self):
        a = DefaultArticle(MOCK_ARTICLE_METADATA_DO_NOT_FETCH)
        a.word_count = 20
        self.assertEqual(a.time_to_read_str(), '< 1 min')

    def test_word_count_ignores_markup(self):
        a = DefaultArticle(MOCK_ARTICLE_METADATA_DO_NOT_FETCH, display_content='<p class="x y z">one <em>two</em></p><img src="a.jpg"/>')
        self.assertEqual(a.word_count, 2)

    def test_to_html_string(self):
        self.maxDiff = None
        a = DefaultArticle(MOCK_ARTICLE_METADATA_DO_NOT_FETCH, "DISPLAY_TITLE", "<p>Some words here.</p>", "next_id",
                           author="Jane Doe", published="2025-03-04")
        self.assertEqual(a.to_html_string(), DEFAULT_ARTICLE_HTML_STRING)

        # no reading time without wpm, no next link at the end, falls back to meta content
        a = DefaultArticle(MOCK_ARTICLE_METADATA_DO_NOT_FETCH, "DISPLAY_TITLE", next_id="top", wpm=-1)
        html = a.to_html_string()
        self.assertIn('<p class="byline">FEED TITLE · 1 words</p>', html)
        self.assertIn('CONTENTS', html)
        self.assertNotIn('Next article', html)

    def test_to_html_string_escapes(self):
        a = DefaultArticle(MOCK_ARTICLE_METADATA_DO_NOT_FETCH, "Cats & <dogs>", "<p>x</p>", note='Fetch "failed"')
        html = a.to_html_string()
        self.assertIn('Cats &amp; &lt;dogs&gt;', html)
        self.assertIn('<p class="note">Fetch &quot;failed&quot;</p>', html)
