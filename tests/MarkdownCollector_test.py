import os
import tempfile
import unittest

from custom_modules.MarkdownCollector import ListItemStatus, MarkdownCollector

LIST = """# Reading list
- [ ] https://example.com/one
- [x] https://example.com/done
- [ ] https://example.com/two
- [ ] https://example.com/one
not a list item
- [\t] https://example.com/odd
"""

class TestMarkdownCollector(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.dir.name, 'list.md')
        with open(self.path, 'w') as f:
            f.write(LIST)
        self.errors = []
        self.infos = []

    def tearDown(self):
        self.dir.cleanup()

    def collector(self) -> MarkdownCollector:
        return MarkdownCollector(self.path, error_log_callback=self.errors.append, info_log_callback=self.infos.append)

    def test_loads_to_do_items_once(self):
        c = self.collector()
        self.assertEqual(len(c), 2)
        self.assertTrue(c.contains('https://example.com/done'))
        self.assertFalse(c.contains('https://example.com/missing'))
        self.assertIn('List contains multiple of url: https://example.com/one', self.infos)
        # '- [\t]' matches the list-item pattern but is neither to-do nor done
        self.assertEqual(self.errors, ["Couldn't read status of url: https://example.com/odd"])

    def test_missing_file(self):
        c = MarkdownCollector(os.path.join(self.dir.name, 'nope.md'), error_log_callback=self.errors.append, info_log_callback=None)
        self.assertEqual(len(c), 0)
        self.assertEqual(c.get_article_metadatas(), [])
        self.assertTrue(self.errors[0].startswith('Could not load file.'))

    def test_get_article_metadatas(self):
        c = self.collector()
        metas = c.get_article_metadatas()
        self.assertEqual([m.url for m in metas], ['https://example.com/one', 'https://example.com/two'])
        self.assertEqual({m.source_title for m in metas}, {'List of Articles To Read'})
        self.assertTrue(all(m.fetch_content_from_url and m.id for m in metas))
        self.assertEqual(len(c), 0)

    def test_add(self):
        c = self.collector()
        c.add('https://example.com/new')
        c.add('https://example.com/new')
        self.assertEqual(len(c), 3)

    def test_used_articles_callback_rewrites_the_list(self):
        c = self.collector()
        metas = c.get_article_metadatas()
        c.add('https://example.com/later')
        c.used_articles_callback(metas[:1])
        with open(self.path) as f:
            lines = f.read().splitlines()
        self.assertEqual(lines, [
            '- [ ] https://example.com/later',
            '- [ ] https://example.com/two',
            '- [x] https://example.com/done',
            '- [x] https://example.com/odd (status not recognized)',
            '- [x] https://example.com/one',
        ])
        self.assertEqual(c._data['https://example.com/one']['status'], ListItemStatus.DONE)
