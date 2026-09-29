from base_classes.ArticleMetadata import ArticleMetadata
from base_classes.collector import Collector
import json
import requests
from custom_modules.ttrss_types import TtrssHeadline, TtrssResponse
from typing import List, Dict, Optional, Sequence, Union, Callable

class TtrssCollector(Collector):
    """
    TtrssCollector collects articles from a user's TinyTinyRSS account.
    It can fetch articles after a certain article id by a user if desired.
    It can store a list of used article ids if desired.
    """
    def __init__(
        self, ttrss_api_url: str, user: str = "", password: str ="", max_num_articles: int = -1,
        fetch_feed_id: str = "-4", fetch_feed_is_category: bool = False, last_article_id: str = "",
        fetch_from_url_source_id_list: Sequence[Union[str, int]] = [],
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
            if the source_id for the article is in this list, set fetch_content_from_url on the ArticleMetadata to true.
            Feed ids can be given as strings or ints.
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
        # tt-rss sends feed_id as an int, but source_id is a str and configs mix the two, so compare as strings.
        self._fetch_from_url_list = {str(i) for i in fetch_from_url_source_id_list}
    
    @staticmethod
    def _request_body(fields: Dict) -> str:
        """The JSON body for one API call. json.dumps escapes quotes, so a
        password containing one can't break or extend the request."""
        return json.dumps(fields, separators=(",", ":"))

    def _send_ttrss_post_request(self, post_body: str) -> Union[TtrssResponse,Dict]:
        # Not followed: on a 307 or 308 requests sends the same body, password included, to
        # wherever the server points, which can be another host or plain http.
        response = requests.post(self._api_url, data=post_body, allow_redirects=False)
        if response.is_redirect:
            location = response.headers.get('Location', '?')
            self.log_error(f'The tt-rss api answered with a redirect to {location}. '
                           f'If that is your server, use it as the api url.')
            return {}
        if response.status_code != 200:
            # Log the operation only: the login body holds the password.
            op = json.loads(post_body).get("op", "?")
            self.log_error(f'Failure to connect to tt-rss api ({op}). Status Code: {response.status_code}')
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
            login_data = self._request_body({"op": "login", "user": self._user, "password": self._password})
        else:
            login_data = self._request_body({"op": "login"})
        session_data = self._send_ttrss_post_request(login_data)
        if len(session_data) == 0:
            raise RuntimeError('Unable to authenticate session for tt-rss api. Check logs for details.')
        self._session_id = session_data['content']['session_id']

    def _logout(self):
        """
        Logs the user out of TTRSS and wipes the session id on the object.
        """
        logout_data = self._request_body({"op": "logout"})
        session_data = self._send_ttrss_post_request(logout_data)
        if len(session_data) == 0:
            raise RuntimeError('Unable to logout of session for tt-rss api. Check logs for details.')
        self._session_id = None

    def _get_articles_from_ttrss(self) -> List[TtrssHeadline]:
        if self._session_id == None:
            raise RuntimeError("Tried to get articles without logging in first")
        if self._max_num_articles == 0:
            return []
        fields: Dict = {"sid": str(self._session_id)}
        if self._max_num_articles > -1:
            fields["limit"] = str(self._max_num_articles)
        if self._is_cat:
            fields["is_cat"] = True
        fields.update({"op": "getHeadlines", "feed_id": str(self._fetch_feed_id),
                       "view_mode": "unread", "show_content": "1"})
        if len(self._last_article_id) > 0:
            fields["since_id"] = self._last_article_id
        get_headlines_data = self._request_body(fields)
        headlines_response = self._send_ttrss_post_request(get_headlines_data)
        if len(headlines_response) == 0:
            # Name only the feed: the request carries the session id.
            raise RuntimeError(
                f'Unable to get headline data from tt-rss api (feed {self._fetch_feed_id}). Check logs for details.')
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
            feed_id = str(headline['feed_id'])
            article = ArticleMetadata(
                headline['title'], headline['link'],
                feed_id, headline['content'],
                headline['feed_title'], str(headline['id']),
                fetch_content_from_url=(feed_id in self._fetch_from_url_list)
                )
            articles.append(article)
            if i%10 == 0:
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