from base_classes.article import Article
from base_classes.ArticleMetadata import ArticleMetadata
from html import escape
from typing import List

"""
An Article contains enough information for the article to be rendered anywhere.
"""
class DefaultArticle(Article):
    def __init__(
        self, meta: ArticleMetadata, display_title: str = "", display_content: str ="", next_id: str ="", wpm: int = 200,
        author: str = "", published: str = "", note: str = ""):
        """
        Parameters
        ----------
        meta: ArticleMetadata
            Metadata for the Article
        display_title: str, optional
            Title you want displayed when the Article is rendered. Defaults to meta.title
            Why: Allows for custom titles or custom length titles when rendering.
        display_content: str, optional
            Content you want displayed when Article is rendered. Defaults to meta.content
            Should already be cleaned HTML (see kindle_html_formatter.clean_html).
        next_id: str, optional
            The id of the Article coming after this. Defaults to empty string. 'top' links back to the table of contents.
        wpm: int, optional
            The words per minute the user reads at. Defaults to 200.
            Pass in -1 to not use wpm in rendering.
        author: str, optional
            Author(s) of the article, shown in the byline.
        published: str, optional
            Publication date of the article, shown in the byline.
        note: str, optional
            A short note shown above the article, e.g. to say the full text couldn't be fetched.
        """
        super().__init__(meta, display_title, display_content)
        self.id = meta.id
        self.next_id = next_id
        self._wpm = wpm
        self.author = author
        self.published = published
        self.note = note

    @staticmethod
    def anchor_for(article_id: str) -> str:
        """HTML id for an article. XHTML ids can't start with a digit, so ids are prefixed."""
        return 'top' if article_id == 'top' else f'article-{article_id}'

    @property
    def anchor_id(self) -> str:
        return DefaultArticle.anchor_for(self.meta.id)

    def time_to_read_in_minutes(self) -> int:
        if self._wpm <= 0:
            return 0
        return self.word_count//self._wpm

    def time_to_read_str(self) -> str:
        per_min = self.time_to_read_in_minutes()
        if per_min == 0 and self._wpm > 0:
            return '< 1 min'
        if per_min < 60:
            return str(per_min) + ' min'
        per_hour = per_min//60
        remainder = per_min%60
        return str(per_hour) + ' hr ' + str(remainder) + ' min'

    def byline_parts(self) -> List[str]:
        parts = [p for p in (self.meta.source_title, self.author, self.published) if p]
        stats = f'{self.word_count:,} words'
        if self._wpm > 0:
            stats += f' · {self.time_to_read_str()}'
        parts.append(stats)
        return parts

    def body_html(self) -> str:
        """The article's title, byline and content, without any document navigation."""
        title = escape(self.display_title)
        heading = f'<a href="{escape(self.meta.url)}">{title}</a>' if self.meta.url else title
        note = f'\n<p class="note">{escape(self.note)}</p>' if self.note else ''
        return (
            f'<h1 class="article-title">{heading}</h1>\n'
            f'<p class="byline">{escape(" · ".join(self.byline_parts()))}</p>{note}\n'
            f'<div class="article-body">\n{self.display_content}\n</div>'
        )

    def to_html_string(self) -> str:
        nav = f'<p class="article-nav"><a href="#top">↑ Contents</a>'
        if self.next_id and self.next_id != 'top':
            nav += f' · <a href="#{DefaultArticle.anchor_for(self.next_id)}">Next article →</a>'
        nav += '</p>'
        return f'<section class="article" id="{self.anchor_id}">\n{self.body_html()}\n{nav}\n</section>\n'
