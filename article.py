import re

import article_parser
import config
from kindle_html_formatter import clean_for_kindle

TITLE_CUTOFF = 100

def time_to_read_in_minutes(num_words):
    return num_words//300

def time_to_read_str(num_words):
    per_min = time_to_read_in_minutes(num_words)
    if per_min < 60:
        return str(per_min) + ' min'
    per_hour = per_min//60
    remainder = per_min%60
    return str(per_hour) + ' hr ' + str(remainder) + ' min'

def combine_articles_from_multiple_sources(rss_list, to_read_list, list_manager, time_limit_minutes, max_num_articles):
    final_list = []
    actually_done = set()
    stop = False
    if time_limit_minutes is None and max_num_articles is None:
        list_manager.update_list_file()
        return rss_list + to_read_list
    if time_limit_minutes is not None:
        time_limit = time_limit_minutes
        for i in range(max(len(rss_list), len(to_read_list))):
            if stop:
                break
            if time_limit <= 0:
                stop = True
            if i < len(rss_list):
                article = rss_list[i]
                final_list.append(article)
                time_limit -= time_to_read_in_minutes(article.word_count)
            if time_limit <= 0:
                stop = True
            if i < len(to_read_list):
                article = to_read_list[i]
                final_list.append(article)
                actually_done.add(article.link)
                time_limit -= time_to_read_in_minutes(article.word_count)
    for url in list_manager.done:
        if url not in actually_done:
            list_manager.to_do.add(url)
    list_manager.done.update(actually_done)
    list_manager.update_list_file()
    return final_list


class Article:
    def __init__(self, article_id, title, link, content, feed_title, feed_id):
        self.id = article_id
        self.link = link
        self.content = content
        self.feed_title = feed_title
        self.feed_id = int(feed_id)
        self.parser = article_parser.get_parser(link)
        if len(title) == 0:
            self.title = self.parser.find('title').string
        else:
            self.title = title
        self.short_title = self.title[:TITLE_CUTOFF]
        self.default_parser_used = False
        self.word_count = len(content.split())
        self.full_content = ""
        self._hydrate_article()
        if self.feed_id in config.replace_table_feeds:
            self.content = article_parser.replace_tables_with_divs(self.content).prettify()


    def _hydrate_article(self):
        if self.feed_id not in config.fetch_content_from_source:
            return
        parseFunction = None
        for key in article_parser.special_parsers:
            if self.link.startswith(key):
                parseFunction = article_parser.special_parsers[key]
        if parseFunction == None:
            self.default_parser_used = True
            parseFunction = article_parser.guess_article_from_para
        try:
            article = clean_for_kindle(parseFunction(self.parser))
            self.word_count = len(article.text.split())
            if self.default_parser_used:
                self.full_content = f'<h3>Full article ({self.word_count} words : est. {time_to_read_str(self.word_count)}) [Default method used]</h3>' + self._get_full_default_article()
            else:
                self.full_content = f'<h3>Full article ({self.word_count} words : est. {time_to_read_str(self.word_count)})</h3>' + article.prettify()
        except Exception as exception:
            self.word_count = -1
            if self.default_parser_used:
                self.full_content = f'<h3>Error rendering full article [Default method used]</h3>' + str(exception)
            else:
                self.full_content = '<h3>Error rendering full article</h3>' + str(exception)

    def _get_full_default_article(self):
        parser = article_parser.get_parser(self.link)
        content = parser.get_text()
        html = "<p>" + re.sub(r'\n+', "<br>", content) + "</p>"
        return html



    def toHtmlString(self,next_id):
        return f'<a href="#top">[← top]</a><h1 id="{self.id}"><a href="{self.link}">{self.short_title}</a></h1><a href="#{next_id}">[skip →]</a><h2>{self.feed_title}</h2>{self.content}{self.full_content}'

