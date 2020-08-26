#!/usr/local/bin/python3
import config
import email_api
import file_creation_api as create_api
from store import *
import sys, getopt
import ttrss_api

allowed_flags = ["all-unread", "feed-id=", "title=", "do-not-track-last-article", "to-email=", "max-num-articles=", "ignore-skip-list"]
edition = 'Evening Edition' if datetime.datetime.now().hour == 17 else ('Morning Edition' if datetime.datetime.now().hour == 10 else f'{datetime.datetime.now().strftime("%H:%M:%S.%f")} TEST')

filestub = f'{datetime.date.today()}: Today\'s Headlines {edition}'
fetch_feed_id = config.fetch_feed_id
ignore_since = False
skip_storing_last_article = False
to_email = config.to_emails
max_num_articles = -1
ignore_skip_list = False

def parse_command_line_args(argv):
	global filestub
	global fetch_feed_id
	global ignore_since
	global skip_storing_last_article
	global to_email, max_num_articles, ignore_skip_list
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
		elif opt in ("--feed_id"):
			fetch_feed_id = arg
		elif opt in ("--title"):
			filestub = arg
		elif opt in ("--to-email"):
			to_email = arg
		elif opt in ("--max-num-articles"):
			max_num_articles = int(arg)
		elif opt in ("--ignore-skip-list"):
			ignore_skip_list = True

def main():
    try:
        store = Store(filestub)
        store.store_articles(ttrss_api.get_articles(store.last_article_id, fetch_feed_id, ignore_since, max_num_articles, ignore_skip_list))
        if len(store.articles) == 0:
            print("No articles found!")
            sys.exit(2)
        create_api.create_file(store.articles, filestub)
        email_api.send_email(store.article_ids, to_email, filestub)
        store.backup(skip_storing_last_article)
    except Exception as e:
        print(e)
        return

if __name__ == "__main__":
   parse_command_line_args(sys.argv[1:])
   main()