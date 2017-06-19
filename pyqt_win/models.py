#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime

from PyQt5.QtCore import QAbstractItemModel, QModelIndex
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QTreeView
from sqlalchemy import desc

import project_conf
from database.database import rss_sess
from database.models import RssItem, Node
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
        self.data = data

    def append_child(self, item):
        self.childItems.append(item)

    def insert_children(self, position, count):
        if position < 0 or position > len(self.childItems):
            return False

        for row in range(count):
            item = TreeItem(None, self)
            self.childItems.insert(position, item)

        return True

    def remove_children(self, start, count):
        if start < 0 or start + count > len(self.childItems):
            return False
        for i in range(count):
            self.childItems.pop(start)
        return True

    def children(self):
        items = []
        items += self.childItems
        for item in self.childItems:
            items += item.children()
        return items

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
        self.data = data


class TreeModel(QAbstractItemModel):
    def __init__(self, parent=None):
        super(TreeModel, self).__init__(parent)
        self.log = project_conf.LOG
        self.sess = rss_sess

        self.rootItem = TreeItem()
        self.header_info = ['title', 'unread']
        self.query = QueryRss()
        self.read_font = None
        self.unread_font = None

        self.init_model_data()

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
            item_data_source_name = self.header_info[index.column()]
            return item.data.get(item_data_source_name)

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

    def make_list_view_query(self, item):
        all_items = [item] + item.children()
        feed_ids = []
        for item in all_items:
            feed_id = self.sess.query(Node.data_id). \
                filter_by(id=item.node.id).scalar()
            feed_ids.append(feed_id)
        query = self.sess.query(RssItem). \
            filter(RssItem.feed_id.in_(feed_ids))
        return query

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
        success = parent_item.remove_children(start, count)
        self.endRemoveRows()
        return success

    def insertRows(self, start, count, parent=QModelIndex()):
        parentItem = self.index_to_item(parent)
        self.beginInsertRows(parent, start, start + count - 1)
        success = parentItem.insert_children(start, count)
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
        self.update_model_data()

    def init_model_data(self):
        self.beginResetModel()
        self.init_model_data_sub()
        self.endResetModel()

    def init_model_data_sub(self, parent_item=None):
        if parent_item:
            parent_id = parent_item.node.id
        else:
            parent_item = self.rootItem
            parent_id = None
        node_rows = self.query.read_node_children_rows(parent_id)
        for node_row in node_rows:
            data = self.query.read_node_row_data(node_row)
            item = TreeItem(data, parent_item)
            parent_item.append_child(item)
            self.init_model_data_sub(item)

    def read_item(self, item, key):
        if key == 'title':
            column = self.header_info.index('title')
            return item.data[column]
        if key == 'unread':
            column = self.header_info.index('unread')
            return item.data[column]
        if key == 'category':
            return item.node.category

    def update_model_data(self, parent_item=None):
        if parent_item:
            parent_id = parent_item.node.id
        else:
            parent_item = self.rootItem
            parent_id = None
        rows = self.sess.query(Node).filter_by(parent_id=parent_id).all()
        for index, row in enumerate(rows):
            row_data = self.get_node_row_data(row)
            data = [row_data.get(col) for col in self.header_info]
            item = parent_item.child(index)
            if item.data != data:
                item.set_data(data)
                item.set_node(row)
                parent_index = self.item_to_index(parent_item)
                col_count = len(self.header_info)
                top_left_index = self.index(index, 0, parent_index)
                bot_right_index = self.index(index, col_count - 1, parent_index)
                self.dataChanged.emit(top_left_index, bot_right_index)
            self.update_model_data(item)


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    model = TreeModel()
    view = QTreeView()
    view.setModel(model)
    view.setWindowTitle("Test Tree Model")
    view.show()
    sys.exit(app.exec_())
