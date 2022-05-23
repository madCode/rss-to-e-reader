from base_classes.ArticleMetadata import ArticleMetadata
from base_classes.collector import Collector
import json
import requests
from custom_modules.ttrss_types import TtrssHeadline, TtrssResponse
from typing import List, Dict, Optional, Union, Callable

class TtrssCollector(Collector):
    """
    TtrssCollector collects articles from a user's TinyTinyRSS account.
    It can fetch articles after a certain article id by a user if desired.
    It can store a list of used article ids if desired.
    """
    def __init__(
        self, ttrss_api_url: str, user: str = "", password: str ="", max_num_articles: int = -1,
        fetch_feed_id: str = "-4", fetch_feed_is_category: bool = False, last_article_id: str = "",
        fetch_from_url_source_id_list: List[str] = [],
        error_log_callback: Optional[Callable] = print, info_log_callback: Optional[Callable] = print
        ):
        """
        Parameters
        ----------
        ttrss_api_url: str
            url of the hosted ttrss service's api
        user: str, optional
            username
            Necessary if your hosted ttrss instance has multiple users
        password: str, optional
            password
            Necessary if your hosted ttrss instance has multiple users
        max_num_articles: int, optional
            the maximum number of articles to get from ttrss. Defaults to as many as ttrss will send back.
        fetch_feed_id: str
            the id of the feed to get from ttrss. Defaults to "All feeds".
        fetch_feed_is_category: bool, optional
            ttrss requirement: needed to fetch a category feed. Defaults to False.
        last_article_id: str, optional
            if this provided, tell ttrss to send only articles created _after_ this article
        fetch_from_url_source_id_list: List[str], optional
            if the source_id for the article is in this list, set fetch_content_from_url on the ArticleMetadata to true
        error_log_callback: func, optional
            callback for error logs. Defaults to system print function.
        info_log_callback: func, optional
            callback for info logs. Defaults to system print function.
        """
        super().__init__(error_log_callback, info_log_callback)
        self._api_url = ttrss_api_url
        self._user = user
        self._password = password
        self._max_num_articles = max_num_articles
        self._fetch_feed_id = fetch_feed_id
        self._is_cat = fetch_feed_is_category
        self._session_id: Optional[str] = None
        self._last_article_id = last_article_id
        self._fetch_from_url_list = fetch_from_url_source_id_list
    
    def _send_ttrss_post_request(self, post_body: str) -> Union[TtrssResponse,Dict]:
        response = requests.post(self._api_url, data=post_body)
        if response.status_code != 200:
            self.log_error(f'Failure to connect to tt-rss api.\nRequest body: {post_body} \nStatus Code: {response.status_code}')
            return {}
        try:
            dict_str = response.content.decode("UTF-8")
            dict = json.loads(dict_str)
            err_response = None
            content = dict.get('content',{})
            if type(content) is dict:
                err_response = content.get('error',None)
            if err_response is not None:
                self.log_error(f'Received error response: {err_response}')
                return {}
            return dict
        except Exception as exception:
            self.log_error(f'Could not parse tt-rss response: {str(exception)}\nResponse was {dict_str}')
            return {}
    
    def _login(self):
        """
        Logs the user into TTRSS and sets the session id on the object.
        TTRSS api spec here: https://tt-rss.org/wiki/ApiReference
        """
        # If your password is empty but you did pass in a username, try anyway
        if len(self._user) > 0:
            login_data = '{"op":"login","user":"'+self._user+'","password":"'+self._password+'"}'
        else:
            login_data = '{"op":"login"}'
        session_data = self._send_ttrss_post_request(login_data)
        if len(session_data) == 0:
            raise RuntimeError('Unable to authenticate session for tt-rss api. Check logs for details.')
        self._session_id = session_data['content']['session_id']

    def _logout(self):
        """
        Logs the user out of TTRSS and wipes the session id on the object.
        """
        logout_data = '{"op":"logout"}'
        session_data = self._send_ttrss_post_request(logout_data)
        if len(session_data) == 0:
            raise RuntimeError('Unable to logout of session for tt-rss api. Check logs for details.')
        self._session_id = None

    def _get_articles_from_ttrss(self) -> List[TtrssHeadline]:
        if self._session_id == None:
            raise RuntimeError("Tried to get articles without logging in first")
        if self._max_num_articles == 0:
            return []
        limit_str = f'"limit":"{self._max_num_articles}",' if self._max_num_articles > -1 else ''
        cat_str = f'"is_cat":true,' if self._is_cat else ''
        if len(self._last_article_id) > 0:
            get_headlines_data = (
                '{"sid":"' + str(self._session_id) + '",'+ limit_str +
                cat_str + '"op":"getHeadlines","feed_id":"' + str(self._fetch_feed_id) +
                '","view_mode":"unread","show_content":"1","since_id":"' + self._last_article_id + '"}'
            )
        else:
            get_headlines_data = (
                '{"sid":"' + str(self._session_id) + '",'+ limit_str +
                cat_str + '"op":"getHeadlines","feed_id":"'+str(self._fetch_feed_id) +
                '","view_mode":"unread","show_content":"1"}'
                )
        headlines_response = self._send_ttrss_post_request(get_headlines_data)
        if len(headlines_response) == 0:
            raise RuntimeError(f'Unable to get headline data from tt-rss api. Called with: {get_headlines_data}')
        return headlines_response['content']

    def get_article_metadatas(self) -> List[ArticleMetadata]:
        """
        Returns a list of ArticleMetadata from the place the user wants to collect them from.
        """
        articles: List[ArticleMetadata] = []
        self._login()
        headlines = self._get_articles_from_ttrss()
        try:
            self._logout()
        except:
            self.log_error("Could not log out. Continuing with collection.")
        
        i = 0
        total = len(headlines)
        for headline in headlines:
            article = ArticleMetadata(
                headline['title'], headline['link'],
                headline['feed_id'], headline['content'],
                headline['feed_title'], str(headline['id']),
                fetch_content_from_url=(headline['feed_id'] in self._fetch_from_url_list)
                )
            articles.append(article)
            if self._info_log_callback and i%10 == 0:
                self.log_info(f'loading article from ttrss {i}/{total}')
            i+=1
        return articles

    def used_articles_callback(self, usedArticles: List[ArticleMetadata]):
        """
        Parameters
        ----------
        usedArticles: List[ArticleMetadata]
            The final list of ArticleMetadata objects that will all make it into the final file
            Why: Allows a Collector to update the place they collected the articles from, if desired.
        """
        pass