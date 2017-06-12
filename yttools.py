#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Name:         yttools.py
# Version:      0.2
# Purpose:      工具和自定义控件
# Author:       Dormouse.Young
# Created:      2016-05-03
# LastModify    2016-08-31
# Copyright:    Dormouse.Young
# Licence:      GPL V3.0
# ---------------------------------------------------------------------------

from PyQt5.QtCore import (Qt, QSortFilterProxyModel, QModelIndex, QAbstractTableModel)
from PyQt5.QtGui import (
    QFont,
)
import datetime
import hashlib
import logging
import json
import os
import platform
import re
import subprocess
from functools import reduce
from urllib.parse import urlparse

# import httplib2
# from bs4 import BeautifulSoup
# from jinja2 import Template

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)s %(levelname)s %(message)s')


"""
class YtTools():
    def __init__(self):
        self.logger = logging.getLogger(__name__)

        timeout = 20  # second
        self.http = httplib2.Http('.cache', timeout=timeout)

    def download(self, url):
        self.logger.info("start download:%s", url)
        try:
            response, content = self.http.request(url)
        except Exception as e:
            self.logger.error("download fail:%s", url)
            self.logger.error(e)
            return None

        if response.status == 200:
            return content
        else:
            return None

"""
class SqlModel(QAbstractTableModel):
    def __init__(self, **kwargs):
        parent = kwargs.get('parent')
        super(SqlModel, self).__init__(parent)
        self.log = logging.getLogger(__name__)
        self.rows = []
        self.rowPerPage = 10  # 默认每次读取 10 条记录
        self.totalRowCount = 0
        self.query = None

    def setHeader(self, datas):
        self.headers = datas

    def setRowPerPage(self, count=10):
        """ 设置每次读取的记录数
        参数：
            count; 每次读取的记录数，默认值为 10 ，类型为 int 。
        """
        self.rowPerPage = count

    def setQuery(self, query=None):
        """
        设置模型的 query ，如果 query 为 None ，那么相当于初始化模型中的数据

        :param query:
        :return:
        """
        self.beginResetModel()
        if query:
            self.query = query
        self.rows = []
        self.totalRowCount = self.getTotalRowCount()
        self.endResetModel()

    def getTotalRowCount(self):
        """
        得到总的行数，如果字段数据不多则不用重载，
        如果字段数据太多，则影响速度，应当重载以加速
        """
        return self.query.count()

    def rowCount(self, QModelIndex_parent=None, *args, **kwargs):
        return len(self.rows)

    def headerData(self, p_int, Qt_Orientation, int_role=None):
        if int_role == Qt.DisplayRole:
            if Qt_Orientation == Qt.Horizontal:
                return self.headers[p_int]
            # if Qt_Orientation == Qt.Vertical:
            #     return p_int + 1

        return super(SqlModel, self).headerData(p_int, Qt_Orientation, int_role)

    def columnCount(self, QModelIndex_parent=None, *args, **kwargs):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if index.row() >= self.totalRowCount or index.row() < 0:
            return None
        if role == Qt.DisplayRole:
            source = self.colSource[index.column()]
            data = getattr(self.rows[index.row()], source)
            return data
        return None

    def canFetchMore(self, QModelIndex):
        return len(self.rows) < self.totalRowCount

    def fetchMore(self, index):
        remainder = self.totalRowCount - len(self.rows)
        itemsToFetch = min(self.rowPerPage, remainder)
        self.beginInsertRows(QModelIndex(), len(self.rows), len(self.rows) + itemsToFetch - 1)
        self.rows = self.fetchRows(len(self.rows) + itemsToFetch)
        self.endInsertRows()

    def fetchRows(self, offset):
        rows = self.query[:offset]
        return rows

class SortFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, **kwargs):
        parent = kwargs.get('parent')
        super(SortFilterProxyModel, self).__init__(parent)

    # Work around the fact that QSortFilterProxyModel always filters datetime
    # values in QtCore.Qt.ISODate format, but the tree views display using
    # QtCore.Qt.DefaultLocaleShortDate format.
    def filterAcceptsRow(self, sourceRow, sourceParent):
        # self.log.debug('self.rowCount:%s', self.rowCount())
        # self.log.debug('source rowCount:%s', self.sourceModel().rowCount())
        # self.log.debug(sourceRow)
        dateCol = 999
        # Do we filter for the date column?
        if self.filterKeyColumn() == dateCol:
            # Fetch datetime value.
            index = self.sourceModel().index(sourceRow, dateCol, sourceParent)
            data = self.sourceModel().data(index)

            # Return, if regExp match in displayed format.
            return (self.filterRegExp().indexIn(data.toString(Qt.DefaultLocaleShortDate)) >= 0)

        # Not our business.
        return super(SortFilterProxyModel, self).filterAcceptsRow(sourceRow, sourceParent)

class DictClass():
    """ covert dict to class """

    def __init__(self, **mydict):
        for k, v in mydict.items():
            if isinstance(v, dict):
                mydict[k] = DictClass(**v)
        self.__dict__.update(mydict)


class Option():
    def __init__(self, option_file='conf.json'):
        self.log = logging.getLogger(__name__)
        self.option_file = option_file
        self.read()

    def read(self):
        """ read data from file """
        try:
            with open(self.option_file, 'r', encoding="utf-8") as f:
                self.to_class(json.load(f))
        except Exception as e:
            self.log.warning('load config file error, use default config')
            self.log.warning(e)
            self.init_default()

    def to_class(self, mydict):
        dc = DictClass(**mydict)
        self.__dict__.update(dc.__dict__)

    def to_dict(self, myclass):
        mydict = {}
        mydict.update(myclass.__dict__)
        for k, v in mydict.items():
            if k == 'option_file':
                pass
            else:
                if isinstance(v, DictClass):
                    mydict[k] = self.to_dict(v)
        return mydict

    def get_default(self):
        # globe
        globe = {
            'width': 1000,
            'height': 690,
            'x': 0,
            'y': 0
        }
        default_dict = {'globe': globe}
        return default_dict

    def save(self):
        with open(self.option_file, 'w', encoding="utf-8") as f:
            mydict = self.to_dict(self)
            for key in ['option_file', 'log']:
                del mydict[key]
            json.dump(mydict, f, ensure_ascii=False)

    def init_default(self):
        self.to_class(self.get_default())
        self.save()
