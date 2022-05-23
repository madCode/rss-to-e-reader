from bs4 import BeautifulSoup # type: ignore
import json
import requests
import re

def get_bs4_parser(link: str) -> BeautifulSoup:
    headers = {'User-Agent': 'Mozilla/5.0 (Android 7.0; Mobile; rv:54.0) Gecko/54.0 Firefox/54.0'}
    response = requests.get(link, headers=headers)
    html_str = response.content.decode("UTF-8")
    return BeautifulSoup(html_str, features="html.parser")

def get_nytimes_article(parser: BeautifulSoup):
    return parser.body.find('section',attrs={'name':'articleBody'})

def get_spectator_article(parser: BeautifulSoup):
    return parser.body.find('main',attrs={'class':'ContentPageBody-module__body__container'})

def get_new_criterion(parser: BeautifulSoup):
    title = parser.body.find('div',attrs={'class':'article-title-container'}).prettify()
    return BeautifulSoup(title + parser.body.find('div',attrs={'class':'article-text-column'}).prettify(), features='html.parser')

def get_smithsonian_mag(parser: BeautifulSoup):
    return parser.find_all('div',{'class':'article-body pagination-first'})[0]

def get_aeon(parser: BeautifulSoup):
    return parser.find('div', attrs={'class':'article__body__content'})

def get_the_tls(parser: BeautifulSoup):
    idString = parser.find(text=re.compile("tlsPageObject"))
    pattern = re.compile(r'tlsPageObject = \{\"ID\":\"(\d+)\"\,')
    idNum = pattern.findall(idString)[0]
    url = "https://www.the-tls.co.uk/wp-json/tls/v2/single-article/" + idNum
    headers = {'User-Agent': 'Mozilla/5.0 (Android 7.0; Mobile; rv:54.0) Gecko/54.0 Firefox/54.0'}
    response = requests.get(url, headers=headers)
    response_dict = json.loads(response.content.decode("UTF-8"))
    article = response_dict['content'].replace('\n',' ').strip()
    article_html = re.sub(r"\s+"," ",article)
    return BeautifulSoup(article_html, features="html.parser")

def get_tablet_mag(parser: BeautifulSoup):
    element = parser.find(text=re.compile('{"@id":"https://www.tabletmag.com/'))
    pattern = re.compile(r'\{"@id"\:".+"@type":"Article","name":"(.+)","headline":"(.+)","articleBody":"(.+)","author')
    matcher = re.match(pattern, element)
    article_title = matcher.group(2) if matcher else ""
    article_body = matcher.group(3) if matcher else ""
    article_body = '<p>' + re.sub(r'\.([A-Z])', r'.</p><p>\1', article_body) + '</p>'
    html_str = '<html><head></head><body><h4>'+article_title+'</h4>'+article_body+'</body></html>'
    return BeautifulSoup(html_str, features="html.parser").body

def replace_tables_with_divs(content_str: str) -> BeautifulSoup:
    parser = BeautifulSoup(content_str, features="html.parser")
    tables = parser.find_all('table')
    if len(tables) == 0:
        return parser
    bodies = parser.find_all('tbody')
    rows = parser.find_all('tr')
    columns = parser.find_all('td')
    for table in tables:
        table.name = 'div'
    for body in bodies:
        body.name = 'div'
    for row in rows:
        row.name = 'div'
    for column in columns:
        column.name = 'div'
    return parser

special_parsers = {
    'https://www.spectator.co.uk/': get_spectator_article,
    'https://newcriterion.com/': get_new_criterion,
    'https://www.smithsonianmag.com/': get_smithsonian_mag,
    'https://aeon.co/': get_aeon,
    'https://www.the-tls.co.uk/': get_the_tls,
    'https://www.nytimes.com/': get_nytimes_article,
    'https://www.tabletmag.com/': get_tablet_mag,
}


# TODO: a potential parser: look for a "skip to content" link and then look for the div that has that id
