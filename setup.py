print("To help set up your config file, the script will ask you some questions.\nThe data will only be printed to your config.py file locally and not be shared anywhere else.\nTo leave something blank for now, just press Enter. You can come back and fill out config.py later.")
ttrss_api_url = input("Enter your ttrss api url. It usually looks like this: 'http://<your_domain_hosting_ttrss.com>/tt-rss/api/': ")
user = input("Enter your ttrss username: ")
password = input("Enter your ttrss password: ")
email_user = input("Enter your email address: ")
email_password = input("Enter your email password: ")
smtp_url = input("Enter your email smtp url. If using gmail, just press Enter: ") or 'smtp.gmail.com'
smtp_port = input("Enter your email smtp port. If using gmail, just press Enter: ") or 465
to_email = input("Enter one of the email address you want to send the doc to. You can add more in config.py later: ")

config_template = f"""
# list of feed_ids
fetch_content_from_source = []
# don't include content from these feed_ids in the final document
ignore_feeds = []
# id of the feed to fetch for. Defaults to -4 which is tt-rss for "everything"
fetch_feed_id = -4
#  list of feed ids where the content of the feed is a table that needs to be reformatted to work well on
replace_table_feeds = []

# a list of feed_ids
# some feeds don't have titles for their articles. Whatever's in content is 
# also in the title. In that case, there's no point in showing the title a second
# time as a subtitle.
hide_subtitle = []

# tt-rss api url. Usually looks like this: 'http://<your_domain_hosting_ttrss.com>/tt-rss/api/'
ttrss_api_url ="{ttrss_api_url}"
# tt-rss login info, both strings
user = "{user}"
password = "{password}"

# smtp info. Currently set to gmail defaults. All strings except port, which is number
email_user = "{email_user}"
email_password = "{email_password}"
smtp_url = "{smtp_url}"
smtp_port = "{smtp_port}"

# string or list of strings
to_emails = ["{to_email}"]
"""

file = open('config.py', "w+")
file.write(config_template)