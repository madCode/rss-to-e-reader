from custom_modules.TtrssCollector import TtrssCollector
from TtrssCollector_mocks import MOCK_HEADLINE
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import threading
import unittest
import unittest.mock as mock

class TestTtrssCollector(unittest.TestCase):

    def test_login_no_credentials(self):
        # Assert that login functions calls send_ttrss_post_request with
        #   the right arguments when no username and password are passed in.
        inst = TtrssCollector("testurl")

        # Assert that runtime error is thrown when nothing is returned
        inst._send_ttrss_post_request = mock.MagicMock(return_value={})
        self.assertRaisesRegex(RuntimeError,
            'Unable to authenticate session for tt-rss api. Check logs for details.',
            inst._login)
        inst._send_ttrss_post_request.assert_called_with('{"op":"login"}')

        # Assert session_id is set when response is valid
        inst._send_ttrss_post_request = mock.MagicMock(return_value={
            'seq':0, 'status':0, 'content':{'session_id':'3000'}
            })
        inst._login()
        inst._send_ttrss_post_request.assert_called_with('{"op":"login"}')
        self.assertEqual(inst._session_id,'3000')

    def test_login_with_credentials(self):
        # Assert that login functions calls send_ttrss_post_request with
        #   the right arguments when a username and password are passed in.
        inst = TtrssCollector("testurl","USER","PASS")

        # Assert that runtime error is thrown when nothing is returned
        inst._send_ttrss_post_request = mock.MagicMock(return_value={})
        self.assertRaisesRegex(RuntimeError,
            'Unable to authenticate session for tt-rss api. Check logs for details.',
            inst._login)
        inst._send_ttrss_post_request.assert_called_with('{"op":"login","user":"USER","password":"PASS"}')

        # Assert session_id is set when response is valid
        inst._send_ttrss_post_request = mock.MagicMock(return_value={
            'seq':0, 'status':0, 'content':{'session_id':'3000'}
            })
        inst._login()
        inst._send_ttrss_post_request.assert_called_with('{"op":"login","user":"USER","password":"PASS"}')
        self.assertEqual(inst._session_id,'3000')

    def test_logout(self):
        # Assert that logout functions calls send_ttrss_post_request with the right arguments
        inst = TtrssCollector("testurl")

        # Assert that runtime error is thrown when nothing is returned
        inst._send_ttrss_post_request = mock.MagicMock(return_value={})
        self.assertRaisesRegex(RuntimeError,
            'Unable to logout of session for tt-rss api. Check logs for details.',
            inst._logout)
        inst._send_ttrss_post_request.assert_called_with('{"op":"logout"}')

        # Assert session_id is set when response is valid
        inst._send_ttrss_post_request = mock.MagicMock(return_value={'status':"ok"})
        inst._logout()
        inst._send_ttrss_post_request.assert_called_with('{"op":"logout"}')
        self.assertIsNone(inst._session_id)

    def test_get_articles_from_ttrss_no_session(self):
        # Assert not called if no session
        inst = TtrssCollector("testurl")
        inst._send_ttrss_post_request = mock.MagicMock(return_value={})
        self.assertRaisesRegex(
            RuntimeError,
            "Tried to get articles without logging in first",
            inst._get_articles_from_ttrss
        )
        inst._send_ttrss_post_request.assert_not_called()
    
    def test_get_articles_from_ttrss_max_num_articles(self):
        # 3
        inst = TtrssCollector("testurl",max_num_articles=3)
        inst._session_id="987"
        inst._send_ttrss_post_request = mock.MagicMock(return_value={
            'seq':0,
            'status':1,
            'content': [MOCK_HEADLINE]
        })
        articles = inst._get_articles_from_ttrss()
        inst._send_ttrss_post_request.assert_called_with(
            '{"sid":"987","limit":"3","op":"getHeadlines","feed_id":"-4","view_mode":"unread","show_content":"1"}'
            )
        self.assertEqual(articles, [MOCK_HEADLINE])

        # 0
        inst = TtrssCollector("testurl",max_num_articles=0)
        inst._session_id="987"
        inst._send_ttrss_post_request = mock.MagicMock(return_value={
            'seq':0,
            'status':1,
            'content': [MOCK_HEADLINE]
        })
        articles = inst._get_articles_from_ttrss()
        inst._send_ttrss_post_request.assert_not_called()
        self.assertEqual(articles, [])

        # -1
        inst = TtrssCollector("testurl")
        inst._session_id="987"
        inst._send_ttrss_post_request = mock.MagicMock(return_value={
            'seq':0,
            'status':1,
            'content': [MOCK_HEADLINE]
        })
        articles = inst._get_articles_from_ttrss()
        inst._send_ttrss_post_request.assert_called_with(
            '{"sid":"987","op":"getHeadlines","feed_id":"-4","view_mode":"unread","show_content":"1"}'
            )
        self.assertEqual(articles, [MOCK_HEADLINE])

    def test_get_articles_from_ttrss_is_cat(self):
        # true
        inst = TtrssCollector("testurl",fetch_feed_is_category=True)
        inst._session_id="987"
        inst._send_ttrss_post_request = mock.MagicMock(return_value={
            'seq':0,
            'status':1,
            'content': [MOCK_HEADLINE]
        })
        articles = inst._get_articles_from_ttrss()
        inst._send_ttrss_post_request.assert_called_with(
            '{"sid":"987","is_cat":true,"op":"getHeadlines","feed_id":"-4","view_mode":"unread","show_content":"1"}'
            )
        self.assertEqual(articles, [MOCK_HEADLINE])

        # false
        inst = TtrssCollector("testurl")
        inst._session_id="987"
        inst._send_ttrss_post_request = mock.MagicMock(return_value={
            'seq':0,
            'status':1,
            'content': [MOCK_HEADLINE]
        })
        articles = inst._get_articles_from_ttrss()
        inst._send_ttrss_post_request.assert_called_with(
            '{"sid":"987","op":"getHeadlines","feed_id":"-4","view_mode":"unread","show_content":"1"}'
            )
        self.assertEqual(articles, [MOCK_HEADLINE])

    def test_get_articles_from_ttrss_last_article_id(self):
        # None
        inst = TtrssCollector("testurl")
        inst._session_id="987"
        inst._send_ttrss_post_request = mock.MagicMock(return_value={
            'seq':0,
            'status':1,
            'content': [MOCK_HEADLINE]
        })
        articles = inst._get_articles_from_ttrss()
        inst._send_ttrss_post_request.assert_called_with(
            '{"sid":"987","op":"getHeadlines","feed_id":"-4","view_mode":"unread","show_content":"1"}'
            )
        self.assertEqual(articles, [MOCK_HEADLINE])

        # 35
        inst = TtrssCollector("testurl", last_article_id="35")
        inst._session_id="987"
        inst._send_ttrss_post_request = mock.MagicMock(return_value={
            'seq':0,
            'status':1,
            'content': [MOCK_HEADLINE]
        })
        articles = inst._get_articles_from_ttrss()
        inst._send_ttrss_post_request.assert_called_with(
            '{"sid":"987","op":"getHeadlines","feed_id":"-4","view_mode":"unread","show_content":"1","since_id":"35"}'
            )
        self.assertEqual(articles, [MOCK_HEADLINE])

    def test_get_articles_from_ttrss_error(self):
        # If ttrss result is empty, error
        inst = TtrssCollector("testurl")
        inst._session_id="987"
        inst._send_ttrss_post_request = mock.MagicMock(return_value={})
        with self.assertRaisesRegex(RuntimeError, 'Unable to get headline data from tt-rss api') as ctx:
            inst._get_articles_from_ttrss()
        # The request carries the session id; the error must not.
        self.assertNotIn("987", str(ctx.exception))
    
    def test_get_article_metadatas_successful_logout(self):
        # Assert that results from get_articles_from_ttrss make ArticleMetadata correctly
        inst = TtrssCollector("testurl")
        inst._session_id="987"
        inst._send_ttrss_post_request = mock.MagicMock(return_value={
            'seq':0,
            'status':1,
            'content': [MOCK_HEADLINE]
        })
        inst._login = mock.MagicMock()
        inst._logout = mock.MagicMock()
        articles = inst.get_article_metadatas()
        inst._login.assert_called_once()
        inst._logout.assert_called_once()
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0].title, MOCK_HEADLINE['title'])
        self.assertEqual(articles[0].url, MOCK_HEADLINE['link'])
        self.assertEqual(articles[0].source_id, MOCK_HEADLINE['feed_id'])
        self.assertEqual(articles[0].content, MOCK_HEADLINE['content'])
        self.assertEqual(articles[0].source_title, MOCK_HEADLINE['feed_title'])
        self.assertEqual(articles[0].id, str(MOCK_HEADLINE['id']))
        self.assertFalse(articles[0].fetch_content_from_url)

    def test_get_article_metadatas_failed_logout(self):
        # Assert that results from get_articles_from_ttrss make ArticleMetadata correctly
        # Assert that if logout fails, a log is printed and things continue
        inst = TtrssCollector("testurl", fetch_from_url_source_id_list=[MOCK_HEADLINE['feed_id']])
        inst._session_id="987"
        inst._send_ttrss_post_request = mock.MagicMock(return_value={
            'seq':0,
            'status':1,
            'content': [MOCK_HEADLINE]
        })
        inst._login = mock.MagicMock()
        inst._logout = mock.MagicMock(side_effect=RuntimeError("yo"))
        articles = inst.get_article_metadatas()
        inst._login.assert_called_once()
        inst._logout.assert_called_once()
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0].title, MOCK_HEADLINE['title'])
        self.assertEqual(articles[0].url, MOCK_HEADLINE['link'])
        self.assertEqual(articles[0].source_id, MOCK_HEADLINE['feed_id'])
        self.assertEqual(articles[0].content, MOCK_HEADLINE['content'])
        self.assertEqual(articles[0].source_title, MOCK_HEADLINE['feed_title'])
        self.assertEqual(articles[0].id, str(MOCK_HEADLINE['id']))
        self.assertTrue(articles[0].fetch_content_from_url)

    def test_get_article_metadatas_logs(self):
        # If info logs callback is passed in, send logs
        info = mock.MagicMock()
        inst = TtrssCollector("testurl",info_log_callback=info)
        inst._session_id="987"
        inst._send_ttrss_post_request = mock.MagicMock(return_value={
            'seq':0,
            'status':1,
            'content': [MOCK_HEADLINE]
        })
        inst._login = mock.MagicMock()
        inst._logout = mock.MagicMock()
        inst.get_article_metadatas()
        info.assert_called_once_with('loading article from ttrss 0/1')

    def _metadatas_for(self, headline, fetch_list):
        inst = TtrssCollector("testurl", fetch_from_url_source_id_list=fetch_list, info_log_callback=None)
        inst._session_id = "987"
        inst._send_ttrss_post_request = mock.MagicMock(return_value={'seq': 0, 'status': 1, 'content': [headline]})
        inst._login = mock.MagicMock()
        inst._logout = mock.MagicMock()
        return inst.get_article_metadatas()

    def test_int_feed_id_matches_either_list_type(self):
        # tt-rss sends feed_id as an int; configs list feed ids as strings or ints
        headline = {**MOCK_HEADLINE, 'feed_id': 111}
        for fetch_list in (['111'], [111]):
            with self.subTest(fetch_list=fetch_list):
                articles = self._metadatas_for(headline, fetch_list)
                self.assertTrue(articles[0].fetch_content_from_url)
                self.assertEqual(articles[0].source_id, '111')

    def test_str_feed_id_matches_an_int_list(self):
        articles = self._metadatas_for(MOCK_HEADLINE, [111])
        self.assertTrue(articles[0].fetch_content_from_url)

    def test_other_feeds_are_not_fetched(self):
        articles = self._metadatas_for({**MOCK_HEADLINE, 'feed_id': 222}, ['111', 111])
        self.assertFalse(articles[0].fetch_content_from_url)

