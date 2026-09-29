from enum import Enum
from base_classes.ArticleMetadata import ArticleMetadata
from base_classes.collector import Collector
from typing import Dict, List, Callable, Optional, TypedDict, Union
import hashlib
import re

class ListItemStatus(Enum):
    TO_DO = "TO_DO"
    DONE = "DONE"

class ListItemDict(TypedDict):
    url: str
    status: Union[ListItemStatus,str]

"""
MarkdownCollector supports pulling in a list of articles from a markdown checklist, passing those articles along,
and marking the used articles as done.

NOTE: this Collector expects the following file format:
- [ ] url.com
- [x] url.com
Note that the first url is considered "to do" and the second article is considered "done" and will be skipped.
"""
class MarkdownCollector(Collector):
    TO_DO_LIST_REGEX = r"\-\s\[(?P<status>[x\s])\]\s(?P<url>.*)"

    def __init__(self, list_filepath: str, error_log_callback: Optional[Callable] = print, info_log_callback: Optional[Callable] = print,
                 source_id: str = "0", source_title: str = 'List of Articles To Read'):
        """
        Parameters
        ----------
        list_filepath: str
        Path to markdown file with list. Should include file extension. The file should be in the following format:
                - [ ] url.com
                - [x] url2.com
            The first url is considered "to do" and will be included in the result,
            the second article is considered "done" and will be skipped.
        error_log_callback: function that takes in a string and does not return, optional
            Allows user to pass in a callback for error level logs.
            Defaults to system print function
        info_logs: function that takes in a string and does not return, optional
            Allows user to pass in a callback for info level logs.
            Defaults to system print function
        source_id: str, optional
            The source_id every article from this list gets. Defaults to "0". Give each list its own when using
            several, so per-source limits and credits treat them separately.
        source_title: str, optional
            The source_title every article from this list gets. Defaults to 'List of Articles To Read'.
        """
        super().__init__(error_log_callback, info_log_callback)
        self._source_id = source_id
        self._source_title = source_title
        self._filepath: str = list_filepath  
        self._to_do: List[str] = []
        self._data: Dict[str,ListItemDict] = {}
        # The file as loaded. The list is usually a note someone keeps by hand, so it's
        # rewritten by editing these lines in place rather than regenerated.
        self._lines: List[str] = []
        self._added: List[str] = []
        self._load_urls()

    def __len__(self):
        return len(self._to_do)

    def _load_urls(self):
        self.log_info("Loading urls from markdown list")
        try:
            with open(self._filepath, 'r') as file:
                lines = file.readlines()
        except Exception as e:
            self.log_error(f"Could not load file. Skipping collecting articles. {e}")
            return
        self._lines = lines
        
        existing_urls = set()
        for line in lines:
            matches = re.search(MarkdownCollector.TO_DO_LIST_REGEX, line)
            if matches is None:
                continue
            status = matches.group('status')
            url = matches.group('url').strip()
            if url not in existing_urls:
                if status == ' ':
                    self._to_do.append(url)
                    self._data[url] = {
                        'url': url,
                        'status': ListItemStatus.TO_DO
                    }
                elif status == 'x':
                    self._data[url] = {
                        'url': url,
                        'status': ListItemStatus.DONE
                    }
                else:
                    self.log_error(f"Couldn't read status of url: {url}")
                    self._data[url] = {
                        'url': url,
                        'status': 'status not recognized'
                    }
            else:
                self.log_info(f"List contains multiple of url: {url}")
            existing_urls.add(url)

    def _get_next_article_metadata(self) -> Optional[ArticleMetadata]:
        article = None
        while article == None and len(self._to_do) > 0:
            url = self._to_do.pop(0)
            try:
                article = ArticleMetadata('', url, source_id=self._source_id, source_title=self._source_title, article_id=hashlib.sha1(url.encode('utf-8')).hexdigest()[:12])
            except Exception as e:
                self.log_error("Error fetching article: ")
                print(e)
                self._data[url] = {
                    'url': url,
                    'status': f'error {e}'
                }
        return article
    
    def contains(self, url: str) -> bool:
        return url in self._to_do or url in self._data

    def add(self, url: str):
        if url in self._to_do:
            return
        self._to_do.append(url)
        self._added.append(url)
 
    def get_article_metadatas(self) -> List[ArticleMetadata]:
        """
        Returns a list of ArticleMetadata from the place the user wants to collect them from.
        """
        articles: List[ArticleMetadata] = []
        while len(self._to_do) > 0:
            article = self._get_next_article_metadata()
            if article is not None:
                articles.append(article)
        return articles

    def _status(self, url: str):
        item = self._data.get(url)
        return item['status'] if item is not None else ListItemStatus.TO_DO

    def used_articles_callback(self, usedArticles: List[ArticleMetadata]):
        """
        Parameters
        ----------
        usedArticles: List[ArticleMetadata]
            The final list of ArticleMetadata objects that will all make it into the final file
        """
        for metadata in usedArticles:
            self._data[metadata.url] = {
                'url': metadata.url,
                'status': ListItemStatus.DONE
            }
        self.log_info("rewriting markdown list file with new article statuses")
        # Only to-do items change: used ones are ticked, ones that errored are ticked with the
        # error. Headings, notes, order and anything unrecognised stay as they were.
        lines = []
        on_page = set()
        for line in self._lines:
            matches = re.search(MarkdownCollector.TO_DO_LIST_REGEX, line)
            if matches is not None:
                url = matches.group('url').strip()
                on_page.add(url)
                status = self._status(url)
                if matches.group('status') == ' ' and status != ListItemStatus.TO_DO:
                    ending = '\n' if line.endswith('\n') else ''
                    line = line[:matches.start('status')] + 'x' + line[matches.end('status'):].rstrip('\n')
                    if status != ListItemStatus.DONE:
                        line += f' ({status})'
                    line += ending
            lines.append(line)
        if lines and not lines[-1].endswith('\n'):
            lines[-1] += '\n'
        # URLs added with add() go at the end.
        for url in self._added:
            if url in on_page:
                continue
            on_page.add(url)
            status = self._status(url)
            if status == ListItemStatus.TO_DO:
                lines.append(f'- [ ] {url}\n')
            elif status == ListItemStatus.DONE:
                lines.append(f'- [x] {url}\n')
            else:
                lines.append(f'- [x] {url} ({status})\n')
        with open(self._filepath, "w") as file:
            file.writelines(lines)