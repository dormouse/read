#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pyqt_win.parser import FeedParser

class TestFeedParser:
    """
        少数派
        rss_url:http://sspai.me/feed
        content:item['summary_detail']['value']

        Mac玩儿法
        rss_url:https://www.waerfa.com/feed
        content:item['content']['value']

    """
    @classmethod
    def setup_class(cls):
        url = 'http://sspai.me/feed'
        feed = FeedParser(url)
        cls.feed_infos = feed.infos()

    def test_title(cls):
        known_value = '少数派'
        result = cls.feed_infos['title']
        assert result == known_value

