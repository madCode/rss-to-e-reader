import unittest
from unittest.mock import MagicMock, patch

import requests

import default_modules.article_parser as article_parser
import default_modules.browser_impersonation as browser_impersonation
from default_modules.browser_impersonation import _cookies_for, impersonated_get, looks_blocked
import default_modules.ebook_images as ebook_images

def response(status: int = 200, content: bytes = b'<html><body>page</body></html>', url: str = 'https://example.com/a'):
    r = requests.Response()
    r.status_code = status
    r._content = content
    r.url = url
    r.headers['content-type'] = 'text/html; charset=utf-8'
    r.encoding = 'utf-8'
    return r

class FakeCurlResponse:
    """curl_cffi's response isn't a requests.Response, but has the same attributes."""
    def __init__(self, status: int, content: bytes, url: str = 'https://example.com/final'):
        self.status_code = status
        self.content = content
        self.url = url
        self.headers = {'content-type': 'text/html; charset=utf-8'}
        self.encoding = 'utf-8'

class TestLooksBlocked(unittest.TestCase):
    def test_status_codes(self):
        for status in (401, 403, 429, 503):
            self.assertTrue(looks_blocked(response(status)))
        for status in (200, 404, 500):
            self.assertFalse(looks_blocked(response(status)))

    def test_challenge_pages(self):
        self.assertTrue(looks_blocked(response(200, b'<html><head><title>Just a moment...</title></head></html>')))
        self.assertTrue(looks_blocked(response(200, b'<script src="https://geo.captcha-delivery.com/x.js"></script>')))
        # a long real page that happens to mention a marker is not a challenge
        self.assertFalse(looks_blocked(response(200, b'challenge-platform ' + b'x' * 200 * 1024)))

class TestCookies(unittest.TestCase):
    def test_only_cookies_for_the_host(self):
        session = requests.Session()
        session.cookies.set('sub', 'yes', domain='.example.com')
        session.cookies.set('exact', '1', domain='www.example.com')
        session.cookies.set('other', 'no', domain='other.com')
        self.assertEqual(_cookies_for(session, 'https://www.example.com/a'), {'sub': 'yes', 'exact': '1'})
        self.assertEqual(_cookies_for(session, 'https://example.com/a'), {'sub': 'yes'})
        self.assertEqual(_cookies_for(None, 'https://example.com/a'), {})

class TestImpersonatedGet(unittest.TestCase):
    def test_passes_options_to_curl_cffi(self):
        if not browser_impersonation.is_available():
            self.skipTest('curl_cffi not installed')
        from curl_cffi import requests as curl_requests
        session = requests.Session()
        session.cookies.set('sub', 'yes', domain='example.com')
        with patch.object(curl_requests, 'get', return_value='resp') as get:
            self.assertEqual(impersonated_get('https://example.com/a', 'safari', 5, session, 'https://ref/'), 'resp')
        self.assertEqual(get.call_args.kwargs['impersonate'], 'safari')
        self.assertEqual(get.call_args.kwargs['cookies'], {'sub': 'yes'})
        self.assertEqual(get.call_args.kwargs['headers'], {'Referer': 'https://ref/'})

    def test_errors_return_none(self):
        if not browser_impersonation.is_available():
            self.skipTest('curl_cffi not installed')
        from curl_cffi import requests as curl_requests
        with patch.object(curl_requests, 'get', side_effect=RuntimeError('boom')):
            self.assertIsNone(impersonated_get('https://example.com/a'))

class TestFetchHtmlRetry(unittest.TestCase):
    def test_not_blocked_means_no_retry(self):
        with patch.object(requests, 'get', return_value=response()), \
             patch.object(article_parser, 'impersonated_get') as impersonated:
            html, _ = article_parser.fetch_html('https://example.com/a')
        impersonated.assert_not_called()
        self.assertIn('page', html)

    def test_blocked_then_retried(self):
        with patch.object(requests, 'get', return_value=response(403, b'Forbidden')), \
             patch.object(article_parser, 'impersonated_get', return_value=FakeCurlResponse(200, b'<p>real page</p>')):
            html, url = article_parser.fetch_html('https://example.com/a')
        self.assertEqual((html, url), ('<p>real page</p>', 'https://example.com/final'))

    def test_retry_also_blocked_raises_original_error(self):
        with patch.object(requests, 'get', return_value=response(403, b'Forbidden')), \
             patch.object(article_parser, 'impersonated_get', return_value=FakeCurlResponse(403, b'<title>Just a moment...</title>')):
            self.assertRaisesRegex(requests.HTTPError, '403 Client Error', article_parser.fetch_html, 'https://example.com/a')

    def test_failed_retry_raises_original_error(self):
        with patch.object(requests, 'get', return_value=response(403, b'Forbidden')), \
             patch.object(article_parser, 'impersonated_get', return_value=FakeCurlResponse(502, b'bad gateway')):
            self.assertRaisesRegex(requests.HTTPError, '403 Client Error', article_parser.fetch_html, 'https://example.com/a')

    def test_curl_cffi_missing(self):
        with patch.object(requests, 'get', return_value=response(403, b'Forbidden')), \
             patch.object(article_parser, 'impersonated_get', return_value=None):
            self.assertRaises(requests.HTTPError, article_parser.fetch_html, 'https://example.com/a')

    def test_disabled(self):
        with patch.object(requests, 'get', return_value=response(403, b'Forbidden')), \
             patch.object(article_parser, 'impersonated_get') as impersonated:
            self.assertRaises(requests.HTTPError, article_parser.fetch_html, 'https://example.com/a', impersonate=None)
        impersonated.assert_not_called()

class TestImageRetry(unittest.TestCase):
    def blocked_stream(self):
        r = MagicMock()
        r.status_code = 403
        r.raise_for_status.side_effect = requests.HTTPError('403')
        return r

    def test_blocked_image_retried_when_enabled(self):
        with patch.object(requests, 'get', return_value=self.blocked_stream()), \
             patch.object(ebook_images, 'impersonated_get', return_value=FakeCurlResponse(200, b'IMG')) as impersonated:
            self.assertEqual(ebook_images.download_image('https://cdn.example.com/a.jpg', 'https://example.com/a', impersonate='chrome'), b'IMG')
        self.assertEqual(impersonated.call_args.args, ('https://cdn.example.com/a.jpg', 'chrome', 20, None, 'https://example.com/a'))

    def test_blocked_image_not_retried_by_default(self):
        with patch.object(requests, 'get', return_value=self.blocked_stream()), \
             patch.object(ebook_images, 'impersonated_get') as impersonated:
            self.assertIsNone(ebook_images.download_image('https://cdn.example.com/a.jpg'))
        impersonated.assert_not_called()
