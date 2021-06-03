#!/usr/local/bin/python3
import config
from datetime import datetime
import email_api
import file_creation_api as create_api
from store import *
import sys, getopt
import ttrss_api
from markdown_list_manager import get_articles_from_list
from article import Article, combine_articles_from_multiple_sources

hour = datetime.datetime.now().hour
allowed_flags = ["all-unread", "feed-id=", "title=", "do-not-track-last-article", "to-email=", "limit=", "ignore-skip-list", "test_url=", "time_limit_minutes="]
edition = 'Evening Edition' if hour >= 16 else 'Afternoon Edition' if hour >= 13 else 'Morning Edition'

filestub = f"{datetime.date.today()}: Today's Headlines {edition}"
fetch_feed_id = config.fetch_feed_id
ignore_since = False
skip_storing_last_article = False
to_email = config.to_emails
max_num_articles = None
ignore_skip_list = False
test_article_url = None
time_limit_minutes = None
from_ttrss = config.ttrss_api_url and len(config.ttrss_api_url) > 0
from_markdown_list = config.list_file_path and len(config.list_file_path) > 0

def parse_command_line_args(argv):
    global filestub
    global fetch_feed_id
    global ignore_since
    global skip_storing_last_article
    global to_email, max_num_articles, ignore_skip_list, test_article_url, time_limit_minutes
    try:
        opts, args = getopt.getopt(argv,"",allowed_flags)
    except getopt.GetoptError as e:
        print(e)
        print(f'Error parsing args. Allowed long flags: {", ".join(allowed_flags)}')
        sys.exit(2)
    for opt, arg in opts:
        if opt == "--all-unread":
            ignore_since = True
        elif opt in ("--do-not-track-last-article"):
            skip_storing_last_article = True
        elif opt in ("--feed-id"):
            fetch_feed_id = arg
        elif opt in ("--title"):
            filestub = arg
        elif opt in ("--to-email"):
            to_email = arg
        elif opt in ("--limit"):
            max_num_articles = int(arg)
        elif opt in ("--ignore-skip-list"):
            ignore_skip_list = True
        elif opt in ("--test_url"):
            test_article_url = arg
        elif opt in ("--time_limit_minutes"):
            time_limit_minutes = int(arg)

def main():
    try:
        store = Store()
        store.store_articles(get_articles(store.last_article_id))
        if len(store.articles) == 0:
            print("No articles found!")
            sys.exit(2)
        create_api.create_file(store.articles, filestub)
        email_api.send_email(store.article_ids, to_email, filestub)
        store.backup(skip_storing_last_article)
    except Exception as e:
        print(e)
        return

def get_articles(last_article_id):
    global time_limit_minutes
    global max_num_articles
    if not test_article_url:
        rss_list, to_read_list = [], []
        if from_ttrss:
            rss_list = ttrss_api.get_articles(last_article_id, fetch_feed_id, ignore_since, max_num_articles, time_limit_minutes, ignore_skip_list)
        if from_markdown_list:
            data = get_articles_from_list(time_limit_minutes, max_num_articles)
            to_read_list = data['articles']
            list_manager = data['list_manager']
        articles = combine_articles_from_multiple_sources(rss_list, to_read_list, list_manager, time_limit_minutes, max_num_articles)
        return articles
    else:
        return get_test_article()

def get_test_article():
    article = Article(0, "Test Article", test_article_url, "test article", "test", 162)
    return [article]


if __name__ == "__main__":
   print("Starting job for: " + str(datetime.datetime.now()))
   parse_command_line_args(sys.argv[1:])
   main()