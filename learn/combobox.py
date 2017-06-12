#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import copy
import datetime
import logging
import os
import sys

from PyQt5.QtCore import (Qt)
from PyQt5.QtGui import (QIcon, QKeySequence)
from PyQt5.QtWidgets import (QLabel, QLineEdit, QAction, QDockWidget,
                             QTextEdit, QWidget, QTableView, QDialog,
                             QMainWindow, QComboBox, QApplication,
                             QMessageBox, QDialogButtonBox, QPushButton,
                             QVBoxLayout, QGridLayout, QFormLayout)
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        cb = QComboBox()
        cb.addItem('first', 1)
        cb.addItem('second', 3)
        cb.addItem('third', 9)
        self.setCentralWidget(cb)
        cb.setCurrentIndex(2)

        cb.currentIndexChanged.connect(self.curr_index_changed)
        self.cb = cb

    def curr_index_changed(self, index):
        print("index:", index)
        print("curr_data:", self.cb.currentData())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())