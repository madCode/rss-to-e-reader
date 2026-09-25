"""
Fetches web pages and pulls the article out of them.

extract_article() runs a pipeline of extractors and keeps the first result with enough text:
1. A site-specific rule from SITE_RULES, if the url's host matches one.
2. trafilatura (https://trafilatura.readthedocs.io), a well-maintained main-content extractor.
3. readability-lxml, a port of the algorithm behind Firefox's Reader View. Both generic extractors run;
   trafilatura's output is cleaner so it wins unless readability finds READABILITY_PREFERENCE_RATIO times
   as much text (trafilatura occasionally stops after the first few paragraphs of long, image-heavy pages).
4. schema.org JSON-LD `articleBody`. Many sites (including some paywalled ones) ship the full text here.
5. The whole <body>, as a last resort. The sanitizer in kindle_html_formatter strips it down.

If no stage reaches MIN_WORDS, the longest result wins. The returned HTML is not sanitized yet:
pass it through kindle_html_formatter.clean_html() before rendering.
"""
from dataclasses import dataclass
import json
import re
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple
from urllib.parse import urlparse

from bs4 import BeautifulSoup, UnicodeDammit  # type: ignore
import requests
import trafilatura  # type: ignore
from readability import Document  # type: ignore

from default_modules.kindle_html_formatter import attr, count_words, text_to_html

USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/126.0 Safari/537.36'
)
DEFAULT_HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}
DEFAULT_TIMEOUT = 20
MIN_WORDS = 150
# class/id substrings of cookie and consent banners (including common consent-management plugins).
OVERLAY_MARKERS = ('cookie', 'consent', 'gdpr', 'cmplz', 'onetrust', 'didomi', 'usercentrics', 'truste')
READABILITY_PREFERENCE_RATIO = 1.5
TITLE_SEPARATORS = re.compile(r'\s+[|\-\u2013\u2014:\u00b7\u2022]\s+')


@dataclass
class ExtractedArticle:
    html: str
    title: str = ''
    author: str = ''
    date: str = ''
    site_name: str = ''
    extractor: str = ''

    @property
    def word_count(self) -> int:
        return count_words(self.html)


def fetch_html(url: str, timeout: float = DEFAULT_TIMEOUT, session: Optional[requests.Session] = None) -> Tuple[str, str]:
    """
    Downloads a page.

    Returns
    -------
    (html, final_url): the decoded page and the url it ended up at after redirects.
    Raises requests.HTTPError for 4xx/5xx responses.
    """
    getter = session.get if session is not None else requests.get
    response = getter(url, headers=DEFAULT_HEADERS, timeout=timeout)
    response.raise_for_status()
    return decode_response(response), response.url or url


def decode_response(response: requests.Response) -> str:
    content_type = response.headers.get('content-type', '').lower()
    if 'charset=' in content_type and response.encoding:
        try:
            return response.content.decode(response.encoding, errors='replace')
        except LookupError:
            pass
    # No charset header: look at <meta charset>, then sniff.
    dammit = UnicodeDammit(response.content, is_html=True)
    return dammit.unicode_markup or response.content.decode('utf-8', errors='replace')


# --- Site-specific rules -----------------------------------------------------------------------------
# A rule gets the parsed page, its url and a function to fetch other urls, and returns article HTML or None.
# Rules only need to exist for sites the generic extractors get wrong. Returning None falls through to them.
SiteRule = Callable[[BeautifulSoup, str, Callable[[str], str]], Optional[str]]


def select_rule(*selectors: str) -> SiteRule:
    """A rule that returns the first element matching any of the CSS selectors."""
    def rule(soup: BeautifulSoup, url: str, fetch: Callable[[str], str]) -> Optional[str]:
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                return ''.join(str(e) for e in elements)
        return None
    return rule


def _the_tls(soup: BeautifulSoup, url: str, fetch: Callable[[str], str]) -> Optional[str]:
    script = soup.find(string=re.compile('tlsPageObject'))
    match = re.search(r'tlsPageObject = \{"ID":"(\d+)"', str(script)) if script else None
    if not match:
        return None
    data = json.loads(fetch('https://www.the-tls.co.uk/wp-json/tls/v2/single-article/' + match.group(1)))
    return data.get('content')


