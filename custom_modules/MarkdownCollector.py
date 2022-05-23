from enum import Enum
from base_classes.ArticleMetadata import ArticleMetadata
from base_classes.collector import Collector
from typing import Dict, List, Callable, Optional, TypedDict, Union
import re
import random

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

    def __init__(self, list_filepath: str, error_log_callback: Optional[Callable] = print, info_log_callback: Optional[Callable] = print):
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
        """
        super().__init__(error_log_callback, info_log_callback)  
        self._filepath: str = list_filepath  
        self._to_do: List[str] = []
        self._data: Dict[str,ListItemDict] = {}
        self._load_urls()

    def __len__(self):
        return len(self._to_do)

    def _load_urls(self):
        self.log_info("Loading urls from markdown list")
        try:
            file = open(self._filepath, 'r')
            lines = file.readlines()
        except Exception as e:
            self.log_error(f"Could not load file. Skipping collecting articles. {e}")
            return
        
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
                article = ArticleMetadata('', url, source_id="0", source_title='List of Articles To Read', article_id=str(random.randint(1,6000)))
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
        lines = []
        with open(self._filepath, "w+") as file:
            for url in self._to_do:
                file.write(f"- [ ] {url}\n")
            for url in self._data:
                status = self._data[url].get('status', ListItemStatus.TO_DO)
                if status == ListItemStatus.DONE:
                    lines.append(f'- [x] {url}\n')
                elif status == ListItemStatus.TO_DO:
                    lines.append(f'- [ ] {url}\n')
                else:
                    lines.append(f'- [x] {url} ({status})\n')
            lines.sort()
            for line in lines:
                file.write(line)