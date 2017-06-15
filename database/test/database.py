#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import QueuePool

base_path = os.path.abspath(os.path.dirname(__file__))

book = 'sqlite:///:memory:'
book_engi = create_engine(book, convert_unicode=True, echo=False)
book_sess = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=book_engi))
book_base = declarative_base()
book_base.query = book_sess.query_property()

rss = 'sqlite:///:memory:'
rss_engi = create_engine(
    rss, connect_args={'check_same_thread': False},
    convert_unicode=True, echo=True)
rss_sess = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=rss_engi))
rss_base = declarative_base()
rss_base.query = rss_sess.query_property()
