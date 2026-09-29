import hashlib
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

    def test_ids_are_stable_and_unique(self):
        first = [m.id for m in self.collector().get_article_metadatas()]
        second = [m.id for m in self.collector().get_article_metadatas()]
        self.assertEqual(first, second)
        self.assertEqual(len(set(first)), len(first))
        self.assertEqual(first[0], hashlib.sha1(b'https://example.com/one').hexdigest()[:12])

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
        # Edited in place: the used item (both copies) is ticked, everything else keeps its text
        # and position, and the added URL goes at the end.
        self.assertEqual(lines, [
            '# Reading list',
            '- [x] https://example.com/one',
            '- [x] https://example.com/done',
            '- [ ] https://example.com/two',
            '- [x] https://example.com/one',
            'not a list item',
            '- [\t] https://example.com/odd',
            '- [ ] https://example.com/later',
        ])
        self.assertEqual(c._data['https://example.com/one']['status'], ListItemStatus.DONE)

    def read(self) -> str:
        with open(self.path) as f:
            return f.read()

    def test_callback_without_consuming_changes_nothing(self):
        # What the link scrapers do: load, add nothing new, write back. Every unread URL used
        # to come back twice, and the heading and notes were dropped.
        self.collector().used_articles_callback([])
        self.assertEqual(self.read(), LIST)

    def test_adding_keeps_the_rest_of_the_note(self):
        c = self.collector()
        c.add('https://example.com/new')
        c.add('https://example.com/one')  # already on the list
        c.used_articles_callback([])
        self.assertEqual(self.read(), LIST + '- [ ] https://example.com/new\n')

    def test_rewriting_twice_is_stable(self):
        c = self.collector()
        c.used_articles_callback(c.get_article_metadatas()[:1])
        once = self.read()
        c = self.collector()
        c.used_articles_callback([])
        self.assertEqual(self.read(), once)

    def test_added_and_used_in_one_run_is_ticked(self):
        c = self.collector()
        c.add('https://example.com/new')
        metas = c.get_article_metadatas()
        c.used_articles_callback([m for m in metas if m.url == 'https://example.com/new'])
        lines = self.read().splitlines()
        self.assertEqual(lines[-1], '- [x] https://example.com/new')
        self.assertIn('- [ ] https://example.com/two', lines)

    def test_blank_lines_indentation_and_missing_final_newline(self):
        with open(self.path, 'w') as f:
            f.write('Intro\n\n  - [ ] https://example.com/a\n- [ ] https://example.com/b')
        c = self.collector()
        c.used_articles_callback([m for m in c.get_article_metadatas() if m.url.endswith('/a')])
        self.assertEqual(self.read(), 'Intro\n\n  - [x] https://example.com/a\n- [ ] https://example.com/b\n')

    def test_errored_item_is_ticked_with_the_reason(self):
        c = self.collector()
        c._data['https://example.com/two'] = {'url': 'https://example.com/two', 'status': 'error boom'}
        c.used_articles_callback([])
        self.assertIn('- [x] https://example.com/two (error boom)', self.read().splitlines())
