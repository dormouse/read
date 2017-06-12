#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from bs4 import BeautifulSoup

def test():
    html = """
    <body>
    <p>
    	&nbsp;天！仅此一天哦→<br />
<a href="https://item.taobao.com/item.htm?id=539146861037" target="_blank">
<img src="file://C:\\Users\gide\AppData\Local\Temp\[5UQ[BL(6~BS2JV6W}N6[%S.png" />https://item.taobao.com/item.htm?id=539146861037</a><br />

    </p>
    </body>
    """

    soup = BeautifulSoup(html, 'html.parser')
    tag_img = soup.find_all('img')
    del_bad_img(tag_img)
    print(soup.prettify())

def del_bad_img(tag_imgs):
    for tag in tag_imgs:
        if tag['src'].strip().startswith('file'):
            print(tag)
            tag.decompose()


if __name__ == '__main__':
    test()
