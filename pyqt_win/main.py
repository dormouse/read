import os
import sys

from PyQt5.QtCore import (
    QThread, pyqtSignal, pyqtSlot, QTimer,
    Qt, QUrl, QSettings, QModelIndex, QObject
)
from PyQt5.QtGui import (QIcon)
from PyQt5.QtWidgets import (
    QAction, QApplication, QDockWidget, QLineEdit, QHeaderView,
    QMainWindow, QMessageBox, QInputDialog, QMenu
)

try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, \
        QWebEngineSettings
except:
    from PyQt5.QtWebKitWidgets import QWebPage, QWebView

from pyqt_win.add_feed_wizard import AddFeedWizard
from pyqt_win.queries import QueryRss
from pyqt_win.dialogs import FeedDialog
from pyqt_win.models import ItemListModel, TreeModel
from pyqt_win.views import TreeMenu, ItemView
import project_conf

FULLPATH = os.path.abspath(os.path.dirname(__file__))


class AppOption:
    def __init__(self, config_file=None):
        if config_file:
            self.config_file = config_file
        else:
            self.config_file = os.path.join(FULLPATH, 'config.ini')

        self.conf = QSettings(self.config_file, QSettings.IniFormat)
        if not os.path.exists(self.config_file):
            self.init_default_value()

    def init_default_value(self):
        conf = self.conf

        conf.setValue('preview_timeout', 2000)

        conf.beginGroup('tree_menu')
        conf.setValue('width', 200)
        conf.endGroup()

        conf.beginGroup('view')
        conf.setValue(
            'all',
            {
                'id': dict(label='Id'),
                'author': dict(label='Author'),
                'feed_id': dict(label='Feed Id'),
                'feed': dict(label='Feed'),
                'published': dict(label='Published'),
                'title': dict(label='Title'),
                'summary': dict(label='Summary'),
                'content': dict(label='Content'),
                'is_read': dict(label='Is Read'),
            }
        )
        conf.setValue(
            'item_list',
            [
                dict(name='published', width=200),
                dict(name='title', width=800),
            ]
        )
        conf.endGroup()
        conf.sync()

    def labels(self, names):
        """
        根据名称返回 label
        :param
            names: 一个列表，形如['tfrq', 'fwdw', 'zh'], 'fwdw' 和 'fwdw_code'
            会返回相同的标签
        :return: 一个列表，形如['填发日期', '发文单位', '字号']
        """
        data = self.conf.value('view/all')
        return [data[name]['label'] for name in names]

    def item_list_view_header_labels(self):
        return self.labels(self.item_list_view_col_names())

    def item_list_view_cols(self):
        items = self.conf.value('view/item_list')
        return items

    def item_list_view_col_names(self):
        items = self.conf.value('view/item_list')
        return [item['name'] for item in items] if items else None

    def item_list_view_col_widths(self):
        items = self.conf.value('view/item_list')
        return [item['width'] for item in items] if items else None


class UpdateFeedsWorker(QObject):
    finished = pyqtSignal()
    start_parseing_feed = pyqtSignal(str)

    def __init__(self, feed_ids):
        super(UpdateFeedsWorker, self).__init__()
        self.feed_ids = feed_ids
        # todo: not thread safe
        self.query = QueryRss()

    @pyqtSlot()
    def work_start(self):
        for feed_id in self.feed_ids:
            feed = self.query.feed_row(feed_id)
            self.start_parseing_feed.emit(feed.title)
            self.query.update_feed(feed_id)

        self.finished.emit()


