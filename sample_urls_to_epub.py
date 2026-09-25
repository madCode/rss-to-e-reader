"""
Turns a list of article urls into an EPUB, optionally sending it on. Handy for testing how well an article extracts.

    python3 sample_urls_to_epub.py https://aeon.co/essays/... https://example.com/article -o reading -t "Weekend reading"

To email the result with Resend, set RESEND_API_KEY, RESEND_FROM and KINDLE_EMAIL and pass --send.
"""
import argparse
import os
from base_classes.ArticleMetadata import ArticleMetadata
from default_modules.DefaultArticleFetcher import DefaultArticleFetcher
from custom_modules.EpubFileCreator import EpubFileCreator
from custom_modules.HTMLFileCreator import HTMLFileCreator
from custom_modules.ResendSender import ResendSender

parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument('urls', nargs='+')
parser.add_argument('-o', '--output', default='articles', help='output path without extension')
parser.add_argument('-t', '--title', default='Articles')
parser.add_argument('--html', action='store_true', help='write a single HTML file instead of an EPUB')
parser.add_argument('--no-images', action='store_true')
parser.add_argument('--grayscale', action='store_true', help='convert images to grayscale (smaller files)')
parser.add_argument('--no-impersonation', action='store_true', help="don't retry blocked pages as a browser")
parser.add_argument('--send', action='store_true', help='email the file with Resend (see above)')
args = parser.parse_args()

metadata = [ArticleMetadata('', url, source_id='cli') for url in args.urls]
impersonate = None if args.no_impersonation else 'chrome'
articles = DefaultArticleFetcher(metadata, keep_images=not args.no_images, impersonate_browser=impersonate).get_articles()
if args.html:
    path = HTMLFileCreator(args.output, articles, args.title).write_file()
else:
    path = EpubFileCreator(args.output, articles, args.title, grayscale_images=args.grayscale, impersonate_browser=impersonate).write_file()
print(f'Wrote {path}')
if args.send:
    ResendSender(os.environ['RESEND_API_KEY'], os.environ['RESEND_FROM'], os.environ['KINDLE_EMAIL']).send(path, args.title)
