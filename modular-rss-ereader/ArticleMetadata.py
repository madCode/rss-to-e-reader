"""
An ArticleMetadata should contain enough information for:
- a CreateList module to order and filter a list of ArticleMetadata based on user-specified criteria
- a FetchArticles module to fetch the article's contents and everything else needed to create the final file
"""
from typing import Optional


class ArticleMetadata:
    def __init__(self, title: str, url: str, source_id: str, content: str = "", source_title: str ="", article_id: str ="", fetch_content_from_url: bool = True):
        """
        Parameters
        ----------
        title: str
            Title of the article
        url: str
            Link to the article.
            Why: Allows FetchArticles modules to get extra data as needed.
        source_id: str
            Unique identifier for the source.
            Why: Allows CreateList modules to filter by source.
        content: str, optional
            Content of the article, if you already know it.
            Why: Useful for RSS feed Collectors that can pull article content from the RSS feed itself.
        source_title: str, optional
            Title of source.
            Why: Allows CreateFile modules to display article source if desired. source_id can be used for this purpose as well.
        article_id: str, optional
            Unique identifier for the article.
            Why: Useful for RSS feed Collectors that may want to mark a given article as read.
        fetch_content_from_url: bool, optional
            Should an ArticleFetcher try to fetch the article's contents from the given url?
            Defaults to True. Unless you're using an RSS reader, you likely want this to be true.
        """
        self.id = article_id
        self.url = url
        self.content = content
        self.source_title = source_title
        self.source_id = source_id
        self.title = title
        self.fetch_content_from_url = fetch_content_from_url
        self.collector_id: Optional[int] = None # Can be set and used optionally by ListCreators