# noinspection PyUnresolvedReferences
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.log = project_conf.LOG
        self.query = QueryRss()
        self.thread = QThread()
        self.option = AppOption()
        self.project_path = project_conf.PROJECT_PATH
        self.config_file = os.path.join(FULLPATH, 'config.ini')
        self.cache_path = os.path.join(FULLPATH, 'cache')
        if not os.path.exists(self.cache_path):
            os.mkdir(self.cache_path)
        self.default_item_index_file = 'index.html'
        self.timer = QTimer()

        if project_conf.DEBUG:
            self.make_debug_database()
        else:
            self.check_database()
        self.create_tree_menu()
        self.create_item_list_view()
        self.create_html_view()
        self.create_actions()
        self.create_menus()
        self.create_tool_bars()
        self.create_status_bar()
        self.create_dock_windows()
        self.create_signals()

        self.setWindowTitle("Rss Hole")
        self.setCentralWidget(self.html_view)
        self.read_settings()

        self.statusBar().showMessage("Ready")

    def add_folder(self):
        text, ok = QInputDialog.getText(self, "Please Input Folder Name",
                                        "Folder Name:", QLineEdit.Normal)
        if ok and text != '':
            self.query.add_folder(text)
            self.query.save()
            self.tree_menu.load_from_database()

    def add_feed(self):
        folder_id = self.tree_menu.folder_id()
        wizard = AddFeedWizard(folder_id)
        wizard.setWindowTitle("Add Feed Wizard")
        wizard.show()

        ok = wizard.exec_()
        if ok:
            data = wizard.get_data()
            self.query.add_feed(**data)
            self.query.save()
            self.tree_menu.load_from_database()
        wizard.destroy()

    def delete_feeds(self):
        """
        delete current tree menu item, item type must be 'feed' or 'folder'
        :return: None

        rowsAboutToBeRemoved(const QModelIndex & parent, int start, int end)

        """
        item = self.tree_menu.current_item()
        item_type = item.type
        item_data = item.user_data
        item_text = item.text

        if item_type not in ['feed', 'folder']:
            return

        msg = 'Are sure to delete {} {}'.format(item_type, item_text)
        reply = QMessageBox.question(
            self, "Confirm", msg, QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            """
            # which item should be current item after delete
            parent_item = item.parent()
            if parent_item.child_count() == 1:
                parent_id = 0
                child_id = parent_item.row()
            else:
                parent_id = item.parent().row()
                if item.row() + 1 == item.parent().child_count():
                    # last child
                    child_id = item.row() - 1
                else:
                    child_id = item.row()
            """

            # deal database data
            if item_type == 'feed':
                self.query.delete_feed(item_data)
            if item_type == 'folder':
                self.query.delete_folder(item_data)
            self.query.save()

            # reload tree menu
            view = self.tree_menu
            model = view.model()
            curr_index = view.currentIndex()
            model.removeRow(curr_index.row(), curr_index.parent())
            model.update_unread_count()

            """
            self.tree_menu.load_from_database()
            model = self.tree_menu.model()
            if parent_id == 0:
                # top item
                parent_index = QModelIndex()
            else:
                parent_index = model.index(parent_id, 0, QModelIndex())
            index = model.index(child_id, 0, parent_index)
            if index.isValid():
                self.tree_menu.setCurrentIndex(index)
            """

    def closeEvent(self, event):
        self.write_settings()
        event.accept()

    def modi_feed(self):
        item = self.tree_menu.current_item()
        item_type = item.type
        item_data = item.user_data
        if item_type == 'feed':
            dlg = FeedDialog(self, feed_id=item_data)
            ok = dlg.exec_()
            if ok:
                data = dlg.getData()
                self.query.modi_feed(item_data, **data)
                self.query.save()
                self.tree_menu.load_from_database()
            dlg.destroy()

    def modi_folder(self):
        item = self.tree_menu.current_item()
        item_type = item.type
        item_data = item.user_data
        item_text = item.text
        if item_type == 'folder':
            new_folder_name, ok = QInputDialog.getText(
                self, "New Folder Name",
                "New Folder Name:",
                QLineEdit.Normal,
                item_text)
            if ok and new_folder_name != '':
                self.query.modi_folder(item_data, new_folder_name)
                self.query.save()
                self.tree_menu.load_from_database()

    def about(self):
        QMessageBox.about(self, "About Rss Hole",
                          "The <b>Rss Hole</b> is a rss reader.")

    def check_database(self):
        db_filename = os.path.join(self.project_path,
                                   'database',
                                   'rss.sqlite')
        if not os.path.exists(db_filename):
            self.query.init_database()
            self.log.debug('new database created')

    def create_action(self, **data):
        triggered = data.get('triggered') if data.get('triggered') \
            else getattr(self, data['name'])
        act = QAction(
            data['text'],
            self,
            triggered=triggered
        )
        if data.get('status_tip'):
            act.setStatusTip(data['status_tip'])
        if data.get('shortcut'):
            act.setShortcut(data['shortcut'])
        if data.get('icon'):
            icon = QIcon(os.path.join(self.project_path,
                                      'static/images',
                                      data['icon']))
            act.setIcon(icon)
        return act

    def create_actions(self):
        pre_actions = [
            dict(
                name='next_item',
                text="&Next Item",
                shortcut="J",
            ),
            dict(
                name='add_folder',
                text='&Add Folder',
                status_tip="Add Rss Folder",
            ),
            dict(
                name='modi_folder',
                text='&Change Folder Name',
            ),
            dict(
                name='delete_folder',
                text='&Delete Folder',
                triggered=self.delete_feeds,
                status_tip="Delete Rss Folder",
            ),
            dict(
                name='add_feed',
                text="&Add Feed",
                status_tip="Add Rss Feed",
            ),
            dict(
                name='delete_feed',
                text="&Delete Feed",
                triggered=self.delete_feeds,
                status_tip="Delete Rss Feed",
            ),
            dict(
                name='mark_feeds_read',
                text="&Mark Feed Read",
            ),
            dict(
                name='mark_all_feeds_read',
                text="&Mark All Read",
                triggered=lambda: self.mark_feeds_read(is_mark_all=True),
            ),
            dict(
                name='modi_feed',
                text="&Modify Feed",
            ),
            dict(
                name='update_feeds',
                text="Update &Feeds",
                triggered=self.update_feeds
            ),
            dict(
                name='update_folder_feeds',
                text="Update &All Feeds In Folder",
                triggered=self.update_feeds
            ),
            dict(
                name='update_all_feeds',
                text="&Update All Feeds",
                shortcut="F5",
                triggered=lambda: self.update_feeds(is_update_all=True),
                icon="update_all.png"
            ),
            dict(
                name='quit',
                text="&Quit",
                shortcut="Ctrl+Q",
                status_tip="Quit the application",
                triggered=self.close
            ),
            dict(
                name='about',
                text="&About",
                status_tip="Show the application's About box",
            ),
            dict(
                name='about_qt',
                text="About &Qt",
                status_tip="Show the Qt library's About box",
                triggered=QApplication.instance().aboutQt
            ),
        ]

        acts = {}
        for item in pre_actions:
            acts[item['name']] = self.create_action(**item)
        self.action_list = acts

    def create_menus(self):
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.action_list['quit'])

        self.viewMenu = self.menuBar().addMenu("&View")

        self.rssMenu = self.menuBar().addMenu("&Rss")
        self.rssMenu.addAction(self.action_list['next_item'])
        self.rssMenu.addAction(self.action_list['mark_all_feeds_read'])
        self.rssMenu.addAction(self.action_list['update_all_feeds'])

        self.menuBar().addSeparator()

        self.helpMenu = self.menuBar().addMenu("&Help")
        self.helpMenu.addAction(self.action_list['about'])
        self.helpMenu.addAction(self.action_list['about_qt'])

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.addAction(self.action_list['about_qt'])
        menu.exec_(event.globalPos())

    def create_status_bar(self):
        pass

    def create_tool_bars(self):
        pass

    def create_tree_menu(self):
        model = TreeModel()
        font = self.font()
        font.setBold(False)
        model.set_read_font(font)
        font = self.font()
        font.setBold(True)
        model.set_unread_font(font)

        view = TreeMenu()
        view.setModel(model)
        view.expandAll()

        self.tree_menu = view

    def create_item_list_view(self):
        model = ItemListModel()
        model.setHeader(self.option.item_list_view_header_labels())
        model.set_col_source(self.option.item_list_view_col_names())
        font = self.font()
        font.setBold(False)
        model.set_read_font(font)
        font = self.font()
        font.setBold(True)
        model.set_unread_font(font)

        view = ItemView()
        view.setModel(model)

        # set column width , ensure title column is stretch
        cols = self.option.item_list_view_cols()
        header = view.horizontalHeader()
        if cols[-1]['name'] == 'title':
            # title is last column
            widths = [col['width'] for col in cols][:-1]
            for index, data in enumerate(widths):
                view.setColumnWidth(index, data)
            header.setStretchLastSection(True)
            # header.setSectionResizeMode(len(widths),
            #                             QHeaderView.Interactive)
        else:
            # title is NOT last column
            header.setStretchLastSection(False)
            for index, col in enumerate(cols):
                if col['name'] == 'title':
                    header.setSectionResizeMode(index, QHeaderView.Stretch)
                else:
                    view.setColumnWidth(index, col['width'])

        self.item_list_view = view

    def create_html_view(self):
        try:
            view = QWebEngineView()
            view.page().settings().setFontSize(
                QWebEngineSettings.DefaultFontSize, 30)
            self.log.debug("Use QWebEngineView")
        except:
            view = QWebView()
            self.log.debug("Use QWebView")
            view.settings().setUserStyleSheetUrl(
                QUrl.fromLocalFile(
                    os.path.join(FULLPATH, "cache/myCustom.css")
                )
            )
            self.log.debug(
                os.path.join(FULLPATH, "cache/myCustom.css")
            )
        self.html_view = view

    def create_dock_windows(self):
        # item list view dock
        dock = QDockWidget("Tree menu", self)
        dock.setObjectName("tree_menu")
        # dock.setAllowedAreas(
        #     Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        dock.setWidget(self.tree_menu)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)
        self.viewMenu.addAction(dock.toggleViewAction())

        # html preview dock
        dock = QDockWidget("Feed items", self)
        dock.setObjectName("feed_items")
        # dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        dock.setWidget(self.item_list_view)
        self.addDockWidget(Qt.TopDockWidgetArea, dock)
        self.viewMenu.addAction(dock.toggleViewAction())

    # noinspection PyUnresolvedReferences
    def create_signals(self):
        self.tree_menu.current_changed.connect(
            self.tree_menu_current_changed)
        self.item_list_view.current_changed.connect(
            self.item_list_view_current_changed)
        self.timer.timeout.connect(self.mark_item_read)

    def load_items(self):
        """
        load items in items list view
        :return:
        """
        query = None
        item = self.tree_menu.current_item()
        self.log.debug(type(item))
        if item:
            item_type = item.type
            item_data = item.user_data
            if item_type == 'command':
                if item_data == 'load_all_items':
                    query = self.query.items_query()
            if item_type == 'feed':
                query = self.query.items_query(feed_id=item_data)
            if item_type == 'folder':
                query = self.query.items_query(folder_id=item_data)

        if query:
            self.item_list_view.model().setQuery(query)

    def show_item_content(self, index):
        """
        show item content in html preview view
        :param index: the index of listview, type:QModelIndex
        :return: None
        """
        data = self.item_list_view.model().read(index)
        self.log.debug(data.content)
        filename = os.path.join(self.cache_path,
                                data.content,
                                self.default_item_index_file)
        self.html_view.load(QUrl.fromLocalFile(filename))
        # self.html_view.setHtml(data.content)
        if not data.is_read:
            # start timer
            settings = AppOption()
            conf = settings.conf
            timeout = int(conf.value("preview_timeout", 2000))
            self.timer.start(timeout)

    def mark_feeds_read(self, is_mark_all=False):
        """
        mark all items of current feed from unread to read

        :return:
        """
        data_changed = False
        if is_mark_all:
            data_changed = self.query.mark_read()
        else:
            item = self.tree_menu.current_item()
            if item:
                if item.type == 'feed':
                    data_changed = self.query.mark_read(
                        feed_id=item.user_data)
                if item.type == 'folder':
                    data_changed = self.query.mark_read(
                        folder_id=item.user_data)
        if data_changed:
            self.tree_menu.model().update_unread_count()
            self.load_items()

    def mark_item_read(self):
        """
        mark current list view item from unread to read
        :return: 
        """
        self.timer.stop()

        # update database
        index = self.item_list_view.currentIndex()
        model_data = self.item_list_view.model().read(index)
        model_data.is_read = True
        self.query.save()

        # update tableview by emit signal
        row = index.row()
        model = self.item_list_view.model()
        col_count = model.columnCount()
        top_left_index = model.index(row, 0, QModelIndex())
        bot_right_index = model.index(row, col_count - 1, QModelIndex())
        model.dataChanged.emit(top_left_index, bot_right_index)

        # update treeview
        self.tree_menu.model().update_unread_count()

    def make_debug_database(self):
        target_db = os.path.join(self.project_path, 'database', 'rss.sqlite')
        debug_db = os.path.join(self.project_path, 'database',
                                'rss_back.sqlite')
        import shutil
        shutil.copy(debug_db, target_db)
        self.log.debug('debug database ready')

    def item_list_view_current_changed(self, curr_index, prev_index):
        self.log.debug("item list current changed ")
        self.show_item_content(curr_index)

    def tree_menu_current_changed(self, curr_index, prev_index):
        self.load_items()

    def update_feeds_end(self):
        self.thread.quit()
        self.tree_menu.model().update_unread_count()
        self.load_items()
        self.statusBar().showMessage('Update done.')

    # noinspection PyUnresolvedReferences
    def update_feeds(self, is_update_all=False):
        self.log.debug("is_update_all %s", is_update_all)
        if is_update_all:
            feed_rows = self.query.feed_rows()
            feed_ids = [row.id for row in feed_rows]
        else:
            feed_ids = self.tree_menu.current_feed_ids()

        self.update_feeds_worker = UpdateFeedsWorker(feed_ids)
        self.update_feeds_worker.start_parseing_feed.connect(
            self.on_start_parseing_feed)
        self.update_feeds_worker.moveToThread(self.thread)
        self.update_feeds_worker.finished.connect(self.update_feeds_end)
        self.thread.started.connect(self.update_feeds_worker.work_start)
        self.thread.start()

    def on_start_parseing_feed(self, feed_title):
        message = 'Updating {0}...'.format(feed_title)
        self.statusBar().showMessage(message)

    def next_item(self):
        cur_index = self.item_list_view.currentIndex()
        next_index = cur_index.row() + 1
        self.item_list_view.setCurrentIndex(
            self.item_list_view.model().index(next_index, cur_index.column())
        )

    def read_settings(self):
        settings = AppOption()
        # for debug
        # settings.init_default_value()
        conf = settings.conf
        if conf.value("geometry"):
            self.restoreGeometry(conf.value("geometry"))
        if conf.value("state"):
            self.restoreState(conf.value("state"))

        # tree menu
        item_id = conf.value("tree_menu_current_item_id")
        if item_id:
            parent_id = int(item_id[:2])
            child_id = int(item_id[-3:])

            model = self.tree_menu.model()
            if parent_id == 0:
                # top item
                parent_index = QModelIndex()
            else:
                parent_index = model.index(parent_id, 0, QModelIndex())
            index = model.index(child_id, 0, parent_index)
            if index.isValid():
                self.tree_menu.setCurrentIndex(index)

    def write_settings(self):
        """ write the settings to config file """
        settings = AppOption()
        conf = settings.conf
        conf.setValue("geometry", self.saveGeometry())
        conf.setValue("state", self.saveState())

        # tree menu
        # save tree menu current item id
        # id is 5 digital string, first 2 is parent item index,
        # if parent item is root item, first 2 is '00'.
        # 3-5 digital is item index.
        item = self.tree_menu.current_item()
        if item:
            item_row = item.row()
            parent_row = item.parent().row()
            item_id = "{:0>2d}{:0>3d}".format(parent_row, item_row)
        else:
            item_id = None
        conf.setValue('tree_menu_current_item_id', item_id)

        # item list view
        # item list view width
        col_names = settings.item_list_view_col_names()
        conf.beginGroup('view')
        list_setting = [
            dict(
                name=data,
                width=self.item_list_view.columnWidth(index)
            )
            for index, data in enumerate(col_names)
        ]
        conf.setValue('item_list', list_setting)
        conf.endGroup()

        # wirte conf
        conf.sync()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())
