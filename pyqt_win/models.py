#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime

from PyQt5.QtCore import QAbstractItemModel, QModelIndex
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QTreeView
from sqlalchemy import desc

import project_conf
from database.database import rss_sess
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

    def reload(self, node_id):
        query = QueryRss().node_items_query(node_id)
        self.setQuery(query)

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
    def __init__(self, parent=None, **kwargs):
        self.log = project_conf.LOG
        self.parentItem = parent
        self.childItems = []
        self.set_value(**kwargs)

    def append_child(self, item):
        self.childItems.append(item)

    def insert_children(self, position, count):
        if position < 0 or position > len(self.childItems):
            return False

        for row in range(count):
            item = TreeItem(self)
            self.childItems.insert(position, item)

        return True

    def remove_children(self, start, count):
        if start < 0 or start + count > len(self.childItems):
            return False
        for i in range(count):
            self.childItems.pop(start)
        return True

    def children(self):
        """
        all children, include children of children
        :return:
        """
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

    def set_value(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def read(self, key):
        if key in ['category', 'data_id', 'id']:
            node = getattr(self, 'node')
            if node:
                return getattr(node, key, None)
            else:
                return None
        if key in ['title', ]:
            node_link = getattr(self, 'node_link')
            if node_link:
                return getattr(node_link, key, None)
            else:
                return None
        if key in ['unread', ]:
            data = getattr(self, 'data')
            if data:
                return data.get(key)
            else:
                return None
        return None


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

        item_data_source_name = self.header_info[index.column()]
        return item.read(item_data_source_name)

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags

        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    # def get_node_id(self, index):
    #     if index.isValid():
    #         item = self.index_to_item(index)
    #         return item.node.id
    #     else:
    #         return None

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
        # if parent.column() > 0:
        #     return 0

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.child_count()

    def index_to_item(self, index):
        if index.isValid():
            return index.internalPointer()
        else:
            return self.rootItem

    def item_to_index(self, item):
        if item == self.rootItem:
            return QModelIndex()
        else:
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

    def feed_ids(self, parent_item):
        """
        get all feed ids belong item, include item itself

        :param
        :return: a list of ids
        """
        items = [parent_item, ] + parent_item.children()
        ids = []
        for item in items:
            category = item.read('category')
            if category == 'feed':
                ids.append(item.read('data_id'))
        return ids

    def find_folder_item(self, folder_id):
        item = None
        folder_items = self.rootItem.childItems
        for folder_item in folder_items:
            if folder_item.user_data == folder_id:
                item = folder_item
        return item

    def prepare_add_feed(self, folder_id, curr_index):
        """
        for add_item function
        :param folder_id:
        :param curr_index:
        :return: start, parent item
        """
        self.log.debug('folder_id:{}, curr_index row:{}'.format(
            folder_id, curr_index.row()))
        # find folder item by folder id
        folder_item = self.rootItem
        folder_node_id = self.query.node_id_folder_id(folder_id)
        if folder_node_id:
            all_items = self.rootItem.children()
            for item in all_items:
                if item.node.id == folder_node_id:
                    folder_item = item
        # get parent item of current item
        if curr_index.isValid():
            parent_index = curr_index.parent()
            parent_item = self.index_to_item(parent_index)
        else:
            parent_item = None
        # compare folder item and parent item
        if folder_item == parent_item:
            start = curr_index.row()
        else:
            parent_item = folder_item
            start = parent_item.child_count() - 1
        self.log.debug("start:{}, parent_item row:{}".format(
            start, parent_item.row()))
        return start, parent_item

    def prepare_add_folder(self, curr_index):
        """
        for add_item function
        :param curr_index:
        :return: start, parent item
        """
        if curr_index.isValid():
            start = curr_index.row()
            parent_index = curr_index.parent()
            parent_item = self.index_to_item(parent_index)
        else:
            start = self.rootItem.child_count() - 1
            parent_item = self.rootItem
        return start, parent_item

    def add_item(self, category, curr_index, **kwargs):
        # check category
        if category not in ('folder', 'feed'):
            self.log.error("item type not in ('folder, 'feed')")
            return

        # add a TreeItem
        if category == 'feed':
            start, parent_item = self.prepare_add_feed(
                kwargs['folder_id'], curr_index)
            del (kwargs['folder_id'])
        else:
            start, parent_item = self.prepare_add_folder(curr_index)
        # if parent item have no child ,start will be -1, so fix it
        start = 0 if start < 0 else start
        parent_index = self.item_to_index(parent_item)
        if not self.insertRow(start, parent_index):
            msg = "Insert Row Fail! start:{}, parent index row:{}".format(
                start, parent_index.row())
            self.log.error(msg)
            return

        item = parent_item.childItems[start]

        # write data to database
        # write data to table of folder or feed
        data_id = self.query.add_data(category, **kwargs)
        # write data to table node
        parent_id = parent_item.read('id')
        kwargs = dict(
            parent_id=parent_id,
            category=category,
            data_id=data_id
        )
        node_id = self.query.add_data('node', **kwargs)

        # set tree item data
        node_row = self.query.node_row(node_id)
        node_row_value = self.query.node_row_value(node_row)
        self.modi_item_data(item, **node_row_value)

        # reorder, write data to database node
        children = item.parent().childItems
        for index, child in enumerate(children):
            child.node.rank = index
        self.query.save()
        # print all node
        # for row in self.query.category_query('node'):
        #     print(row.id, row.category, row.data_id)

    def init_model_data(self, parent_item=None):
        if parent_item:
            parent_id = parent_item.node.id
        else:
            parent_item = self.rootItem
            parent_id = None
        node_rows = self.query.node_children_rows(parent_id)
        for node_row in node_rows:
            node_row_value = self.query.node_row_value(node_row)
            item = TreeItem(parent_item, **node_row_value)
            parent_item.append_child(item)
            self.init_model_data(item)

    def read_item(self, item, key):
        if item == self.rootItem:
            return None
        if key in ['category', 'data_id', 'id']:
            return getattr(item.node, key, None)
        if key in ['title', ]:
            return getattr(item.node_link, key, None)
        if key in ['unread', ]:
            return item.data.get(key)
        return None

    def update_model_data(self, parent_item=None):
        if not parent_item:
            parent_item = self.rootItem

        for child in parent_item.childItems:
            node_row_value = self.query.node_row_value(child.node)
            self.modi_item_data(child, **node_row_value)
            self.update_model_data(child)

    def modi_item_data(self, item, **node_row_value):
        changed = False
        for k, v in node_row_value.items():
            if getattr(item, k, None) != v:
                changed = True
                setattr(item, k, v)
        if changed:
            # emit signal
            parent_item = item.parent()
            parent_index = self.item_to_index(parent_item)
            col_count = len(self.header_info)
            row = item.row()
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
