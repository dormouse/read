"""

Of particular interest:

feed[ "bozo" ]
1 if the feed data isn't well-formed XML.
feed[ "url" ]
URL of the feed's RSS feed
feed[ "version" ]
version of the RSS feed
feed[ "channel" ][ "title" ]
"PythonInfo Wiki" - Title of the Feed.
feed[ "channel" ][ "description" ]
"RecentChanges at PythonInfo Wiki." - Description of the Feed
feed[ "channel" ][ "link" ]
Link to RecentChanges - Web page associated with the feed.
feed[ "channel" ][ "wiki_interwiki" ]
"Python``Info" - For wiki, the wiki's preferred InterWiki moniker.
feed[ "items" ]
A gigantic list of all of the RecentChanges items.
For each item in feed["items"], we have:

item[ "date" ]
"2004-02-13T22:28:23+08:00" - ISO 8601 date
item[ "date_parsed" ]
(2004,02,13,14,28,23,4,44,0)
item[ "title" ]
title for item
item[ "summary" ]
change summary
item[ "link" ]
URL to the page
item[ "wiki_diff" ]
for wiki, a link to the diff for the page
item[ "wiki_history" ]
for wiki, a link to the page history
"""
import feedparser
url = 'http://sspai.me/feed'
feed = feedparser.parse(url)
tests = [
    feed['bozo'],
    feed['version'],
]
for test in tests:
    print(test)

item = feed['items'][0]
print(item)

