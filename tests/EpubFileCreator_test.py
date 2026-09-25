from io import BytesIO
import os
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from PIL import Image

from base_classes.ArticleMetadata import ArticleMetadata
from custom_modules.EpubFileCreator import EpubFileCreator
from default_modules.DefaultArticle import DefaultArticle
import default_modules.ebook_images as ebook_images
from default_modules.ebook_images import process_image

def image_bytes(size=(800, 600), mode='RGB', fmt='PNG') -> bytes:
    output = BytesIO()
    Image.new(mode, size, 'red' if mode == 'RGB' else None).save(output, format=fmt)
    return output.getvalue()

def article(i: int, content: str) -> DefaultArticle:
    meta = ArticleMetadata(f'Article {i} & more', f'https://example.com/{i}', 'src', '', 'Example Feed', f'id{i}')
    return DefaultArticle(meta, display_content=content, next_id='top', author='Jane')

class TestProcessImage(unittest.TestCase):
    def test_downscales_and_converts(self):
        processed = process_image(image_bytes((3000, 1500)), max_dimension=1200)
        assert processed is not None
        self.assertEqual((processed.width, processed.height), (1200, 600))
        self.assertEqual(Image.open(BytesIO(processed.data)).format, 'JPEG')

    def test_transparent_and_grayscale(self):
        processed = process_image(image_bytes(mode='RGBA'), grayscale=True)
        assert processed is not None
        self.assertEqual(Image.open(BytesIO(processed.data)).mode, 'L')

    def test_rejects_garbage_and_icons(self):
        self.assertIsNone(process_image(b'not an image'))
        self.assertIsNone(process_image(image_bytes((16, 16))))

class TestEpubFileCreator(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.stub = os.path.join(self.dir.name, 'book')

    def tearDown(self):
        self.dir.cleanup()

    def write(self, articles, **kwargs) -> zipfile.ZipFile:
        creator = EpubFileCreator(self.stub, articles, 'Daily <Reading>', info_log_callback=None, **kwargs)
        path = creator.write_file()
        self.assertEqual(path, self.stub + '.epub')
        return zipfile.ZipFile(path)

    def test_structure(self):
        book = self.write([article(1, '<p>First.</p>'), article(2, '<p>Second.</p>')])
        names = book.namelist()
        # EPUB requires an uncompressed mimetype file first
        self.assertEqual(names[0], 'mimetype')
        self.assertEqual(book.getinfo('mimetype').compress_type, zipfile.ZIP_STORED)
        self.assertEqual(book.read('mimetype'), b'application/epub+zip')
        for name in ('EPUB/article001.xhtml', 'EPUB/article002.xhtml', 'EPUB/contents.xhtml', 'EPUB/nav.xhtml',
                     'EPUB/toc.ncx', 'EPUB/cover.jpg', 'EPUB/style/main.css'):
            self.assertIn(name, names)
        chapter = book.read('EPUB/article001.xhtml').decode()
        self.assertIn('Article 1 &amp; more', chapter)
        self.assertIn('Example Feed · Jane', chapter)
        self.assertIn('Original: <a href="https://example.com/1">', chapter)
        self.assertNotIn('Next article', chapter)
        contents = book.read('EPUB/contents.xhtml').decode()
        self.assertIn('Daily &lt;Reading&gt;', contents)
        self.assertIn('href="article002.xhtml"', contents)
        opf = book.read('EPUB/content.opf').decode()
        self.assertIn('<dc:title>Daily &lt;Reading&gt;</dc:title>', opf)
        self.assertNotIn('linear="no"', opf)

    def test_without_cover(self):
        names = self.write([article(1, '<p>x</p>')], include_cover=False).namelist()
        self.assertNotIn('EPUB/cover.jpg', names)

    def test_embeds_images_and_drops_failures(self):
        content = ('<figure><img src="https://example.com/good.png" alt="good"/><figcaption>Cap</figcaption></figure>'
                   '<figure><img src="https://example.com/bad.png" alt="bad"/></figure>'
                   '<p><img src="https://example.com/good.png"/></p>')
        good = image_bytes()
        with patch.object(ebook_images, 'download_image', side_effect=lambda url, *a: good if 'good' in url else None) as download:
            book = self.write([article(1, content)])
        # each url is downloaded once, with the article as referer
        self.assertEqual(sorted(c.args[0] for c in download.call_args_list), ['https://example.com/bad.png', 'https://example.com/good.png'])
        self.assertEqual(download.call_args_list[0].args[1], 'https://example.com/1')
        images = [n for n in book.namelist() if n.startswith('EPUB/images/')]
        self.assertEqual(images, ['EPUB/images/img0001.jpg'])
        chapter = book.read('EPUB/article001.xhtml').decode()
        self.assertEqual(chapter.count('src="images/img0001.jpg"'), 2)
        self.assertNotIn('bad.png', chapter)
        self.assertIn('<figcaption>Cap</figcaption>', chapter)

    def test_image_limits(self):
        content = ''.join(f'<img src="https://example.com/{i}.png"/>' for i in range(5))
        with patch.object(ebook_images, 'download_image', return_value=image_bytes()):
            book = self.write([article(1, content)], max_images_per_article=2)
        self.assertEqual(len([n for n in book.namelist() if n.startswith('EPUB/images/')]), 2)
        with patch.object(ebook_images, 'download_image', return_value=image_bytes()):
            book = self.write([article(1, content)], max_total_image_bytes=1)
        self.assertEqual(len([n for n in book.namelist() if n.startswith('EPUB/images/')]), 0)

    def test_embed_images_false_removes_images(self):
        with patch.object(ebook_images, 'download_image') as download:
            book = self.write([article(1, '<p>a</p><img src="https://example.com/x.png"/>')], embed_images=False)
        download.assert_not_called()
        self.assertNotIn('<img', book.read('EPUB/article001.xhtml').decode())
