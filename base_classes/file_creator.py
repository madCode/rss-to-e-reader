from abc import abstractmethod
from base_classes.article import Article
from base_classes.module import Module
from typing import Sequence, Callable, Optional

"""
An FileCreator does the following:
- takes in a list of Article in a specific order
- takes in a file location and file name in the form of a filestub
- creates a file based on those Article and maintains the order
"""
class FileCreator(Module):
    def __init__(
        self, filestub: str, articles: Sequence[Article], error_log_callback: Optional[Callable], info_log_callback: Optional[Callable]):
        """
        Parameters
        ----------
        filestub: str
            The path and filename desired for the resulting file. Should not include the extension unless specified by the FileCreator you're using.
        articles: Sequence[Article]
            The set of Articles to be used in file creation.
        error_log_callback: function that takes in a string and does not return, optional
            Allows user to pass in a callback for error level logs.
            Why? By making this required, it requires implementors of Collector to consider
                surfacing these arguments to users in their initializers.
        info_logs: function that takes in a string and does not return, optional
            Allows user to pass in a callback for info level logs.
            Why? By making this required, it requires implementors of Collector to consider
                surfacing these arguments to users in their initializers.
        """
        self.filestub = filestub
        self.articles = articles
        super().__init__(error_log_callback, info_log_callback)
    
    @abstractmethod
    def write_file(self):
        """
        Writes a file to the path specified by self.filestub with the name specified by self.filestub.
        """
        pass
