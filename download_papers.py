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
        if key and key not in os.environ:
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
    encoded = urllib.parse.quote(doi, safe="")
    data = _json_request(f"{CROSSREF_API}/{encoded}")
    publisher = str(data.get("message", {}).get("publisher", "")).strip()
    lower = publisher.lower()

    if "elsevier" in lower:
        return "elsevier"
    if "wiley" in lower or "john wiley" in lower:
        return "wiley"

    return "unsupported"


def _looks_like_pdf(headers: dict[str, str], body: bytes) -> bool:
    content_type = headers.get("content-type", "").lower()
    return "application/pdf" in content_type or body.startswith(b"%PDF")


def download_wiley(
    doi: str,
    token: str,
    output_path: Path,
) -> DownloadResult:
    encoded = urllib.parse.quote(doi, safe="")
    url = WILEY_API.format(doi=encoded)

    status, headers, body = _request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Wiley-TDM-Client-Token": token,
            "Accept": "application/pdf",
        },
    )

    if status == 200 and _looks_like_pdf(headers, body):
        tmp = output_path.with_suffix(output_path.suffix + ".part")
        tmp.write_bytes(body)
        tmp.replace(output_path)
        return DownloadResult(doi, "wiley", "downloaded", str(output_path), "정상 다운로드")

    return _failure_result(doi, "wiley", status, headers, body)


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
    if status == 403:
        state = "forbidden"
        message = "기관 구독 또는 API 권한이 확인되지 않음"
    elif status == 404:
        state = "not_found"
        message = "DOI를 찾지 못함"
    elif status == 429:
        state = "rate_limited"
        retry_after = headers.get("retry-after")
        message = "API 호출 한도 초과"
        if retry_after:
            message += f" (Retry-After: {retry_after})"
    elif status in (401,):
        state = "forbidden"
        message = "API 키 또는 토큰 인증 실패"
    else:
        state = "error"
        message = f"HTTP {status}"

    if body and len(body) < 1000:
        try:
            text = body.decode("utf-8", errors="replace").strip()
            if text:
                message += f" | {text[:300]}"
        except Exception:
            pass

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
