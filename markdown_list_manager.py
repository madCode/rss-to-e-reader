import datetime
import random
import re
import uuid
import config
from functools import reduce

from article import Article, time_to_read_in_minutes

def get_articles_from_list(time_limit_minutes, num_articles_limit):
	print("getting articles from list")
	list_manager = MarkdownListManager()
	list_manager.process_list_and_get_articles()
	articles = list_manager.articles
	if len(articles) == 0 or (time_limit_minutes is None and num_articles_limit is None):
		return {
		'articles': articles,
		'time_used': 0,
		'list_manager': list_manager
		}
	word_count = reduce(lambda x, y: x+y, [article.word_count for article in articles])
	if num_articles_limit is not None and len(articles) < num_articles_limit:
		[list_manager.not_done.add(article.link) for article in articles[num_articles_limit:]]
		articles = articles[:num_articles_limit]
	if time_limit_minutes is not None and time_to_read_in_minutes(word_count) > time_limit_minutes:
		word_count = 0
		to_print = []
		for article in articles:
			word_count += article.word_count
			if time_to_read_in_minutes(word_count) > time_limit_minutes and len(to_print) > 0:
				list_manager.not_done.add(article.link)
			else:
				to_print.append(article)
		articles = to_print
	for article in articles:
		list_manager.done.add(article.link)
	return {
		'list_manager': list_manager,
		'articles': articles,
		'time_used': time_to_read_in_minutes(word_count),
		}



TO_DO_LIST_REGEX = r"\-\s\[(?P<status>[x\s])\]\s(?P<url>.*)"

class MarkdownListManager:
	def __init__(self):
		self.done = set()
		self.to_do = set()
		self.not_done = set()
		self.articles = []

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
				self.to_do.add(url)
			elif status == 'x':
				self.done.add(url)
			else:
				self.not_done.add(url)

	def _process_urls(self):
		articles = []
		for url in self.to_do:
			try:
				article = Article(str(random.randint(1,6000)), '', url, '', 'List of Articles To Read', 0)
				articles.append(article)
				self.done.add(url)
			except Exception as e:
				print(e)
				self.not_done.add(url)
				continue
		self.articles = articles
		self.to_do = set([url for url in self.to_do if url not in self.done])

	def update_list_file(self):
		with open(config.list_file_path, "w+") as file:
			for url in self.not_done:
				file.write(f"- [ ] {url}\n")
			for url in self.done:
				file.write(f'- [x] {url}\n')

	def process_list_and_get_articles(self):
		self._load_urls()
		self._process_urls()