if __name__ == '__main__':
    unittest.main()


class TestTtrssRequests(unittest.TestCase):
    """What goes over the wire and into the logs. Logs are often kept
    (a cron log, say), and the login request carries the password."""

    def response(self, status, body=b'{}'):
        resp = mock.Mock()
        resp.status_code = status
        resp.content = body
        resp.is_redirect = False
        return resp

    def test_a_redirect_is_not_followed_with_the_password(self):
        """A 307 or 308 would make requests send the login body again to whatever
        host the server names."""
        received = []

        class Elsewhere(BaseHTTPRequestHandler):
            def do_POST(self):
                received.append(self.rfile.read(int(self.headers['Content-Length'])))
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"content":{"session_id":"stolen"}}')

            def log_message(self, *args):
                pass

        elsewhere = HTTPServer(('127.0.0.1', 0), Elsewhere)
        target = f'http://127.0.0.1:{elsewhere.server_port}/api/'

        class Redirecting(BaseHTTPRequestHandler):
            def do_POST(self):
                self.rfile.read(int(self.headers['Content-Length']))
                self.send_response(308)
                self.send_header('Location', target)
                self.end_headers()

            def log_message(self, *args):
                pass

        redirecting = HTTPServer(('127.0.0.1', 0), Redirecting)
        for server in (elsewhere, redirecting):
            threading.Thread(target=server.serve_forever, daemon=True).start()
            self.addCleanup(server.server_close)
            self.addCleanup(server.shutdown)
        # A proxy from the environment would otherwise get these local requests.
        no_proxy = os.environ.get('NO_PROXY', '')
        env = mock.patch.dict(os.environ, {'NO_PROXY': f'{no_proxy},127.0.0.1', 'no_proxy': f'{no_proxy},127.0.0.1'})
        env.start()
        self.addCleanup(env.stop)

        errors = []
        inst = TtrssCollector(f'http://127.0.0.1:{redirecting.server_port}/api/', "USER", "PASSWORD-123",
                              error_log_callback=errors.append)
        with self.assertRaises(RuntimeError):
            inst._login()

        self.assertEqual(received, [])
        self.assertIn(target, errors[0])

    def test_a_relative_redirect_is_reported_as_a_full_url(self):
        errors = []
        inst = TtrssCollector("https://rss.example.com/api/", error_log_callback=errors.append)
        resp = self.response(308)
        resp.is_redirect = True
        resp.headers = {'Location': '/tt-rss/api/'}
        with mock.patch("custom_modules.TtrssCollector.requests.post", return_value=resp):
            self.assertEqual(inst._send_ttrss_post_request('{"op":"login"}'), {})
        self.assertIn("https://rss.example.com/tt-rss/api/", errors[0])
        self.assertNotIn("PASSWORD-123", errors[0])

    def test_http_error_log_names_the_operation_not_the_request(self):
        errors = []
        inst = TtrssCollector("testurl", "USER", "PASSWORD-123", error_log_callback=errors.append)
        with mock.patch("custom_modules.TtrssCollector.requests.post", return_value=self.response(502)):
            with self.assertRaises(RuntimeError):
                inst._login()
        self.assertEqual(len(errors), 1)
        self.assertIn("login", errors[0])
        self.assertIn("502", errors[0])
        self.assertNotIn("PASSWORD-123", errors[0])

    def test_quote_in_password_is_escaped(self):
        inst = TtrssCollector("testurl", "USER", 'pa"ss')
        sent = {}

        def post(url, data, **kwargs):
            sent["body"] = data
            return self.response(200, b'{"content":{"session_id":"1"}}')
        with mock.patch("custom_modules.TtrssCollector.requests.post", side_effect=post):
            inst._login()
        self.assertEqual(json.loads(sent["body"]), {"op": "login", "user": "USER", "password": 'pa"ss'})

