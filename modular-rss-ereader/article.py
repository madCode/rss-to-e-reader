from abc import abstractmethod
from ArticleMetadata import ArticleMetadata

"""
An Article contains enough information for the article to be rendered anywhere.
"""
class Article():
    def __init__(self, meta: ArticleMetadata, display_title: str = "", display_content: str =""):
        """
        Parameters
        ----------
        meta: ArticleMetadata
            Metadata for the Article
        display_title: str, optional
            Title you want displayed when the Article is rendered. Defaults to meta.title
            Why: Allows for custom titles or custom length titles when rendering.
        display_content: str optional
            Content you want displayed when Article is rendered. Defaults to meta.content
        """
        self.meta = meta
        self.display_title = display_title if len(display_title) > 0 else meta.title
        self.display_content = display_content if len(display_content) > 0 else meta.content
        self.used_meta_content = True if len(display_content) <= 0 else False
        self.word_count = len(self.display_content.split())
    
    @abstractmethod
    def to_html_string(self) -> str:
        pass