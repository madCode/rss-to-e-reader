from bs4 import BeautifulSoup
import json
import requests
import re

def get_parser(link):
    headers = {'User-Agent': 'Mozilla/5.0 (Android 7.0; Mobile; rv:54.0) Gecko/54.0 Firefox/54.0'}
    response = requests.get(link, headers=headers)
    html_str = response.content.decode("UTF-8")
    return BeautifulSoup(html_str, features="html.parser")

def guess_article_from_para(parser):
    all_para = parser.find_all('p')
    index = len(all_para)//4 if len(all_para)//4 < len(all_para) else 0
    random_para = all_para[index]
    return_node = random_para.parent
    attempts = 0
    while len(return_node) <= 1 and attempts < 3:
        return_node = return_node.parent
        attempts += 1
    return return_node

def get_nytimes_article(parser):
    return parser.body.find('section',attrs={'name':'articleBody'})

def get_spectator_article(parser):
    return parser.body.find('main',attrs={'class':'ContentPageBody-module__body__container'})

def get_new_criterion(parser):
    title = parser.body.find('div',attrs={'class':'article-title-container'})
    return title + parser.body.find('div',attrs={'class':'article-text-column'})

def get_smithsonian_mag(parser):
    return parser.find_all('div',{'class':'article-body pagination-first'})[0]

def get_aeon(parser):
    return parser.find('div', attrs={'class':'article__body__content'})

def get_the_tls(parser):
    idString = parser.find(text=re.compile("tlsPageObject"))
    pattern = re.compile(r'tlsPageObject = \{\"ID\":\"(\d+)\"\,')
    idNum = pattern.findall(idString)[0]
    url = "https://www.the-tls.co.uk/wp-json/tls/v2/single-article/" + idNum
    headers = {'User-Agent': 'Mozilla/5.0 (Android 7.0; Mobile; rv:54.0) Gecko/54.0 Firefox/54.0'}
    response = requests.get(url, headers=headers)
    response_dict = json.loads(response.content.decode("UTF-8"))
    article = response_dict['content'].replace('\n',' ').strip()
    return re.sub(r"\s+"," ",article)

def get_tablet_mag(parser):
    element = parser.find(text=re.compile('{"@id":"https://www.tabletmag.com/'))
    pattern = re.compile(r'\{"@id"\:".+"@type":"Article","name":"(.+)","headline":"(.+)","articleBody":"(.+)","author')
    matcher = re.match(pattern, element)
    article_title = matcher.group(2)
    article_body = matcher.group(3)
    article_body = '<p>' + re.sub(r'\.([A-Z])', r'.</p><p>\1', article_body) + '</p>'
    html_str = '<html><head></head><body><h4>'+article_title+'</h4>'+article_body+'</body></html>'
    return BeautifulSoup(html_str, features="html.parser").body

special_parsers = {
    'https://www.spectator.co.uk/': get_spectator_article,
    'https://newcriterion.com/': get_new_criterion,
    'https://www.smithsonianmag.com/': get_smithsonian_mag,
    'https://aeon.co/': get_aeon,
    'https://www.the-tls.co.uk/': get_the_tls,
    'https://www.nytimes.com/': get_nytimes_article,
    'https://www.tabletmag.com/': get_tablet_mag,
}

