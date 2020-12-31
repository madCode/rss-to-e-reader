#!/bin/sh
echo "running job.sh"
cd ~/code/rss-to-e-reader
cp ~/Sync/sync_to_phone/notes/articles.md .
/usr/bin/python3 main.py --time_limit_minutes 60 --all-unread
cp articles.md ~/Sync/sync_to_phone/notes/
