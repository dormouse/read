import logging
import httplib2
import json
import os
import re
from bs4 import BeautifulSoup
import subprocess


class MakeMobiPenti():
    """ make mobi ebook of dapenti.com"""

    def __init__(self, url):
        self.url = url
        self.output_path = ''
        self.all_h2 = []
        self.name = ''
        self.title = ''

    def make_book(self):
        content = self.get_webpage(self.url)
        if content:
            # todo auto get content_code
            content_code = 'gb2312'
            html = content.decode(content_code)
            self.make_content(html)
            self.make_style_css()
            self.make_toc_html()
            self.make_toc_ncx()
            self.make_opf()
            # start gen
            filename = os.path.join(os.getcwd(), self.name, '%s.opf' % self.name)
            returnCode = subprocess.call(['./kindlegen', filename])
            print(returnCode)

    def get_webpage(self, url):
        """ download webpage
        :param
            url: the url of webpage which need to be download
        :return
            if success return webpage, else return None
        """

        h = httplib2.Http('.cache')
        response, content = h.request(url)
        if response.status == 200:
            return content
        else:
            return None

    def output(self, filename, content):
        with open(filename, mode='w', encoding='utf-8') as a_file:
            a_file.write(content)

    def make_content(self, html):
        """ the content of book """
        # title
        soup = BeautifulSoup(html, 'html.parser')
        self.title = soup.find_all(href=re.compile('more'))[0].string
        # name
        self.name = 'pttg%s' % self.title[5:13]
        # output path
        self.output_path = 'pttg%s' % self.title[5:13]
        if not os.path.exists(self.output_path):
            os.mkdir(self.output_path)
        # output html name
        output_filename = os.path.join(self.output_path, '%s.html' % self.name)
        # html body
        txts = soup.find_all(class_='oblog_text')[1]
        all_p = txts.find_all('p')
        h2_pattern = re.compile(r'【\d+】')

        body = []
        self.all_h2 = []
        for p in all_p:
            for ptext in p.text.split('\r\n'):
                text = ptext.strip()
                if text:
                    if h2_pattern.search(text):
                        self.all_h2.append(text)
                        body.append('<h2 id="ch%d">%s</h2>' % (len(self.all_h2), text))
                    else:
                        body.append("<p>%s</p>" % text)

        # make up together
        template = """<html>
<head>
<meta http-equiv = "content-type" content="text/html; charset=UTF-8" >
<title> %s </title>
<link rel="stylesheet" href="style.css" type="text/css" / >
</head>
<body> %s </body>
</html>
"""

        content = template % (self.title, "\n".join(body))
        self.output(output_filename, content)

    def make_style_css(self):
        template = """p { margin-top: 1em; text-indent: 0em; }
h1 {margin-top: 1em}
h2 {margin: 2em 0 1em; text-align: center; font-size: 2.5em;}
h3 {margin: 0 0 2em; font-weight: normal; text-align:center; font-size: 1.5em; font-style: italic;}

.center { text-align: center; }
.pagebreak { page-break-before: always; }
"""
        output_filename = os.path.join(self.output_path, 'style.css')
        self.output(output_filename, template)

    def make_toc_html(self):
        """ index page """
        lis = []
        html = '%s.html' % self.name
        for index, h2 in enumerate(self.all_h2):
            lis.append('< li > < a href = "%s#ch%d" >%s< / a > < / li >' % (html, index + 1, h2))

        template = """<html>
<head>
    <meta http-equiv="content-type" content="text/html; charset=UTF-8">
    <title>TOC</title>
</head>
<body>
<h1 id="toc">Table of Contents</h1>
<ul>%s</ul>
</body>"""

        output_filename = os.path.join(self.output_path, 'toc.html')
        content = template % '\n'.join(lis)
        self.output(output_filename, content)

    def make_toc_ncx(self):
        """ navigation page """
        navpoints = []
        navpoint_template = """<navPoint id="ch%d" playOrder="%d">
            <navLabel>
                <text>
                    %s
                </text>
            </navLabel>
            <content src="%s.html#ch%d" />
        </navPoint>
        """
        for index, h2 in enumerate(self.all_h2):
            navpoints.append(navpoint_template % (index + 1, index + 1, h2, self.name, index + 1))

        template = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
<head>
</head>
    <docTitle>
        <text>%s</text>
    </docTitle>
    <navMap>
        %s
    </navMap>
</ncx>"""

        output_filename = os.path.join(self.output_path, 'toc.ncx')
        content = template % (self.title, '\n'.join(navpoints))
        self.output(output_filename, content)

    def make_opf(self):
        """ book info, ie: ISBN, title, cover """
        template = """<?xml version="1.0" encoding="UTF-8"?>
<package unique-identifier="uid" xmlns:opf="http://www.idpf.org/2007/opf" xmlns:asd="http://www.idpf.org/asdfaf">
    <metadata>
        <dc-metadata  xmlns:dc="http://purl.org/metadata/dublin_core" xmlns:oebpackage="http://openebook.org/namespaces/oeb-package/1.0/">
            <dc:Title>%s</dc:Title>
            <dc:Language>zh_cn</dc:Language>
            <dc:Creator>喷嚏图卦</dc:Creator>
            <dc:Copyrights>喷嚏图卦</dc:Copyrights>
            <dc:Publisher>Dormouse Young</dc:Publisher>
        </dc-metadata>
    </metadata>
    <manifest>
        <item id="content" media-type="text/x-oeb1-document" href="pttg20161113.html"></item>
        <item id="ncx" media-type="application/x-dtbncx+xml" href="toc.ncx"/>
    </manifest>
    <spine toc="ncx">
        <itemref idref="content"/>
    </spine>
    <guide>
        <reference type="toc" title="Table of Contents" href="toc.html"/>
        <reference type="text" title="Book" href="%s.html"/>
    </guide>
</package>"""

        output_filename = os.path.join(self.output_path, '%s.opf' % self.name)
        content = template % (self.title, self.name)
        self.output(output_filename, content)


def test():
    url = 'http://www.dapenti.com/blog/more.asp?name=xilei&id=116232'
    tea = MakeMobiPenti(url)
    tea.make_book()


if __name__ == '__main__':
    test()
