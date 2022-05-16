from abc import abstractmethod
from ArticleMetadata import ArticleMetadata
from module import Module
from typing import List, Callable, Optional

"""
A ListCreator does the following:
- take in a list of ArticleMetadata
- surface filtering options to the end user
- return an ordered list of ArticleMetadata that meets the user's filtering criteria
- must call any passed in used_article_callback when it's done
"""
class ListCreator(Module):
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
    def get_article_metadatas(self) -> List[ArticleMetadata]:
        """
        Returns the list of ArticleMetadata that should appear in the final output in the order they should appear in the final output.
        """
        pass
