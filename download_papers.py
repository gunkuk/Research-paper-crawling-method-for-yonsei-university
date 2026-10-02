#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

import requests
from pathlib import Path
from typing import Any

CROSSREF_API = "https://api.crossref.org/works"
WILEY_API = "https://api.wiley.com/onlinelibrary/tdm/v1/articles/{doi}"
ELSEVIER_API = "https://api.elsevier.com/content/article/doi/{doi}?view=FULL"
USER_AGENT = (
    "yonsei-paper-downloader/1.0 "
    "(https://github.com/gunkuk/Research-paper-crawling-method-for-yonsei-university)"
)


@dataclass
class DownloadResult:
    doi: str
    publisher: str
    status: str
    file: str
    message: str


def load_env(path: str = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            # The local .env is the explicit configuration for this CLI run.
            # Always prefer it over stale process/user environment variables.
            os.environ[key] = value


def normalize_doi(value: str) -> str:
    value = value.strip()
    prefixes = (
        "https://doi.org/",
        "http://doi.org/",
        "https://dx.doi.org/",
        "http://dx.doi.org/",
        "doi:",
    )

    lower = value.lower()
    for prefix in prefixes:
        if lower.startswith(prefix):
            value = value[len(prefix):]
            break

    return value.strip()


def read_dois(path: str) -> list[str]:
    seen: set[str] = set()
    dois: list[str] = []

    for raw_line in Path(path).read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        doi = normalize_doi(line)
        if doi and doi not in seen:
            seen.add(doi)
            dois.append(doi)

    return dois


def safe_filename(doi: str) -> str:
    value = doi.replace("/", "__")
    value = re.sub(r'[^A-Za-z0-9._()\-]+', "_", value)
    return value[:220] or "paper"


def _request(
    url: str,
    headers: dict[str, str],
    timeout: int = 90,
) -> tuple[int, dict[str, str], bytes]:
    request = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response_headers = {k.lower(): v for k, v in response.headers.items()}
            return response.status, response_headers, response.read()
    except urllib.error.HTTPError as exc:
        headers_out = {k.lower(): v for k, v in exc.headers.items()}
        body = exc.read()
        return exc.code, headers_out, body


def _json_request(url: str, timeout: int = 30) -> dict[str, Any]:
    status, _, body = _request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
        timeout=timeout,
    )

    if status != 200:
        raise RuntimeError(f"Crossref HTTP {status}")

    return json.loads(body.decode("utf-8"))


def detect_publisher(doi: str) -> str:
    """Route well-known publisher DOI prefixes before consulting mutable metadata.

    Journal ownership/hosting can change over time. For example, some legacy
    Wiley DOIs may currently expose Elsevier as the journal publisher in
    metadata even though Wiley's TDM endpoint still serves the DOI.
    """
    normalized = normalize_doi(doi).lower()

    wiley_prefixes = (
        "10.1002/",
        "10.1111/",
        "10.1046/",
    )
    elsevier_prefixes = (
        "10.1016/",
    )

    if normalized.startswith(wiley_prefixes):
        return "wiley"
    if normalized.startswith(elsevier_prefixes):
        return "elsevier"

    encoded = urllib.parse.quote(normalized, safe="")
    data = _json_request(f"{CROSSREF_API}/{encoded}")
    publisher = str(data.get("message", {}).get("publisher", "")).strip()
    lower = publisher.lower()

    if "wiley" in lower or "john wiley" in lower:
        return "wiley"
    if "elsevier" in lower:
        return "elsevier"

    return "unsupported"


def _looks_like_pdf(headers: dict[str, str], body: bytes) -> bool:
    content_type = headers.get("content-type", "").lower()
    return "application/pdf" in content_type or body.startswith(b"%PDF")


def _sanitize_url(url: str) -> str:
    """Remove query/fragment so diagnostics never expose signed URL parameters."""
    parts = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def _body_excerpt(body: bytes | str, limit: int = 500) -> str:
    if isinstance(body, bytes):
        text = body.decode("utf-8", errors="replace")
    else:
        text = body
    return " ".join(text.strip().split())[:limit]


