import datetime
import re
import uuid
from functools import reduce

from article import Article, time_to_read_in_minutes

def get_articles_from_list(time_limit_minutes, num_articles_limit):
	list_manager = MarkdownListManager()
	articles = list_manager.process_list_and_get_articles()
	if len(articles) == 0 or (time_limit_minutes is None and num_articles_limit is None):
		return {
		'articles': articles,
		'time_used': 0,
		}
	word_count = 0
	for article in articles:
		# TODO: figure out how reduce works. It seemed to get an int in the middle for some reason
		word_count += article.word_count
	if num_articles_limit is not None and len(articles) < num_articles_limit:
		[list_manager.not_done.append(article.link) for article in articles[num_articles_limit:]]
		articles = articles[:num_articles_limit]
	if time_limit_minutes is not None and time_to_read_in_minutes(word_count) > time_limit_minutes:
		word_count = 0
		for i in range(len(articles)):
			print(type(article))
			word_count += article.word_count
			if time_to_read_in_minutes(word_count) > time_limit_minutes:
				[list_manager.not_done.append(article.link) for article in articles[i:]]
				articles = articles[:i]
	list_manager.done = [article.link for article in articles]
	return {
		'articles': articles,
		'time_used': time_to_read_in_minutes(word_count),
		}



TO_DO_LIST_REGEX = r"\-\s\[(?P<status>[x\s])\]\s(?P<url>.*)"

class MarkdownListManager:
	def __init__(self):
		self.done = []
		self.to_do = []
		self.not_done = []

	def _load_urls(self):
		file = open('articles.md', 'r')
		lines = file.readlines()
		for line in lines:
			matches = re.search(TO_DO_LIST_REGEX, line)
			if matches is None:
				continue
			status = matches.group('status')
			url = matches.group('url')
			if status == ' ':
				self.to_do.append(url)
			elif status == 'x':
				self.done.append(url)
			else:
				self.not_done.append(url)

	def _process_urls(self):
		articles = []
		for url in self.to_do:
			try:
				article = Article(str(uuid.uuid1()), '', url, '', 'List of Articles To Read', 0)
				articles.append(article)
				self.done.append(url)
			except Exception as e:
				print(e)
				self.not_done.append(url)
				continue
		return articles

	def update_list_file(self):
		with open('articles.md', "w+") as file:
			for url in self.not_done:
				file.write(f"- [ ] {url}\n")
			for url in self.done:
				file.write(f'- [x] {url}\n')

	def process_list_and_get_articles(self):
		self._load_urls()
		return self._process_urls()