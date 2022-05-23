from default_modules.DefaultArticle import DefaultArticle
from base_classes.file_creator import FileCreator
from typing import Sequence, Callable, Optional
from unidecode import unidecode # type: ignore

"""
An FileCreator does the following:
- takes in a list of Article in a specific order
- takes in a file location and file name in the form of a filestub
- creates a file based on those Article and maintains the order
"""
class HTMLFileCreator(FileCreator):
    def __init__(
        self, filestub: str, articles: Sequence[DefaultArticle], title: str, error_log_callback: Optional[Callable] = print, info_log_callback: Optional[Callable] = print):
        """
        Parameters
        ----------
        filestub: str
            The path and filename desired for the resulting file. Should not include the extension unless specified by the FileCreator you're using.
        title: str
            Title for the file.
        articles: Sequence[Article]
            The set of Articles to be used in file creation.
        error_log_callback: function that takes in a string and does not return, optional
            Allows user to pass in a callback for error level logs.
            Defaults to system print function
        info_logs: function that takes in a string and does not return, optional
            Allows user to pass in a callback for info level logs.
            Defaults to system print function
        """
        self.title = title
        super().__init__(filestub, articles, error_log_callback, info_log_callback)
    
    def _time_to_read_str(self, min: int) -> str:
        if min < 60:
            return str(min) + ' min'
        per_hour = min//60
        remainder = min%60
        return str(per_hour) + ' hr ' + str(remainder) + ' min'
    
    def _get_table_of_contents(self):
        total_minutes = 0
        results = []
        for article in self.articles:
            results.append(f'<li>({article.time_to_read_str()}) <a href="#{article.meta.id}">{article.display_title}</a></li>')
            total_minutes += article.time_to_read_in_minutes()
        results.insert(0, f'<h1 id="top">Table of Contents (Total Read Time: {self._time_to_read_str(total_minutes)})</h1><ol>')
        results.append('</ol>')
        return "".join(results)
    
    def write_file(self):
        """
        Writes a file to the path specified by self.filestub with the name specified by self.filestub.
        """
        file = open(self.filestub +'.html', "w+")
        content_html = f'<!DOCTYPE html><html lang="en"><head><title>{self.title}</title></head><body>'
        content_html += self._get_table_of_contents()
        total = len(self.articles)
        i = 0
        for article in self.articles:
            content_html += article.to_html_string()
            if i%10 == 0:
                self._info_log_callback(f'writing article {i}/{total}')
            i += 1
        content_html += '</body></html>'
        content_html = unidecode(content_html)
        file.write(content_html)
        file.close()
