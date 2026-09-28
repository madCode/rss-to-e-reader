from default_modules.DefaultArticle import DefaultArticle
from default_modules.ereader_css import EREADER_CSS
from html import escape
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
        self, filestub: str, articles: Sequence[DefaultArticle], title: str, error_log_callback: Optional[Callable] = print,
        info_log_callback: Optional[Callable] = print, ascii_only: bool = False):
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
        ascii_only: bool, optional
            Transliterate the file to plain ASCII (e.g. “quotes” -> "quotes", é -> e). Only needed for old
            e-readers that mangle UTF-8. Defaults to False.
        """
        self.title = title
        self.ascii_only = ascii_only
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
            results.append(f'<li>({article.time_to_read_str()}) <a href="#{article.anchor_id}">{escape(article.display_title)}</a></li>')
            total_minutes += article.time_to_read_in_minutes()
        results.insert(0, f'<h1 id="top">Table of Contents (Total Read Time: {self._time_to_read_str(total_minutes)})</h1><ol>')
        results.append('</ol>')
        return "".join(results)
    
    def write_file(self) -> str:
        """
        Writes the file to self.filestub + '.html' and returns that path.
        """
        content_html = (
            '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"/>'
            '<meta name="viewport" content="width=device-width, initial-scale=1"/>'
            f'<title>{escape(self.title)}</title><style>{EREADER_CSS}</style></head><body>'
        )
        content_html += self._get_table_of_contents()
        total = len(self.articles)
        for i, article in enumerate(self.articles):
            content_html += article.to_html_string()
            if i%10 == 0:
                self.log_info(f'writing article {i}/{total}')
        content_html += '</body></html>'
        if self.ascii_only:
            content_html = unidecode(content_html)
        path = self.filestub + '.html'
        with open(path, 'w', encoding='utf-8') as file:
            file.write(content_html)
        return path
