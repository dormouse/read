#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import os
import shutil

from sqlalchemy import desc

from database.test.database import rss_engi, rss_sess, rss_base
from pyqt_win.queries import QueryRss
import datetime
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.sqlite import INTEGER, TEXT, DATETIME, BOOLEAN
from sqlalchemy.orm import column_property, relationship
from sqlalchemy.sql import func
from sqlalchemy import and_

class Node(rss_base):
    __tablename__ = 'node'

    id = Column(INTEGER, primary_key=True)
    parent_id = Column(INTEGER, ForeignKey('node.id'))
    category = Column(TEXT)
    children = relationship("Node")
    data_id = Column(INTEGER)  # RssAction.id or RssFolder.id or RssFeed.id
    rank = Column(INTEGER)  # rank for display in tree

    def __repr__(self):
        return "Node:{}".format(self.id)


class RssCommand(rss_base):
    __tablename__ = 'rss_command'
    id = Column(INTEGER, primary_key=True)
    name = Column(TEXT)
    command = Column(TEXT)

    def __repr__(self):
        return "Commander:{}".format(self.name)


class RssFolder(rss_base):
    __tablename__ = 'rss_folder'
    id = Column(INTEGER, primary_key=True)
    name = Column(TEXT)

    def __repr__(self):
        return "folder:{}".format(self.name)


class RssFeed(rss_base):
    __tablename__ = 'rss_feed'
    id = Column(INTEGER, primary_key=True)
    title = Column(TEXT)
    subtitle = Column(TEXT)
    url = Column(TEXT)
    encoding = Column(TEXT)
    language = Column(TEXT)
    author = Column(TEXT)
    site_url = Column(TEXT)
    published = Column(DATETIME)
    updated = Column(DATETIME)

    def __repr__(self):
        return "feed:{}".format(self.title)


class RssItem(rss_base):
    __tablename__ = 'rss_item'
    id = Column(INTEGER, primary_key=True)
    author = Column(TEXT)
    feed_id = Column(INTEGER,
                     ForeignKey('rss_feed.id'),
                     info={'relationFieldName': 'feed'}
                     )
    feed = relationship("RssFeed")
    published = Column(DATETIME)
    link = Column(TEXT)
    title = Column(TEXT)
    summary = Column(TEXT)
    content = Column(TEXT)
    is_read = Column(BOOLEAN)

    @property
    def foreignKeyFieldNames(self):
        # a list of name of field which have foreign key
        cols = self.__table__.columns
        fieldNames = [col.name for col in cols]
        return filter(self.isForeignKeyField, fieldNames)

    @property
    def foreignKeyRelationFieldNames(self):
        return [self.relationFieldName(name) for name in
                self.foreignKeyFieldNames]

    @property
    def allFieldNames(self):
        cols = self.__table__.columns
        fieldNames = [col.name for col in cols]
        return fieldNames + self.foreignKeyRelationFieldNames

    def __repr__(self):
        return '<item {0}>'.format(self.title)

    def updateByDict(self, dictData):
        for name, value in dictData.item_rows():
            setattr(self, name, value)

    def isForeignKeyField(self, name):
        """ 判断是否是一个外键字段 """
        if self.__table__.columns[name].foreign_keys:
            return True
        else:
            return False

    def relationFieldName(self, name):
        """ 返回外键字段对应的关系字段 """
        cols = self.__table__.columns
        relationName = dict(cols)[name].info['relationFieldName']
        return relationName

    def valuesAsDict(self, fieldNames=None):
        names = fieldNames if fieldNames else self.allFieldNames
        values = self.valuesAsList(names)
        return dict(zip(names, values))

    def valuesAsList(self, fieldNames):
        """
        根据字段列表返回相应的值
        :param fieldNames: 字段名称，类型：list
        :return: 字段值，类型: list
        """
        return [self.fieldValue(name) for name in fieldNames]

    def fieldValue(self, fieldName):
        """
        根据字段名称返回其值，关系字段返回其中文字典短名称
        :param fieldName: 字段名称
        :return: 字段值
        """
        value = getattr(self, fieldName, None)
        if fieldName == 'published':
            value = value.strftime("%Y年%m月%d日 %X")
        return value
        # return value.value_short if isinstance(value, ModelCqDict) else value


class MyQueryRss(QueryRss):

    def __init__(self):
        super(MyQueryRss, self).__init__()
        self.engi = rss_engi
        self.sess = rss_sess
        self.base = rss_base

    def init_data(self):
        # base.metadata.drop_all(engi)
        self.base.metadata.create_all(self.engi)
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
        command_datas = [
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

        for data in command_datas:
            self.add_data('command', **data)
        for data in folder_datas:
            self.add_data('folder', **data)
        for data in feed_datas:
            self.add_data('feed', **data)
        for data in node_datas:
            self.add_data('node', **data)
        self.save()

def setup_module(module):
    """ setup any state specific to the execution of the given module."""
    pass


def teardown_module(module):
    """ teardown any state that was previously setup with a setup_module
    method.
    """
    pass


class TestQueries:

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
        self.query = MyQueryRss()
        self.query.init_data()

    @classmethod
    def teardown_class(self):
        """ teardown any state that was previously setup with a call to
        setup_class.
        """
        # if self.need_recover:
        #     shutil.copy(self.bak_db_file, self.src_db_file)
        #     os.remove(self.bak_db_file)

    def test_category_class(self):
        known_value = [type(RssItem), type(RssFolder), type(RssFeed),
                       type(Node), type(RssCommand)]
        texts = ['item', 'feed', 'folder', 'node', 'command']
        result = [type(self.query.category_class(text)) for text in texts]
        assert result == known_value

    """
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
