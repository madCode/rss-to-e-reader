import datetime


class Store:
    def __init__(self):
        self.articles = []
        self.article_ids = []
        self.last_article_id = Store._load_last_article_id()

    def store_articles(self, articles):
        self.articles = articles
        self.article_ids = [str(article.id) for article in articles]

    def backup(self, skip_storing_last_article):
        self._store_all_article_ids()
        if skip_storing_last_article:
            return
        self._update_last_article()

    def _update_last_article(self):
        if len(self.article_ids) == 0:
            print("No articles ids to update with")
            return
        file = open("generated_files/last_article_id.txt", "w+")
        file.write(str(self.article_ids[0]))
        file.close()
        print("Updated last article id")

    def _store_all_article_ids(self):
        if len(self.article_ids) == 0:
            print("No articles ids to store")
            return
        file = open("generated_files/article_ids.txt", "w+")
        file.write(", ".join(self.article_ids))
        file.close()
        print("Stored all article ids")

    @staticmethod
    def _load_last_article_id():
        file = open("generated_files/last_article_id.txt", "r")
        article_id = file.read()
        file.close()
        return article_id