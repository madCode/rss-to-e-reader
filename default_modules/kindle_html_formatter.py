"""
Cleans article HTML so it renders well on e-readers (Kindle, Kobo, KOReader, ...).

E-readers want simple, semantic HTML: paragraphs, headings, lists, quotes, images and the occasional
data table. Web pages give us the opposite: layout divs, inline styles, lazy-loaded images, share buttons,
newsletter sign-ups and scripts. clean_html() strips a fragment of HTML down to an allowlist of tags and
attributes, fixes up images and links so they work outside of the original site, and removes the usual
clutter that article extractors let through.
"""
import re
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Comment, NavigableString, Tag  # type: ignore

from base_classes.article import count_words  # noqa: F401 (re-exported)

# Elements whose contents are never useful in an e-book.
REMOVE_TAGS: Set[str] = {
    'script', 'style', 'noscript', 'iframe', 'object', 'embed', 'applet', 'form', 'input', 'button',
    'select', 'textarea', 'label', 'nav', 'aside', 'footer', 'svg', 'canvas', 'video', 'audio', 'track',
    'template', 'link', 'meta', 'head', 'title', 'base', 'dialog', 'menu', 'map', 'area', 'source',
}

# Elements we keep. Anything not in this set (and not removed above) is unwrapped: the tag goes, its text stays.
ALLOWED_TAGS: Set[str] = {
    'p', 'br', 'hr', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div',
    'em', 'i', 'strong', 'b', 'u', 's', 'del', 'ins', 'sub', 'sup', 'small', 'mark',
    'code', 'pre', 'kbd', 'samp', 'var', 'blockquote', 'q', 'cite', 'abbr',
    'a', 'ul', 'ol', 'li', 'dl', 'dt', 'dd', 'figure', 'figcaption', 'img',
    'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td', 'caption',
}

ALLOWED_ATTRIBUTES: Dict[str, Set[str]] = {
    'a': {'href'},
    'img': {'src', 'alt'},
    'td': {'colspan', 'rowspan'},
    'th': {'colspan', 'rowspan'},
    'ol': {'start'},
}
GLOBAL_ATTRIBUTES: Set[str] = {'id'}

# class/id tokens that mark page furniture rather than article text.
JUNK_TOKENS: Set[str] = {
    'ad', 'ads', 'advert', 'advertisement', 'adsbygoogle', 'promo', 'promotion', 'newsletter', 'subscribe',
    'subscription', 'signup', 'share', 'sharing', 'social', 'related', 'recommended', 'recommendations',
    'comments', 'comment', 'sidebar', 'popup', 'modal', 'cookie', 'cookies', 'banner', 'sponsored',
    'outbrain', 'taboola', 'paywall', 'breadcrumb', 'breadcrumbs', 'toolbar',
}

# Attributes sites use to lazy-load images, in order of preference.
LAZY_IMAGE_ATTRIBUTES: Tuple[str, ...] = (
    'data-src', 'data-original', 'data-lazy-src', 'data-hi-res-src', 'data-full-src', 'data-url',
)

