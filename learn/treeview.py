#!/usr/bin/env python

import os
import sys

from PyQt5.QtCore import QAbstractItemModel
from PyQt5.QtCore import (
    Qt, QModelIndex
)
from PyQt5.QtWidgets import QTreeView
from PyQt5.QtWidgets import (QWidget, QPushButton,
                             QApplication, QMainWindow, QVBoxLayout
                             )

try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, \
        QWebEngineSettings
except:
    from PyQt5.QtWebKitWidgets import QWebPage, QWebView

from pyqt_win.models import TreeModel

FULLPATH = os.path.abspath(os.path.dirname(__file__))


class TreeItem(object):
    def __init__(self, data, parent=None):
        self.parentItem = parent
        self.itemData = data
        self.childItems = []

    def appendChild(self, item):
        self.childItems.append(item)

    def removeChild(self, item):
        self.childItems.remove(item)

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def columnCount(self):
        return len(self.itemData)

    def data(self, column):
        try:
            return self.itemData[column]
        except IndexError:
            return None

    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)

        return 0


class TreeModel(QAbstractItemModel):
    def __init__(self, parent=None):
        super(TreeModel, self).__init__(parent)

        self.rootItem = TreeItem(("Title", "Summary"))
        self.setupModelData()

    def columnCount(self, parent):
        if parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return self.rootItem.columnCount()

    def data(self, index, role):
        if not index.isValid():
            return None

        if role != Qt.DisplayRole:
            return None

        item = index.internalPointer()

        return item.data(index.column())

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags

        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.rootItem.data(section)

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

    def removeRows(self, row, count, parent):
        parentItem = self.rootItem
        self.beginRemoveRows(parent, row, row+count-1)
        for i in range(count):
            parentItem.childItems.remove(parentItem.childItems[i])
        self.endRemoveRows()
        return True

    def rowCount(self, parent):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()

    def setupModelData(self):
        self.rootItem.appendChild(TreeItem(("第一个", 10), self.rootItem))
        self.rootItem.appendChild(TreeItem(("第二个", 20), self.rootItem))
        self.rootItem.appendChild(TreeItem(("第三个", 30), self.rootItem))
        self.rootItem.appendChild(TreeItem(("第四个", 40), self.rootItem))

        first = self.rootItem.childItems[0]
        first.appendChild(TreeItem(("第1.1个", 11), first))


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        widget = QWidget()
        self.setCentralWidget(widget)

        model = TreeModel()
        self.view = QTreeView()
        self.view.setModel(model)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.view)

        bt1 = QPushButton("第二个选中")
        bt1.clicked.connect(self.bt1_clicked)
        main_layout.addWidget(bt1)

        bt2 = QPushButton("第三个删除")
        bt2.clicked.connect(self.bt2_clicked)
        main_layout.addWidget(bt2)

        widget.setLayout(main_layout)
        self.view.expandAll()

    def bt1_clicked(self):
        row = 2
        index = self.view.model().index(row - 1, 0, QModelIndex())
        self.view.setCurrentIndex(index)

    def bt2_clicked(self):
        row = 3
        model = self.view.model()

        parent_index = QModelIndex()
        model.removeRows(row,1,parent_index)



if __name__ == '__main__':

    if __name__ == '__main__':
        app = QApplication(sys.argv)
        mainWin = MainWindow()
        mainWin.show()
        sys.exit(app.exec_())
