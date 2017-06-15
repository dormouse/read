#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime

from PyQt5.QtCore import QAbstractItemModel, QModelIndex
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QTreeView
from sqlalchemy import desc

import project_conf
from database.models import RssItem
from pyqt_win.queries import QueryRss
from yttools import SqlModel


class ItemListModel(SqlModel):
    def __init__(self, parent=None):
        super(ItemListModel, self).__init__(parent=parent)
        self.setRowPerPage(50)
        self.col_source = None
        self.read_font = None
        self.unread_font = None

    def set_col_source(self, source):
        self.col_source = source

    def set_read_font(self, font):
        self.read_font = font

    def set_unread_font(self, font):
        self.unread_font = font

    def setQuery(self, query=None):
        """
        设置模型的 query ，如果 query 为 None ，那么相当于初始化模型中的数据

        :param query:
        :return:
        """
        self.beginResetModel()
        if query:
            # default add order for item list view
            self.query = query.order_by(desc(RssItem.published))
        self.rows = []
        self.totalRowCount = self.getTotalRowCount()
        self.endResetModel()

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if index.row() >= self.totalRowCount or index.row() < 0:
            return None

        if role == Qt.DisplayRole:
            source = self.col_source[index.column()]
            data = getattr(self.read(index), source)
            if source == 'published':
                if datetime.datetime.date(data) == datetime.date.today():
                    data = data.strftime("%X")
                else:
                    data = data.strftime("%Y-%m-%d")
            return data

        if role == Qt.FontRole:
            row = self.read(index)
            return self.read_font if row.is_read else self.unread_font

        return None

    def read(self, index):
        data = self.query[index.row()]
        return data


class TreeItem(object):
    def __init__(self, data=None, parent=None):
        self.log = project_conf.LOG

        self.parentItem = parent
        self.childItems = []
        self.data = None
        if data:
            self.set_data(data)

    def append_child(self, item):
        self.childItems.append(item)

    def insertChildren(self, position, count):
        if position < 0 or position > len(self.childItems):
            return False

        for row in range(count):
            item = TreeItem(None, self)
            self.childItems.insert(position, item)

        return True

    def removeChildren(self, start, count):
        if start < 0 or start + count > len(self.childItems):
            return False
        for i in range(count):
            self.childItems.pop(start)
        return True

    def child(self, row):
        return self.childItems[row]

    def child_count(self):
        return len(self.childItems)

    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)
        return 0

    def set_data(self, data):
        # todo: check data keys
        self.data = data
        for k, v in data.items():
            setattr(self, k, v)


