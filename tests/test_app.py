import unittest

import paper_downloader_app


class AppHelperTests(unittest.TestCase):
    def test_parse_doi_text(self):
        text = """
        # comment
        10.1016/example
        https://doi.org/10.1002/example
        10.1016/example
        """
        self.assertEqual(
            paper_downloader_app.parse_doi_text(text),
            ["10.1016/example", "10.1002/example"],
        )


if __name__ == "__main__":
    unittest.main()
