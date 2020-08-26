from article import Article
import config
import json
import requests

def get_ttrss_data(data):
    response = requests.post(config.ttrss_api_url, data=data)
    if response.status_code != 200:
        print('Failure to connect to tt-rss api.\nData: {data} \nStatus Code: {response.status_code}')
        return {}
    dict_str = response.content.decode("UTF-8")
    return json.loads(dict_str)

def get_articles(last_article_id, fetch_feed_id, ignore_since, max_num_articles, ignore_skip_list):
    login_data = '{"op":"login","user":"'+config.user+'","password":"'+config.password+'"}'
    session_data = get_ttrss_data(login_data)
    if len(session_data) == 0:
        raise RuntimeError('Unable to authenticate session for tt-rss api')

    session_id = session_data['content']['session_id']
    limit_str = f'"limit":"{max_num_articles}",' if max_num_articles >= -1 else ''
    if ignore_since:
           get_headlines_data = '{"sid":"' + session_id + '",'+ limit_str +'"op":"getHeadlines","feed_id":"'+str(fetch_feed_id)+'","view_mode":"unread","show_content":"1"}'
    else:
        get_headlines_data = '{"sid":"' + session_id + '",'+ limit_str +'"op":"getHeadlines","feed_id":"'+str(fetch_feed_id)+'","view_mode":"unread","show_content":"1","since_id":"' + last_article_id + '"}'
    headlines_response = get_ttrss_data(get_headlines_data)
    if len(headlines_response) == 0:
        raise RuntimeError(f'Unable to get headline data from tt-rss api. Called with: {data}')

    headlines = headlines_response['content']
    total = len(headlines)
    articles = []
    i = 0
    for headline in headlines:
        if not ignore_skip_list and headline['feed_id'] in config.ignore_feeds:
            continue
        article = Article(headline['id'], headline['title'], headline['link'], headline['content'], headline['feed_title'], headline['feed_id'])
        articles.append(article)
        if i%10 == 0:
            print(f'loading article {i}/{total}')
        i += 1
    return articles