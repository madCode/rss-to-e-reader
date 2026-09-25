import os
import unittest
import requests
from unittest.mock import patch
from ArticleMetadata_mocks import MOCK_ARTICLE_METADATA_DO_NOT_FETCH, MOCK_ARTICLE_METADATA_FETCH

from base_classes.ArticleMetadata import ArticleMetadata
from default_modules.DefaultArticleFetcher import DefaultArticleFetcher
from DefaultArticleFetcher_mocks import MOCK_GOOGLE_RESPONSE_CONTENT

FIXTURE = open(os.path.join(os.path.dirname(__file__), 'fixtures', 'article_page.html'), encoding='utf-8').read()

def create_response(content: str, url: str = 'https://www.google.com', status: int = 200) -> requests.Response:
    r = requests.Response()
    r._content = bytes(content, 'utf-8')
    r.status_code = status
    r.url = url
    r.headers['content-type'] = 'text/html; charset=utf-8'
    r.encoding = 'utf-8'
    return r

def metadata(url: str = 'https://example.com/culture/slow', content: str = '', title: str = '') -> ArticleMetadata:
    return ArticleMetadata(title, url, 'source', content, 'Example feed', 'abc')

class TestDefaultArticleFetcher(unittest.TestCase):
    def test_get_article_content_without_fetching(self):
        d = DefaultArticleFetcher([], info_log_callback=None)
        # if fetch_content_from_url is false, the feed's content is used (and cleaned up)
        result = d._get_article_content(MOCK_ARTICLE_METADATA_DO_NOT_FETCH)
        self.assertEqual(result.content, "<p>CONTENTS</p>")
        self.assertEqual(result.title, "THIS IS THE TITLE")
        self.assertTrue(result.success)

    def test_get_article_content_extracts_article(self):
        d = DefaultArticleFetcher([], info_log_callback=None)
        with patch.object(requests, 'get', return_value=create_response(FIXTURE, 'https://example.com/culture/slow')) as mock_method:
            result = d._get_article_content(metadata())
        mock_method.assert_called_once()
        self.assertEqual(mock_method.call_args.args[0], 'https://example.com/culture/slow')
        self.assertTrue(result.success)
        self.assertEqual(result.title, 'The Quiet Joy of Reading Slowly')
        self.assertEqual(result.author, 'Jane Doe')
        self.assertEqual(result.published, '2025-03-04')
        self.assertIn('particular pleasure in reading slowly', result.content)
        self.assertIn('<h2>A short history of attention</h2>', result.content)
        self.assertIn('src="https://example.com/images/hero.jpg"', result.content)
        # page furniture is gone
        for junk in ('Subscribe now', 'Buy stuff', 'Comments (212)', 'All rights reserved', 'tracking', 'Ten gadgets'):
            self.assertNotIn(junk, result.content)
        # the title isn't repeated inside the content
        self.assertNotIn('<h1', result.content)

    def test_get_article_content_prefers_given_title(self):
        d = DefaultArticleFetcher([], info_log_callback=None)
        with patch.object(requests, 'get', return_value=create_response(FIXTURE)):
            result = d._get_article_content(metadata(title='Feed title'))
        self.assertEqual(result.title, 'Feed title')

    def test_get_article_content_error(self):
        d = DefaultArticleFetcher([], error_log_callback=None, info_log_callback=None)
        with patch.object(requests, 'get', side_effect=RuntimeError("yo")) as mock_method:
            result = d._get_article_content(metadata(content=''))
        mock_method.assert_called_once()
        self.assertEqual('<p>Error: yo</p>', result.content)
        self.assertEqual(result.title, 'Slow (example.com)')
        self.assertFalse(result.success)

    def test_get_article_content_http_error_falls_back_to_feed_content(self):
        d = DefaultArticleFetcher([], error_log_callback=None, info_log_callback=None)
        with patch.object(requests, 'get', return_value=create_response('Forbidden', status=403)):
            result = d._get_article_content(MOCK_ARTICLE_METADATA_FETCH)
        self.assertFalse(result.success)
        self.assertEqual(result.content, '<p>CONTENTS</p>')
        self.assertIn('Could not fetch the full article', result.note)

    def test_get_articles_given_meta(self):
        d = DefaultArticleFetcher([], error_log_callback=None, info_log_callback=None)

        # if fetch_content_from_url is false
        articles = d._get_articles_given_meta([MOCK_ARTICLE_METADATA_DO_NOT_FETCH])
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0].display_title,"THIS IS THE TITLE")
        self.assertEqual(articles[0].display_content,"<p>CONTENTS</p>")

        # error occurs: the article is still included, with the error
        with patch.object(requests, 'get', side_effect=RuntimeError("yo")):
            articles = d._get_articles_given_meta([metadata(content='')])
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0].display_content,"<p>Error: yo</p>")

    def test_get_articles_keeps_order_and_links_articles(self):
        metas = [metadata(f'https://example.com/{i}') for i in range(5)]
        for i, m in enumerate(metas):
            m.id = ''
            m.content = f'<p>article {i}</p>'
            m.fetch_content_from_url = False
        articles = DefaultArticleFetcher(metas, info_log_callback=None, max_workers=3).get_articles()
        self.assertEqual([a.display_content for a in articles], [f'<p>article {i}</p>' for i in range(5)])
        # every article got a unique id, and each links to the next
        self.assertEqual(len({a.meta.id for a in articles}), 5)
        self.assertEqual([a.next_id for a in articles], [a.meta.id for a in articles[1:]] + ['top'])

    def test_replace_table_source_ids(self):
        m = metadata(content='<table><tr><td>a</td><td>b</td></tr><tr><td>c</td><td>d</td></tr></table>')
        m.fetch_content_from_url = False
        self.assertIn('<table>', DefaultArticleFetcher([], info_log_callback=None)._get_article_content(m).content)
        d = DefaultArticleFetcher([], replace_table_source_ids=['source'], info_log_callback=None)
        self.assertNotIn('<table>', d._get_article_content(m).content)

    def test_non_article_page_does_not_crash(self):
        d = DefaultArticleFetcher([], info_log_callback=None)
        with patch.object(requests, 'get', return_value=create_response(MOCK_GOOGLE_RESPONSE_CONTENT)):
            result = d._get_article_content(metadata('https://www.google.com'))
        self.assertTrue(result.success)
        self.assertNotIn('<script', result.content)
