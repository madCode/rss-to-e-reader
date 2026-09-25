from base_classes.file_creator import FileCreator
from bs4 import BeautifulSoup  # type: ignore
from datetime import date
from default_modules.browser_impersonation import DEFAULT_IMPERSONATE
from default_modules.DefaultArticle import DefaultArticle
from default_modules.ebook_images import ProcessedImage, fetch_images
from default_modules.ereader_css import EREADER_CSS
from default_modules.kindle_html_formatter import attr
from ebooklib import epub  # type: ignore
from html import escape
from io import BytesIO
import requests
from typing import Callable, Dict, List, Optional, Sequence, Tuple
import uuid

"""
EpubFileCreator writes the articles as an EPUB e-book: one chapter per article, a contents page, a generated
cover, and the articles' images downloaded and embedded in the book.

EPUB is the format Amazon recommends for Send to Kindle (it no longer accepts MOBI), and Kobo, KOReader,
Apple Books, Google Play Books and Calibre all read it natively.
"""
class EpubFileCreator(FileCreator):
    def __init__(
        self, filestub: str, articles: Sequence[DefaultArticle], title: str,
        author: str = 'RSS to e-Reader', language: str = 'en',
        embed_images: bool = True, max_images_per_article: int = 20, max_total_image_bytes: int = 15 * 1024 * 1024,
        image_max_dimension: int = 1200, grayscale_images: bool = False, include_cover: bool = True,
        include_source_links: bool = True, image_timeout: float = 20, session: Optional[requests.Session] = None,
        impersonate_browser: Optional[str] = DEFAULT_IMPERSONATE,
        error_log_callback: Optional[Callable] = print, info_log_callback: Optional[Callable] = print):
        """
        Parameters
        ----------
        filestub: str
            The path and filename desired for the resulting file, without the .epub extension.
        articles: Sequence[DefaultArticle]
            The Articles to put in the book, in order.
        title: str
            Title of the book.
        author: str, optional
            Author shown in the e-reader's library.
        language: str, optional
            Language code of the book. Defaults to 'en'.
        embed_images: bool, optional
            Download the articles' images and put them in the book. Defaults to True.
            When False, images are removed (an e-book can't load images from the internet).
        max_images_per_article: int, optional
            Stop embedding images in an article after this many. Defaults to 20.
        max_total_image_bytes: int, optional
            Stop embedding images once they add up to this size. Defaults to 15MB, which keeps the book
            under the attachment limits of most email providers (Gmail allows 25MB, Send to Kindle 50MB).
        image_max_dimension: int, optional
            Images are scaled down to fit in a square this many pixels wide. Defaults to 1200.
        grayscale_images: bool, optional
            Convert images to grayscale, which makes them much smaller. Defaults to False.
        include_cover: bool, optional
            Generate a cover image with the title, date and article count. Defaults to True.
        include_source_links: bool, optional
            End each article with a link to the original page. Defaults to True.
        image_timeout: float, optional
            Seconds to wait for each image download.
        session: requests.Session, optional
            Session to download images with.
        impersonate_browser: str, optional
            Browser to impersonate when an image server blocks the download (see DefaultArticleFetcher). None turns it off.
        """
        super().__init__(filestub, articles, error_log_callback, info_log_callback)
        self.title = title
        self.author = author
        self.language = language
        self.embed_images = embed_images
        self.max_images_per_article = max_images_per_article
        self.max_total_image_bytes = max_total_image_bytes
        self.image_max_dimension = image_max_dimension
        self.grayscale_images = grayscale_images
        self.include_cover = include_cover
        self.include_source_links = include_source_links
        self.image_timeout = image_timeout
        self.session = session
        self.impersonate_browser = impersonate_browser
        self.articles: Sequence[DefaultArticle] = articles

    @property
    def filepath(self) -> str:
        return self.filestub + '.epub'

    def _total_minutes(self) -> int:
        return sum(a.time_to_read_in_minutes() for a in self.articles)

    def _contents_page(self, chapter_files: List[str]) -> str:
        items = []
        for article, file_name in zip(self.articles, chapter_files):
            meta = ' · '.join(p for p in (article.meta.source_title, article.time_to_read_str()) if p)
            items.append(
                f'<li><a href="{file_name}">{escape(article.display_title)}</a>'
                f'<br/><span class="meta">{escape(meta)}</span></li>')
        return (f'<h1>{escape(self.title)}</h1>'
                f'<p class="byline">{len(self.articles)} articles · {self._time_str(self._total_minutes())}</p>'
                f'<ol class="contents">{"".join(items)}</ol>')

    @staticmethod
    def _time_str(minutes: int) -> str:
        if minutes < 60:
            return f'{minutes} min'
        return f'{minutes // 60} hr {minutes % 60} min'

    def _embed_images(self, soups: List[BeautifulSoup], articles: Sequence[DefaultArticle]) -> Dict[str, Tuple[str, ProcessedImage]]:
        """
        Downloads the images referenced in each soup, rewrites the <img> tags to point at the embedded copies
        and removes the ones that couldn't be embedded. Returns {url: (file name in the book, image)}.
        """
        wanted: List[Tuple[str, str]] = []  # (url, referer)
        for soup, article in zip(soups, articles):
            images = soup.find_all('img')
            for img in images[:self.max_images_per_article] if self.embed_images else []:
                wanted.append((attr(img, 'src'), article.meta.url))
        fetched: Dict[str, ProcessedImage] = {}
        if wanted:
            by_referer: Dict[str, List[str]] = {}
            for url, referer in wanted:
                by_referer.setdefault(referer, []).append(url)
            for referer, urls in by_referer.items():
                fetched.update(fetch_images(
                    urls, referer=referer, max_dimension=self.image_max_dimension,
                    grayscale=self.grayscale_images, timeout=self.image_timeout, session=self.session,
                    impersonate=self.impersonate_browser))

        embedded: Dict[str, Tuple[str, ProcessedImage]] = {}
        total = 0
        for soup in soups:
            for img in soup.find_all('img'):
                src = attr(img, 'src')
                if src not in embedded:
                    image = fetched.get(src)
                    if image is None or total + len(image.data) > self.max_total_image_bytes:
                        parent = img.parent
                        img.decompose()
                        if parent is not None and parent.name == 'figure' and not parent.find('img'):
                            parent.decompose()
                        continue
                    total += len(image.data)
                    embedded[src] = (f'images/img{len(embedded) + 1:04d}.{image.extension}', image)
                img['src'] = embedded[src][0]
        self.log_info(f'Embedded {len(embedded)} images ({total // 1024} KB)')
        return embedded

    def _cover(self) -> bytes:
        from PIL import Image, ImageDraw, ImageFont  # type: ignore
        width, height = 1264, 1680
        image = Image.new('L', (width, height), 255)
        draw = ImageDraw.Draw(image)

        def font(size: int):
            for name in ('DejaVuSerif-Bold.ttf', 'DejaVuSerif.ttf', 'Georgia.ttf', 'Times New Roman.ttf'):
                try:
                    return ImageFont.truetype(name, size)
                except OSError:
                    continue
            try:
                return ImageFont.load_default(size=size)
            except TypeError:
                return ImageFont.load_default()

        def wrap(text: str, fnt, max_width: int) -> List[str]:
            lines: List[str] = []
            for word in text.split():
                candidate = f'{lines[-1]} {word}' if lines else word
                if lines and draw.textlength(candidate, font=fnt) <= max_width:
                    lines[-1] = candidate
                else:
                    lines.append(word)
            return lines

        margin = 100
        draw.rectangle([margin // 2, margin // 2, width - margin // 2, height - margin // 2], outline=0, width=6)
        y = 320
        title_font = font(110)
        for line in wrap(self.title, title_font, width - 2 * margin)[:5]:
            draw.text((margin, y), line, font=title_font, fill=0)
            y += 130
        y += 60
        draw.line([margin, y, width - margin, y], fill=0, width=4)
        y += 60
        detail_font = font(54)
        details = [date.today().strftime('%A, %B %-d, %Y'),
                   f'{len(self.articles)} articles · {self._time_str(self._total_minutes())}']
        sources = list(dict.fromkeys(a.meta.source_title for a in self.articles if a.meta.source_title))
        if sources:
            details.append(', '.join(sources[:4]) + (' and more' if len(sources) > 4 else ''))
        for detail in details:
            for line in wrap(detail, detail_font, width - 2 * margin)[:3]:
                draw.text((margin, y), line, font=detail_font, fill=0)
                y += 72
            y += 20
        output = BytesIO()
        image.save(output, format='JPEG', quality=85)
        return output.getvalue()

    def build_book(self) -> epub.EpubBook:
        book = epub.EpubBook()
        book.set_identifier(f'urn:uuid:{uuid.uuid4()}')
        book.set_title(self.title)
        book.set_language(self.language)
        book.add_author(self.author)
        book.add_metadata('DC', 'date', date.today().isoformat())

        style = epub.EpubItem(uid='style', file_name='style/main.css', media_type='text/css', content=EREADER_CSS)
        book.add_item(style)

        if self.include_cover:
            book.set_cover('cover.jpg', self._cover(), create_page=True)
            # ebooklib marks the cover page non-linear, which EPUB validators (and Send to Kindle) reject
            # unless something links to it.
            book.get_item_with_id('cover').is_linear = True

        soups = []
        for article in self.articles:
            html = article.body_html()
            if self.include_source_links and article.meta.url:
                html += f'<p class="source-link">Original: <a href="{escape(article.meta.url)}">{escape(article.meta.url)}</a></p>'
            soups.append(BeautifulSoup(html, 'html.parser'))
        embedded = self._embed_images(soups, self.articles)
        for file_name, image in embedded.values():
            book.add_item(epub.EpubItem(
                uid=file_name.replace('/', '_').replace('.', '_'), file_name=file_name,
                media_type=image.media_type, content=image.data))

        chapters = []
        for i, (article, soup) in enumerate(zip(self.articles, soups)):
            chapter = epub.EpubHtml(title=article.display_title or f'Article {i + 1}', file_name=f'article{i + 1:03d}.xhtml', lang=self.language)
            chapter.content = str(soup)
            chapter.add_item(style)
            book.add_item(chapter)
            chapters.append(chapter)

        contents = epub.EpubHtml(title='Contents', file_name='contents.xhtml', lang=self.language)
        contents.content = self._contents_page([c.file_name for c in chapters])
        contents.add_item(style)
        book.add_item(contents)

        book.toc = [epub.Link(c.file_name, c.title, f'chapter{i + 1}') for i, c in enumerate(chapters)]
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        book.spine = (['cover'] if self.include_cover else []) + [contents] + chapters
        book.guide.append({'type': 'toc', 'title': 'Contents', 'href': contents.file_name})
        return book

    def write_file(self) -> str:
        """
        Writes the book to filestub + '.epub' and returns that path.
        """
        self.log_info(f'Writing {len(self.articles)} articles to {self.filepath}')
        epub.write_epub(self.filepath, self.build_book())
        return self.filepath
