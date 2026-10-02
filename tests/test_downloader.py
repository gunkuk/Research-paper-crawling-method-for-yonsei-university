import tempfile
import unittest
from pathlib import Path

import download_papers


class DownloaderTests(unittest.TestCase):
    def test_normalize_doi(self):
        self.assertEqual(
            download_papers.normalize_doi("https://doi.org/10.1016/j.test.2026.01.001"),
            "10.1016/j.test.2026.01.001",
        )
        self.assertEqual(
            download_papers.normalize_doi("doi:10.1002/example.123"),
            "10.1002/example.123",
        )

    def test_safe_filename(self):
        self.assertEqual(
            download_papers.safe_filename("10.1016/j.test.2026.01.001"),
            "10.1016__j.test.2026.01.001",
        )

    def test_read_dois_deduplicates_and_ignores_comments(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "dois.txt"
            path.write_text(
                "# comment\n"
                "10.1016/example\n"
                "https://doi.org/10.1016/example\n"
                "\n"
                "10.1002/example\n",
                encoding="utf-8",
            )

            self.assertEqual(
                download_papers.read_dois(str(path)),
                ["10.1016/example", "10.1002/example"],
            )

    def test_pdf_detection(self):
        self.assertTrue(
            download_papers._looks_like_pdf(
                {"content-type": "application/pdf"},
                b"not-important",
            )
        )
        self.assertTrue(
            download_papers._looks_like_pdf(
                {"content-type": "application/octet-stream"},
                b"%PDF-1.7",
            )
        )


if __name__ == "__main__":
    unittest.main()
