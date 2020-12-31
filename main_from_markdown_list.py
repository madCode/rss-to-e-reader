import datetime
import re
import uuid

from markdown_list_manager import get_articles_from_list
import email_api
import file_creation_api as create_api

def main():
	articles = get_articles_from_list(None, None)['articles']
	if len(articles) == 0:
		return
	filestub = f"{datetime.date.today()}: Today's To-Read Articles"
	create_api.create_file(articles, filestub)
	email_api.send_email(to_do, config.to_emails, filestub)
	update_list_file()


if __name__ == "__main__":
   print("Starting articles job for: " + str(datetime.datetime.now()))
   main()