#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging

logging.basicConfig(
    format='%(asctime)s %(module)s %(funcName)s %(levelname)s %(message)s',
    level=logging.DEBUG
)
DEBUG = True
PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))
LOG = logging.getLogger(__name__)
