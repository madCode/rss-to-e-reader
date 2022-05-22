import unittest
import requests
from unittest.mock import patch
from ArticleMetadata_mocks import MOCK_ARTICLE_METADATA_DO_NOT_FETCH, MOCK_ARTICLE_METADATA_FETCH

from DefaultArticleFetcher import DefaultArticleFetcher
from DefaultArticleFetcher_mocks import MOCK_GOOGLE_RESPONSE_CONTENT, SANITIZED_GOOGLE_CONTENT

def create_response(content: str) -> requests.Response:
    r = requests.Response()
    r._content = bytes(content, 'utf-8')
    return r

class TestDefaultArticleFetcher(unittest.TestCase):
    def test_get_parser(self):
        # default is true
        d = DefaultArticleFetcher()
        with patch.object(requests, 'get', return_value=create_response(MOCK_GOOGLE_RESPONSE_CONTENT)) as mock_method:
            _, b = d._get_parser('https://www.spectator.co.uk/')
        self.assertFalse(b)

        # default is false
        with patch.object(requests, 'get', return_value=create_response(MOCK_GOOGLE_RESPONSE_CONTENT)) as mock_method:
            _, b = d._get_parser('https://www.pecktactoe.co.uk/')
        self.assertTrue(b)
    
    def test_get_article_content(self):
        d = DefaultArticleFetcher()

        # if fetch_content_from_url is false
        content, b = d._get_article_content(MOCK_ARTICLE_METADATA_DO_NOT_FETCH)
        self.assertEqual(content, "CONTENTS")
        self.assertTrue(b)

        # if fetch_content_from_url is true
        with patch.object(requests, 'get', return_value=create_response(MOCK_GOOGLE_RESPONSE_CONTENT)) as mock_method:
            content, b = d._get_article_content(MOCK_ARTICLE_METADATA_FETCH)
        mock_method.assert_called_once_with("https://www.google.com", headers={'User-Agent': 'Mozilla/5.0 (Android 7.0; Mobile; rv:54.0) Gecko/54.0 Firefox/54.0'})
        self.assertEqual(SANITIZED_GOOGLE_CONTENT, content)
        self.assertTrue(b)

        # error occurs
        with patch.object(requests, 'get', side_effect=RuntimeError("yo")) as mock_method:
            content, b = d._get_article_content(MOCK_ARTICLE_METADATA_FETCH)
        mock_method.assert_called_once_with("https://www.google.com", headers={'User-Agent': 'Mozilla/5.0 (Android 7.0; Mobile; rv:54.0) Gecko/54.0 Firefox/54.0'})
        self.assertEqual('<p>Error: yo</p>', content)
        self.assertFalse(b)

    def test_get_articles_given_meta(self):
        d = DefaultArticleFetcher()

        # if fetch_content_from_url is false
        articles = d._get_articles_given_meta([MOCK_ARTICLE_METADATA_DO_NOT_FETCH])
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0].display_title,"THIS IS THE TITLE")
        self.assertEqual(articles[0].display_content,"CONTENTS")

        # error occurs
        with patch.object(requests, 'get', side_effect=RuntimeError("yo")) as mock_method:
            articles = d._get_articles_given_meta([MOCK_ARTICLE_METADATA_FETCH])
        mock_method.assert_called_once_with("https://www.google.com", headers={'User-Agent': 'Mozilla/5.0 (Android 7.0; Mobile; rv:54.0) Gecko/54.0 Firefox/54.0'})
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0].display_title,"THIS IS THE TITLE")
        self.assertEqual(articles[0].display_content,"<p>Error: yo</p>")

    def test_get_articles(self):
        d = DefaultArticleFetcher([MOCK_ARTICLE_METADATA_DO_NOT_FETCH])
        articles = d.get_articles()
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0].display_title,"THIS IS THE TITLE")
        self.assertEqual(articles[0].display_content,"CONTENTS")