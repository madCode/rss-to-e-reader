import unittest
import unittest.mock as mock
from custom_modules.FetchThenOrderList import FetchThenOrderList, MaxType

from custom_modules.TtrssCollector import TtrssCollector
from TtrssCollector_mocks import MOCK_HEADLINE, MOCK_HEADLINE_2

class TestFetchThenOrderList(unittest.TestCase):

    def test_get_article_metadatas(self):
        f = FetchThenOrderList([])
        self.assertRaises(NotImplementedError,f.get_article_metadatas)

    def test_get_articles_max_num_articles(self):
        inst = TtrssCollector("testurl")
        inst._session_id="987"
        inst._send_ttrss_post_request = mock.MagicMock(return_value={
            'seq':0,
            'status':1,
            'content': [MOCK_HEADLINE]
        })
        inst._login = mock.MagicMock()
        inst._logout = mock.MagicMock()

        inst2 = TtrssCollector("testurl")
        inst2._session_id="987"
        inst2._send_ttrss_post_request = mock.MagicMock(return_value={
            'seq':0,
            'status':1,
            'content': [MOCK_HEADLINE_2]
        })
        inst2._login = mock.MagicMock()
        inst2._logout = mock.MagicMock()

        # gets only the number of articles
        f = FetchThenOrderList([inst, inst2],max_val=1)
        articles = f._get_articles_max_num_articles()
        self.assertEqual(len(articles),1)
        self.assertEqual(articles[0].display_title,MOCK_HEADLINE['title'])

    def test_hit_max_time(self):
        # when max_time is less than 0, return False
        f = FetchThenOrderList([],max_type=MaxType.TIME_IN_MINUTES)
        self.assertFalse(f._hit_max_time(100000000000000000000000000000000000000000))

        # otherwise returns whether curr_time is greater
        #   than or equal to max_time
        f = FetchThenOrderList([],max_type=MaxType.TIME_IN_MINUTES,max_val=50)
        self.assertTrue(f._hit_max_time(51))

    def test_get_articles_max_time(self):
        a = """
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

            She pointed vaguely into the darkness, and I followed her gesture with my eyes.  But I could see no sign of house or light or living creature—only the darkness and, in the fore-ground, the blurred outlines of masses of rock.
        """
        m = dict(MOCK_HEADLINE)
        m['content'] = a
        m2 = dict(MOCK_HEADLINE_2)
        m2['content'] = a

        inst = TtrssCollector("testurl")
        inst._session_id="987"
        inst._send_ttrss_post_request = mock.MagicMock(return_value={
            'seq':0,
            'status':1,
            'content': [m]
        })
        inst._login = mock.MagicMock()
        inst._logout = mock.MagicMock()

        inst2 = TtrssCollector("testurl")
        inst2._session_id="987"
        inst2._send_ttrss_post_request = mock.MagicMock(return_value={
            'seq':0,
            'status':1,
            'content': [m2]
        })
        inst2._login = mock.MagicMock()
        inst2._logout = mock.MagicMock()

        # return all articles when max_val is -1
        f = FetchThenOrderList([inst, inst2],max_type=MaxType.TIME_IN_MINUTES,reading_speed_wpm=5)
        articles = f._get_articles_max_time()
        self.assertEqual(len(articles),2)
        self.assertEqual(articles[0].display_title,MOCK_HEADLINE['title'])
        self.assertEqual(articles[1].display_title,MOCK_HEADLINE_2['title'])

        # return some articles when max_val is few minues
        f = FetchThenOrderList([inst, inst2],max_type=MaxType.TIME_IN_MINUTES,max_val=1,reading_speed_wpm=5)
        articles = f._get_articles_max_time()
        self.assertEqual(len(articles),1)
        self.assertEqual(articles[0].display_title,MOCK_HEADLINE['title'])

    def test_get_articles(self):
        f = FetchThenOrderList([])
        f._get_articles_max_time = mock.MagicMock()
        f._get_articles_max_num_articles = mock.MagicMock()

        # num_articles type
        f.get_articles()
        f._get_articles_max_time.assert_not_called()
        f._get_articles_max_num_articles.assert_called_once()

        f._get_articles_max_time.reset_mock()
        f._get_articles_max_num_articles.reset_mock()

        # time_in_minutes type
        f._max_type = MaxType.TIME_IN_MINUTES
        f.get_articles()
        f._get_articles_max_time.assert_called_once()
        f._get_articles_max_num_articles.assert_not_called()