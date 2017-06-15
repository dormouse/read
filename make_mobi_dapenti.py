#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from make_mobi import MakeMobi


class MakeMobiPenti(MakeMobi):
    """ make mobi ebook of dapenti.com"""

    def __init__(self):
        book_info = {
            'creator': '喷嚏图卦',
            'copyrights': '喷嚏图卦',
            'publisher': 'dormouse young'
        }
        super(MakeMobiPenti, self).__init__(**book_info)


def test():
    # url = 'http://www.dapenti.com/blog/more.asp?name=xilei&id=116232'
    url = 'http://www.dapenti.com/blog/more.asp?name=xilei&id=116504'
    # url = 'http://127.0.0.1:8000'
    book = MakeMobiPenti()
    book.set_url(url)
    book.make_book()

if __name__ == '__main__':
    test()
