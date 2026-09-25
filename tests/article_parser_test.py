import json
import os
import unittest
from unittest.mock import patch

import requests

import default_modules.article_parser as article_parser
from default_modules.article_parser import clean_title, extract_article, fetch_html, find_site_rule, title_from_url

FIXTURE = open(os.path.join(os.path.dirname(__file__), 'fixtures', 'article_page.html'), encoding='utf-8').read()
LONG_TEXT = ' '.join(['word'] * 300)

class TestArticleParser(unittest.TestCase):
    def test_extracts_fixture_with_metadata(self):
        article = extract_article(FIXTURE, 'https://example.com/culture/slow')
        self.assertEqual(article.extractor, 'trafilatura')
        self.assertEqual(article.title, 'The Quiet Joy of Reading Slowly')
        self.assertEqual(article.author, 'Jane Doe')
        self.assertEqual(article.date, '2025-03-04')
        self.assertEqual(article.site_name, 'Example Magazine')
        self.assertGreater(article.word_count, 200)
        self.assertNotIn('Comments (212)', article.html)

    def test_cookie_banners_and_dialogs_are_removed_before_extraction(self):
        banner = ('<div id="cmplz-cookiebanner-container"><div class="cmplz-cookiebanner" role="dialog">'
                  '<p>The technical storage or access is strictly necessary for the legitimate purpose.</p>'
                  '<p>Statistics</p><p>Marketing</p></div></div>'
                  '<div aria-modal="true"><p>Subscribe to our newsletter for more great content today.</p></div>')
        article = extract_article(FIXTURE.replace('</main>', '</main>' + banner), 'https://example.com/culture/slow')
        self.assertIn('particular pleasure in reading slowly', article.html)
        self.assertNotIn('technical storage', article.html)
        self.assertNotIn('Subscribe to our newsletter', article.html)

    def test_overlay_markers_never_remove_most_of_the_page(self):
        html = f'<html><body><div class="cookie-recipes"><p>{LONG_TEXT}</p></div><p>footer</p></body></html>'
        self.assertGreater(extract_article(html, 'https://example.com/recipes').word_count, 250)

    def test_site_rule_wins_when_it_finds_enough_text(self):
        html = f'<html><body><section name="articleBody"><p>{LONG_TEXT}</p></section><div>other</div></body></html>'
        article = extract_article(html, 'https://www.nytimes.com/2024/01/01/story.html')
        self.assertEqual(article.extractor, 'site rule')
        self.assertTrue(article.html.startswith('<section name="articleBody">'))

    def test_site_rule_miss_falls_through(self):
        article = extract_article(FIXTURE, 'https://www.nytimes.com/2024/01/01/story.html')
        self.assertEqual(article.extractor, 'trafilatura')

    def test_prefers_readability_when_it_finds_much_more_text(self):
        with patch.object(article_parser, '_trafilatura', return_value='<p>short</p>'), \
             patch.object(article_parser, '_readability', return_value=f'<p>{LONG_TEXT}</p>'):
            self.assertEqual(extract_article(FIXTURE, 'https://example.com/a').extractor, 'readability')

    def test_json_ld_article_body(self):
        data = {'@context': 'https://schema.org', '@graph': [{'@type': 'NewsArticle', 'articleBody': 'Para one.\n\n' + LONG_TEXT}]}
        html = f'<html><head><script type="application/ld+json">{json.dumps(data)}</script></head><body><p>Subscribe to read</p></body></html>'
        with patch.object(article_parser, '_trafilatura', return_value=None), \
             patch.object(article_parser, '_readability', return_value=None):
            article = extract_article(html, 'https://example.com/a')
        self.assertEqual(article.extractor, 'json-ld')
        self.assertTrue(article.html.startswith('<p>Para one.</p><p>word word'))

    def test_falls_back_to_longest_result_then_body(self):
        with patch.object(article_parser, '_trafilatura', return_value='<p>one two</p>'), \
             patch.object(article_parser, '_readability', return_value='<p>one two three</p>'):
            self.assertEqual(extract_article('<p>x</p>', 'https://example.com/a').extractor, 'readability')
        with patch.object(article_parser, '_trafilatura', side_effect=ValueError), \
             patch.object(article_parser, '_readability', return_value=None):
            article = extract_article('<html><body><p>only this</p></body></html>', '')
        self.assertEqual(article.extractor, 'body')
        self.assertIn('only this', article.html)

    def test_find_site_rule(self):
        self.assertIsNotNone(find_site_rule('https://aeon.co/essays/x'))
        self.assertIsNotNone(find_site_rule('https://www.smithsonianmag.com/history/x'))
        self.assertIsNone(find_site_rule('https://notaeon.co/essays/x'))
        self.assertIsNone(find_site_rule('https://example.com/'))

    def test_clean_title(self):
        self.assertEqual(clean_title('E-reader - Wikipedia', 'Wikimedia Foundation', 'https://en.wikipedia.org/wiki/E-reader'), 'E-reader')
        self.assertEqual(clean_title('An essay | Aeon Essays', 'Aeonmag', 'https://aeon.co/essays/x'), 'An essay')
        self.assertEqual(clean_title('Life - a story - The Atlantic', 'The Atlantic', ''), 'Life - a story')
        self.assertEqual(clean_title('It’s a World | Zoë Hu', 'The Baffler', 'https://thebaffler.com/x', 'Zoë Hu'), 'It’s a World')
        # separators that aren't followed by the site name stay
        self.assertEqual(clean_title('Review: a book - worth it', 'Example', 'https://example.org/'), 'Review: a book - worth it')

    def test_title_from_url(self):
        self.assertEqual(title_from_url('https://www.theatlantic.com/ideas/2026/09/why-meditation-hurts/688474/'), 'Why meditation hurts (theatlantic.com)')
        self.assertEqual(title_from_url('https://example.com/'), 'example.com')

    def test_fetch_html_decoding_and_errors(self):
        response = requests.Response()
        response._content = '<html><head><meta charset="iso-8859-1"></head><body>café</body></html>'.encode('iso-8859-1')
        response.status_code = 200
        response.url = 'https://example.com/final'
        with patch.object(requests, 'get', return_value=response) as get:
            html, url = fetch_html('https://example.com/start')
        self.assertIn('café', html)
        self.assertEqual(url, 'https://example.com/final')
        self.assertIn('timeout', get.call_args.kwargs)

        response.status_code = 404
        with patch.object(requests, 'get', return_value=response):
            self.assertRaises(requests.HTTPError, fetch_html, 'https://example.com/missing')