SITE_RULES: Dict[str, SiteRule] = {
    'nytimes.com': select_rule('section[name=articleBody]'),
    'newcriterion.com': select_rule('div.article-text-column'),
    'smithsonianmag.com': select_rule('div.article-body'),
    'aeon.co': select_rule('div.article__body__content', 'div[data-component="essay-body"]'),
    'the-tls.co.uk': _the_tls,
}


def find_site_rule(url: str) -> Optional[SiteRule]:
    host = (urlparse(url).hostname or '').lower()
    for domain, rule in SITE_RULES.items():
        if host == domain or host.endswith('.' + domain):
            return rule
    return None


# --- Generic extractors ------------------------------------------------------------------------------

def _trafilatura(html: str, url: str) -> Optional[str]:
    return trafilatura.extract(
        html, url=url or None, output_format='html', include_images=True, include_links=True,
        include_formatting=True, include_tables=True, include_comments=False, favor_recall=True,
    )


def _readability(html: str, url: str) -> Optional[str]:
    return Document(html, url=url or None).summary(html_partial=True)


def _iter_json_ld(soup: BeautifulSoup) -> Iterator[Dict[str, Any]]:
    for script in soup.find_all('script', attrs={'type': 'application/ld+json'}):
        try:
            data = json.loads(script.string or '')
        except (ValueError, TypeError):
            continue
        stack = data if isinstance(data, list) else [data]
        while stack:
            item = stack.pop(0)
            if isinstance(item, list):
                stack.extend(item)
            elif isinstance(item, dict):
                yield item
                stack.extend(item.get('@graph', []))


def _json_ld_body(soup: BeautifulSoup) -> Optional[str]:
    bodies = [item['articleBody'] for item in _iter_json_ld(soup) if isinstance(item.get('articleBody'), str)]
    if not bodies:
        return None
    body = max(bodies, key=len)
    return body if re.search(r'<\s*p[\s>]', body) else text_to_html(body)


def _body(soup: BeautifulSoup) -> Optional[str]:
    body = soup.body or soup
    return str(body)


def remove_overlays(soup: BeautifulSoup) -> bool:
    """
    Removes cookie/consent banners and modal dialogs from the page. They have to go before extraction:
    trafilatura drops attributes, so their text would otherwise reach the sanitizer looking like ordinary
    paragraphs. Returns whether anything was removed.
    """
    total_words = len(soup.get_text(' ').split()) or 1
    removed = False
    for element in soup.find_all(True):
        if element.decomposed or element.name in ('html', 'head', 'body'):
            continue
        marks = f"{attr(element, 'class')} {attr(element, 'id')}".lower()
        is_overlay = (
            element.name == 'dialog' or attr(element, 'role') in ('dialog', 'alertdialog')
            or attr(element, 'aria-modal') == 'true' or any(marker in marks for marker in OVERLAY_MARKERS)
        )
        # Safety net, as in clean_html: never remove most of the page because of an unlucky class name.
        if is_overlay and len(element.get_text(' ').split()) / total_words < 0.4:
            element.decompose()
            removed = True
    return removed


# --- Metadata ----------------------------------------------------------------------------------------

def clean_title(title: str, site_name: str = '', url: str = '') -> str:
    """Removes a trailing site name, e.g. 'E-reader - Wikipedia' -> 'E-reader'."""
    title = re.sub(r'\s+', ' ', title or '').strip()
    parts = TITLE_SEPARATORS.split(title)
    if len(parts) < 2:
        return title
    suffix = re.sub(r'[^a-z0-9]', '', parts[-1].lower())
    host = (urlparse(url).hostname or '').lower()
    host_words = [w for w in re.split(r'[.\-]', host) if w not in ('www', 'com', 'org', 'net', 'co', 'uk', '')]
    site = re.sub(r'[^a-z0-9]', '', site_name.lower())
    matches_site = bool(suffix) and (
        (site and (site in suffix or suffix in site)) or any(w in suffix for w in host_words if len(w) > 2)
    )
    if matches_site and len(parts[-1].split()) <= 5:
        last_separator = list(TITLE_SEPARATORS.finditer(title))[-1]
        return title[:last_separator.start()].strip()
    return title


