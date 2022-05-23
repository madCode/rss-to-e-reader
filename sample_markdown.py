"""
You can create an HTML file based on a markdown list by doing the following:

1. Set up a Collector to pull what you want from you markdown file
2. Set up a ListCreator to order the articles.
3. Set up an ArticleFetcher to fetch the articles.
4. Set up a FileCreator to format the file the way you like.
5. Hook up all the data and call write_file on the FileCreator

The code below follows those steps. To test out this sample,
fill in markdown_list_filepath below and run `python3 ./examples/sample_markdown.py` from your terminal.
Then look for sample2.html in this folder and view it in your browser. Be sure to also check sample_markdown_list.md
to see how the status of your articles changed.

REMEMBER to reset the url statuses in sample_markdown_list.py if testing multiple times in a row.
"""
from custom_modules.MarkdownCollector import MarkdownCollector
from default_modules.DefaultListCreator import DefaultListCreator
from default_modules.DefaultArticleFetcher import DefaultArticleFetcher
from custom_modules.HTMLFileCreator import HTMLFileCreator

markdown_list_filepath = "sample_markdown_list.md" # Replace with your own list
collector = MarkdownCollector(markdown_list_filepath) #1
list_creator = DefaultListCreator([collector]) #2
metadata = list_creator.get_article_metadatas()
article_fetcher = DefaultArticleFetcher(metadata) #3
articles = article_fetcher.get_articles()
file_creator = HTMLFileCreator("sample2", articles, "SAMPLE FILE") #4
file_creator.write_file() #5
# optional: email the file to your kindle
# default_send_email_kindle("to_email", "filestub", "email_user", "smtp_url", "smtp_port", "email_password")
