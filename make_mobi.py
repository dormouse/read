#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hashlib
import logging
import os
import platform
import re
import subprocess
import shutil
from functools import reduce
from urllib.parse import urlparse, urljoin

import httplib2
from bs4 import BeautifulSoup
from jinja2 import Template

from yttools import YtTools

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)s %(levelname)s %(message)s')


class MakeMobi():
    """ make mobi ebook """

    def __init__(self, **book_info):
        self.logger = logging.getLogger(__name__)

        timeout = 20  # second
        self.http = httplib2.Http('.cache', timeout=timeout)
        self.url = ''
        self.template_path = 'template'
        self.build_path = 'build'
        self.output_path = ''
        self.output_img_path = ''
        self.all_h2 = []
        self.name = ''
        self.title = ''

        if not os.path.exists(self.build_path):
            os.mkdir(self.build_path)

        self.creator = book_info.get('creator', 'default creator')
        self.copyrights = book_info.get('copyrights', 'default copyrights')
        self.publisher = book_info.get('publisher', 'default publisher')

    def set_url(self, url):
        self.url = url

    def make_book(self):
        """ make the whole book """

        html = YtTools().download(self.url)
        if html:
            self.make_content(html)
            self.make_style_css()
            self.make_toc_html()
            self.make_toc_ncx()
            self.make_opf()
            self.make_cover()
            # start gen
            filename = os.path.join(
                os.getcwd(), self.output_path, '%s.opf' % self.name)

            if platform.system() == 'Darwin':
                # osx
                return_code = subprocess.call(['./kindlegen_mac', filename])
            elif platform.system() == 'Linux':
                # Linux
                return_code = subprocess.call(['./kindlegen_linux', filename])
            else:
                # other
                return_code = 999
        else:
            return_code = 110

        return return_code

    def guess_charset(self, html):
        charset = 'utf-8'
        soup = BeautifulSoup(html, 'html.parser')
        if 'gb2312' in soup.meta['content'].lower():
            charset = 'gb2312'
        return charset

    def make_content(self, html):
        """ the content of book """
        charset = self.guess_charset(html)
        html = html.decode(charset, 'ignore')
        soup = BeautifulSoup(html, 'html.parser')
        self.title = soup.find_all(href=re.compile('more'))[0].string
        # name
        self.name = 'pttg%s' % self.title[5:13]
        # output path
        output_path = 'pttg%s' % self.title[5:13]
        self.output_path = os.path.join(self.build_path, output_path)
        if not os.path.exists(self.output_path):
            os.mkdir(self.output_path)
        # output img path
        self.output_img_path = os.path.join(self.output_path, 'img')
        if not os.path.exists(self.output_img_path):
            os.mkdir(self.output_img_path)

        # del bad img
        tag_imgs = soup.find_all('img')
        self.make_content_make_img(tag_imgs)

        # html body
        self.all_h2 = []
        txts = soup.find_all(class_='oblog_text')[1]
        body_tags = txts.find_all(['p', 'div'])
        # body_tags = map(self.make_content_replace_br, body_tags)
        body_tags = reduce(
            lambda x, y: x + self.make_content_replace_br(y),
            body_tags,
            []
        )
        # body_tags = map(self.make_content_make_h2, body_tags)
        # body_tags = map(self.make_content_make_img, body_tags)
        output = '%s.html' % self.name
        template = 'index.html'
        objs = {
            'title': self.title,
            'body': '\n'.join([tag.prettify() for tag in body_tags])
        }
        self.make_output(template, objs, output)

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

    def make_content_make_h2(self, tag):
        """ make the line that contain "【\d+】" to h2"""

        h2_pattern = re.compile(r'【\d+】')
        if h2_pattern.search(''.join(tag.strings)):
            self.all_h2.append(''.join(tag.stripped_strings))
            new_h2_tag = BeautifulSoup('', 'html.parser').new_tag('h2')
            new_h2_tag.contents = tag.contents
            new_h2_tag['id'] = "ch%d" % len(self.all_h2)
            return new_h2_tag
        else:
            return tag

    def make_content_make_img(self, tag_imgs):
        """ make the img relative content """

        for tag in tag_imgs:
            if not tag['src'].strip().startswith('http'):
                # delete all bad img like:
                # <img src="file://C:...>
                # evernotecid://A6B65A9E-9762-414E-82B3-4C06FE717BD2/
                tag.decompose()
            else:
                try:
                    url = tag['src']
                    if urlparse(url).scheme == '':
                        # is relative url?
                        url = urljoin(self.url, url)
                    img_url = self.download_img(url)
                    if img_url:
                        tag['src'] = img_url
                except Exception as e:
                    self.logger.error("download fail:%s", tag['src'])
                    self.logger.error(e)

    def download_img(self, url):
        """ download image
        :keyword
            url: the url of image
        :return
            if download success return the new url of image
            else return None
        """

        base_name = os.path.split(urlparse(url).path)[1]
        ext_name = os.path.splitext(base_name)[1]
        m = hashlib.md5()
        m.update(url.encode())
        target_base_name = m.hexdigest() + ext_name
        target_filename = os.path.join(self.output_img_path, target_base_name)
        new_url = os.path.join('img', target_base_name)
        # check image exists
        if os.path.exists(target_filename):
            return new_url
        # download now
        content = YtTools().download(url)
        if content:
            with open(target_filename, 'wb') as f:
                f.write(content)
            return new_url
        else:
            return None

    def make_style_css(self):
        """ make the style.css """

        template = 'style.css'
        self.make_output(template)

    def make_toc_html(self):
        """ make the toc.html """

        lis = ['<li><a href="%s.html#ch%d">%s</a></li>' % (
            self.name, index + 1, h2)
               for index, h2 in enumerate(self.all_h2)
               ]
        template = 'toc.html'
        objs = {'tocs': '\n'.join(lis)}
        self.make_output(template, objs)

    def make_toc_ncx(self):
        """ navigation page """

        # make navpoints
        navpoint_template = """
        <navPoint id="ch{{ id }}" playOrder="{{ id }}">
            <navLabel>
                <text>
                    {{ text }}
                </text>
            </navLabel>
            <content src="{{ name }}.html#ch{{ id }}" />
        </navPoint>
        """
        jinja_template = Template(navpoint_template)
        navpoints = [jinja_template.render(
            id=index + 1, text=h2, name=self.name)
                     for index, h2 in enumerate(self.all_h2)
                     ]

        # make toc.ncx
        template = 'toc.ncx'
        objs = {
            'title': self.title,
            'navpoints': '\n'.join(navpoints),
        }
        self.make_output(template, objs)

    def make_opf(self):
        """ book info, ie: ISBN, title, cover """
        template = 'index.opf'
        output = '%s.opf' % self.name
        objs = {
            'name': self.name,
            'title': self.title,
            'creator': self.creator,
            'copyrights': self.copyrights,
            'publisher': self.publisher,
        }
        self.make_output(template, objs, output)

    def make_cover(self):
        template = os.path.join(self.template_path, 'cover.jpg')
        output = os.path.join(self.output_img_path, 'cover.jpg')
        shutil.copyfile(template, output)

    def make_output(self, template, objs=None, output=None):
        """
        make output file
        :keyword
            template: the base filename of template
            objs: the render objs
            output: the base filename of output, if output is None then
                same as template
        """

        output = output if output else template
        objs = objs if objs else {}

        output_file = os.path.join(self.output_path, output)
        template_file = os.path.join(self.template_path, template)
        with open(template_file, mode='r', encoding='utf-8') as a_file:
            output_content = Template(a_file.read()).render(objs)
        with open(output_file, mode='w', encoding='utf-8') as a_file:
            a_file.write(output_content)


def test():
    # url = 'http://www.dapenti.com/blog/more.asp?name=xilei&id=116232'
    url = 'http://www.dapenti.com/blog/more.asp?name=xilei&id=116383'
    # url = 'http://127.0.0.1:8000'
    tea = MakeMobi()
    tea.set_url(url)
    tea.make_book()


if __name__ == '__main__':
    test()
