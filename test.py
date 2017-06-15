from bs4 import BeautifulSoup

tag_body = BeautifulSoup('', 'html.parser').new_tag('body')
tag_p = BeautifulSoup('', 'html.parser').new_tag('p')
tag_p.string = 'the p section'
tag_br = BeautifulSoup('', 'html.parser').new_tag('br')

tag_body.append(tag_p)
tag_body.append(tag_br)
print(tag_body)

tag_body.contents = [tag_p, tag_br, tag_p, tag_br, tag_p]
print(tag_body)

def clear_br(all_p):
    """ clear tag br in all tag p
    If tag br in tag p, then split tag p to multiple tag p by tag br.
    """

    p_list = []
    br_tag = BeautifulSoup('', 'html.parser').new_tag('br')
    for p in all_p:
        for i in p.contents:
            print('i:', i)
            print('name:', i.name)
            print('-'*20)
        split_p_list = []
        if br_tag in p.contents:
            for item in p.contents:
                if item.name == 'br':
                    if split_p_list:
                        new_p_tag = BeautifulSoup('', 'html.parser').new_tag('p')
                        new_p_tag.contents = split_p_list
                        p_list.append(new_p_tag)
                        split_p_list = []
                else:
                    split_p_list.append(item)
            if split_p_list:
                new_p_tag = BeautifulSoup('', 'html.parser').new_tag('p')
                new_p_tag.contents = split_p_list
                p_list.append(new_p_tag)
        else:
            p_list.append(p)
    return p_list

html = """
<body>
<p>
	【1】八一表演队唐山坠机 中国首位歼-10女飞行员牺牲<br>
11月12日上午，驻扎在天津武清杨村机场的中国空军八一飞行表演队<br>
kkkk
</p>
</body>
"""
soup = BeautifulSoup(html, 'html.parser')
all_tags = clear_br(soup.find_all('p'))
soup.body.contents = all_tags
print(soup.prettify())

class cleaner():

    def dealp(tag):
        cons = tag.contents
        for con in cons:
            if con.name == "br":
                con = kill_br(con)
        return tag

    def kill_br(tag)