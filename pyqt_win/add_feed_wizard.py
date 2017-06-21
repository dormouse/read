#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QApplication,
                             QLabel, QLineEdit, QComboBox,
                             QFormLayout, QVBoxLayout,
                             QWizard, QWizardPage)
from pyqt_win.parser import FeedParser
from pyqt_win.queries import QueryRss
import project_conf


class AddFeedWizard(QWizard):
    def __init__(self, folder_id=None):
        super(AddFeedWizard, self).__init__()
        self.addPage(UrlPage())
        self.addPage(DetailPage(parent=None, folder_id=folder_id))

    def accept(self):
        super(AddFeedWizard, self).accept()

    def get_data(self):
        data = dict(
            title=self.field('p_title'),
            url=self.field('p_url'),
            folder_id=self.field('p_folder_id')
        )
        return data


class UrlPage(QWizardPage):
    def __init__(self, parent=None):
        super(UrlPage, self).__init__(parent)
        self.feed_infos = None
        self.setTitle("Add Feed")
        self.setSubTitle("Please fill url field.")

        url_label = QLabel("Url:")
        if project_conf.DEBUG:
            url_line_edit = QLineEdit('http://news.smzdm.com/feed')
        else:
            url_line_edit = QLineEdit()
        self.registerField('url*', url_line_edit)

        form_layout = QFormLayout()
        form_layout.addRow(url_label, url_line_edit)

        self.setLayout(form_layout)

    def validatePage(self):
        url = self.field('url')
        feed = FeedParser(url)
        self.feed_infos = feed.infos()
        if feed.is_parse_success():
            return True
        else:
            self.setSubTitle("Error: Url parser fail! Please check url.")
            return False


class DetailPage(QWizardPage):
    def __init__(self, parent=None, folder_id=None):
        super(DetailPage, self).__init__(parent)
        self.query = QueryRss()
        self.feed_infos = None
        self.setTitle("Feed Detail")
        self.setSubTitle("Please Check the feed detail.")

        form_layout = QFormLayout()

        url_label = QLabel("Url:")
        self.url_line_edit = QLineEdit()
        form_layout.addRow(url_label, self.url_line_edit)

        title_label = QLabel("Title:")
        self.title_line_edit = QLineEdit()
        form_layout.addRow(title_label, self.title_line_edit)

        folder_label = QLabel("Folder:")
        self.folder_combobox = QComboBox()
        rows = self.query.read_data('folder').all()
        for row in rows:
            self.folder_combobox.addItem(row.title, userData=row.id)
        form_layout.addRow(folder_label, self.folder_combobox)
        if folder_id:
            kwargs = dict(id=folder_id)
            folder_title = self.query.read_data('folder', **kwargs).one().title
            self.folder_combobox.setCurrentText(folder_title)

        self.setLayout(form_layout)

        self.registerField('p_url', self.url_line_edit)
        self.registerField('p_title', self.title_line_edit)
        self.registerField('p_folder_id', self.folder_combobox, 'currentData')

    def initializePage(self):
        url = self.field('url')
        feed = FeedParser(url)
        self.feed_infos = feed.infos()
        self.title_line_edit.setText(self.feed_infos.get('title'))
        self.url_line_edit.setText(self.feed_infos.get('href'))


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)

    wizard = AddFeedWizard(0)
    wizard.setWindowTitle("Add Feed Wizard")
    wizard.show()

    sys.exit(app.exec_())
