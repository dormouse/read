import os

import feedparser

from database.database import rss_sess, rss_base, rss_engi
from database.models import RssFeed, RssFolder, RssItem
from pyqt_win.parser import ItemParser
import project_conf

FULLPATH = os.path.abspath(os.path.dirname(__file__))


class QueryRss(object):
    def __init__(self):
        self.engi = rss_engi
        self.sess = rss_sess
        self.base = rss_base

        self.log = project_conf.LOG
        self.cache_path = os.path.join(FULLPATH, 'cache')
        self.default_item_index_file = 'index.html'

    def set_test_db(self, engi, sess, base):
        self.engi = rss_engi
        self.sess = rss_sess
        self.base = rss_base

    def feed_rows(self, folder_id=None):
        if folder_id:
            rows = self.sess.query(RssFeed). \
                filter(RssFeed.folder_id == folder_id).all()
        else:
            rows = self.sess.query(RssFeed).all()
        return rows

    def feeds_query(self, **kwargs):
        query = self.sess.query(RssFeed)
        for key, value in kwargs.items():
            query = query.filter(getattr(RssFeed, key) == value)
        return query

    def feed_row(self, **kwargs):
        """
        get first feed row
        :param feed_id:
        :return:
        """
        query = self.feeds_query(**kwargs)
        return query.first()

    def feed_url(self, feed_id):
        url = self.sess.query(RssFeed.url).filter(
            RssFeed.id == feed_id).scalar()
        return url

    def folder_rows(self):
        rows = self.sess.query(RssFolder).all()
        return rows

    def folder_row(self, folder_id):
        row = self.sess.query(RssFolder). \
            filter(RssFolder.id == folder_id).first()
        return row

    def folder_name(self, folder_id):
        name = self.sess.query(RssFolder.name). \
            filter(RssFolder.id == folder_id).scalar()
        return name

    def folder_id(self, folder_name):
        folder_id = self.sess.query(RssFolder.id). \
            filter(RssFolder.name == folder_name).scalar()
        return folder_id

    def add(self, obj, **kwargs):
        for k, v in kwargs.items():
            if hasattr(obj, k):
                setattr(obj, k, v)
        self.sess.add(obj)

    def add_folder(self, name):
        folder = RssFolder(name)
        self.add(folder)

    def add_feed(self, **kwargs):
        feed = RssFeed()
        self.add(feed, **kwargs)

    def add_item(self, **kwargs):
        item = RssItem()
        self.add(item, **kwargs)

    def delete_feed(self, feed_id):
        # delete feed's item
        items = self.item_rows(feed_id=feed_id)
        for item in items:
            self.sess.delete(item)
        # map(self.sess.delete, items)
        # delete feed
        feed = self.feed_row(id=feed_id)
        self.sess.delete(feed)

    def delete_folder(self, folder_id):
        feeds = self.feed_rows(folder_id)
        feed_ids = [feed.id for feed in feeds]
        for feed_id in feed_ids:
            self.delete_feed(feed_id)
        folder = self.folder_row(folder_id)
        self.sess.delete(folder)

    def item_rows(self, **kwargs):
        query = self.items_query(**kwargs)
        return query.all()

    def items_count(self, **kwargs):
        query = self.items_query(**kwargs)
        return query.count()

    def items_query(self, **kwargs):
        query = self.sess.query(RssItem)
        for key, value in kwargs.items():
            if key == 'folder_id':
                query = query.join(RssFeed). \
                    filter(RssFeed.folder_id == value)
            else:
                query = query.filter(getattr(RssItem, key) == value)
        return query

    def is_item_existed(self, **kwargs):
        """
        only compare title and publish_time
        :param kwargs must have title and publish_time 
        :return: 
        """
        query_data = {
            'title': kwargs['title'],
            'published': kwargs['published']
        }
        query = self.items_query(**query_data)
        return True if query.count() else False

    def modi_feed(self, feed_id, **kwargs):
        feed_row = self.feed_row(id=feed_id)
        for k, v in kwargs.items():
            if hasattr(feed_row, k):
                setattr(feed_row, k, v)

    def modi_folder(self, folder_id, new_folder_name):
        row = self.folder_row(folder_id)
        row.name = new_folder_name

    def save(self):
        self.sess.commit()

    def init_database(self):
        self.base.metadata.create_all(self.engi)
        # some default rss feed
        self.add_folder('default')
        feeds = [
            dict(
                title='少数派',
                folder_id=1,
                url='http://sspai.me/feed'
            ),
            dict(
                title='Mac玩儿法',
                folder_id=1,
                url='http://www.waerfa.com/feed'
            ),

        ]
        for feed in feeds:
            self.add_feed(**feed)
            self.save()

    def update_feed(self, feed_id):
        feed = self.feed_row(id=feed_id)
        url = feed.url
        feed_data = feedparser.parse(url)
        if feed_data['bozo'] == 1:
            # todo present in tree menu
            self.log.warning("{} parse fail!".format(feed.url))
            return
        else:
            item_datas = [
                self.parse_feed_item(feed_id, url, item) \
                for item in feed_data['items']
            ]
            if item_datas:
                self.save_item_datas(item_datas)

    def parse_feed_item(self, feed_id, feed_url, item):
        parser = ItemParser(feed_id, feed_url, item)
        data = parser.get_data()
        return data

    def save_item_datas(self, datas):
        need_save = False
        for data in datas:
            db_data = data['db']
            file_data = data['file']
            if self.is_item_existed(**db_data):
                # already exsit
                pass
            else:
                # save content to cache dir
                item_dir = file_data['dir']
                item_html = file_data['html']

                item_abs_dir = os.path.join(self.cache_path, item_dir)
                if not os.path.exists(item_abs_dir):
                    os.mkdir(item_abs_dir)
                filename = os.path.join(item_abs_dir,
                                        self.default_item_index_file)
                with open(filename, 'w') as f:
                    f.write(item_html)
                # save item datas to db
                data['content'] = item_dir
                self.add_item(**db_data)
                need_save = True
        if need_save:
            self.save()

    def mark_read(self, **kwargs):
        """
        mark items as read
        :param all: if True mark all unread items
        :return: True if has data changed
        """
        kwargs['is_read'] = False
        query = self.items_query(**kwargs)
        if query.count():
            query.update({'is_read': True})
            self.save()
            return True
        else:
            return False
