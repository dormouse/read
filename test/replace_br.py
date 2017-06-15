import re
from bs4 import BeautifulSoup

def replace_br(tag_p):
    pattern = re.compile(r'</?br\s*/?>')
    if tag_p.br:
        old_html = tag_p.prettify()
        new_html = pattern.sub("</p><p>", old_html)
        new_soup = BeautifulSoup(new_html, 'html.parser')
        value = new_soup.find_all('p')
        print(value)
        return value
    else:
        return tag_p


def find_br(html):
    pattern = r'^</{0,1}br\s*/{0,1}>$'
    if re.search(pattern, html):
        return True
    else:
        print(html)
        return False
