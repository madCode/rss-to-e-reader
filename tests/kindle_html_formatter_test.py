import unittest

from default_modules.kindle_html_formatter import best_srcset_candidate, clean_html, text_to_html

BASE = 'https://example.com/articles/one'

class TestCleanHtml(unittest.TestCase):
    def test_plain_text_becomes_paragraphs(self):
        self.assertEqual(clean_html('first para\nstill first\n\nsecond <3'), '<p>first para still first</p><p>second &lt;3</p>')
        self.assertEqual(text_to_html(''), '')
        self.assertEqual(clean_html('   '), '')

    def test_removes_scripts_styles_and_page_furniture(self):
        html = '''<div><script>alert(1)</script><style>p{}</style><nav>Home</nav>
            <p>Real text that is long enough to matter in this article.</p>
            <div class="share-tools">Share on Facebook</div><div id="newsletter-signup">Sign up!</div>
            <aside>Sidebar</aside><form><input/></form><iframe src="x"></iframe>
            <p style="display:none">hidden</p><!-- a comment --></div>'''
        cleaned = clean_html(html, BASE)
        self.assertEqual(cleaned, '<div>\n<p>Real text that is long enough to matter in this article.</p>\n</div>')

    def test_junk_class_does_not_remove_most_of_the_article(self):
        html = '<div class="comment-body"><p>' + 'word ' * 100 + '</p></div>'
        self.assertIn('word', clean_html(html))

    def test_strips_attributes_and_unknown_tags(self):
        cleaned = clean_html('<p class="x" style="color:red" onclick="evil()"><span><font>Hi</font></span> <b data-x="1">there</b></p>')
        self.assertEqual(cleaned, '<p>Hi <b>there</b></p>')

    def test_resolves_links(self):
        cleaned = clean_html('<p><a href="/other">rel</a> <a href="javascript:x()">js</a> <a href="https://a.com/b">abs</a> <a>none</a></p>', BASE)
        self.assertEqual(cleaned, '<p><a href="https://example.com/other">rel</a> js <a href="https://a.com/b">abs</a> none</p>')

    def test_drops_malformed_links(self):
        cleaned = clean_html('<p><a href=\'\\"http:/x\\"\'>bad</a></p>', BASE)
        self.assertEqual(cleaned, '<p>bad</p>')

    def test_encodes_invalid_url_characters(self):
        html = '<p><a href="https://a.com/x y#one#two">a</a> <a href="/p?q={1}|2">b</a></p><img src="/i m g.jpg"/>'
        self.assertEqual(clean_html(html, BASE),
                         '<p><a href="https://a.com/x%20y#one%23two">a</a> <a href="https://example.com/p?q=%7B1%7D%7C2">b</a></p>'
                         '<img alt="" src="https://example.com/i%20m%20g.jpg"/>')
        # already-encoded urls are left alone
        self.assertEqual(clean_html('<a href="https://a.com/a%20b">x</a>'), '<a href="https://a.com/a%20b">x</a>')

    def test_keep_links_false(self):
        self.assertEqual(clean_html('<p><a href="/x">text</a></p>', BASE, keep_links=False), '<p>text</p>')

    def test_prefixes_ids_and_fragment_links(self):
        cleaned = clean_html('<p><a href="#fn1">1</a> <a href="#missing">2</a></p><p id="fn1">Note</p>', id_prefix='a1-')
        self.assertEqual(cleaned, '<p><a href="#a1-fn1">1</a> 2</p><p id="a1-fn1">Note</p>')

    def test_ids_are_valid_and_unique(self):
        cleaned = clean_html('<p id="1 x">a</p><p id="1 x">b</p>')
        self.assertEqual(cleaned, '<p id="id-1-x">a</p><p>b</p>')

    def test_lazy_images(self):
        html = ('<img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=" data-src="/lazy.jpg" alt=" A ">'
                '<img src="/plain.jpg" width="600">'
                '<img src="/pixel.gif" width="1" height="1">'
                '<img data-srcset="/s.jpg 300w, /m.jpg 1024w, /l.jpg 2000w">'
                '<img alt="no source">')
        cleaned = clean_html(html, BASE)
        self.assertEqual(cleaned, '<img alt="A" src="https://example.com/lazy.jpg"/><img alt="" src="https://example.com/plain.jpg"/>'
                                  '<img alt="" src="https://example.com/m.jpg"/>')

    def test_picture_elements(self):
        html = '<figure><picture><source srcset="/a.webp" type="image/webp"><source srcset="/a.jpg 1x, /a@2x.jpg 2x" type="image/jpeg"><img alt="pic"></picture><figcaption>Cap</figcaption></figure>'
        self.assertEqual(clean_html(html, BASE), '<figure><img alt="pic" src="https://example.com/a@2x.jpg"/><figcaption>Cap</figcaption></figure>')

    def test_keep_images_false(self):
        self.assertEqual(clean_html('<figure><img src="/a.jpg"></figure><p>text</p>', BASE, keep_images=False), '<p>text</p>')

    def test_removes_duplicate_title_and_normalizes_headings(self):
        html = '<h1>The Title!</h1><p>Intro</p><h1>Section</h1><h3>Sub</h3>'
        self.assertEqual(clean_html(html, title='The title'), '<p>Intro</p><h2>Section</h2><h4>Sub</h4>')
        # a heading that matches the title further down is kept
        self.assertEqual(clean_html('<p>Intro</p><h2>The Title</h2>', title='The title'), '<p>Intro</p><h2>The Title</h2>')

    def test_removes_boilerplate_and_empty_elements(self):
        html = '<p>Listen to this article</p><p>5 min read</p><p></p><div><span> </span></div><p>Keep me</p><p>Advertisement</p>'
        self.assertEqual(clean_html(html), '<p>Keep me</p>')

    def test_layout_tables_are_flattened_data_tables_kept(self):
        data = '<table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>'
        self.assertIn('<table>', clean_html(data))
        self.assertNotIn('<table>', clean_html(data, flatten_tables=True))
        nested = '<table><tr><td><table><tr><td>x</td><td>y</td></tr></table></td></tr></table>'
        self.assertNotIn('<table', clean_html(nested))
        single_column = '<table><tr><td><p>Newsletter paragraph</p></td></tr><tr><td><p>Another</p></td></tr></table>'
        self.assertEqual(clean_html(single_column), '<div><div><div><p>Newsletter paragraph</p></div></div><div><div><p>Another</p></div></div></div>')

    def test_best_srcset_candidate(self):
        self.assertEqual(best_srcset_candidate('a.jpg 300w, b.jpg 1200w, c.jpg 2400w'), 'b.jpg')
        self.assertEqual(best_srcset_candidate('a.jpg 300w, b.jpg 600w'), 'b.jpg')
        self.assertEqual(best_srcset_candidate('a.jpg 1x, b.jpg 2x, c.jpg 3x'), 'b.jpg')
        self.assertEqual(best_srcset_candidate('a.jpg'), 'a.jpg')
        self.assertIsNone(best_srcset_candidate(''))
