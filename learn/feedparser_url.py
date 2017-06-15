#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import feedparser
import datetime
import time


def test():
    url = 'http://feeds.bbci.co.uk/zhongwen/simp/rss.xml'
    feed = feedparser.parse(url)
    item = feed['items'][0]
    data = {}
    # data['publish_time'] = item['published_parsed']
    if url == 'http://feed.smzdm.com':
        time_str = item['published']
        data['publish_time'] = datetime.datetime.strptime(
            time_str, '%a, %d %b %Y %H:%M:%S')
    else:
        time_str = item['published_parsed']
        data['publish_time'] = datetime.datetime.fromtimestamp(
            time.mktime(time_str) - time.timezone
        )

    data['title'] = item['title']
    data['summary'] = item['summary']
    if url == 'http://sspai.me/feed':
        data['content'] = item['summary_detail']['value']
    if url == 'http://www.waerfa.com/feed':
        data['content'] = item['content'][0]['value']
    if url == 'http://feed.smzdm.com':
        data['content'] = item['content'][0]['value']
    # print(data)

    feed_infos = {
        'href': feed['href'],
        'version': feed['version'],
        'encoding': feed['encoding'],
        'language': feed['feed']['language'],
        'author': feed['feed']['author'],
        'link': feed['feed']['link'],
        'published': feed['feed']['published'],
        'published_parsed': feed['feed']['published_parsed'],
        'subtitle': feed['feed']['subtitle'],
        'title': feed['feed']['title'],
    }
    print(feed_infos)

    item_infos = {
        'title': item['title'],
        'author': item['author'],
        'link': item['link'],
        'published': item['published'],
        'published_parsed': item['published_parsed'],
        'summary': item['summary'],
    }
    print(item_infos)


if __name__ == '__main__':
    test()
