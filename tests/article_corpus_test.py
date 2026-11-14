"""
Regression corpus: saved article pages run through the whole extraction pipeline, compared with the text
we expect a reader to see.

Each case in fixtures/corpus/cases.json names a page (<name>.html) and its expected result (<name>.expected.md).
The page goes through article_parser.extract_article() and kindle_html_formatter.clean_html() the way
DefaultArticleFetcher runs them; feed-content cases (`"extract": false`) skip extraction, as articles that
aren't fetched from their url do. The cleaned HTML is rendered as Markdown-like text (headings as #, list items
as -, quotes as >, images as ![alt](src), table rows as | cells |) so a failure shows a readable diff of what
was lost or let through, not a wall of HTML.

The pages are hand-written in the markup of each kind of site (WordPress, Substack, Ghost, MediaWiki, ...) with
original text, so they can live in the repo and never need the network. The expected files record what the
pipeline produces today, not an ideal: each case's `known_issues` lists where that falls short, so a fix shows
up as an intended diff to an expected file and a regression as an unexpected one.

When a dependency upgrade or a deliberate change alters the output, regenerate the expected files with

    UPDATE_CORPUS=1 python -m unittest discover -s tests -p "article_corpus_test.py"

and read the diff before committing it: the expected files are the record of what each page should look like.
"""
import json
import os
from pathlib import Path
from typing import List
import unittest

from bs4 import BeautifulSoup, NavigableString, Tag  # type: ignore

from default_modules.article_parser import extract_article
from default_modules.kindle_html_formatter import clean_html

CORPUS = Path(__file__).parent / 'fixtures' / 'corpus'
CASES = json.loads((CORPUS / 'cases.json').read_text(encoding='utf-8'))
INLINE_TAGS = {
    'a', 'em', 'i', 'strong', 'b', 'u', 's', 'del', 'ins', 'sub', 'sup', 'small', 'mark', 'code', 'kbd', 'samp',
    'var', 'q', 'cite', 'abbr', 'span', 'br', 'img',
}


def _inline(node: Tag) -> str:
    """Text of an inline element; images inside it (e.g. a linked image) are kept as ![alt](src)."""
    if node.name == 'img':
        return f" ![{node.get('alt', '')}]({node.get('src', '')}) "
    if node.name == 'br':
        return ' '
    return ''.join(str(c) if isinstance(c, NavigableString) else _inline(c) for c in node.children
                   if isinstance(c, (NavigableString, Tag)))


def render(node: Tag) -> List[str]:
    """The lines of text a reader would see in cleaned HTML, one per block."""
    lines: List[str] = []
    inline: List[str] = []

    def flush():
        text = ' '.join(''.join(inline).split())
        if text:
            lines.append(text)
        inline.clear()

    for child in node.children:
        if isinstance(child, NavigableString):
            inline.append(str(child))
            continue
        if not isinstance(child, Tag):
            continue
        if child.name in INLINE_TAGS:
            inline.append(_inline(child))
            continue
        flush()
        if child.name in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            lines.append('#' * int(child.name[1]) + ' ' + ' '.join(child.get_text(' ').split()))
        elif child.name in ('ul', 'ol'):
            for number, item in enumerate(child.find_all('li', recursive=False), start=int(str(child.get('start', '1')))):
                marker = f'{number}. ' if child.name == 'ol' else '- '
                item_lines = render(item) or ['']
                lines.append(marker + item_lines[0])
                lines += ['  ' + line for line in item_lines[1:]]
        elif child.name == 'blockquote':
            lines += ['> ' + line for line in render(child)]
        elif child.name == 'figcaption':
            lines += ['Caption: ' + line for line in render(child)]
        elif child.name == 'pre':
            lines += ['```'] + child.get_text().strip('\n').splitlines() + ['```']
        elif child.name == 'hr':
            lines.append('---')
        elif child.name == 'table':
            for caption in child.find_all('caption'):
                lines.append('Table: ' + ' '.join(caption.get_text(' ').split()))
            for row in child.find_all('tr'):
                cells = [' '.join(cell.get_text(' ').split()) for cell in row.find_all(['th', 'td'])]
                lines.append('| ' + ' | '.join(cells) + ' |')
        else:
            lines += render(child)
    flush()
    return lines


def run_case(case: dict) -> str:
    """The expected-file text for a case: the metadata found, then the article as a reader sees it."""
    page = (CORPUS / f"{case['name']}.html").read_text(encoding='utf-8')
    header = []
    if case.get('extract', True):
        article = extract_article(page, case['url'], fetch=_no_network)
        html, title = article.html, article.title
        header = [f'title: {article.title}', f'author: {article.author}', f'date: {article.date}',
                  f'extractor: {article.extractor}']
    else:
        html, title = page, case.get('title', '')
    cleaned = clean_html(html, base_url=case['url'], flatten_tables=case.get('flatten_tables', False), title=title)
    body = render(BeautifulSoup(cleaned, 'html.parser'))
    return '\n'.join(header + ['---'] + body) + '\n'


def _no_network(url: str) -> str:
    raise AssertionError(f'corpus pages must not need the network (tried {url})')


class TestArticleCorpus(unittest.TestCase):
    maxDiff = None

    def test_corpus(self):
        update = os.environ.get('UPDATE_CORPUS') == '1'
        for case in CASES:
            with self.subTest(case['name']):
                actual = run_case(case)
                expected_path = CORPUS / f"{case['name']}.expected.md"
                if update:
                    expected_path.write_text(actual, encoding='utf-8')
                self.assertEqual(expected_path.read_text(encoding='utf-8'), actual)

    def test_every_page_has_a_case(self):
        named = {case['name'] for case in CASES}
        self.assertEqual({p.stem for p in CORPUS.glob('*.html')}, named)
        self.assertEqual({p.name.removesuffix('.expected.md') for p in CORPUS.glob('*.expected.md')}, named)


class TestRender(unittest.TestCase):
    def test_render(self):
        html = ('<h2>Head</h2><p>One <em>two</em><br>three <a href="x"><img alt="a" src="s"></a></p>'
                '<ol start="3"><li>x<ul><li>y</li></ul></li></ol><blockquote><p>q</p></blockquote>'
                '<figure><img alt="" src="i"><figcaption>cap</figcaption></figure><pre>a\n  b</pre><hr>'
                '<table><caption>T</caption><tr><th>h</th><td>d</td></tr></table>')
        self.assertEqual(render(BeautifulSoup(html, 'html.parser')), [
            '## Head', 'One two three ![a](s)', '3. x', '  - y', '> q', '![](i)', 'Caption: cap',
            '```', 'a', '  b', '```', '---', 'Table: T', '| h | d |',
        ])


if __name__ == '__main__':
    unittest.main()
