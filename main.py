import logging
import httplib2
import json


from bs4 import BeautifulSoup
import os

from yttools import YtTools
from database.database import book_sess, book_engi, book_base
from database.models import BookJob, BookDict
from make_mobi_dapenti import MakeMobiPenti

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)s %(levelname)s %(message)s')


class MakeBook():
    """ make book """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        self.base_path = os.path.abspath(os.path.dirname(__file__))
        db_filename = os.path.join(self.base_path, 'database', 'book.sqlite')
        if not os.path.exists(db_filename):
            self.init_database()

    def make_book(self):
        self.check_update()
        self.download_content()
        self.make_mobi_book()
        self.sent_mobi_book()

    def init_Database(self):
        book_base.metadata.create_all(book_engi)
        book_sess.add_all([
            BookDict(name='job_type', code='01', value='webpage'),
            BookDict(name='job_type', code='02', value='image'),
            BookDict(name='job_status', code='01', value='done'),
            BookDict(name='job_status', code='02', value='fail'),
            BookDict(name='job_status', code='03', value='not start'),
        ])
        book_sess.commit()

    def check_update(self):
        """ check webpage update """
        # dapenti.com
        start_url = 'http://www.dapenti.com/blog/blog.asp?subjectid=70&name=xilei'
        content = YtTools().download(start_url)
        if content:
            items = self.get_dapenti_items(content)
            for item in items:
                if self.check_dapenti_job(item):
                    pass
                else:
                    self.add_dapenti_job(item)
        else:
            self.logger.info('No update.')

    def get_dapenti_items(self, content):
        """ parse content, get all dapenti items
        :param
            content: the webpage of dapenti list page
        :return
            items: a list of urls parsed in web page, something like:
                ['http://www.dapenti.com/blog/more.asp?name=xilei&id=116232',
                 'http://www.dapenti.com/blog/more.asp?name=xilei&id=116209',
                  ... ]

        """

        dapenti_base_url = 'http://www.dapenti.com/blog/'
        soup = BeautifulSoup(content, 'html.parser')
        lis = soup.find_all('li')
        items = [dapenti_base_url + li.a['href'] for li in lis]
        return items

    def check_dapenti_job(self, item):
        row = book_sess.query(BookJob) \
            .filter(BookJob.url == item) \
            .first()
        if row:
            return True
        else:
            return False

    def add_dapenti_job(self, item):
        self.logger.info('Add dapenti job:%s', item)
        job = BookJob(item)
        job.type_code = book_sess.query(BookDict.code). \
            filter(BookDict.value == 'webpage'). \
            filter(BookDict.name == 'job_type'). \
            first().code
        job.status_code = book_sess.query(BookDict.code). \
            filter(BookDict.value == 'not start'). \
            filter(BookDict.name == 'job_status'). \
            first().code
        book_sess.add(job)
        book_sess.commit()

    def get_undo_dapenti_jobs(self):
        job_type_code = book_sess.query(BookDict.code). \
            filter(BookDict.value == 'webpage'). \
            filter(BookDict.name == 'job_type'). \
            first().code
        job_status_code = book_sess.query(BookDict.code). \
            filter(BookDict.value == 'done'). \
            filter(BookDict.name == 'job_status'). \
            first().code
        jobs = book_sess.query(BookJob). \
            filter(BookJob.type_code == job_type_code). \
            filter(BookJob.status_code != job_status_code). \
            all()
        return jobs

    def do_datpenti_job(self, job):
        url = job.url
        penti_book = MakeMobiPenti()
        penti_book.set_url(url)
        result = penti_book.make_book()
        if result == 0:
            # success
            job_status_code = book_sess.query(BookDict.code). \
                filter(BookDict.value == 'done'). \
                filter(BookDict.name == 'job_status'). \
                first().code
            job.status_code = job_status_code
            book_sess.commit()
            self.logger.info("job done!")
            self.logger.info("job id: %s" % job.id)
            self.logger.info("job url: %s" % job.url)
        else:
            # not success
            job_status_code = book_sess.query(BookDict.code). \
                filter(BookDict.value == 'fail'). \
                filter(BookDict.name == 'job_status'). \
                first().code
            job.status_code = job_status_code
            book_sess.commit()
            self.logger.warning("job fail!")
            self.logger.warning("make book return code: %s" % result)
            self.logger.warning("job id: %s" % job.id)
            self.logger.warning("job url: %s" % job.url)

    def download_content(self):
        jobs = self.get_undo_dapenti_jobs()
        for job in jobs:
            self.do_datpenti_job(job)

    def make_mobi_book(self):
        pass

    def sent_mobi_book(self):
        pass


if __name__ == '__main__':
    book = MakeBook()
    book.make_book()
