import os
import tempfile
import unittest

from base_classes.ArticleMetadata import ArticleMetadata
from custom_modules.HTMLFileCreator import HTMLFileCreator
from default_modules.DefaultArticle import DefaultArticle

class TestHTMLFileCreator(unittest.TestCase):
    def test_write_file(self):
        metas = [ArticleMetadata(f'Café <{i}>', f'https://example.com/{i}', 's', '', 'Feed', f'{i}') for i in range(2)]
        articles = [DefaultArticle(metas[0], display_content='<p>“Quoted” naïve</p>', next_id='1'),
                    DefaultArticle(metas[1], display_content='<p>Two</p>', next_id='top')]
        with tempfile.TemporaryDirectory() as d:
            path = HTMLFileCreator(os.path.join(d, 'out'), articles, 'Title & co', info_log_callback=None).write_file()
            html = open(path, encoding='utf-8').read()
            self.assertIn('<meta charset="utf-8"/>', html)
            self.assertIn('<title>Title &amp; co</title>', html)
            self.assertIn('<a href="#article-0">Café &lt;0&gt;</a>', html)
            self.assertIn('id="article-0"', html)
            self.assertIn('href="#article-1">Next article', html)
            self.assertIn('“Quoted” naïve', html)

            path = HTMLFileCreator(os.path.join(d, 'ascii'), articles, 'T', info_log_callback=None, ascii_only=True).write_file()
            self.assertIn('"Quoted" naive', open(path, encoding='utf-8').read())
