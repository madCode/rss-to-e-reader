import unittest

from default_modules.kindle_html_formatter import best_srcset_candidate, clean_html, text_to_html

BASE = 'https://example.com/articles/one'

class TestCleanHtml(unittest.TestCase):
    def test_related_link_lists_go_but_the_articles_own_sections_stay(self):
        body = '<p>' + 'Words of the article itself. ' * 30 + '</p>'
        links = '<ul><li><a href="https://example.com/a">Story A</a></li><li><a href="https://example.com/b">Story B</a></li></ul>'
        self.assertEqual(clean_html(body + '<h2>Read next</h2>' + links), body)
        self.assertEqual(clean_html(body + '<h2>More on this story</h2>' + links), body)
        own = '<h2>Related research</h2><p>Earlier studies found the same effect in mice.</p>'
        self.assertEqual(clean_html(body + own), body + own)
        # The whole box goes when the heading and its lists are all it holds.
        self.assertEqual(clean_html(body + '<div class="more"><h3>Related stories</h3>' + links + links + '</div>'), body)
        gallery = '<h2>More from our photographers</h2><ul><li><a href="https://example.com/p"><img alt="" src="https://example.com/p.jpg"/></a></li></ul>'
        self.assertEqual(clean_html(body + gallery), body + gallery)

    def test_a_furniture_heading_left_without_its_links_goes(self):
        # trafilatura drops the box of links but can keep its heading over the next paragraph.
        body = '<p>' + 'Words of the article itself. ' * 30 + '</p>'
        self.assertEqual(clean_html(body + '<h2>Recommended Stories</h2>' + body), body + body)

    def test_an_authors_own_lists_and_headings_stay(self):
        body = '<p>' + 'Words of the article itself. ' * 30 + '</p>'
        refs = '<h2>Further reading</h2><ul><li><a href="https://example.com/1">A paper</a></li><li><a href="https://example.com/2">A book</a></li></ul>'
        self.assertEqual(clean_html(body + refs), body + refs)
        intro = '<h2>Read more</h2>Two earlier pieces on this:<ul><li><a href="https://example.com/1">One</a></li></ul>'
        self.assertEqual(clean_html(body + intro), body + intro)
        items = ''.join(f'<li><a href="https://example.com/{i}">A long and interesting book title number {i}</a></li>' for i in range(12))
        long_list = f'<h2>Recommended reading</h2><ul>{items}</ul>'
        self.assertEqual(clean_html('<p>Intro.</p>' + long_list), '<p>Intro.</p>' + long_list)

    def test_an_articles_own_section_titles_stay(self):
        body = '<p>' + 'Words of the article itself. ' * 30 + '</p>'
        for section in ('<h2>More on the method</h2><p>We sampled weekly.</p>',
                        '<h2>Read more</h2><p>Our findings are below.</p>',
                        '<h2>Read next</h2><table><tr><th>Part</th><th>Date</th></tr><tr><td>Two</td><td>May</td></tr></table>',
                        '<h2>Recommended</h2><ul><li>Plain advice</li><li>Without links</li></ul>'):
            self.assertEqual(clean_html(body + section), body + section)

    def test_screen_reader_text_that_labels_an_icon_link_stays(self):
        self.assertEqual(
            clean_html('<p>Text <a href="https://example.com/f.pdf"><span class="sr-only">Download PDF</span></a> end.</p>'),
            '<p>Text <a href="https://example.com/f.pdf">Download PDF</a> end.</p>')

    def test_a_long_reading_list_under_a_related_heading_stays(self):
        items = ''.join(f'<li><a href="https://example.com/{i}">A long and interesting book title number {i}</a></li>' for i in range(12))
        self.assertEqual(clean_html(f'<p>A short introduction.</p><h2>Further reading</h2><ul>{items}</ul>').count('<li>'), 12)

    def test_screen_reader_labels_go_but_not_long_hidden_text_or_images(self):
        story = 'The whole story sits in this paragraph for readers of every kind. ' * 5
        self.assertEqual(
            clean_html(f'<p>Text.<span class="sr-only">list 1 of 4</span></p><div class="visually-hidden"><p>{story}</p></div>'),
            f'<p>Text.</p><div><p>{story}</p></div>')

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

    def test_keeps_paragraphs_in_paywall_containers(self):
        # The New Yorker wraps each run of article paragraphs in a div with class "paywall"
        sections = ''.join(f'<div class="body__inner-container paywall"><p>Section {i} {"text " * 30}</p></div>' for i in range(4))
        cleaned = clean_html(f'<div>{sections}</div>')
        for i in range(4):
            self.assertIn(f'Section {i}', cleaned)

    def test_keeps_article_body_marked_aria_hidden(self):
        # The NYT's paywall script marks the whole article body aria-hidden; small aria-hidden bits still go
        html = f'<section aria-hidden="true" inert=""><p>{"word " * 100}</p><span aria-hidden="true">icon</span></section>'
        cleaned = clean_html(html)
        self.assertIn('word', cleaned)
        self.assertNotIn('icon', cleaned)

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
