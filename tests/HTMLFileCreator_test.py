import os
import tempfile
import unittest
from pathlib import Path

from base_classes.ArticleMetadata import ArticleMetadata
from custom_modules.HTMLFileCreator import HTMLFileCreator
from default_modules.DefaultArticle import DefaultArticle

class TestHTMLFileCreator(unittest.TestCase):
    def test_write_file(self):
        metas = [ArticleMetadata(f'Café <{i}>', f'https://example.com/{i}', 's', '', 'Feed', f'{i}') for i in range(2)]
        articles = [DefaultArticle(metas[0], display_content='<p>“Quoted” naïve</p>', next_id='1'),
                    DefaultArticle(metas[1], display_content='<p>Two</p>')]
        with tempfile.TemporaryDirectory() as d:
            path = HTMLFileCreator(os.path.join(d, 'out'), articles, 'Title & co', info_log_callback=None).write_file()
            html = Path(path).read_text(encoding='utf-8')
            self.assertIn('<meta charset="utf-8"/>', html)
            self.assertIn('<title>Title &amp; co</title>', html)
            self.assertIn('<a href="#article-0">Café &lt;0&gt;</a>', html)
            self.assertIn('id="article-0"', html)
            self.assertIn('href="#article-1">Next article', html)
            self.assertIn('“Quoted” naïve', html)

            path = HTMLFileCreator(os.path.join(d, 'ascii'), articles, 'T', info_log_callback=None, ascii_only=True).write_file()
            self.assertIn('"Quoted" naive', Path(path).read_text(encoding='utf-8'))

    def test_total_read_time_adds_up_short_pieces(self):
        metas = [ArticleMetadata(f'T{i}', f'https://example.com/{i}', 's', '', 'Feed', f'{i}') for i in range(3)]
        words = '<p>' + 'word ' * 150 + '</p>'
        articles = [DefaultArticle(m, display_content=words) for m in metas]
        toc = HTMLFileCreator('unused', articles, 'T', info_log_callback=None)._get_table_of_contents()
        self.assertIn('Total Read Time: 2 min', toc)
        short = HTMLFileCreator('unused', articles[:1], 'T', info_log_callback=None)
        short.articles[0].word_count = 20
        self.assertIn('(&lt; 1 min)', short._get_table_of_contents())
        self.assertIn('Total Read Time: &lt; 1 min', short._get_table_of_contents())
