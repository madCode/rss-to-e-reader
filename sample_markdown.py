"""
You can create an HTML file based on a markdown list by doing the following:

1. Set up a Collector to pull what you want from you markdown file
2. Set up a ListCreator to order the articles.
3. Set up an ArticleFetcher to fetch the articles.
4. Set up a FileCreator to format the file the way you like.
5. Hook up all the data and call write_file on the FileCreator

The code below follows those steps. To test out this sample,
fill in markdown_list_filepath below and run `python3 sample_markdown.py` from your terminal.
Then look for sample2.epub in this folder and open it in an e-book reader (or Calibre). Be sure to also check sample_markdown_list.md
to see how the status of your articles changed.

REMEMBER to reset the url statuses in sample_markdown_list.py if testing multiple times in a row.
"""
from custom_modules.MarkdownCollector import MarkdownCollector
from default_modules.DefaultListCreator import DefaultListCreator
from default_modules.DefaultArticleFetcher import DefaultArticleFetcher
from custom_modules.EpubFileCreator import EpubFileCreator

markdown_list_filepath = "sample_markdown_list.md" # Replace with your own list
collector = MarkdownCollector(markdown_list_filepath) #1
list_creator = DefaultListCreator([collector]) #2
metadata = list_creator.get_article_metadatas()
article_fetcher = DefaultArticleFetcher(metadata) #3
articles = article_fetcher.get_articles()
file_creator = EpubFileCreator("sample2", articles, "SAMPLE FILE") #4 (or HTMLFileCreator for a single .html file)
path = file_creator.write_file() #5
# optional: send the file to your e-reader. Pick one:
# from default_modules.SmtpSender import SmtpSender
# SmtpSender.gmail("you@gmail.com", "your app password", "you@kindle.com").send(path)
# import os; from custom_modules.ResendSender import ResendSender
# ResendSender(os.environ["RESEND_API_KEY"], "kindle@yourdomain.com", "you@kindle.com").send(path)
# from custom_modules.FolderSender import FolderSender
# FolderSender("/path/to/Dropbox/Apps/Rakuten Kobo").send(path)
