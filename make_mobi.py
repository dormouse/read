#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

        timeout = 20 #second
        self.http = httplib2.Http('.cache', timeout=timeout)
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
            html = content.decode(content_code, 'ignore')
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

        self.logger.info("Getting webpage:%s", url)
        response, content = self.http.request(url)
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
        self.all_h2 = []
        txts = soup.find_all(class_='oblog_text')[1]
        all_p = txts.find_all('p')
        body_tags = self.make_content_clear_br(all_p)
        body_tags = self.make_content_make_h2(body_tags)
        body_tags = self.make_content_make_img(body_tags)

        template = self.load_template('index.html')
        output_soup = BeautifulSoup(template)
        output_soup.title = self.title
        output_soup.body.contents = body_tags
        self.output(output_filename, output_soup.prettify())

    def make_content_clear_br(self, all_p):
        """ clear tag br in all tag p
        If tag br in tag p, then split tag p to multiple tag p by tag br.
        """
        p_list = []
        for p in all_p:
            p_tags = self.make_content_replace_br(p)
            p_list += p_tags
        return p_list

    def make_content_replace_br(self, tag_p):
        """ replce all br in tag p
        :keyword
            tag_p: tag p
        :return
            a list make up of tag p
        """

        pattern = re.compile(r'</?br\s*/?>')
        if tag_p.br:
            old_html = tag_p.prettify()
            new_html = pattern.sub("</p><p>", old_html)
            new_soup = BeautifulSoup(new_html, 'html.parser')
            value = new_soup.find_all('p')
            return value
        else:
            return [tag_p]

    def make_content_make_h2(self, tags):
        new_tags = []
        for tag in tags:
            h2_pattern = re.compile(r'【\d+】')
            if h2_pattern.search(''.join(tag.strings)):
                self.all_h2.append(''.join(tag.stripped_strings))
                new_h2_tag = BeautifulSoup('', 'html.parser').new_tag('h2')
                new_h2_tag.contents = tag.contents
                new_h2_tag['id'] = "ch%d" % len(self.all_h2)
                new_tags.append(new_h2_tag)
            else:
                new_tags.append(tag)
        return new_tags


    def make_content_make_img(self, tags):
        # parse img
        new_tags = []
        for tag in tags:
            for content in tag.contents:
                if content.name == 'img':
                    img_url = self.download_img(content['src'])
                    if img_url:
                        content['src'] = img_url
            new_tags.append(tag)
        return new_tags

    def download_img(self, url):
        """ download image
        :keyword
            url: the url of image
        :return
            if download success return the new url of image
            else return None
        """

        self.logger.info("Downloading image:%s", url)
        base_name = os.path.split(urlparse(url).path)[1]
        ext_name = os.path.splitext(base_name)[1]
        m = hashlib.md5()
        m.update(url.encode())
        target_base_name = m.hexdigest() + ext_name
        target_filename = os.path.join(self.output_img_path, target_base_name)
        try:
            resp, content = self.http.request(url, "GET")
            with open(target_filename, 'wb') as f:
                f.write(content)
            new_url = os.path.join('img', target_base_name)
            return new_url
        except Exception as e:
            self.logger.error("Download image:%s fail", url)
            self.logger.error(e)
            return None

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
    # url = 'http://www.dapenti.com/blog/more.asp?name=xilei&id=116232'
    url = 'http://www.dapenti.com/blog/more.asp?name=xilei&id=116327'
    # url = 'http://127.0.0.1:8000'
    tea = MakeMobiPenti(url)
    tea.make_book()


if __name__ == '__main__':
    test()