class TreeModel(QAbstractItemModel):
    def __init__(self, parent=None):
        super(TreeModel, self).__init__(parent)
        self.log = project_conf.LOG

        self.rootItem = None
        self.header_info = ['text', 'unread']
        self.query = QueryRss()
        self.read_font = None
        self.unread_font = None

        self.init_model_data()
        self.update_unread_count()

    def set_read_font(self, font):
        self.read_font = font

    def set_unread_font(self, font):
        self.unread_font = font

    def columnCount(self, parent=QModelIndex()):
        return len(self.header_info)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if role != Qt.DisplayRole:
            return None

        item = index.internalPointer()
        if role == Qt.FontRole:
            return self.unread_font if item.unread else self.read_font
        if item.data:
            return item.data.get(self.header_info[index.column()])
        else:
            return None

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags

        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header_info[section]

        return None

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent()

        if parentItem == self.rootItem:
            return QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.child_count()

    def index_to_item(self, index):
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item
        return self.rootItem

    def item_to_index(self, item):
        return self.createIndex(item.row(), 0, item)

    def removeRows(self, start, count, parent=QModelIndex()):
        parent_item = self.index_to_item(parent)
        self.beginRemoveRows(parent, start, start + count - 1)
        success = parent_item.removeChildren(start, count)
        self.endRemoveRows()
        return success

    def insertRows(self, start, count, parent=QModelIndex()):
        parentItem = self.index_to_item(parent)
        self.beginInsertRows(parent, start, start + count - 1)
        success = parentItem.insertChildren(start, count)
        self.endInsertRows()
        return success

    def find_folder_item(self, folder_id):
        item = None
        folder_items = self.rootItem.childItems
        for folder_item in folder_items:
            if folder_item.user_data == folder_id:
                item = folder_item
        return item

    def add_item(self, item_type, curr_index, **kwargs):
        if item_type not in ('folder', 'feed'):
            self.log.error("item type not in ('folder, 'feed')")
            return

        if item_type == 'folder':
            folder_name = kwargs['item_text']
            # write data to database
            self.query.add_folder(folder_name)
            self.query.save()
            # add tree menu item
            if curr_index.isValid():
                curr_item = curr_index.internalPointer()
                if curr_item.type == 'feed':
                    curr_index = curr_index.parent()
                start = curr_index.row()
            else:
                start = self.rootItem.child_count() - 1
            if self.insertRow(start, curr_index.parent()):
                folder_id = self.query.folder_id(folder_name)
                data = {
                    'text': folder_name,
                    'type': 'folder',
                    'user_data': folder_id,
                    'unread': 0
                }
                item = self.rootItem.childItems[start]
                item.set_data(data)
        else:
            # add feed
            # kwargs should be {title=,url= ,folder_id=}
            folder_id = kwargs['folder_id']
            # write data to database
            self.query.add_feed(**kwargs)
            self.query.save()

            # add tree menu item
            parent_item = self.find_folder_item(folder_id)
            parent_index = self.item_to_index(parent_item)
            start = parent_item.child_count() - 1
            if curr_index.isValid():
                curr_item = curr_index.internalPointer()
                if curr_item.type == 'feed':
                    self.log.debug("current item is a feed")
                    if curr_item.parent() == parent_item:
                        self.log.debug("current item's parent same")
                        start = curr_index.row()
            self.log.debug(
                "start insert row, start:{}, parent title:{}".format(
                    start, parent_item.text))
            if self.insertRow(start, parent_index):
                self.log.debug("insert row success")
                feed_id = self.query.feed_row(**kwargs).id
                data = {
                    'text': kwargs['title'],
                    'type': 'feed',
                    'user_data': feed_id,
                    'unread': 0
                }
                item = parent_item.childItems[start]
                item.set_data(data)

    def delete_item(self, index):
        item = index.internalPointer()
        if item:
            item_type = item.type
            item_data = item.user_data
        else:
            return

        # delete database data
        if item_type == 'feed':
            self.query.delete_feed(item_data)
        if item_type == 'folder':
            self.query.delete_folder(item_data)
        self.query.save()

        # remove model item
        self.removeRow(index.row(), index.parent())
        self.update_unread_count()

    def init_model_data(self):
        self.beginResetModel()
        root_item_data = {
            'text': 'root',
            'type': None,
            'user_data': None,
            'unread': 'unread'
        }
        self.rootItem = TreeItem(root_item_data)

        # command
        datas = [
            {
                'text': 'ALL',
                'type': 'command',
                'user_data': 'load_all_items',
                'unread': 0
            },
        ]
        for data in datas:
            self.rootItem.append_child(TreeItem(data, self.rootItem))

        # folder
        rows = self.query.folder_rows()
        for row in rows:
            data = {
                'text': row.name,
                'type': 'folder',
                'user_data': row.id,
                'unread': 0
            }
            item = TreeItem(data, self.rootItem)
            self.rootItem.append_child(item)
            self.init_model_data_feed(item, row.id)

        self.endResetModel()

        # update unread count
        self.update_unread_count()

    def init_model_data_feed(self, parent_item, folder_id):
        rows = self.query.feed_rows(folder_id)
        for row in rows:
            data = {
                'text': row.title,
                'type': 'feed',
                'user_data': row.id,
                'unread': 0
            }
            item = TreeItem(data, parent_item)
            parent_item.append_child(item)

    def update_unread_count(self):
        for child in self.rootItem.childItems:
            self.update_unread_count_item(child)
            if child.type == 'folder':
                for feed in child.childItems:
                    self.update_unread_count_item(feed)

    def update_unread_count_item(self, item):
        unread = 0

        if item.type == 'command':
            if item.user_data == 'load_all_items':
                unread = self.query.items_count(is_read=False)
        if item.type == 'feed':
            unread = self.query.items_count(is_read=False,
                                            feed_id=item.user_data)
        if item.type == 'folder':
            unread = self.query.items_count(is_read=False,
                                            folder_id=item.user_data)

        if item.unread != unread:
            # update item data
            data = item.data
            data['unread'] = unread
            item.set_data(data)
            # Follow line is wrong!!
            # item.unread = unread

            # emit signal
            if item.parent() == self.rootItem:
                parent_index = QModelIndex()
            else:
                parent_index = self.index(item.parent().row(), 0, QModelIndex())
            row = item.row()
            col_count = self.columnCount(parent_index)
            top_left_index = self.index(row, 0, parent_index)
            bot_right_index = self.index(row, col_count - 1, parent_index)
            self.dataChanged.emit(top_left_index, bot_right_index)


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    model = TreeModel()
    view = QTreeView()
    view.setModel(model)
    view.setWindowTitle("Test Tree Model")
    view.show()
    sys.exit(app.exec_())
