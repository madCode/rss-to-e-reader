"""
You can create an HTML file based on your RSS feed by doing the following:

1. Set up a Collector to pull what you want from you RSS reader
2. Set up a ListCreator to order the articles.
3. Set up an ArticleFetcher to fetch the articles.
4. Set up a FileCreator to format the file the way you like.
5. Hook up all the data and call write_file on the FileCreator

The code below follows those steps. To test out this sample,
fill in ttrss_api_url below and run `python3 ./examples/sample_ttrss.py` from your terminal.
Then look for sample.html in this folder and view it in your browser.
"""
from custom_modules.TtrssCollector import TtrssCollector
from default_modules.DefaultListCreator import DefaultListCreator
from default_modules.DefaultArticleFetcher import DefaultArticleFetcher
from custom_modules.HTMLFileCreator import HTMLFileCreator

ttrss_api_url = "" # Usually looks like this: 'http://<your_domain_hosting_ttrss.com>/tt-rss/api/'
collector = TtrssCollector(ttrss_api_url, max_num_articles=5) #1
list_creator = DefaultListCreator([collector]) #2
metadata = list_creator.get_article_metadatas()
article_fetcher = DefaultArticleFetcher(metadata) #3
articles = article_fetcher.get_articles()
file_creator = HTMLFileCreator("sample", articles, "SAMPLE FILE") #4
file_creator.write_file() #5
# optional: email the file to your kindle
# default_send_email_kindle("to_email", "filestub", "email_user", "smtp_url", "smtp_port", "email_password")
