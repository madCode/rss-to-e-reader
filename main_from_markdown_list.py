import datetime
import re
import uuid

import config
from markdown_list_manager import get_articles_from_list
import email_api
import file_creation_api as create_api

def main():
	# limit to 15 minutes worth of articles for now
	data = get_articles_from_list(15, None)
	articles = data['articles']
	print("num articles:", len(articles))
	if len(articles) == 0:
		return
	filestub = f"{datetime.date.today()}: Today's To-Read Articles"
	create_api.create_file(articles, filestub)
	email_api.send_email(["from","to","read","list"], config.to_emails, filestub)
	data['list_manager'].update_list_file()


if __name__ == "__main__":
   print("Starting articles job for: " + str(datetime.datetime.now()))
   main()