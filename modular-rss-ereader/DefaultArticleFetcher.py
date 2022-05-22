from article_fetcher import ArticleFetcher
import article_parser
from ArticleMetadata import ArticleMetadata
from DefaultArticle import Article, DefaultArticle
import kindle_html_formatter
from typing import List, Callable, Optional, Any, Tuple, Sequence

"""
DefaultArticleFetcher uses basic html parsing to fetch article contents.
It has some custom parsers for a few websites, but defaults to printing
the entire html contents of the page.
It truncates Article titles to 100 characters.
"""
class DefaultArticleFetcher(ArticleFetcher):
    TITLE_CUTOFF = 100
    def __init__(
        self, meta: List[ArticleMetadata] = [], replace_table_source_ids: List[str] = [], error_log_callback: Optional[Callable] = print, info_log_callback: Optional[Callable] = print):
        """
        Parameters
        ----------
        error_log_callback: Optional[Callable], optional
        info_log_callback: Optional[Callable], optional
        """
        super().__init__(error_log_callback, info_log_callback)
        self._replace_table_sources = replace_table_source_ids
        self._meta = meta
    
    def _get_parser(self, url: str) -> Tuple[Any, bool]:
        """
        Parameters
        ----------
        url: str
            The url you want to get the parser for.
        
        Returns
        -------
        A Tuple of some kind of parser object and a boolean to denote whether it was the default parser or a specialized one
        The parser object doesn't have a type right now because it's one of many possible BeautifulSoup object types
        """
        is_default = False
        parseFunction = None
        for key in article_parser.special_parsers:
            if url.startswith(key):
                parseFunction = article_parser.special_parsers[key]
        if parseFunction == None:
            parseFunction = article_parser.get_bs4_parser(url)
            is_default = True
        return parseFunction, is_default

    def _get_article_content(self, meta: ArticleMetadata) -> Tuple[str, bool]:
        """
        Parameters
        ----------
        meta: ArticleMetadata
            The ArticleMetadata you want to get the display content for
        
        Returns
        -------
        A Tuple of the display content for the Article and a boolean to denote whether fetching the content was successful or not
        """
        if not meta.fetch_content_from_url:
            return (meta.content, True)
        
        try:
            content = ''
            parser, is_default = self._get_parser(meta.url)
            article = kindle_html_formatter.clean_for_kindle(parser)
            self.word_count = len(article.text.split())
            content = '<p>[Default parser used]</p>' if is_default else ''
            if is_default:
                if meta.source_id in self._replace_table_sources:
                    return (content + article_parser.replace_tables_with_divs(parser.get_text()).prettify(), True)
                else:
                    return (content + parser.get_text(), True)
            else:
                return (article.prettify(), True)
        except Exception as e:
            return (content + f'<p>Error: {str(e)}</p>', False)

    def _get_articles_given_meta(self, meta: List[ArticleMetadata]) -> List[Article]:
        """
        Returns the list of Article that should appear in the final output in the order they should appear in the final output.
        In this implementation, even if an article errors out, it is added to the document. This was a developer choice in order
        to surface to the user that this article will always fail. Otherwise, the user may never notice that a specific article 
        in one of their Collectors never makes it to their doc.
        """
        result: List[Article] = []
        for i in range(len(meta)):
            m = meta[i]
            next_id = meta[i+1].id if i < len(meta) - 1 else 'top'
            content, success = self._get_article_content(m)
            if not success:
                self.log_error(f"Failed to fetch article. Adding the following error message to document:\n{content}")
            result.append(DefaultArticle(m, m.title[:DefaultArticleFetcher.TITLE_CUTOFF], content,next_id))
        return result

    def get_articles(self) -> Sequence[Article]:
        return self._get_articles_given_meta(self._meta)