def _wiley_failure_result(
    doi: str,
    status: int,
    headers: dict[str, str],
    body: bytes | str,
    *,
    final_url: str = "",
    redirect_history: list[str] | None = None,
) -> DownloadResult:
    redirects = redirect_history or []
    diagnostic = f"HTTP {status}"
    if final_url:
        diagnostic += f"; final={_sanitize_url(final_url)}"
    if redirects:
        diagnostic += f"; redirects={' -> '.join(redirects)}"

    content_type = headers.get("content-type", "")
    if content_type:
        diagnostic += f"; content-type={content_type}"

    if status == 400:
        state = "forbidden"
        message = "Wiley TDM API 400: 요청에 TDM Client Token이 전달되지 않았습니다."
    elif status == 403:
        state = "forbidden"
        message = (
            "Wiley TDM API 403: Wiley가 TDM Token을 invalid/unregistered로 거부했습니다. "
            "앱에 저장된 Token이 최신 값인지 확인하거나 Wiley에서 Token을 재발급하세요."
        )
    elif status == 404:
        state = "not_found"
        message = (
            "Wiley TDM API 404: DOI 또는 해당 콘텐츠의 접근 권한을 확인해야 합니다. "
            "기관 구독 콘텐츠라면 기관 네트워크에서 요청해야 합니다."
        )
    elif status == 429:
        state = "rate_limited"
        message = "Wiley TDM API 429: 요청 횟수 제한에 걸렸습니다."
        retry_after = headers.get("retry-after")
        if retry_after:
            message += f" Retry-After={retry_after}"
    else:
        state = "error"
        message = f"Wiley TDM API 오류: HTTP {status}"

    excerpt = _body_excerpt(body)
    if excerpt:
        message += f" | {excerpt}"

    message += f" | {diagnostic}"
    return DownloadResult(doi, "wiley", state, "", message)


def download_wiley(
    doi: str,
    token: str,
    output_path: Path,
) -> DownloadResult:
    """Download a Wiley PDF using the request pattern of Wiley's official TDM client."""
    encoded = urllib.parse.quote(doi, safe="")
    url = WILEY_API.format(doi=encoded)
    token = token.strip()

    if not token:
        return DownloadResult(
            doi,
            "wiley",
            "forbidden",
            "",
            "Wiley TDM Token이 비어 있습니다.",
        )

    session = requests.Session()
    session.headers.update(
        {
            "Wiley-TDM-Client-Token": token,
            "User-Agent": USER_AGENT,
            "Connection": "keep-alive",
        }
    )

    response = None
    try:
        response = session.get(
            url,
            allow_redirects=True,
            stream=True,
            timeout=(15, 90),
        )
        status = response.status_code
        headers = {k.lower(): v for k, v in response.headers.items()}
        redirect_history = [
            f"{item.status_code}:{_sanitize_url(item.url)}"
            for item in response.history
        ]

        if status != 200:
            return _wiley_failure_result(
                doi,
                status,
                headers,
                response.text,
                final_url=response.url,
                redirect_history=redirect_history,
            )

        tmp = output_path.with_suffix(output_path.suffix + ".part")
        try:
            with tmp.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        handle.write(chunk)

            with tmp.open("rb") as handle:
                magic = handle.read(4)

            if "application/pdf" not in headers.get("content-type", "").lower() and magic != b"%PDF":
                excerpt = _body_excerpt(tmp.read_bytes()[:1000])
                tmp.unlink(missing_ok=True)
                return DownloadResult(
                    doi,
                    "wiley",
                    "error",
                    "",
                    (
                        "Wiley TDM API가 HTTP 200을 반환했지만 PDF가 아닙니다. "
                        f"content-type={headers.get('content-type', '')}; "
                        f"final={_sanitize_url(response.url)}"
                        + (f" | {excerpt}" if excerpt else "")
                    ),
                )

            tmp.replace(output_path)
        except Exception:
            tmp.unlink(missing_ok=True)
            raise

        redirect_note = (
            f", redirect {len(response.history)}회"
            if response.history
            else ""
        )
        return DownloadResult(
            doi,
            "wiley",
            "downloaded",
            str(output_path),
            f"정상 다운로드 (Wiley TDM API{redirect_note})",
        )

    except requests.RequestException as exc:
        return DownloadResult(
            doi,
            "wiley",
            "error",
            "",
            f"Wiley 네트워크 요청 실패: {exc}",
        )
    finally:
        if response is not None:
            response.close()
        session.close()

