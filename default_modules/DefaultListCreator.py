from base_classes.ArticleMetadata import ArticleMetadata
from base_classes.collector import Collector
from enum import Enum
from base_classes.list_creator import ListCreator
from base_classes.list_creator import ListCreator
import random
from typing import List, Optional, Callable, Dict, Set

def _url_key(url: str) -> str:
    """The url compared for duplicates: an anchor (#comments) or trailing slash doesn't make it another
    page, but a hash route (#/post/2, #!/post/2) does."""
    url = url.strip()
    base, _, fragment = url.partition('#')
    if fragment.startswith(('/', '!')):
        return url
    return base.rstrip('/')


class ArticleOrder(Enum):
    """
    IN_ORDER: returns the articles in the order they were passed in based on the order the Collectors were passed in.
    ZIP_COLLECTORS: alternates through the Collectors to make sure a mix is in the document. Returns the articles in the order they appeared in the Collectors.
    RANDOM: returns the article in a random order with no attention paid to which Collector they came from.
    """
    IN_ORDER = 1
    ZIP_COLLECTORS = 2
    RANDOM = 3

"""
DefaultListCreator allows the user to choose the following:
- pass in a set of Collectors that articles should be chosen from
- decide how many articles they want in their final document
- decide how many articles per source they want in their final document
- decide what order they want the articles to appear in
"""
class DefaultListCreator(ListCreator):
    def __init__(
        self, collectors: List[Collector], article_order: ArticleOrder = ArticleOrder.ZIP_COLLECTORS,
        max_num_articles: int = -1, max_per_source_id: int = -1,
        should_call_used_articles_callback: bool = True,
        error_log_callback: Optional[Callable] = print, info_log_callback: Optional[Callable] = print,
        skip_duplicate_urls: bool = False,
    ):
        """
        Parameters
        ----------
        collectors: List[Collectors]
            A list of Collector objects that the DefaultListCreator can get ArticleMetadata from
        article_order: ArticleOrder, optional
            The order articles should appear in the final document. Defaults to ZIP_COLLECTORS.
        max_num_articles: int, optional
            The max number of articles that should be returned. Defaults to -1, which acts as no max.
        max_per_source_id: int, optional
            The max number of articles that should be returned per source. Defaults to -1, which acts as no max.
        should_call_used_articles_callback: bool, optional
            Should the DefaultListCreator call each Collectors' used_articles_callback function? Defaults to true.
        error_log_callback: Optional[Callable], optional
        info_log_callback: Optional[Callable], optional
        skip_duplicate_urls: bool, optional
            Include a link only once when several Collectors (or feeds) carry it. The copies left out
            are still passed to their own Collector's used_articles_callback when the included one is
            used, so each Collector marks it done, and used_article_metadatas() lists them. Anything
            that tracks delivery from the returned list instead (such as a tt-rss since-id cursor taken
            from the delivered articles) must use used_article_metadatas(), or a left-out copy comes
            back on a later run. Defaults to False.
        """
        super().__init__(error_log_callback, info_log_callback)
        self._skip_duplicate_urls = skip_duplicate_urls
        # Copies left out, by the key of the included article's url.
        self._duplicates: Dict[str, List[ArticleMetadata]] = {}
        self._collectors = collectors
        self._article_order = article_order
        self._max_num_articles = max_num_articles
        self._max_per_source_id = max_per_source_id
        self._call_collector_callback = should_call_used_articles_callback

    def _should_include_article(self, article: ArticleMetadata, source_id_dict: Dict[str, int]) -> bool:
        """
        Parameters
        ----------
        article: ArticleMetadata
            The article in question
        source_id_dict: Dict[str,int]
            The dictionary counting how many articles have already been included for each source.

        Returns
        -------
        Returns true if the article should be included in the final document, false if the article should not be included
        """
        hit_max_for_this_source = self._max_per_source_id > -1 and source_id_dict.get(article.source_id, 0) >= self._max_per_source_id
        return not hit_max_for_this_source
    
    def _filter_collector_articles(self) -> Dict[int,List[ArticleMetadata]]:
        """
        Returns
        -------
        Returns a dictionary where the key is the index of the Collector in self._collectors and the value is the filtered
            list of all ArticleMetadata for that Collector that is qualified to be in the final document.
        """
        chosen_articles_by_collector: Dict[int,List[ArticleMetadata]] = {}
        self._duplicates = {}
        seen: Set[str] = set()
        i = 0
        for collector in self._collectors:
            articles = collector.get_article_metadatas()
            total_per_source: Dict[str, int] = {}
            chosen_articles = []
            for article in articles:
                article.set_collector_id(str(i))
                key = _url_key(article.url) if self._skip_duplicate_urls else ''
                # Before the per-source cap: a copy over its source's cap still has to be marked used.
                if key and key in seen:
                    self._duplicates.setdefault(key, []).append(article)
                    continue
                if self._should_include_article(article, total_per_source):
                    if key:
                        seen.add(key)
                    source_amount = total_per_source.get(article.source_id, 0)
                    total_per_source[article.source_id] = source_amount + 1
                    chosen_articles.append(article)
            chosen_articles_by_collector[i] = chosen_articles
            i += 1
        return chosen_articles_by_collector
    
    def _hit_max(self, num_articles) -> bool:
        if self._max_num_articles < 0:
            return False
        else:
            return num_articles >= self._max_num_articles
    
    def zip_collectors(self, articles_by_collector: Dict[int,List[ArticleMetadata]]) -> List[ArticleMetadata]:
        """
        Parameters
        ----------
        articles_by_collector: Dict[int, List[ArticleMetadata]]
            a dictionary where the key is the index of the Collector in self._collectors and the value is the filtered
            list of all ArticleMetadata for that Collector that is qualified to be in the final document.

        Returns
        -------
        List[ArticleMetadata] sorted such that each Collector's articles are interleaved with the other.
            e.g. if collector1 has article list [1,2,3] and collector2 has article list [5,6,7], this function
            will return [1,5,2,6,3,7]
        """
        num_keys = len(self._collectors) # not an ideal way to know what's in articles_by_collector, but oh well
        articles: List[ArticleMetadata] = []
        while not self._hit_max(len(articles)):
            articles_remain = False
            for i in range(num_keys):
                if self._hit_max(len(articles)):
                    break
                if len(articles_by_collector[i]) == 0:
                    continue
                articles.append(articles_by_collector[i].pop(0))
                # If at least one of the collectors still has articles, set articles_remain to True
                articles_remain = articles_remain or len(articles_by_collector[i]) > 0 
            if not articles_remain:
                break
        return articles
    
    def in_order(self, articles_by_collector: Dict[int,List[ArticleMetadata]]) -> List[ArticleMetadata]:
        """
        Parameters
        ----------
        articles_by_collector: Dict[int, List[ArticleMetadata]]
            a dictionary where the key is the index of the Collector in self._collectors and the value is the filtered
            list of all ArticleMetadata for that Collector that is qualified to be in the final document.

        Returns
        -------
        List[ArticleMetadata] sorted such that each Collector's articles appears in the order the Collectors were passed in.
            e.g. if collector1 has article list [1,2,3] and collector2 has article list [5,6,7], this function
            will return [1,2,3,5,6,7]
        """
        num_keys = len(self._collectors) # not an ideal way to know what's in articles_by_collector, but oh well
        articles: List[ArticleMetadata] = []
        # If order didn't matter, we could just use a list comprehension. But since dict.values() will return the collectors
        # in a random order, we're using a for loop
        for i in range(num_keys):
            articles += articles_by_collector[i]
        if self._max_num_articles > 0:
            return articles[:self._max_num_articles]
        else:
            return articles

    def random_order(self, articles_by_collector: Dict[int,List[ArticleMetadata]]) -> List[ArticleMetadata]:
        """
        Parameters
        ----------
        articles_by_collector: Dict[int, List[ArticleMetadata]]
            a dictionary where the key is the index of the Collector in self._collectors and the value is the filtered
            list of all ArticleMetadata for that Collector that is qualified to be in the final document.

        Returns
        -------
        List[ArticleMetadata] in a random order.
            e.g. if collector1 has article list [1,2,3] and collector2 has article list [5,6,7], this function
            may return any order such as [5,2,1,6,3,7]
        """
        articles: List[ArticleMetadata] = [y for x in articles_by_collector.values() for y in x]
        random.shuffle(articles)
        if self._max_num_articles > 0:
            return articles[:self._max_num_articles]
        else:
            return articles
    
    def used_article_metadatas(self, articles: List[ArticleMetadata]) -> List[ArticleMetadata]:
        """
        The articles used, plus the duplicate copies left out for them (see skip_duplicate_urls).
        Parameters
        ----------
        articles: List[ArticleMetadata]
            The final list of used articles
        """
        used = list(articles)
        for article in articles:
            used += self._duplicates.get(_url_key(article.url), [])
        return used

    def callback_collectors(self, articles: List[ArticleMetadata]):
        """
        For each Collector passed in, call its used_articles_callback function with the ArticleMetadata relevant to that Collector
        Parameters
        ----------
        articles: List[ArticleMetadata]
            The final list of used articles
        """
        used = self.used_article_metadatas(articles)
        i = 0
        for collector in self._collectors:
            collector.used_articles_callback([a for a in used if a.collector_id == str(i)])
            i += 1

    def get_article_metadatas(self) -> List[ArticleMetadata]:
        """
        Returns the list of ArticleMetadata that should appear in the final file in the order they should appear in the final file.
        """
        articles_by_collector = self._filter_collector_articles()
        switch: Dict[ArticleOrder, Callable[[Dict[int,List[ArticleMetadata]]],List[ArticleMetadata]]]={
            ArticleOrder.IN_ORDER: self.in_order,
            ArticleOrder.ZIP_COLLECTORS: self.zip_collectors,
            ArticleOrder.RANDOM: self.random_order,
        }
        order_function = switch.get(self._article_order,self.zip_collectors)
        articles = order_function(articles_by_collector)
        if self._call_collector_callback:
            self.callback_collectors(articles)
        return articles
