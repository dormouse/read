#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import os
import shutil

from sqlalchemy import desc

from database.test.database import rss_engi, rss_sess, rss_base
from database.models import Node, RssFolder, RssFeed, RssCommand, RssItem
from pyqt_win.queries import QueryRss


def setup_module(module):
    """ setup any state specific to the execution of the given module."""
    pass


def teardown_module(module):
    """ teardown any state that was previously setup with a setup_module
    method.
    """
    pass


class TestQueries:
    def init_data(self):
        rss_base.metadata.drop_all(rss_engi)
        rss_base.metadata.create_all(rss_engi)
        """
        ALL
        ALL Unread
        feed1
        feed2
        Apple
            apple_feed1
            apple_feed2
            apple_feed3
        Imported
            Funny
                funny_feed1
                funny_feed2
                funny_feed3
            News
                news_feed1
                news_feed2
        """
        commander_datas = [
            dict(name="ALL",
                 command="load_all_items"),
            dict(name="All Unread",
                 command="load_all_unread_items")
        ]
        folder_datas = [
            dict(name="Apple"),
            dict(name="Imported"),
            dict(name="Funny"),
            dict(name="News"),
        ]
        feed_datas = [
            dict(title='feed1'),
            dict(title='feed2'),
            dict(title='apple_feed1'),
            dict(title='apple_feed2'),
            dict(title='apple_feed3'),
            dict(title='funny_feed1'),
            dict(title='funny_feed2'),
            dict(title='funny_feed3'),
            dict(title='news_feed1'),
            dict(title='news_feed2'),
        ]

        node_datas = [
            dict(parent_id=None, category='command',
                 data_id=1, rank=0),
            dict(parent_id=None, category='command',
                 data_id=2, rank=1),
            dict(parent_id=None, category='feed',
                 data_id=1, rank=2),
            dict(parent_id=None, category='feed',
                 data_id=2, rank=3),
            dict(parent_id=None, category='folder',
                 data_id=1, rank=4),
            dict(parent_id=5, category='feed',
                 data_id=3, rank=0),
            dict(parent_id=5, category='feed',
                 data_id=4, rank=1),
            dict(parent_id=5, category='feed',
                 data_id=5, rank=2),
            dict(parent_id=None, category='folder',
                 data_id=2, rank=5),
            dict(parent_id=9, category='folder',
                 data_id=3, rank=0),
            dict(parent_id=10, category='feed',
                 data_id=6, rank=0),
            dict(parent_id=10, category='feed',
                 data_id=7, rank=1),
            dict(parent_id=10, category='feed',
                 data_id=8, rank=2),
            dict(parent_id=9, category='folder',
                 data_id=4, rank=1),
            dict(parent_id=14, category='feed',
                 data_id=9, rank=0),
            dict(parent_id=14, category='feed',
                 data_id=10, rank=1),
        ]
        sess = self.query.sess
        sess.add_all(commander_datas)
        sess.add_all(folder_datas)
        sess.add_all(feed_datas)
        sess.add_all(node_datas)
        """
        self.init_items = [
            {
                'feed_id': 1,
                'published': datetime.datetime(2017, 1, 1, 8, 8, 8),
                'title': 'test_title1',
                'summary': 'test_summary1',
                'content': 'test_content1',
                'is_read': False
            },
            {
                'feed_id': 1,
                'published': datetime.datetime(2017, 1, 2, 8, 8, 8),
                'title': 'test_title2',
                'summary': 'test_summary2',
                'content': 'test_content2',
                'is_read': False
            },
            {
                'feed_id': 1,
                'published': datetime.datetime(2017, 1, 3, 8, 8, 8),
                'title': 'test_title3',
                'summary': 'test_summary3',
                'content': 'test_content3',
                'is_read': False
            },
            {
                'feed_id': 3,
                'published': datetime.datetime(2017, 1, 4, 8, 8, 8),
                'title': 'test_title4',
                'summary': 'test_summary4',
                'content': 'test_content4',
                'is_read': False
            },
        ]
        for folder in self.init_folders:
            self.query.add_folder(folder)
        for feed in self.init_feeds:
            self.query.add_feed(**feed)
        for item in self.init_items:
            self.query.add_item(**item)
        """
        self.query.save()

    @classmethod
    def setup_class(self):
        """ setup any state specific to the execution of the given class (which
        usually contains tests).
        """
        # base_path = os.path.abspath(os.path.dirname(__file__))
        # db_path = os.path.dirname(base_path)
        # self.src_db_file = os.path.join(db_path, 'rss.sqlite')
        # self.bak_db_file = os.path.join(db_path, 'rss.sqlite.bak')
        #
        # if os.path.exists(self.src_db_file):
        #     self.need_recover = True
        #     shutil.copy(self.src_db_file, self.bak_db_file)
        #     os.remove(self.src_db_file)
        # else:
        #     self.need_recover = False
        self.query = QueryRss()
        self.query.set_test_db(rss_engi, rss_sess, rss_base)
        self.init_test_data(self)

    @classmethod
    def teardown_class(self):
        """ teardown any state that was previously setup with a call to
        setup_class.
        """
        # if self.need_recover:
        #     shutil.copy(self.bak_db_file, self.src_db_file)
        #     os.remove(self.bak_db_file)

    def test_add_folder(self):
        # add "New Folder" in first level
        folder_name1 = "New Folder1"
        self.query.add(folder_name1)
        folder_name2 = "New Folder2"
        self.query.add(folder_name1)

        known_value = self.init_folders + [new_folder_name, ]

        self.query.add_folder(new_folder_name)
        self.query.save()
        rows = self.query.folder_rows()
        result = [row.name for row in rows]

        self.init_data()
        assert result == known_value

    """
    def test_feed_rows(self):
        known_value = self.init_feeds
        rows = self.query.feed_rows()
        result = [
            dict(
                title=row.title,
                folder_id=row.folder_id,
                url=row.url
            ) for row in rows
        ]
        assert result == known_value

    def test_feed_row(self):
        known_value = self.init_feeds[0]
        row = self.query.feed_row(id=1)
        result = dict(
            title=row.title,
            folder_id=row.folder_id,
            url=row.url
        )
        assert result == known_value

    def test_feed_url(self):
        known_value = self.init_feeds[0]['url']
        result = self.query.feed_url(1)
        assert result == known_value

    def test_folders(self):
        known_value = self.init_folders
        rows = self.query.folder_rows()
        result = [row.name for row in rows]
        assert result == known_value

    def test_folder_name(self):
        index = 0
        known_value = self.init_folders[index]
        result = self.query.folder_name(index + 1)
        assert result == known_value



    def test_add_feed(self):
        new_feed = dict(
            title='new_test_title',
            folder_id=1,
            url='http://www.new_test.com/feed'
        )
        self.query.add_feed(**new_feed)
        self.query.save()
        known_value = self.init_feeds + [new_feed, ]
        rows = self.query.feed_rows()
        result = [
            dict(
                title=row.title,
                folder_id=row.folder_id,
                url=row.url
            ) for row in rows
        ]
        self.init_test_data()
        assert result == known_value

    def test_add_item(self):
        data = {'feed_id': 1,
                'published': datetime.datetime(2017, 1, 1, 8, 8, 8),
                'title': 'new_item_title',
                'summary': 'test_summary',
                'content': 'test_content',
                'is_read': False}
        self.query.add_item(**data)
        self.query.save()
        row = self.query.sess.query(RssItem). \
            filter(RssItem.title == 'new_item_title'). \
            one()
        result = dict(
            feed_id=row.feed_id,
            published=row.published,
            title=row.title,
            summary=row.summary,
            content=row.content,
            is_read=row.is_read
        )
        known_value = data
        self.init_test_data()
        assert result == known_value

    def test_delete_feed(self):
        feed_id = 1
        known_value = {
            'feed_titles': ['test_feed2', 'test_feed3'],
            'item_titles': ['test_title4', ]
        }

        self.query.delete_feed(feed_id)
        self.query.save()
        feeds = self.query.feed_rows()
        feed_titles = [feed.title for feed in feeds]
        items = self.query.item_rows()
        item_titles = [item.title for item in items]
        result = {
            'feed_titles': feed_titles,
            'item_titles': item_titles
        }

        self.init_test_data()
        assert result == known_value

    def test_delete_folder(self):
        folder_id = 1
        known_value = {
            'folder_names':['apple',],
            'feed_titles': ['test_feed3',],
            'item_titles': ['test_title4', ]
        }

        self.query.delete_folder(folder_id)
        self.query.save()

        folders = self.query.folder_rows()
        folder_names = [folder.name for folder in folders]
        feeds = self.query.feed_rows()
        feed_titles = [feed.title for feed in feeds]
        items = self.query.item_rows()
        item_titles = [item.title for item in items]
        result = {
            'folder_names':folder_names,
            'feed_titles': feed_titles,
            'item_titles': item_titles
        }

        self.init_test_data()
        assert result == known_value

    def test_item_rows(self):
        # all items
        known_value1 = self.query.sess. \
            query(RssItem). \
            order_by(desc(RssItem.published)). \
            all()
        result1 = self.query.item_rows()
        # folder items
        known_value2 = self.query.sess. \
            query(RssItem). \
            filter(RssItem.id <= 3). \
            order_by(desc(RssItem.published)). \
            all()
        result2 = self.query.item_rows(folder_id=1)
        # feed items
        known_value3 = self.query.sess. \
            query(RssItem). \
            filter(RssItem.id <= 3). \
            order_by(desc(RssItem.published)). \
            all()
        result3 = self.query.item_rows(feed_id=1)
        known_value = (known_value1, known_value2, known_value3)
        result = (result1, result2, result3)
        assert result == known_value

    def test_is_item_existed(self):
        item = self.init_items[0]
        known_value = [True, False]
        result0 = self.query.is_item_existed(**item)
        result1 = self.query.is_item_existed(
            title='not exist title',
            published=None
        )
        result = [result0, result1]
        assert result == known_value

    def test_modi_feed(self):
        feed_id = 1
        data = {
            'title': 'modi_feed_title',
            'folder_id': 1,
            'url': 'http://test.com/feed',
        }
        self.query.modi_feed(feed_id, **data)
        self.query.save()
        feed = self.query.feed_row(id=1)
        known_value = data['title']
        result = feed.title
        self.init_test_data()
        assert result == known_value
    """
