import os
from pyqt_win.main import AppOption

FULLPATH = os.path.abspath(os.path.dirname(__file__))

class TestAppOption():

    def test_labels(self):
        config_file = '/tmp/test_app_config.ini'
        op = AppOption(config_file)
        assert op.labels(['id', 'feed_id']) == ['id', 'feed_id']

    def test_item_list_view_header_labels(self):
        config_file = '/tmp/test_app_config.ini'
        op = AppOption(config_file)
        assert op.item_list_view_header_labels() == ['publish_time', 'title']

    def test_item_list_view_col_names(self):
        config_file = '/tmp/test_app_config.ini'
        op = AppOption(config_file)
        assert op.item_list_view_col_names() == ['publish_time', 'title']

    def test_item_list_view_col_width(self):
        config_file = '/tmp/test_app_config.ini'
        op = AppOption(config_file)
        assert op.item_list_view_col_widths() == [200, 800]
