import unittest
import unittest.mock as mock
from TtrssCollector import TtrssCollector
from TtrssCollector_mocks import MOCK_HEADLINE

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
        self.assertEquals(articles, [MOCK_HEADLINE])

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
        self.assertEquals(articles, [])

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
        self.assertEquals(articles, [MOCK_HEADLINE])

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
        self.assertEquals(articles, [MOCK_HEADLINE])

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
        self.assertEquals(articles, [MOCK_HEADLINE])

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
        self.assertEquals(articles, [MOCK_HEADLINE])

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
        self.assertEquals(articles, [MOCK_HEADLINE])

    def test_get_articles_from_ttrss_error(self):
        # If ttrss result is empty, error
        inst = TtrssCollector("testurl")
        inst._session_id="987"
        inst._send_ttrss_post_request = mock.MagicMock(return_value={})
        self.assertRaisesRegex(RuntimeError,
            'Unable to get headline data from tt-rss api. Called with: {"sid":"987","op":"getHeadlines","feed_id":"-4","view_mode":"unread","show_content":"1"}',
            inst._get_articles_from_ttrss)
    
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
        self.assertEquals(len(articles), 1)
        self.assertEquals(articles[0].title, MOCK_HEADLINE['title'])
        self.assertEquals(articles[0].url, MOCK_HEADLINE['link'])
        self.assertEquals(articles[0].source_id, MOCK_HEADLINE['feed_id'])
        self.assertEquals(articles[0].content, MOCK_HEADLINE['content'])
        self.assertEquals(articles[0].source_title, MOCK_HEADLINE['feed_title'])
        self.assertEquals(articles[0].id, str(MOCK_HEADLINE['id']))
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
        self.assertEquals(len(articles), 1)
        self.assertEquals(articles[0].title, MOCK_HEADLINE['title'])
        self.assertEquals(articles[0].url, MOCK_HEADLINE['link'])
        self.assertEquals(articles[0].source_id, MOCK_HEADLINE['feed_id'])
        self.assertEquals(articles[0].content, MOCK_HEADLINE['content'])
        self.assertEquals(articles[0].source_title, MOCK_HEADLINE['feed_title'])
        self.assertEquals(articles[0].id, str(MOCK_HEADLINE['id']))
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

if __name__ == '__main__':
    unittest.main()