def download_elsevier(
    doi: str,
    api_key: str,
    output_path: Path,
) -> DownloadResult:
    encoded = urllib.parse.quote(doi, safe="")
    url = ELSEVIER_API.format(doi=encoded)

    status, headers, body = _request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "X-ELS-APIKey": api_key,
            "Accept": "application/pdf",
        },
    )

    if status == 200 and _looks_like_pdf(headers, body):
        tmp = output_path.with_suffix(output_path.suffix + ".part")
        tmp.write_bytes(body)
        tmp.replace(output_path)
        return DownloadResult(doi, "elsevier", "downloaded", str(output_path), "정상 다운로드")

    return _failure_result(doi, "elsevier", status, headers, body)


def _failure_result(
    doi: str,
    publisher: str,
    status: int,
    headers: dict[str, str],
    body: bytes,
) -> DownloadResult:
    excerpt = _body_excerpt(body)

    if publisher == "elsevier":
        if status == 403:
            state = "forbidden"
            message = (
                "Elsevier Article Retrieval API returned 403. "
                "API key/resource/account configuration 또는 institutional authorization 확인이 필요합니다."
            )
        elif status == 401:
            state = "forbidden"
            message = "Elsevier API Key 인증에 실패했습니다."
        elif status == 404:
            state = "not_found"
            message = "Elsevier Article Retrieval API에서 DOI를 찾지 못했습니다."
        elif status == 429:
            state = "rate_limited"
            message = "Elsevier API 요청 횟수 제한에 걸렸습니다."
        else:
            state = "error"
            message = f"Elsevier Article Retrieval API 오류: HTTP {status}"
    else:
        if status == 403:
            state = "forbidden"
            message = "접근이 거부되었습니다."
        elif status == 401:
            state = "forbidden"
            message = "API 인증에 실패했습니다."
        elif status == 404:
            state = "not_found"
            message = "DOI를 찾지 못했습니다."
        elif status == 429:
            state = "rate_limited"
            message = "API 요청 횟수 제한에 걸렸습니다."
        else:
            state = "error"
            message = f"HTTP {status}"

    retry_after = headers.get("retry-after")
    if status == 429 and retry_after:
        message += f" Retry-After={retry_after}"

    if excerpt:
        message += f" | {excerpt}"

    return DownloadResult(doi, publisher, state, "", message)


