import logging
import os

from PyQt5.QtCore import (pyqtSignal, QModelIndex )
from PyQt5.QtWidgets import ( QTableView, QTreeView, QMenu )

try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, \
        QWebEngineSettings

except:
    from PyQt5.QtWebKitWidgets import QWebPage, QWebView

import project_conf
FULLPATH = os.path.abspath(os.path.dirname(__file__))

logging.basicConfig(
    format='%(asctime)s %(module)s %(funcName)s %(levelname)s %(message)s',
    level=logging.DEBUG
)


class TreeMenu(QTreeView):
    current_changed = pyqtSignal(object, object)

    def __init__(self, parent=None):
        super(TreeMenu, self).__init__(parent)
        self.log = project_conf.LOG
        self.setHeaderHidden(True)
        self.setRootIsDecorated(False)
        self.setColumnWidth(1, 20)

    def contextMenuEvent(self, event):
        """

        :param event:
        :return:
        """
        """
        All items
            mark all items read
            
        folder
            mark "folder name" read(if exists unread)
            update "folder name"
            rename
            delete
        
        feed
            mark "feed name" read(if exists unread)
            update "feed name"
            rename
            unSubscribe
            
        always on menu
            add folder
            add feed
            update all feeds
        """
        self.log.debug("context Menu Event")
        menu = QMenu(self)
        acts = self.window().action_list
        item = self.current_item()
        model = self.model()

        item_category = item.node.category
        item_title = model.get_title(item)
        item_unread_count = model.get_unread_count(item)

        if item_category == 'command' and item_title == 'load_all_items':
            act = acts['mark_all_feeds_read']
            menu.addAction(act)

        if item_category == 'folder':
            # mark read
            if item_unread_count:
                act = acts['mark_feeds_read']
                act.setText('Mark "{}" Read'.format(item_title))
                menu.addAction(act)
            # update all feeds in folder
            act = acts['update_feeds']
            act.setText('Update All Feeds in "{}"'.format(item_title))
            menu.addAction(act)
            # change folder name
            act = acts['modi_folder']
            menu.addAction(act)
            # delete folder
            act = acts['delete_folder']
            menu.addAction(act)

        if item_category == 'feed':
            # mark read
            if item_unread_count:
                act = acts['mark_feeds_read']
                act.setText('Mark "{}" Read'.format(item_title))
                menu.addAction(act)
            # update feeds
            act = acts['update_feeds']
            act.setText('Update "{}"'.format(item_title))
            menu.addAction(act)
            # modify feed
            act = acts['modi_feed']
            menu.addAction(act)
            # delete feed
            act = acts['delete_feed']
            menu.addAction(act)

        actions = ['add_folder', 'add_feed', 'update_all_feeds']
        for act in actions:
            menu.addAction(acts[act])
        menu.exec_(event.globalPos())

    def load_from_database(self):
        self.model().init_model_data()
        self.expandAll()

    def currentChanged(self, curr_index, prev_index):
        self.log.debug("current changed")
        self.current_changed.emit(curr_index, prev_index)

    def current_item(self):
        index = self.currentIndex()
        if index.isValid():
            item = index.internalPointer()
            return item
        else:
            return None

    def current_feed_ids(self):
        """
        get current tree menu feed ids
        all-> id of all feeds
        folder-> id of all feeds in folder
        feed-> id of feed
        :return: list of feed ids
        """
        feed_ids = []
        item = self.current_item()
        item_type = item.type
        item_data = item.user_data
        query = self.model().query
        if item_type == 'feed':
            feed_ids.append(item_data)
        if item_type == 'folder':
            rows = query.feed_rows(item_data)
            feed_ids = [row.id for row in rows]
        if item_type == 'command' and item_data == 'load_all_items':
            rows = query.feed_rows()
            feed_ids = [row.id for row in rows]
        return feed_ids


class ItemView(QTableView):
    current_changed = pyqtSignal(object, object)

    def __init__(self, parent=None):
        super(ItemView, self).__init__(parent)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableView.SelectRows)

        # self.setSortingEnabled(True)
        # self.sortByColumn(0, Qt.DescendingOrder)
        # self.sortByColumn(0, Qt.AscendingOrder)

    def contextMenuEvent(self, event):
        """

        mark unread/read
        mark all read above
        makr all read blow

        :param event:
        :return:
        """
        pass

    def currentChanged(self, curr_index, prev_index):
        self.current_changed.emit(curr_index, prev_index)

    def update_row(self, index):
        row = index.row()
        model = self.model()
        col_count = model.columnCount()
        for col in range(col_count):
            model_index = model.index(row, col, QModelIndex())
            self.update(model_index)
