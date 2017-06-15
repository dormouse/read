import locale
import datetime
import hashlib
import time
import os
import feedparser
from bs4 import BeautifulSoup

import project_conf
FULLPATH = os.path.abspath(os.path.dirname(__file__))


class FeedParser(object):
    def __init__(self, url):
        self.url = url
        self.feed = None

    def is_parse_success(self):
        """
        bozo may not be present. Some platforms, such as Mac OS X 10.2 and some
        versions of FreeBSD, do not include an XML parser in their Python
        distributions. Universal Feed Parser will still work on these platforms,
        but it will not be able to detect whether a feed is well-formed.
        However, it can detect whether a feed’s character encoding is
        incorrectly declared. (This is done in Python, not by the XML parser.)
        See Character Encoding Detection for details.
        :return:
        """
        if self.feed['bozo'] == 0:
            return True
        else:
            return False

    def infos(self):
        self.feed = feedparser.parse(self.url)
        feed = self.feed

        if feed['bozo'] == 0:
            feed_infos = dict(bozo=feed['bozo'],
                              href=feed.get('href'),
                              version=feed.get('version'),
                              encoding=feed.get('encoding'))
            if feed.get('feed'):
                feed_feed_dict = {
                    'language': feed['feed'].get('language'),
                    'author': feed['feed'].get('author'),
                    'link': feed['feed'].get('link'),
                    'published': feed['feed'].get('published'),
                    'published_parsed': feed['feed'].get('published_parsed'),
                    'subtitle': feed['feed'].get('subtitle'),
                    'title': feed['feed'].get('title'),
                }
                feed_infos.update(**feed_feed_dict)
            return feed_infos
        else:
            return None


class ItemParser(object):
    def __init__(self, feed_id, feed_url, item):
        self.feed_id = feed_id
        self.feed_url = feed_url
        self.item = item
        self.html = None
        self.item_dir = None

    def get_data(self):
        data = {
            'db': self.get_db_data(),
            'file': self.get_file_data()
        }
        return data

    def get_db_data(self):
        data = {
            'feed_id': self.feed_id,
            'is_read': False,
            'link': self.item.get('link'),
            'title': self.item.get('title'),
            'summary': self.item.get('summary')
        }

        if self.feed_url == 'http://feed.smzdm.com':
            time_str = self.item.get('published')
            if time_str:
                loc = locale.getlocale()
                locale.setlocale(locale.LC_ALL, ('en_US', 'UTF-8'))
                data['published'] = datetime.datetime.strptime(
                    time_str, '%a, %d %b %Y %H:%M:%S')
                locale.setlocale(locale.LC_ALL, loc)
        else:
            time_str = self.item.get('published_parsed')
            if time_str:
                data['published'] = datetime.datetime.fromtimestamp(
                    time.mktime(time_str) - time.timezone
                )

        data['content'] = self.make_item_dir()

        return data

    def get_file_data(self):
        if 'sspai.' in self.feed_url:
            html = self.item['summary_detail']['value']
        else:
            try:
                html = self.item['content'][0]['value']
            except:
                html = self.item.get('summary')

        data = {
            'dir': self.make_item_dir(),
            'html': self.clean_html(html)
        }
        return data

    def make_item_dir(self):
        # todo: deal with encode fail
        hash_string = (self.item['title'] + self.item['link']).encode('utf-8')
        return hashlib.md5(hash_string).hexdigest()

    def clean_html(self, body):
        data = {
            'title': self.item['title'],
            'body': body
        }
        content = self.template().format(**data)
        soup = BeautifulSoup(content, 'html.parser')
        imgs = soup.find_all('img')
        for img in imgs:
            del img['width']
            del img['height']
        return soup.prettify()

    @staticmethod
    def template():
        tp_file = "index.html"
        tp_file_full = os.path.join(FULLPATH, 'template', tp_file)
        with open(tp_file_full, encoding='utf-8') as f:
            template = f.read()
        return template
