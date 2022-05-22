from base_classes.ArticleMetadata import ArticleMetadata
from base_classes.collector import Collector
from default_modules.DefaultArticle import DefaultArticle
from default_modules.DefaultArticleFetcher import DefaultArticleFetcher
from default_modules.DefaultListCreator import ArticleOrder, DefaultListCreator
from enum import Enum
from typing import Callable, List, Optional, Sequence

class MaxType(Enum):
    """
    NUM_ARTICLES: determines the max size based on number of articles
    TIME_IN_MINUTES: determines the max size based on time to read in minutes
    """
    NUM_ARTICLES = 1
    TIME_IN_MINUTES = 2

"""
FetchAndOrderList is a custom ListCreator _and_ ArticleFetcher that inherits from both DefaultListCreator and DefaultArticleFetcher.
By combining the functions of filtering the list _and_ fetching the articles, this module allows users to specify a max read time
for their final output.
"""
class FetchAndOrderList(DefaultListCreator, DefaultArticleFetcher):
    def __init__(
        self, collectors: List[Collector], article_order: ArticleOrder = ArticleOrder.ZIP_COLLECTORS,
        max_type: MaxType = MaxType.NUM_ARTICLES, max_per_source_id: int = -1,
        max_val: int = -1, reading_speed_wpm: int = 300,
        should_call_used_articles_callback: bool = True,
        replace_table_source_ids: List[str] = [],
        error_log_callback: Optional[Callable] = print, info_log_callback: Optional[Callable] = print):

        max_num_articles = max_val if max_type == MaxType.NUM_ARTICLES else -1
        # Note that we're passing False in for should_call_used_articles_callback here because we don't want
        #   the DefaultListCreator calling the callback. FetchAndOrderList will decide when to call the callbacks, if at all.
        DefaultListCreator.__init__(self, collectors, article_order, max_num_articles, max_per_source_id,
            False, error_log_callback, info_log_callback)
        DefaultArticleFetcher.__init__(self, [], replace_table_source_ids, error_log_callback, info_log_callback)
        self.call_collector_callback = should_call_used_articles_callback
        self._max_time = max_val if max_type == MaxType.TIME_IN_MINUTES else -1
        self._wpm = reading_speed_wpm
        self._max_type = max_type
    
    def get_article_metadatas(self) -> List[ArticleMetadata]:
        raise NotImplementedError("FetchAndOrderList combines the ArticleMetadata creation step and the Article creation step. Use get_articles instead.")

    def _get_articles_max_num_articles(self) -> List[DefaultArticle]:
        meta = super().get_article_metadatas()
        return self._get_articles_given_meta(meta)

    def _hit_max_time(self, curr_time: int) -> bool:
        if self._max_time < 0:
            return False
        else:
            return curr_time >= self._max_time
    
    def _get_articles_max_time(self) -> Sequence[DefaultArticle]:
        meta = super().get_article_metadatas()
        current_time = 0
        result: List[DefaultArticle] = []
        for i in range(len(meta)):
            m = meta[i]
            next_id = meta[i+1].id if i < len(meta) - 1 else meta[0].id
            if self._hit_max_time(current_time):
                break
            content, title, success = self._get_article_content(m)
            if not success:
                self.log_error(f"Failed to fetch article. Adding the following error message to document:\n{content}")
            article = DefaultArticle(m, title[:DefaultArticleFetcher.TITLE_CUTOFF], content,next_id,self._wpm)
            result.append(article)
            current_time += article.time_to_read_in_minutes()
        # Rewrite the next_id on the last one to cycle back to the beginning
        result[-1].next_id = 'top'
        return result

    def get_articles(self) -> Sequence[DefaultArticle]:
        if self._max_type == MaxType.TIME_IN_MINUTES:
            articles = self._get_articles_max_time()
        else:
            # Default to MaxType.NUM_ARTICLES
            articles = self._get_articles_max_num_articles()
        # Call the Collector callbacks if requested
        if self.call_collector_callback:
            super().callback_collectors([a.meta for a in articles])
        return articles
        