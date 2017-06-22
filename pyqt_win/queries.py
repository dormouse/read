import os

import feedparser

from database.database import rss_sess, rss_base, rss_engi
from database.models import Node, RssFeed, RssFolder, RssItem, RssCommand
from pyqt_win.parser import ItemParser
import project_conf

FULLPATH = os.path.abspath(os.path.dirname(__file__))


class QueryRss(object):
    def __init__(self):
        self.log = project_conf.LOG

        self.engi = rss_engi
        self.sess = rss_sess
        self.base = rss_base

        self.log = project_conf.LOG
        self.cache_path = os.path.join(FULLPATH, 'cache')
        self.default_item_index_file = 'index.html'

    def feed_rows(self, folder_id=None):
        if folder_id:
            rows = self.sess.query(RssFeed). \
                filter(RssFeed.folder_id == folder_id).all()
        else:
            rows = self.sess.query(RssFeed).all()
        return rows

    def feeds_query(self, **kwargs):
        query = self.sess.query(RssFeed)
        for key, value in kwargs.items():
            query = query.filter(getattr(RssFeed, key) == value)
        return query

    def feed_row(self, **kwargs):
        """
        get first feed row
        :param feed_id:
        :return:
        """
        query = self.feeds_query(**kwargs)
        return query.first()

    def feed_url(self, feed_id):
        url = self.sess.query(RssFeed.url).filter(
            RssFeed.id == feed_id).scalar()
        return url

    def folder_rows(self):
        rows = self.sess.query(RssFolder).all()
        return rows

    def folder_row(self, folder_id):
        row = self.sess.query(RssFolder). \
            filter(RssFolder.id == folder_id).first()
        return row

    def folder_name(self, folder_id):
        name = self.sess.query(RssFolder.name). \
            filter(RssFolder.id == folder_id).scalar()
        return name

    def folder_id(self, folder_name):
        folder_id = self.sess.query(RssFolder.id). \
            filter(RssFolder.name == folder_name).scalar()
        return folder_id

    def category_class(self, category):
        categories = ['node', 'folder', 'feed', 'item', 'command']
        if category not in categories:
            self.log.error(
                "category error: {} not in ['node', 'folder', "
                "'feed', 'item', 'command']".format(category)
            )
            return None
        if category == 'item':
            obj_class = RssItem
        elif category == 'feed':
            obj_class = RssFeed
        elif category == 'folder':
            obj_class = RssFolder
        elif category == 'node':
            obj_class = Node
        elif category == 'command':
            obj_class = RssCommand
        return obj_class

    def category_query(self, category):
        query = None
        obj_class = self.category_class(category)
        if obj_class:
            query = self.sess.query(obj_class)
        return query

    def add_data(self, category_text, **kwargs):
        obj_class = self.category_class(category_text)
        if obj_class:
            obj = obj_class()
            for k, v in kwargs.items():
                if hasattr(obj, k):
                    setattr(obj, k, v)
            self.sess.add(obj)
            self.save()
            return obj.id
        else:
            return None

    def read_data(self, category, **kwargs):
        obj_class = self.category_class(category)
        if obj_class:
            query = self.sess.query(obj_class)
            for key, value in kwargs.items():
                query = query.filter(
                    getattr(obj_class, key) == value
                )
            return query
        else:
            return None

    def node_all_children(self, node):
        """
        :param node: a database.models.Node object
        :return:
            all_children: a database.models.Node object list ,
                          include node and all children of node recursively
        """
        all_children = [node, ]
        for child in node.children:
            all_children += self.node_all_children(child)
        return all_children

    def node_children_rows(self, parent_id):
        kwargs = dict(parent_id=parent_id)
        node_rows = self.read_data('node', **kwargs).all()
        return node_rows

    def node_row(self, node_id):
        return self.sess.query(Node).get(node_id)

    def node_id_folder_id(self, folder_id):
        """
        folder id --> node id
        :param folder_id:
        :return:
        """
        query = self.sess.query(Node). \
            filter_by(category='folder'). \
            filter_by(data_id=folder_id)
        row = query.first()
        if row:
            return row.id
        else:
            return None

    def node_row_data(self, node_row):
        cate_query = self.category_query(node_row.category)
        row = cate_query.filter_by(id=node_row.data_id).one()
        # title
        title = row.title
        # unread count
        item_query = self.node_items_query(node_row.id)
        item_query = item_query.filter_by(is_read=False)
        unread = item_query.count()
        # return data
        data = dict(title=title, unread=unread)
        return data

    def node_items_query(self, node_id):
        """

        :param node_id:
        :return: None or
                 query of all RssItem object of node_id
        """
        row = self.node_row(node_id)
        if row.category == 'command':
            command_row = self.sess.query(RssCommand). \
                filter_by(id=row.data_id).one()
            if command_row.title == 'ALL':
                query = self.sess.query(RssItem)
                return query
            else:
                return None
        else:
            # get all nodes include row and row's all children
            nodes = self.node_all_children(row)
            # get all feed ids
            feed_ids = []
            for node in nodes:
                if node.category == 'feed':
                    feed_ids.append(node.data_id)
            # make query
            query = self.sess.query(RssItem).filter(
                RssItem.feed_id.in_(feed_ids))
            return query

    def modi_data(self, category, filter_value, new_value):
        query = self.read_data(category, **filter_value)
        if query:
            query.update(new_value)

    def dele_data(self, category, **kwargs):
        query = self.read_data(category, **kwargs)
        if query:
            query.delete()

    def delete_feed(self, feed_id):
        # delete feed's item
        items = self.item_rows(feed_id=feed_id)
        for item in items:
            self.sess.delete(item)
        # map(self.sess.delete, items)
        # delete feed
        feed = self.feed_row(id=feed_id)
        self.sess.delete(feed)

    def delete_folder(self, folder_id):
        feeds = self.feed_rows(folder_id)
        feed_ids = [feed.id for feed in feeds]
        for feed_id in feed_ids:
            self.delete_feed(feed_id)
        folder = self.folder_row(folder_id)
        self.sess.delete(folder)

    def item_rows(self, **kwargs):
        query = self.items_query(**kwargs)
        return query.all()

    def items_count(self, **kwargs):
        query = self.items_query(**kwargs)
        return query.count()

    def items_query(self, **kwargs):
        query = self.sess.query(RssItem)
        for key, value in kwargs.items():
            if key == 'folder_id':
                query = query.join(RssFeed). \
                    filter(RssFeed.folder_id == value)
            else:
                query = query.filter(getattr(RssItem, key) == value)
        return query

    def is_item_existed(self, **kwargs):
        """
        only compare title and publish_time
        :param kwargs must have title and publish_time 
        :return: 
        """
        query_data = {
            'title': kwargs['title'],
            'published': kwargs['published']
        }
        query = self.items_query(**query_data)
        return True if query.count() else False

    def modi_feed(self, feed_id, **kwargs):
        feed_row = self.feed_row(id=feed_id)
        for k, v in kwargs.items():
            if hasattr(feed_row, k):
                setattr(feed_row, k, v)

    def modi_folder(self, folder_id, new_folder_name):
        row = self.folder_row(folder_id)
        row.name = new_folder_name

    def save(self):
        self.sess.commit()

    def init_database(self):
        self.base.metadata.create_all(self.engi)
        # some default rss feed
        command_datas = [
            dict(title="ALL",
                 command="load_all_items"),
        ]
        folder_datas = [
            dict(title="Apple"),
        ]
        feed_datas = [
            dict(title='少数派', url='http://sspai.me/feed'),
            dict(title='Mac玩儿法', url='http://www.waerfa.com/feed'),
            dict(title='SMZDM', url='http://feed.smzdm.com'),
        ]
        node_datas = [
            dict(parent_id=None, category='command',
                 data_id=1, rank=0),
            dict(parent_id=None, category='folder',
                 data_id=1, rank=1),
            dict(parent_id=2, category='feed',
                 data_id=1, rank=0),
            dict(parent_id=2, category='feed',
                 data_id=2, rank=1),
            dict(parent_id=None, category='feed',
                 data_id=3, rank=2),
        ]

        for data in command_datas:
            self.add_data('command', **data)
        for data in folder_datas:
            self.add_data('folder', **data)
        for data in feed_datas:
            self.add_data('feed', **data)
        for data in node_datas:
            self.add_data('node', **data)
        self.save()

    def update_feed(self, feed_id):
        feed = self.feed_row(id=feed_id)
        url = feed.url
        feed_data = feedparser.parse(url)
        if feed_data['bozo'] == 1:
            # todo present in tree menu
            self.log.warning("{} parse fail!".format(feed.url))
            return
        else:
            item_datas = [
                self.parse_feed_item(feed_id, url, item) \
                for item in feed_data['items']
            ]
            if item_datas:
                self.save_item_datas(item_datas)

    def parse_feed_item(self, feed_id, feed_url, item):
        parser = ItemParser(feed_id, feed_url, item)
        data = parser.get_data()
        return data

    def save_item_datas(self, datas):
        need_save = False
        for data in datas:
            db_data = data['db']
            file_data = data['file']
            if self.is_item_existed(**db_data):
                # already exsit
                pass
            else:
                # save content to cache dir
                item_dir = file_data['dir']
                item_html = file_data['html']

                item_abs_dir = os.path.join(self.cache_path, item_dir)
                if not os.path.exists(item_abs_dir):
                    os.mkdir(item_abs_dir)
                filename = os.path.join(item_abs_dir,
                                        self.default_item_index_file)
                with open(filename, 'w') as f:
                    f.write(item_html)
                # save item datas to db
                data['content'] = item_dir
                self.add_data('item', **db_data)
                need_save = True
        if need_save:
            self.save()

    def mark_read(self, node_id=None):
        """
        mark items as read
        :param:
            node_id: all items belong node_id will mark read
                     if node_id is None, all unread item will mark read
        :return: True if has data changed
        """
        self.log.debug("node_id:%d", node_id)
        if node_id:
            query = self.node_items_query(node_id)
        else:
            query = self.sess.query(RssItem)
        query = query.filter_by(is_read=False)
        self.log.debug("node count:%d", query.count())
        if query.count():
            query.update({'is_read': True}, synchronize_session='fetch')
            self.save()
            return True
        else:
            return False
