import config
import json
import requests
import ttrss_api

login_data = '{"op":"login","user":"'+config.user+'","password":"'+config.password+'"}'
session_data = ttrss_api.get_ttrss_data(login_data)
if len(session_data) == 0:
    raise RuntimeError('Unable to authenticate session for tt-rss api')

session_id = session_data['content']['session_id']
get_feeds_data = '{"sid":"' + session_id + '","op":"getFeeds","cat_id":"-4","include_nested":"1"}'
feeds_response = ttrss_api.get_ttrss_data(get_feeds_data)
print(feeds_response)
