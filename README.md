# How to Use

## Run the setup file
1. open terminal and navigate to the folder containing the script
2. run `./setup.sh` or `./setup.sh --hold-hand`
The setup function does the following:
	- ensure you have python3, pip3, [BeautifulSoup](LINK), and [unidecode](LINK) installed.
	- anything that's not installed gets installed
If the hold-hand flag is enabled, the following also happens
	- the script asks for your tt-rss url, login, password and smtp info so that it can modify the config.py file for you
	- the script then creates a cronjob for you that runs twice a day: once at 8am and once at 5pm.
3. modify the config file with your own data
	If you didn't use the hold-hand option, open up config.py file and fill in the info you need. If you used the hand-hold option, this has already been done for you.
	For help setting up email and email-to-my-device, read on.
4. (optional) set up your device to receive info by email
5. (optional) set up your email account to allow sending via script.
	If you use gmail, [you may need to change some security settings to allow the script to email things for you](#how-to-set-up-your-gmail-for-smtp). Your config file does contain your plaintext email password, so make sure it never gets uploaded anywhere. As an audit of this code can show: no code in this codebase uploads your config file's contents anywhere. Your data is safe provided it remains on your personal device. Future iterations of this product may try to store these things in a more secure way.
6. (for those using Mohave on Mac) [allow cron jobs to access files on your computer](https://blog.bejarano.io/fixing-cron-jobs-in-mojave/)

## Modify the Config File
This section covers all the options in the config file in detail. Feel free to skip if you find it all self-explanatory.

### fetch_content_from_source
This is a list of feed_ids (aka a list of integers). Let's use the [Arts & Letters Daily](https://aldaily.com/) website as an example. The RSS feed for A&L Daily does not contain much. They have a long title which links to the article and then the content of the feed is simply that long title all over again. To truly read the article, you have to click on the title and go to that webpage. If you want the script to try and go the link, try to pull the article text out of the site, and render it as part of the html document you get, add the feed_id to the `fetch_content_from_source` list. You can get the feed id using [this approach](#how-to-get-a-feed-id).

### ignore_feeds
If there are any feeds you want to be ignored, put their ids in this list.

### fetch_feed_id
This is the feed id that is pulled by default. It can be modified by the `--feed-id` command line argument for a single run if necessary. By default it's set to -4 as that, for tt-rss, is how you get your entire feed.

### hide_subtitle
Currently I limit the titles of articles to 100 characters. That's because article titles are put in `h1` tags, which render them in a huge font. Over 100 characters in that font is overwhelming. In order to accomodate long titles, the script then renders the full title in normal text underneath as a "subtitle". However, this doesn't work well for all feeds. Again, A&L Daily is an example of this. As mentioned previously, A&L Daily feed items have a very long title and then the content of the entry is the exact same very long title. If I were to also render a subtitle, we'd get the same text 3 times in a row. To avoid this, I can add the A&L feed id to the `hide_subtitle` list.

### ttrss_api_url, user, password
This is the api url to where the api sits on your server. If your domain hosting tt-rss usually looks like this `http://www.me.com/tt-rss`, then your api url is most likely `http://www.me.com/tt-rss/api`. You can test this by going to that url in your browser. You'll know you've succeeded if the resulting page is blank with only the message `{"seq":null,"status":1,"content":{"error":"NOT_LOGGED_IN"}}` or something similar.

user is the username you use to log into your tt-rss server
password is the password you use to log into your tt-rss server

All of this info is the mostly the same as what you put into your tt-rss client (e.g. any app you're using on your phone) to read your feed.
Is it weird that all this info is sitting in plaintext in a file? Yes. Feel free to change that and let me know how! I'd love to up the security here.

### email_user, email_password, smtp_url, smtp_port
The first two are relatively straightforward: the email address and password for who is sending the emails. After all, someone needs to send them! If you're using gmail, just put your email address and password and leave the other two as is. Also check to see if you need to [change the security settings on your gmail account](#how-to-set-up-your-gmail-for-smtp) to allow the send to happen.

If you use another email service, search online for "[name of your email service] smtp settings". It should all be pretty easily available.
Is it weird that all this info is sitting in plaintext in a file? Yes. Feel free to change that and let me know how! I'd love to up the security here.

### to_emails
This can either be a string representing the email you want to send it to, or a list of strings if you want to send to multiple devices or people. This list just needs to contain email addresses. It doesn't need to be kindle-specific or anything.

## Setup the Cron Job

## Command-line Arguments
You have the option to customize the run in three ways:
"all-unread", "feed-id=", "title=", "do-not-track-last-article", "to-email=", "max-num-articles=", "ignore-skip-list"
1. `--all-unread`:
	the --all-unread flag causes the program to ignore the last_article_id and fetch everything unread
2. `--feed-id <feed_id>`:
	the default setup uses feed_id -4: which is everything coming. If you want to only send stuff for a specific feed, you can use the `--feed-id` flag to do a run for one specific feed (e.g. if you only want to send articles from your local newspaper's feed to your device.)
3. `--title "<title>"`
	the default setup uses the time of day to generate a title for you. You can use the --title flag to set a custom title for the run.
4. `--do-not-track-last-article`
	the default setup stores the last_article_id in a text file. You can pass the --do-not-track-last-article flag to not do that.
5. `--to-email "email@email.com"`
	If, for a single given run, you want to override the `config.to_emails` variable with a single email address, you can use the `--to-email` flag to do so.
6. `--max-num-articles <num>`
	Limit the number of articles in your file with this flag.
7. `--ignore-skip-list`
	Let's say I want to enjoy A&L articles only on weekends. I can add the feed_id for A&L (let's pretend it's 3) to `config.ignore_feeds` so that my daily cron job doesn't send any A&L articles. But then I can use `--ignore-skip-list` to run an A&L only job like so: `python3 main.py --feed-id 3 --ignore-skip-list`.

e.g.
Let's say you ran:
`python3 main.py`
on August 4th 2015 at 8am. This would:
- emails a doc with the title: "8/4/2015: Today's Headlines Morning Edition" to your kindle.
- the doc would contain unread articles from all feeds
- the doc would only contain articles published after the article whose id is stored in last_article_id.txt
- the script would update `last_article_id.txt`


Now let's say you ran:
`python3 main.py --all-unread --feed_id 3 --title "Morning Long Reads" --do-not-track-last-article --max-num-articles 5 --ignore-skip-list --to-email "hello@email.com"`
on August 4th 2015 at 8am. This would:
- emails a doc with the title: "Morning Long Reads" to your kindle.
- the doc would contain unread articles from the feed with id 3 (let's say for the sake of argument that it's [Arts & Letters Daily](https://aldaily.com/))
- the doc would contain 5 unread articles from the Arts & Letters Daily feed. They can be unread articles posted at any time. They don't have to posted after the article in `last_article_id.txt`
- the script would _not_ update `last_article_id.txt`
- the doc would be emailed to `hello@email.com`, regardless of what's stored in `config.to_emails`

## Do some test runs
You can run `python3 main.py` from the folder the code is contained in to test the python code. And `./job.sh` to test the job file. After the first cron job run, you can check `generated-files/cron_log.txt` to see what the logs from the cron job.

## How to get a feed id
To print a list of all your feeds, you can run `python3 print_all_feeds.py`. It will print a huge json object that you can copy to a text file and skim to find the feeds you want.

## How to set up your gmail for smtp