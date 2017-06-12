#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.sqlite import INTEGER, TEXT, DATETIME, BOOLEAN
from sqlalchemy.orm import column_property, relationship
from sqlalchemy.sql import func
from sqlalchemy import and_
from .database import book_base, rss_base


class BookJob(book_base):
    """ Jobs for book """

    __tablename__ = 'book_job'
    id = Column(INTEGER, primary_key=True)
    type_code = Column(TEXT, ForeignKey('book_dict.code'))
    type = relationship(
        "BookDict",
        primaryjoin="and_(BookJob.type_code==BookDict.code,"
                    "BookDict.name=='job_type')",
        backref='job_type'
    )
    file_name = Column(TEXT)
    url = Column(TEXT)
    create_time = Column(DATETIME, default=datetime.datetime.utcnow)
    last_update = Column(DATETIME, default=datetime.datetime.utcnow)
    status_code = Column(TEXT, ForeignKey('book_dict.code'))
    status = relationship(
        "BookDict",
        primaryjoin="and_(BookJob.status_code==BookDict.code,"
                    "BookDict.name=='job_status')",
        backref='job_status'
    )

    def __init__(self, url):
        self.url = url

    def __repr__(self):
        return 'BookJob %s' % self.url


class BookDict(book_base):
    """ BookDict """

    __tablename__ = 'book_dict'
    id = Column(INTEGER, primary_key=True)
    name = Column(TEXT)
    code = Column(TEXT)
    value = Column(TEXT)


class RssFolder(rss_base):
    __tablename__ = 'rss_folder'
    id = Column(INTEGER, primary_key=True)
    name = Column(TEXT)

    def __init__(self, name):
        self.name = name

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
    folder_id = Column(INTEGER, ForeignKey('rss_folder.id'))
    folder = relationship("RssFolder")

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
