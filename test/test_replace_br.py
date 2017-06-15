import replace_br
import unittest
from bs4 import BeautifulSoup

class KnownValues(unittest.TestCase):
    known_values = (
        ("<br>", True),
        ("<br />", True),
        ("</br>", True),
    )


    def test_to_replace_br_find_br(self):
        """ find_br should give known result with known input """

        for html, value in self.known_values:
            result = replace_br.find_br(html)
            self.assertEqual(value, result)

    def test_to_replace_br_replace_br(self):
        """ replace_br should convert old_html to new html """
        old_html = """
            <body>
            <p>
                【1】八一表演队唐山坠机 中国首位歼-10女飞行员牺牲<br>
            11月12日上午，驻扎在天津武清杨村机场的中国空军八一飞行表演队<br>
            kkkk
            </p>
            </body>
        """

        new_html = """
            <body>
            <p>【1】八一表演队唐山坠机 中国首位歼-10女飞行员牺牲</p>
            <p>11月12日上午，驻扎在天津武清杨村机场的中国空军八一飞行表演队</p>
            <p>kkkk</p>
            </body>
        """

        old_soup = BeautifulSoup(old_html, 'html.parser')
        new_soup = BeautifulSoup(new_html, 'html.parser')
        value = new_soup.find_all('p')
        result = replace_br.replace_br(old_soup.p)
        self.assertEqual(value, result)


if __name__ == '__main__':
    unittest.main()
