import unittest
import urllib.parse

import paper_search


class PaperSearchTests(unittest.TestCase):
    def test_normalize_doi(self):
        self.assertEqual(
            paper_search.normalize_doi("https://doi.org/10.1109/CVPR.2016.90"),
            "10.1109/CVPR.2016.90",
        )

    def test_yonsei_openlink_url(self):
        target = "https://doi.org/10.1109/CVPR.2016.90"
        link = paper_search.yonsei_openlink_url(target)
        self.assertTrue(link.startswith("https://openlink.access.yonsei.ac.kr/link.n2s?url="))
        encoded = link.split("url=", 1)[1]
        self.assertEqual(urllib.parse.unquote(encoded), target)

    def test_parse_crossref_item(self):
        item = {
            "title": ["Example Paper"],
            "author": [{"given": "Gun", "family": "Kuk"}],
            "container-title": ["Example Journal"],
            "DOI": "10.1234/example",
            "issued": {"date-parts": [[2026, 1, 2]]},
        }
        paper = paper_search.paper_from_crossref_item(item)
        self.assertEqual(paper.title, "Example Paper")
        self.assertEqual(paper.authors, "Gun Kuk")
        self.assertEqual(paper.year, "2026")
        self.assertEqual(paper.doi, "10.1234/example")
        self.assertIn("openlink.access.yonsei.ac.kr", paper.yonsei_openlink)


if __name__ == "__main__":
    unittest.main()
