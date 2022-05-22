from article import Article
from ArticleMetadata import ArticleMetadata

"""
An Article contains enough information for the article to be rendered anywhere.
"""
class DefaultArticle(Article):
    def __init__(self, meta: ArticleMetadata, display_title: str = "", display_content: str ="", next_id: str ="", wpm: int = 200):
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
        next_id: str, optional
            The id of the Article coming after this. Defaults to empty string.
        wpm: int, optional
            The words per minute the user reads at. Defaults to 200.
            Pass in -1 to not use wpm in rendering.
        """
        super().__init__(meta, display_title, display_content)
        self.next_id = next_id
        self._wpm = wpm

    def _time_to_read_in_minutes(self) -> int:
        if self._wpm <= 0:
            return 0
        return self.word_count//self._wpm

    def _time_to_read_str(self) -> str:
        per_min = self._time_to_read_in_minutes()
        if per_min < 60:
            return str(per_min) + ' min'
        per_hour = per_min//60
        remainder = per_min%60
        return str(per_hour) + ' hr ' + str(remainder) + ' min'

    def to_html_string(self) -> str:
        reading_time_str = f': est. {self._time_to_read_str()})' if self._wpm > 0 else ')'
        return (f"""        <a href="#top">[← top]</a>
        <h1 id="{self.meta.id}"><a href="{self.meta.url}">{self.display_title}</a></h1>
        <a href="#{self.next_id}">[skip →]</a>
        <h2>{self.meta.source_title}</h2>
        <h3>{'Fetched content' if not self.used_meta_content else ''}({self.word_count} words{reading_time_str}</h3>
        {self.display_content}""")