from abc import abstractmethod
from DefaultArticle import Article
from module import Module
from typing import Sequence, Callable, Optional

"""
An ArticleFetcher does the following:
- takes in a list of ArticleMetadata in a specific order
- fetches and constructs the display contents for each of those ArticleMetadata as needed
- returns a list of corresponding Articles in the same order as the passed in ArticleMetadata
"""
class ArticleFetcher(Module):
    def __init__(
        self, error_log_callback: Optional[Callable], info_log_callback: Optional[Callable]):
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
    
    @abstractmethod
    def get_articles(self) -> Sequence[Article]:
        """
        Returns the list of Article that should appear in the final output in the order they should appear in the final output.
        """
        pass
