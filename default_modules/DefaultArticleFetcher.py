from base_classes.article_fetcher import ArticleFetcher
import default_modules.article_parser as article_parser
from base_classes.ArticleMetadata import ArticleMetadata
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from default_modules.DefaultArticle import DefaultArticle
from default_modules.kindle_html_formatter import clean_html
import hashlib
from html import escape
import re
import requests
import threading
from typing import List, Callable, Optional, Sequence

@dataclass
class FetchResult:
    content: str
    title: str
    success: bool
    author: str = ''
    published: str = ''
    note: str = ''

"""
DefaultArticleFetcher fetches each article's page and extracts the article from it (see article_parser for the
extraction pipeline), then cleans the result up for e-readers (see kindle_html_formatter).
When fetching fails and the Collector provided content (e.g. an RSS feed's summary), that content is used instead.
Articles are fetched in parallel. It truncates Article titles to 100 characters.
"""
class DefaultArticleFetcher(ArticleFetcher):
    TITLE_CUTOFF = 100
    # Downloads run in parallel, but parsing is serialized: it's CPU-bound (so threads don't speed it up) and
    # libxml2, which lxml/trafilatura/readability are built on, has a history of thread-safety bugs.
    _PARSE_LOCK = threading.Lock()
    def __init__(
        self, meta: List[ArticleMetadata], replace_table_source_ids: List[str] = [],
        error_log_callback: Optional[Callable] = print, info_log_callback: Optional[Callable] = print,
        keep_images: bool = True, timeout: float = article_parser.DEFAULT_TIMEOUT, max_workers: int = 4,
        session: Optional[requests.Session] = None):
        """
        Parameters
        ----------
        meta: List[ArticleMetadata]
            The ordered collection of ArticleMetadata you want to produce articles for.
        replace_table_source_ids: List[str], optional
            Sometimes you want to replace <table> HTML elements with normal divs. This field allows you to pass in
            source_ids for which you'd like that replacement to happen. Tables that look like page layout (common in
            email newsletters) are always replaced; this forces every table from those sources to be replaced.
        error_log_callback: Optional[Callable], optional
        info_log_callback: Optional[Callable], optional
        keep_images: bool, optional
            Keep images in the article content. Defaults to True. EpubFileCreator embeds them in the book.
        timeout: float, optional
            Seconds to wait for each page to download. Defaults to 20.
        max_workers: int, optional
            How many articles to fetch at the same time. Defaults to 4. Use 1 to fetch one at a time.
        session: requests.Session, optional
            Session to fetch with, e.g. one carrying cookies for sites you subscribe to.
        """
        super().__init__(error_log_callback, info_log_callback)
        self._replace_table_sources = replace_table_source_ids
        self._meta = meta
        self._keep_images = keep_images
        self._timeout = timeout
        self._max_workers = max(1, max_workers)
        self._session = session

    @staticmethod
    def _ensure_id(meta: ArticleMetadata):
        """Every article needs a stable id for in-document links."""
        if not meta.id:
            meta.id = hashlib.sha1(meta.url.encode('utf-8')).hexdigest()[:12]

    def _clean(self, meta: ArticleMetadata, html: str, base_url: str, title: str) -> str:
        return clean_html(
            html, base_url=base_url, keep_images=self._keep_images,
            flatten_tables=meta.source_id in self._replace_table_sources,
            title=title, id_prefix=f'a{re.sub(r"[^A-Za-z0-9]", "", meta.id)}-',
        )

    def _fetch_page(self, url: str) -> str:
        return article_parser.fetch_html(url, timeout=self._timeout, session=self._session)[0]

    def _get_article_content(self, meta: ArticleMetadata) -> FetchResult:
        """
        Parameters
        ----------
        meta: ArticleMetadata
            The ArticleMetadata you want to get the display content for

        Returns
        -------
        A FetchResult with the cleaned display content for the Article, its title, whether fetching the content
        was successful, and any author/date found on the page.
        If fetch_content_from_url is False, the returned content is the cleaned up meta.content.
        """
        self._ensure_id(meta)
        if not meta.fetch_content_from_url:
            self.log_info(f"Not fetching content from url for article {meta.title}")
            with DefaultArticleFetcher._PARSE_LOCK:
                content = self._clean(meta, meta.content, meta.url, meta.title)
            return FetchResult(content, meta.title, True)

        title = meta.title
        try:
            self.log_info(f"Fetching {meta.url}")
            html, final_url = article_parser.fetch_html(meta.url, timeout=self._timeout, session=self._session)
            with DefaultArticleFetcher._PARSE_LOCK:
                extracted = article_parser.extract_article(html, final_url, fetch=self._fetch_page)
                title = meta.title or extracted.title or article_parser.title_from_url(meta.url)
                content = self._clean(meta, extracted.html, final_url, title)
            self.log_info(f"Extracted {title} with {extracted.extractor}")
            return FetchResult(content, title, True, extracted.author, extracted.date)
        except Exception as e:
            title = title or article_parser.title_from_url(meta.url)
            if meta.content.strip():
                with DefaultArticleFetcher._PARSE_LOCK:
                    content = self._clean(meta, meta.content, meta.url, title)
                return FetchResult(
                    content, title, False,
                    note=f'Could not fetch the full article ({e}). Showing the feed\'s version instead.')
            return FetchResult(f'<p>Error: {escape(str(e))}</p>', title, False)

    def _build_article(self, meta: ArticleMetadata, next_id: str, wpm: int = 200) -> DefaultArticle:
        result = self._get_article_content(meta)
        if not result.success:
            self.log_error(f"Failed to fetch article {result.title}. {result.note or result.content}")
        return DefaultArticle(
            meta, result.title[:DefaultArticleFetcher.TITLE_CUTOFF], result.content, next_id, wpm,
            author=result.author, published=result.published, note=result.note)

    def _get_articles_given_meta(self, meta: List[ArticleMetadata], wpm: int = 200) -> List[DefaultArticle]:
        """
        Returns the list of Article that should appear in the final output in the order they should appear in the final output.
        In this implementation, even if an article errors out, it is added to the document. This was a developer choice in order
        to surface to the user that this article will always fail. Otherwise, the user may never notice that a specific article
        in one of their Collectors never makes it to their doc.
        """
        for m in meta:
            self._ensure_id(m)
        next_ids = [m.id for m in meta[1:]] + ['top']
        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            return list(executor.map(lambda args: self._build_article(args[0], args[1], wpm), zip(meta, next_ids)))

    def get_articles(self) -> Sequence[DefaultArticle]:
        return self._get_articles_given_meta(self._meta)