EMPTY_REMOVABLE_TAGS: Set[str] = {
    'p', 'div', 'li', 'ul', 'ol', 'dl', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a', 'figure', 'figcaption',
    'blockquote', 'em', 'i', 'strong', 'b', 'u', 'span', 'small', 'table', 'tr', 'td', 'th', 'tbody', 'thead',
}
BLOCK_TAGS: Set[str] = {'p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'ul', 'ol', 'table', 'figure'}

# Short paragraphs matching these are page furniture ("Listen to this article", "5 min read", ...).
BOILERPLATE_PATTERN = re.compile(
    r'^(listen to (this|the) (article|essay|story|episode)|\d+[ -]min(ute)?s? (read|listen)|share (this|on)\b|'
    r'advertisement$|sign up (for|to)\b|subscribe (to|now|today)\b|read more:|related:|recommended:|'
    r'click here to\b|follow us on\b|skip past newsletter|after newsletter promotion)', re.I)
BOILERPLATE_MAX_WORDS = 12

PREFERRED_IMAGE_WIDTH = 1000
LAYOUT_TABLE_CELL_WORDS = 80
_HTML_TAG_PATTERN = re.compile(r'<\s*[a-zA-Z!/]')
_WHITESPACE = re.compile(r'\s+')
_INVALID_URL_CHARACTERS = re.compile(r'[\s"\\<>`{}|^]')


def attr(element: Tag, name: str) -> str:
    """An attribute's value as a string ('' if missing). bs4 returns lists for multi-valued attributes like class."""
    value = element.get(name)
    if value is None:
        return ''
    return value if isinstance(value, str) else ' '.join(value)


def text_to_html(text: str) -> str:
    """Wraps plain text in paragraphs, using blank lines as paragraph breaks."""
    import html as html_lib
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    return ''.join(f'<p>{html_lib.escape(_WHITESPACE.sub(" ", p))}</p>' for p in paragraphs)


def clean_html(
    html: str, base_url: str = '', keep_images: bool = True, keep_links: bool = True,
    flatten_tables: bool = False, title: str = '', id_prefix: str = '',
) -> str:
    """
    Parameters
    ----------
    html: str
        An HTML fragment or document. Plain text is accepted too and is split into paragraphs.
    base_url: str, optional
        URL the HTML came from. Used to turn relative links and image sources into absolute ones.
    keep_images: bool, optional
        Keep <img> elements. Defaults to True.
    keep_links: bool, optional
        Keep <a> elements. When False, links are replaced by their text. Defaults to True.
    flatten_tables: bool, optional
        Turn every table into plain divs. Tables that look like page layout (common in email newsletters)
        are always flattened; this forces data tables to be flattened too. Defaults to False.
    title: str, optional
        The article's title. If the content starts with a heading repeating it, that heading is removed,
        since renderers print the title themselves.
    id_prefix: str, optional
        Prefix added to every id (and to the matching #fragment links) so several articles can share one
        document without their ids colliding.

    Returns
    -------
    The cleaned HTML fragment as a string.
    """
    if not html or not html.strip():
        return ''
    if not _HTML_TAG_PATTERN.search(html):
        return text_to_html(html)

    soup = BeautifulSoup(html, 'html.parser')
    for comment in soup.find_all(string=lambda s: isinstance(s, Comment)):
        comment.extract()
    for element in soup.find_all(list(REMOVE_TAGS - {'source'})):
        element.decompose()
    _remove_hidden(soup)
    _remove_junk(soup)
    _remove_boilerplate(soup)
    _fix_pictures(soup)
    _fix_images(soup, base_url, keep_images)
    for element in soup.find_all('source'):
        element.decompose()
    _flatten_tables(soup, flatten_tables)
    _strip_tags_and_attributes(soup)
    _fix_links(soup, base_url, keep_links, id_prefix)
    _remove_duplicate_title(soup, title)
    _normalize_headings(soup)
    _remove_empty(soup)
    _collapse_blank_lines(soup)
    return str(soup).strip()


def clean_for_kindle(parser: BeautifulSoup) -> BeautifulSoup:
    """
    Kept for backwards compatibility with custom modules. Prefer clean_html().
    """
    return BeautifulSoup(clean_html(str(parser)), 'html.parser')


def _classes_and_id(element: Tag) -> List[str]:
    value = f"{attr(element, 'class')} {attr(element, 'id')}".lower()
    return [t for t in re.split(r'[\s_\-]+', value) if t]


def _remove_hidden(soup: BeautifulSoup):
    for element in soup.find_all(True):
        if element.decomposed:
            continue
        style = attr(element, 'style').replace(' ', '').lower()
        if (element.has_attr('hidden') or element.get('aria-hidden') == 'true'
                or 'display:none' in style or 'visibility:hidden' in style):
            element.decompose()


def _remove_junk(soup: BeautifulSoup):
    total_words = len(soup.get_text(' ').split()) or 1
    for element in soup.find_all(True):
        if element.decomposed or element.name in ('html', 'body', 'img'):
            continue
        role = element.get('role')
        tokens = _classes_and_id(element)
        if role in ('navigation', 'complementary', 'banner', 'contentinfo', 'dialog') or JUNK_TOKENS.intersection(tokens):
            # Safety net: never throw away most of the article because of an unlucky class name.
            if len(element.get_text(' ').split()) / total_words < 0.4:
                element.decompose()


def _remove_boilerplate(soup: BeautifulSoup):
    for element in soup.find_all(['p', 'div', 'li', 'span', 'h2', 'h3', 'h4', 'h5', 'h6']):
        if element.decomposed:
            continue
        text = element.get_text(' ', strip=True)
        if len(text.split()) <= BOILERPLATE_MAX_WORDS and BOILERPLATE_PATTERN.match(text):
            element.decompose()


def _parse_srcset(srcset: str) -> List[Tuple[str, float, str]]:
    """Returns (url, value, unit) for each srcset candidate. unit is 'w', 'x' or ''."""
    candidates = []
    for candidate in re.split(r',\s+', srcset.strip()):
        parts = candidate.strip().split()
        if not parts:
            continue
        url = parts[0].rstrip(',')
        value, unit = 1.0, ''
        if len(parts) > 1:
            match = re.match(r'([\d.]+)([wx])', parts[1])
            if match:
                value, unit = float(match.group(1)), match.group(2)
        candidates.append((url, value, unit))
    return candidates


def best_srcset_candidate(srcset: str) -> Optional[str]:
    """Picks a srcset candidate big enough for an e-reader screen without being huge."""
    candidates = _parse_srcset(srcset)
    if not candidates:
        return None
    widths = [c for c in candidates if c[2] == 'w']
    if widths:
        big_enough = sorted((c for c in widths if c[1] >= PREFERRED_IMAGE_WIDTH), key=lambda c: c[1])
        return big_enough[0][0] if big_enough else max(widths, key=lambda c: c[1])[0]
    densities = sorted((c for c in candidates if c[1] <= 2), key=lambda c: c[1])
    return densities[-1][0] if densities else candidates[0][0]


def _is_placeholder(src: str) -> bool:
    return src.startswith('data:') and len(src) < 1000


def _image_source(img: Tag) -> Optional[str]:
    for attribute in ('data-srcset', 'srcset'):
        srcset = attr(img, attribute)
        if srcset:
            best = best_srcset_candidate(srcset)
            if best and not _is_placeholder(best):
                return best
    for attribute in LAZY_IMAGE_ATTRIBUTES:
        value = attr(img, attribute).strip()
        if value and not _is_placeholder(value):
            return value
    src = attr(img, 'src').strip()
    if src and not _is_placeholder(src):
        return src
    return None


def _fix_pictures(soup: BeautifulSoup):
    for picture in soup.find_all('picture'):
        img = picture.find('img')
        if img is None:
            img = soup.new_tag('img')
        if _image_source(img) is None:
            sources = picture.find_all('source')
            # Prefer formats every e-reader understands over webp/avif.
            sources.sort(key=lambda s: 1 if any(f in attr(s, 'type') for f in ('webp', 'avif')) else 0)
            for source in sources:
                srcset = attr(source, 'srcset') or attr(source, 'data-srcset')
                if srcset:
                    img['srcset'] = srcset
                    break
        picture.replace_with(img)


def _fix_images(soup: BeautifulSoup, base_url: str, keep_images: bool):
    for img in soup.find_all('img'):
        if not keep_images:
            img.decompose()
            continue
        if attr(img, 'width') in ('0', '1') or attr(img, 'height') in ('0', '1'):
            img.decompose()  # tracking pixel
            continue
        src = _image_source(img)
        if src is None:
            img.decompose()
            continue
        if not src.startswith('data:'):
            src = urljoin(base_url, src) if base_url else src
            if _INVALID_URL_CHARACTERS.search(src) or urlparse(src).scheme not in ('http', 'https', ''):
                img.decompose()
                continue
        img.attrs = {'src': src, 'alt': attr(img, 'alt').strip()}


def _is_layout_table(table: Tag) -> bool:
    if table.get('role') == 'presentation' or table.find('table') is not None:
        return True
    rows = table.find_all('tr')
    if rows and all(len(row.find_all(['td', 'th'], recursive=False)) <= 1 for row in rows):
        return True
    return any(len(cell.get_text(' ').split()) > LAYOUT_TABLE_CELL_WORDS for cell in table.find_all(['td', 'th']))


def _flatten_tables(soup: BeautifulSoup, flatten_all: bool):
    for table in soup.find_all('table'):
        if table.decomposed or not (flatten_all or _is_layout_table(table)):
            continue
        for element in [table] + table.find_all(['thead', 'tbody', 'tfoot', 'tr', 'td', 'th', 'caption', 'table']):
            element.name = 'div'
            element.attrs = {}


def _strip_tags_and_attributes(soup: BeautifulSoup):
    for element in soup.find_all(True):
        if element.name not in ALLOWED_TAGS:
            element.unwrap()
            continue
        allowed = ALLOWED_ATTRIBUTES.get(element.name, set()) | GLOBAL_ATTRIBUTES
        element.attrs = {k: v for k, v in element.attrs.items() if k in allowed}


def _sanitize_id(value: str) -> str:
    return re.sub(r'[^A-Za-z0-9_.\-]', '-', value)


def _fix_links(soup: BeautifulSoup, base_url: str, keep_links: bool, id_prefix: str):
    ids: Dict[str, str] = {}
    for element in soup.find_all(id=True):
        old = attr(element, 'id')
        new = _sanitize_id(id_prefix + old)
        if not new[0].isalpha():
            new = 'id-' + new
        if old in ids or new in ids.values():
            del element['id']  # duplicate ids make invalid XHTML
            continue
        ids[old] = new
        element['id'] = new

    for link in soup.find_all('a'):
        href = attr(link, 'href').strip()
        if not keep_links or not href:
            link.unwrap()
            continue
        if href.startswith('#'):
            target = ids.get(href[1:])
            if target is None:
                link.unwrap()
            else:
                link['href'] = '#' + target
            continue
        absolute = urljoin(base_url, href) if base_url else href
        if _INVALID_URL_CHARACTERS.search(absolute) or urlparse(absolute).scheme not in ('http', 'https', 'mailto'):
            link.unwrap()
            continue
        link['href'] = absolute


def _normalize_text(text: str) -> str:
    return re.sub(r'[^\w]+', ' ', text.lower()).strip()


def _remove_duplicate_title(soup: BeautifulSoup, title: str):
    if not title:
        return
    heading = soup.find(['h1', 'h2', 'h3'])
    if heading is None:
        return
    # Only when the heading is at the very start of the content.
    preceding_words = sum(
        len(el.get_text(' ').split()) for el in heading.find_all_previous(['p', 'li', 'blockquote'])
    )
    if preceding_words == 0 and _normalize_text(heading.get_text(' ')) == _normalize_text(title):
        heading.decompose()


def _normalize_headings(soup: BeautifulSoup):
    """The article title is the only <h1>; content headings start at <h2>."""
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    if not headings:
        return
    top = min(int(h.name[1]) for h in headings)
    shift = 2 - top
    if shift <= 0:
        return
    for heading in headings:
        heading.name = f'h{min(6, int(heading.name[1]) + shift)}'


def _remove_empty(soup: BeautifulSoup):
    for element in reversed(soup.find_all(True)):
        if element.name not in EMPTY_REMOVABLE_TAGS:
            continue
        if element.get_text(strip=True):
            continue
        if element.find(['img', 'hr', 'table']) is not None:
            continue
        if element.name == 'a' and element.get('id'):
            continue
        element.decompose()


def _collapse_blank_lines(soup: BeautifulSoup):
    soup.smooth()  # merge adjacent text nodes left behind by removed elements
    for text in soup.find_all(string=True):
        if isinstance(text, NavigableString) and '\n' in text and not text.strip() and text.find_parent('pre') is None:
            text.replace_with('\n')