def write_results(path: Path, results: list[DownloadResult]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["doi", "publisher", "status", "file", "message"],
        )
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "doi": result.doi,
                    "publisher": result.publisher,
                    "status": result.status,
                    "file": result.file,
                    "message": result.message,
                }
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="YSVPN 환경에서 Wiley/Elsevier 공식 API로 DOI 목록의 PDF를 다운로드합니다."
    )
    parser.add_argument("--input", default="doi_list.txt", help="DOI 목록 텍스트 파일 (기본값: doi_list.txt)")
    parser.add_argument("--output", default="downloads", help="PDF 저장 폴더")
    parser.add_argument(
        "--results",
        default="download_results.csv",
        help="처리 결과 CSV 경로",
    )
    parser.add_argument("--max", type=int, default=None, help="앞에서 N개 DOI만 처리")
    parser.add_argument("--dry-run", action="store_true", help="다운로드 없이 출판사만 판별")
    parser.add_argument("--overwrite", action="store_true", help="기존 PDF가 있어도 다시 다운로드")
    parser.add_argument(
        "--wiley-delay",
        type=float,
        default=10.0,
        help="Wiley 요청 간격(초). 공식 제한 준수를 위해 최소 10초 적용",
    )
    parser.add_argument(
        "--elsevier-delay",
        type=float,
        default=1.0,
        help="Elsevier 요청 간격(초)",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    load_env()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"입력 파일을 찾을 수 없습니다: {input_path}", file=sys.stderr)
        return 2

    dois = read_dois(str(input_path))
    if args.max is not None:
        dois = dois[: max(0, args.max)]

    if not dois:
        print("처리할 DOI가 없습니다.", file=sys.stderr)
        return 2

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    results_path = Path(args.results)

    wiley_token = os.getenv("WILEY_TDM_TOKEN", "").strip()
    elsevier_key = os.getenv("ELSEVIER_API_KEY", "").strip()

    wiley_delay = max(10.0, args.wiley_delay)
    elsevier_delay = max(0.0, args.elsevier_delay)

    results: list[DownloadResult] = []
    last_wiley_request = 0.0
    last_elsevier_request = 0.0

    for index, doi in enumerate(dois, 1):
        print(f"[{index}/{len(dois)}] {doi}")

        try:
            publisher = detect_publisher(doi)
        except Exception as exc:
            result = DownloadResult(doi, "unknown", "error", "", f"출판사 판별 실패: {exc}")
            results.append(result)
            print(f"  -> {result.status}: {result.message}")
            write_results(results_path, results)
            continue

        print(f"  출판사: {publisher}")

        if args.dry_run:
            result = DownloadResult(doi, publisher, "dry_run", "", "출판사 판별만 수행")
            results.append(result)
            write_results(results_path, results)
            continue

        if publisher == "unsupported":
            result = DownloadResult(
                doi,
                publisher,
                "unsupported",
                "",
                "Wiley/Elsevier DOI가 아님",
            )
            results.append(result)
            print("  -> unsupported")
            write_results(results_path, results)
            continue

        target = output_dir / f"{safe_filename(doi)}.pdf"
        if target.exists() and target.stat().st_size > 0 and not args.overwrite:
            result = DownloadResult(doi, publisher, "skipped", str(target), "기존 파일 사용")
            results.append(result)
            print("  -> skipped")
            write_results(results_path, results)
            continue

        if publisher == "wiley":
            if not wiley_token:
                result = DownloadResult(
                    doi,
                    publisher,
                    "error",
                    "",
                    ".env의 WILEY_TDM_TOKEN이 비어 있음",
                )
            else:
                elapsed = time.monotonic() - last_wiley_request
                if last_wiley_request and elapsed < wiley_delay:
                    time.sleep(wiley_delay - elapsed)

                last_wiley_request = time.monotonic()
                result = download_wiley(doi, wiley_token, target)

        elif publisher == "elsevier":
            if not elsevier_key:
                result = DownloadResult(
                    doi,
                    publisher,
                    "error",
                    "",
                    ".env의 ELSEVIER_API_KEY가 비어 있음",
                )
            else:
                elapsed = time.monotonic() - last_elsevier_request
                if last_elsevier_request and elapsed < elsevier_delay:
                    time.sleep(elsevier_delay - elapsed)

                last_elsevier_request = time.monotonic()
                result = download_elsevier(doi, elsevier_key, target)

        else:
            result = DownloadResult(doi, publisher, "unsupported", "", "지원하지 않는 출판사")

        results.append(result)
        print(f"  -> {result.status}: {result.message}")
        write_results(results_path, results)

    downloaded = sum(r.status == "downloaded" for r in results)
    skipped = sum(r.status == "skipped" for r in results)
    failed = len(results) - downloaded - skipped

    print()
    print(f"완료: downloaded={downloaded}, skipped={skipped}, other={failed}")
    print(f"결과 CSV: {results_path}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
