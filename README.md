# Article-to-e-Reader
Article-to-e-Reader is a modular open source python library that allows you to send articles to your eReader with the push of a button.

## Supported Inputs
- TinyTinyRSS: the TtrssCollector allows pulling articles directly from your TinyTinyRSS reader.
- list of urls: the MarkdownListCollector allows pulling articles from a markdown list of your choosing

## Supported Outputs
- epub (recommended): the EpubFileCreator creates an e-book with a cover, a contents page, one chapter per article and the articles' images embedded. EPUB is the format Amazon recommends for Send to Kindle, and Kobo, KOReader, Apple Books and Calibre all read it natively.
- html: the HTMLFileCreator creates a single HTML file in a location of your choosing.
- email_api: the email_api.py file contains functions allowing you to email any file to your eReader.

## How articles are extracted
DefaultArticleFetcher downloads each article (several at a time) and runs an extraction pipeline (`default_modules/article_parser.py`):
1. a site-specific rule, if one exists for the site (`SITE_RULES`);
2. [trafilatura](https://trafilatura.readthedocs.io) and [readability](https://github.com/buriy/python-readability) (the algorithm behind Firefox's Reader View). Trafilatura's output is cleaner, so it's preferred unless readability finds a lot more text;
3. the schema.org `articleBody` many sites embed for search engines.

The result is then cleaned up for e-readers (`default_modules/kindle_html_formatter.py`): only simple, semantic tags are kept, lazy-loaded images and relative links are fixed, share buttons/newsletter sign-ups/related-article lists are removed, and layout tables (common in email newsletters) are flattened. If a page can't be fetched (paywalls, bot blocking), the content from your RSS feed is used instead, with a note saying so.

To see how well a page extracts, run `python3 sample_urls_to_epub.py <url> [<url> ...] -o test` and open `test.epub`.

## Basic Usage
1. Clone or download this repo into a folder in your system. Nagivate to that folder in your terminal.
2. Install python3 if it's not already on your system.
3. Install the dependencies with `pip install -r requirements.txt`. This library relies on:
    - [trafilatura](https://trafilatura.readthedocs.io) and [readability-lxml](https://github.com/buriy/python-readability) to find the article in a web page, and [BeautifulSoup4](https://beautiful-soup-4.readthedocs.io/en/latest/) to clean it up.
    - [EbookLib](https://github.com/aerkalov/ebooklib) and [Pillow](https://python-pillow.org) to build EPUB files and shrink images for e-readers.
    - mypy for static type checking (not necessary unless you're building custom modules)
4. To see basic usage, take a look at the examples folder. The sample_ttrss.py and the sample_markdown.py files show two different approaches. In either file, in the marked variables and run from your terminal as outlined in the comments at the top of the selected file. 

## Custom Modules
While this library currently contains enough default modules for basic usage, you may prefer to create modify some or all of the system. RSS-to-e-Reader has been designed to make that as straightforward as possible. Here's how:

### Architecture
This library is made up for 4 types of Modules, the basics of each can be seen in the `base_classes` package:
1. Collector: a module that pulls information in from the user's preferred source of articles and formats them in ArticleMetadata objects.
2. ListCreator: a module that, given a list of ArticleMetadata objects, uses user-defined selection criteria to filter and sort the ArticleMetadata objects into the exact list that should go in the final result.
3. ArticleFetcher: a module that, given a list of ArticleMetadata objects, pulls in all necessary information for the final result. (In DefaultArticleFetcher, for example, this involves visiting the article url to fetch the article's text). It outputs a list of DefaultArticles.
4. FileCreator: a module that, given a list of Article objects, creates a file as specified by the user.

Splitting things up into modules allows for easy developer customization. If you don't like the sorting and filtering options in DefaultListCreator, you can create your own (check out FetchThenOrderList, for example, which is a combination ListCreator and ArticleFetcher that allows the user to specify a max reading time for the final output). Or if you want a markdown or epub file instead of an HTML file, you can create your own FileCreator while using the stock modules for everything else. As long as you are properly inheriting from the proper base_class, everything should work seamlessly.

### Putting the modules together into a script
The examples folder contains samples of how to hook the modules together. They flow roughly in the order outlined above: 
1. create the Collectors first, pass as many Collectors as needed into the ListCreator.
2. Use the ListCreator's `get_article_metadatas` function to generate a list of ArticleMetadata.
3. Pass that into your ArticleFetcher and call `get_articles` to generate your list of Articles.
4. Pass the list of Articles into your FileCreator and call `write_file` to generate the file. It returns the file's path.
5. If you wish to email the file, pass the filestub into the `default_send_file_in_email` function provided in `email_api.py`.

### Help grow the library!
If you create a Module that you feel others will benefit from, open a PR. The architecture is designed (with unit tests) to make collaboration and group improvement as easy as possible. This library would benefit hugely from FileCreators that support different formats or ArticleFetchers that are smarter at getting the article contents. The world is our oyester.

## Questions?
If you have any questions or need help making your own scripts, feel free to open a Github issue with a title beginning with `[Question]`.
