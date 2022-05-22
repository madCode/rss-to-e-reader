from base_classes.ArticleMetadata import ArticleMetadata
from base_classes.module import Module
from typing import List, Callable, Optional

"""
MarkdownCollector supports pulling in a list of articles from a markdown checklist, passing those articles along,
and marking the used articles as done.

NOTE: this Collector expects the following file format:
- [ ] url.com
- [x] url.com
Note that the first url is considered "to do" and the second article is considered "done" and will be skipped.
"""
class MarkdownCollector(Module):
    def __init__(self, error_log_callback: Optional[Callable], info_log_callback: Optional[Callable]):
        """
        Parameters
        ----------
        error_log_callback: function that takes in a string and does not return, optional
            Allows user to pass in a callback for error level logs.
            Why? By making this required, it requires implementors of Collector to consider
                surfacing these arguments to users in their initializers.
        info_logs: function that takes in a string and does not return, optional
            Allows user to pass in a callback for info level logs.
            Why? By making this required, it requires implementors of Collector to consider
                surfacing these arguments to users in their initializers.
        """
        super().__init__(error_log_callback, info_log_callback)
 
    def get_article_metadatas(self) -> List[ArticleMetadata]:
        """
        Returns a list of ArticleMetadata from the place the user wants to collect them from.
        """
        pass

    def used_articles_callback(self, usedArticles: List[ArticleMetadata]):
        """
        Parameters
        ----------
        usedArticles: List[ArticleMetadata]
            The final list of ArticleMetadata objects that will all make it into the final file
            Why: Allows a Collector to update the place they collected the articles from, if desired.
        """
        pass