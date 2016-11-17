import logging
import httplib2
import json
import os
import re
from bs4 import BeautifulSoup
import subprocess
from urllib.request import urlretrieve
from urllib.parse import urlparse
import hashlib


class MakeMobiPenti():
    """ make mobi ebook of dapenti.com"""

    def __init__(self, url):
        self.url = url
        self.template_path = 'template'
        self.output_path = ''
        self.output_img_path = ''
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
            return_code = subprocess.call(['./kindlegen', filename])
            print(return_code)

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

    def load_template(self, name):
        filename = os.path.join(self.template_path, name)
        with open(filename, mode='r', encoding='utf-8') as a_file:
            data = a_file.read()
        return data

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
        # output img path
        self.output_img_path = os.path.join(self.output_path, 'img')
        if not os.path.exists(self.output_img_path):
            os.mkdir(self.output_img_path)
        # output html name
        output_filename = os.path.join(self.output_path, '%s.html' % self.name)
        # html body
        txts = soup.find_all(class_='oblog_text')[1]
        all_p = txts.find_all('p')

        body = []
        self.all_h2 = []
        for p in all_p:
            for content in p.contents:
                result = self.make_content_sub(content)
                if result:
                    body.append(result)

        # make up together
        template = self.load_template('index.html')
        output_content = template % (self.title, "\n".join(body))
        self.output(output_filename, output_content)

    def make_content_sub(self, content):
        # parse img
        if content.name == 'img':
            img_url = self.download_img(content['src'])
            if img_url:
                content['src'] = img_url
                result = "<p>%s</p>" % content.prettify().strip()
                return result
            else:
                return None
        # parse a
        if content.name == 'a':
            result = "<p>%s</p>" % content.prettify().strip()
            return result

        # parse h2
        if content.string:
            text = content.string.strip()
            h2_pattern = re.compile(r'【\d+】')
            if text:
                if h2_pattern.search(text):
                    self.all_h2.append(text)
                    result = '<h2 id="ch%d">%s</h2>' % (len(self.all_h2), text)
                else:
                    result = "<p>%s</p>" % text
                return result

        return None

    def download_img(self, url):
        # TEST
        return None

        base_name = os.path.split(urlparse(url).path)[1]
        ext_name = os.path.splitext(base_name)[1]
        m = hashlib.md5()
        m.update(url.encode())
        target_name = m.hexdigest() + ext_name
        filename = os.path.join(self.output_img_path, target_name)
        urlretrieve(url, filename)
        new_url = os.path.join('img', target_name)
        return new_url

    def make_style_css(self):
        template = self.load_template('style.css')
        output_filename = os.path.join(self.output_path, 'style.css')
        output_content = template
        self.output(output_filename, output_content)

    def make_toc_html(self):
        """ index page """
        lis = []
        html = '%s.html' % self.name
        for index, h2 in enumerate(self.all_h2):
            lis.append('<li><a href="%s#ch%d">%s</a></li>' % (html, index+1, h2))

        template = self.load_template('toc.html')
        output_filename = os.path.join(self.output_path, 'toc.html')
        output_content = template % '\n'.join(lis)
        self.output(output_filename, output_content)

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

        template = self.load_template('toc.ncx')
        output_filename = os.path.join(self.output_path, 'toc.ncx')
        output_content = template % (self.title, '\n'.join(navpoints))
        self.output(output_filename, output_content)

    def make_opf(self):
        """ book info, ie: ISBN, title, cover """
        template = self.load_template('index.opf')
        output_filename = os.path.join(self.output_path, '%s.opf' % self.name)
        output_content = template % (self.title, self.name)
        self.output(output_filename, output_content)


def test():
    url = 'http://www.dapenti.com/blog/more.asp?name=xilei&id=116232'
    tea = MakeMobiPenti(url)
    tea.make_book()


if __name__ == '__main__':
    test()