def title_from_url(url: str) -> str:
    """A readable stand-in title, e.g. '.../2026/09/why-genre-matters/123' -> 'Why genre matters (example.com)'."""
    parsed = urlparse(url)
    host = (parsed.hostname or '').removeprefix('www.')
    segments = [s for s in parsed.path.split('/') if s and not s.isdigit() and not re.fullmatch(r'[\d\W_]+', s)]
    slug = re.sub(r'\.[a-z]+$', '', segments[-1]) if segments else ''
    words = [w for w in re.split(r'[-_+]+', slug) if w]
    if not words:
        return host or url
    return f"{' '.join(words).capitalize()} ({host})" if host else ' '.join(words).capitalize()


def _clean_author(author: str) -> str:
    author = re.sub(r'\s+', ' ', author or '').strip()
    # Metadata extractors sometimes grab a whole block of page text as the "author".
    return author if 0 < len(author) <= 80 and len(author.split()) <= 10 else ''


def _metadata(html: str, url: str) -> Dict[str, str]:
    try:
        meta = trafilatura.extract_metadata(html, default_url=url or None)
    except Exception:
        meta = None
    if meta is None:
        return {}
    return {
        'title': clean_title(meta.title or '', meta.sitename or '', url),
        'author': _clean_author(meta.author or ''),
        'date': meta.date or '',
        'site_name': meta.sitename or '',
    }


def extract_article(
    html: str, url: str = '', fetch: Optional[Callable[[str], str]] = None, min_words: int = MIN_WORDS,
) -> ExtractedArticle:
    """
    Parameters
    ----------
    html: str
        The page's HTML.
    url: str, optional
        The page's url. Used to choose site rules and resolve relative links.
    fetch: function taking a url and returning its body as a string, optional
        Lets site rules make extra requests (e.g. to a JSON API). Defaults to fetch_html.
    min_words: int, optional
        A stage's result is accepted once it has at least this many words.
    """
    fetch = fetch or (lambda u: fetch_html(u)[0])
    soup = BeautifulSoup(html, 'html.parser')
    meta = _metadata(html, url)
    if not meta.get('title'):
        title_tag = soup.find('title')
        meta['title'] = clean_title(title_tag.get_text() if title_tag else '', url=url)
    if remove_overlays(soup):
        html = str(soup)

    def run(name: str, stage: Callable[[], Optional[str]]) -> Optional[ExtractedArticle]:
        try:
            content = stage()
        except Exception:
            return None
        return ExtractedArticle(html=content, extractor=name, **meta) if content else None

    candidates: List[ExtractedArticle] = []
    rule = find_site_rule(url)
    if rule is not None:
        site_result = run('site rule', lambda: rule(soup, url, fetch))  # type: ignore
        if site_result is not None:
            if site_result.word_count >= min_words:
                return site_result
            candidates.append(site_result)

    generic = [r for r in (run('trafilatura', lambda: _trafilatura(html, url)),
                           run('readability', lambda: _readability(html, url))) if r is not None]
    if generic:
        chosen = generic[0]
        if len(generic) == 2 and generic[1].word_count >= READABILITY_PREFERENCE_RATIO * generic[0].word_count:
            chosen = generic[1] if generic[0].extractor == 'trafilatura' else generic[0]
        if chosen.word_count >= min_words:
            return chosen
        candidates += generic

    json_ld = run('json-ld', lambda: _json_ld_body(soup))
    if json_ld is not None:
        if json_ld.word_count >= min_words:
            return json_ld
        candidates.append(json_ld)

    if candidates:
        return max(candidates, key=lambda c: c.word_count)
    return ExtractedArticle(html=_body(soup) or '', extractor='body', **meta)
