import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import download_papers


class FakeHistory:
    def __init__(self, status_code, url):
        self.status_code = status_code
        self.url = url


class FakeResponse:
    def __init__(
        self,
        *,
        status_code=200,
        headers=None,
        body=b"%PDF-1.7\nTEST",
        text="",
        url="https://download.wiley.example/article.pdf?signature=secret",
        history=None,
    ):
        self.status_code = status_code
        self.headers = headers or {"Content-Type": "application/pdf"}
        self._body = body
        self.text = text
        self.url = url
        self.history = history or []
        self.closed = False

    def iter_content(self, chunk_size):
        yield self._body

    def close(self):
        self.closed = True


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.headers = {}
        self.get_calls = []
        self.closed = False

    def get(self, url, **kwargs):
        self.get_calls.append((url, kwargs))
        return self.response

    def close(self):
        self.closed = True


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

    def test_load_env_overrides_stale_environment_value(self):
        old = os.environ.get("WILEY_TDM_TOKEN")
        try:
            os.environ["WILEY_TDM_TOKEN"] = "stale-token"
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / ".env"
                path.write_text(
                    "WILEY_TDM_TOKEN=fresh-token\n",
                    encoding="utf-8",
                )
                download_papers.load_env(str(path))

            self.assertEqual(os.environ["WILEY_TDM_TOKEN"], "fresh-token")
        finally:
            if old is None:
                os.environ.pop("WILEY_TDM_TOKEN", None)
            else:
                os.environ["WILEY_TDM_TOKEN"] = old

    def test_wiley_regression_uses_official_request_shape(self):
        response = FakeResponse(
            history=[
                FakeHistory(
                    302,
                    "https://api.wiley.com/onlinelibrary/tdm/v1/articles/10.1111%2Fmice.12983",
                )
            ]
        )
        session = FakeSession(response)

        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "paper.pdf"
            with patch("download_papers.requests.Session", return_value=session):
                result = download_papers.download_wiley(
                    "10.1111/mice.12983",
                    "current-wiley-token",
                    target,
                )

            self.assertEqual(result.status, "downloaded")
            self.assertTrue(target.exists())
            self.assertTrue(target.read_bytes().startswith(b"%PDF"))

        self.assertEqual(
            session.headers["Wiley-TDM-Client-Token"],
            "current-wiley-token",
        )
        self.assertEqual(session.headers["Connection"], "keep-alive")
        self.assertNotIn("Accept", session.headers)

        self.assertEqual(len(session.get_calls), 1)
        url, kwargs = session.get_calls[0]
        self.assertEqual(
            url,
            "https://api.wiley.com/onlinelibrary/tdm/v1/articles/10.1111%2Fmice.12983",
        )
        self.assertTrue(kwargs["allow_redirects"])
        self.assertTrue(kwargs["stream"])
        self.assertEqual(kwargs["timeout"], (15, 90))
        self.assertTrue(response.closed)
        self.assertTrue(session.closed)

    def test_wiley_403_is_reported_as_token_problem(self):
        response = FakeResponse(
            status_code=403,
            headers={"Content-Type": "text/plain"},
            text="invalid token",
            body=b"",
            url="https://api.wiley.com/onlinelibrary/tdm/v1/articles/10.1111%2Fmice.12983",
        )
        session = FakeSession(response)

        with tempfile.TemporaryDirectory() as tmp:
            with patch("download_papers.requests.Session", return_value=session):
                result = download_papers.download_wiley(
                    "10.1111/mice.12983",
                    "bad-token",
                    Path(tmp) / "paper.pdf",
                )

        self.assertEqual(result.status, "forbidden")
        self.assertIn("invalid/unregistered", result.message)
        self.assertNotIn("기관 구독 또는 API 권한이 확인되지 않음", result.message)

    def test_wiley_404_is_reported_as_content_access_problem(self):
        result = download_papers._wiley_failure_result(
            "10.1111/mice.12983",
            404,
            {"content-type": "text/plain"},
            "not available",
        )
        self.assertEqual(result.status, "not_found")
        self.assertIn("접근 권한", result.message)

    def test_elsevier_403_does_not_claim_subscription_is_the_cause(self):
        result = download_papers._failure_result(
            "10.1016/j.jinorgbio.2026.113297",
            "elsevier",
            403,
            {"content-type": "application/xml"},
            (
                b"<statusText>Requestor configuration settings insufficient "
                b"for access to this resource.</statusText>"
            ),
        )

        self.assertEqual(result.status, "forbidden")
        self.assertIn("API key/resource/account configuration", result.message)
        self.assertIn("institutional authorization", result.message)
        self.assertNotIn("기관 구독 또는 API 권한이 확인되지 않음", result.message)


if __name__ == "__main__":
    unittest.main()
