import copy
import datetime
import logging
import os

from PyQt5.QtCore import (Qt)
from PyQt5.QtGui import (QIcon, QKeySequence)
from PyQt5.QtWidgets import (QLabel, QLineEdit, QAction, QDockWidget,
                             QTextEdit, QWidget, QTableView, QDialog,
                             QMainWindow, QComboBox,
                             QMessageBox, QDialogButtonBox, QPushButton,
                             QVBoxLayout, QGridLayout, QFormLayout)

from pyqt_win.queries import QueryRss


class FeedDialog(QDialog):
    def __init__(self, parent, **kwargs):
        super(FeedDialog, self).__init__(parent)
        self.feed_id = kwargs.get('feed_id')
        self.query = QueryRss()
        # init UI
        formLayout = QFormLayout()
        labelWidget = QLabel("Title:")
        self.titleWidget = QLineEdit()
        formLayout.addRow(labelWidget, self.titleWidget)
        labelWidget = QLabel("Url:")
        self.urlWidget = QLineEdit()
        formLayout.addRow(labelWidget, self.urlWidget)
        labelWidget = QLabel("Folder:")
        self.folderWidget = QComboBox()
        formLayout.addRow(labelWidget, self.folderWidget)
        rows = self.query.folder_rows()
        for row in rows:
            self.folderWidget.addItem(row.name, userData=row.id)

        buttonBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        # buttonBox.button(QDialogButtonBox.Ok).setText('保存')
        # buttonBox.button(QDialogButtonBox.Cancel).setText('取消')
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        mainLayout = QVBoxLayout()
        mainLayout.addLayout(formLayout)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)
        if self.feed_id:
            self.loadData(self.feed_id)
            title = 'Modify New Feed'
        else:
            title = 'Add New Feed'
        self.setWindowTitle(title)

        folder_id = kwargs.get('folder_id')
        if folder_id:
            folder_name = self.query.folder_name(folder_id)
            self.folderWidget.setCurrentText(folder_name)

    def loadData(self, feed_id):
        row = self.query.feed_row(id=feed_id)
        if row:
            self.titleWidget.setText(row.title)
            self.urlWidget.setText(row.url)
            self.folderWidget.setCurrentText(row.folder.name)

    def getData(self):
        title = self.titleWidget.text()
        url = self.urlWidget.text()
        folder_id = self.folderWidget.currentData()
        data = {
            'title': title,
            'folder_id': folder_id,
            'url': url,
        }
        return data
