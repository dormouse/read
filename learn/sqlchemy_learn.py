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
    title = Column(TEXT)
    command = Column(TEXT)

    def __repr__(self):
        return "Commander:{}".format(self.title)


class RssFolder(rss_base):
    __tablename__ = 'rss_folder'
    id = Column(INTEGER, primary_key=True)
    title = Column(TEXT)

    def __repr__(self):
        return "folder:{}".format(self.title)


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


if __name__ == '__main__':
    query = MyQueryRss()
    query.init_data()
    sess = query.sess
    new_query = sess.query(Node, RssFeed)
    new_query = new_query.join(RssFeed, Node.data_id == RssFeed.id)
    new_query = new_query.filter(Node.category == 'feed')
    print(new_query.all())
    row = new_query.first()
    n, f = row
    print(n.id)
    print(f.title)
