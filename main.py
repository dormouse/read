import logging
import httplib2
import json
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)s %(levelname)s %(message)s')
LOG = logging.getLogger('test')


def main():
    """ the main function """

    urls = check_update()
    for url in urls:
        content = download(url)

        if content:
            book = make(content)
        else:
            LOG.warning('Get web content fail!')
            return

        if book:
            status = sent(book)
        else:
            LOG.warning('Make book fail!')
            return

        if status:
            LOG.info('Done')
        else:
            LOG.warning('Sent book fail')


def check_update():
    """ check webpage update
    The old items saved in dapenti.json
    :return
        urls: a list. if updated then return the new urls
              else return []
    """
    dapenti_items_filename = 'dapenti.json'
    start_url = 'http://www.dapenti.com/blog/blog.asp?subjectid=70&name=xilei'
    content = download(start_url)
    if content:
        old_dapenti_items = get_old_dapenti_items(dapenti_items_filename)
        new_dapenti_items = get_new_dapenti_items(content)
        if old_dapenti_items == new_dapenti_items:
            LOG.info('No update.')
            return []
        else:
            # save_new_dapenti_items(dapenti_items_filename, new_dapenti_items)

            # for test only
            save_new_dapenti_items(dapenti_items_filename, new_dapenti_items[1:])

            return set(new_dapenti_items) - set(old_dapenti_items)
    else:
        LOG.warning('Check update fail')
        return []


def get_old_dapenti_items(filename):
    """get items from file
    :param
        filename: the name of file which store the items
    :return
        items: a list of urls.
               If success return all items in file, else return empty list([])
    """

    items = []
    try:
        with open(filename) as file:
            items = json.load(file)
    except Exception as exc:
        LOG.error('Load dapenti items error!')
        LOG.error(str(exc))

    return items


def save_new_dapenti_items(filename, items):
    """ save items to file
    :param
        filename: name of the file to save items
        items: a list of urls
    """

    try:
        with open(filename, 'w') as file:
            json.dump(items, file)
    except Exception as exc:
        LOG.error(str(exc))


def get_new_dapenti_items(content):
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
    # todo auto get content_code
    content_code = 'gb2312'
    html = content.decode(content_code)
    soup = BeautifulSoup(html, 'html.parser')
    lis = soup.find_all('li')
    items = [dapenti_base_url + li.a['href'] for li in lis]
    return items


def download(url):
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


def make(content):
    html = content.decode('gb2312')
    return None


def sent(book):
    return None


if __name__ == '__main__':
    # main()
    print(check_update())
