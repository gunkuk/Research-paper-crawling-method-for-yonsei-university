#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
import urllib.parse
import urllib.request
import webbrowser
from dataclasses import dataclass, asdict
from typing import Any

CROSSREF_API = "https://api.crossref.org/works"
YONSEI_OPENLINK = "https://openlink.access.yonsei.ac.kr/link.n2s?url={target}"
USER_AGENT = "yonsei-paper-helper/1.0 (+https://github.com/gunkuk/Research-paper-crawling-method-for-yonsei-university)"


@dataclass
class Paper:
    title: str
    authors: str
    year: str
    venue: str
    doi: str
    doi_url: str
    yonsei_openlink: str


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


def doi_url(doi: str) -> str:
    doi = normalize_doi(doi)
    return f"https://doi.org/{doi}"


def yonsei_openlink_url(target_url: str) -> str:
    encoded = urllib.parse.quote(target_url, safe="")
    return YONSEI_OPENLINK.format(target=encoded)


def _get_json(url: str) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.load(response)


def _first_text(value: Any) -> str:
    if isinstance(value, list) and value:
        return str(value[0])
    if value is None:
        return ""
    return str(value)


def _year_from_item(item: dict[str, Any]) -> str:
    for key in ("published-print", "published-online", "issued", "created"):
        parts = item.get(key, {}).get("date-parts")
        if parts and parts[0]:
            return str(parts[0][0])
    return ""


def paper_from_crossref_item(item: dict[str, Any]) -> Paper:
    title = _first_text(item.get("title"))
    authors = "; ".join(
        " ".join(filter(None, [a.get("given", ""), a.get("family", "")])).strip()
        for a in item.get("author", [])
    )
    venue = _first_text(item.get("container-title"))
    doi = normalize_doi(item.get("DOI", ""))
    target = doi_url(doi) if doi else item.get("URL", "")
    return Paper(
        title=title,
        authors=authors,
        year=_year_from_item(item),
        venue=venue,
        doi=doi,
        doi_url=target,
        yonsei_openlink=yonsei_openlink_url(target) if target else "",
    )


def search_crossref(query: str, rows: int = 10) -> list[Paper]:
    params = urllib.parse.urlencode({"query.bibliographic": query, "rows": rows})
    data = _get_json(f"{CROSSREF_API}?{params}")
    items = data.get("message", {}).get("items", [])
    return [paper_from_crossref_item(item) for item in items]


def lookup_doi(doi: str) -> Paper:
    doi = normalize_doi(doi)
    encoded = urllib.parse.quote(doi, safe="")
    data = _get_json(f"{CROSSREF_API}/{encoded}")
    return paper_from_crossref_item(data.get("message", {}))


def print_table(papers: list[Paper]) -> None:
    for i, paper in enumerate(papers, 1):
        print(f"[{i}] {paper.title}")
        if paper.authors:
            print(f"    Authors: {paper.authors}")
        if paper.year:
            print(f"    Year: {paper.year}")
        if paper.venue:
            print(f"    Venue: {paper.venue}")
        if paper.doi:
            print(f"    DOI: {paper.doi}")
        if paper.doi_url:
            print(f"    URL: {paper.doi_url}")
        if paper.yonsei_openlink:
            print(f"    Yonsei: {paper.yonsei_openlink}")


def write_csv(path: str, papers: list[Paper]) -> None:
    fields = list(asdict(Paper("", "", "", "", "", "", "")).keys())
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for paper in papers:
            writer.writerow(asdict(paper))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Search public paper metadata and generate Yonsei OpenLink URLs."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--query", help="Paper title or keyword query")
    group.add_argument("--doi", help="DOI or DOI URL")
    group.add_argument("--url", help="Existing article URL to wrap with Yonsei OpenLink")
    parser.add_argument("--rows", type=int, default=10, help="Number of Crossref results (default: 10)")
    parser.add_argument("--out", help="Write search/lookup results to CSV")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of human-readable text")
    parser.add_argument("--open", action="store_true", help="Open the generated Yonsei OpenLink in the browser")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        if args.url:
            link = yonsei_openlink_url(args.url)
            if args.json:
                print(json.dumps({"url": args.url, "yonsei_openlink": link}, ensure_ascii=False, indent=2))
            else:
                print(link)
            if args.open:
                webbrowser.open(link)
            return 0

        papers = search_crossref(args.query, args.rows) if args.query else [lookup_doi(args.doi)]

        if args.json:
            print(json.dumps([asdict(p) for p in papers], ensure_ascii=False, indent=2))
        else:
            print_table(papers)

        if args.out:
            write_csv(args.out, papers)

        if args.open:
            if len(papers) != 1:
                print("--open requires exactly one paper; use --doi for individual access.", file=sys.stderr)
                return 2
            if papers[0].yonsei_openlink:
                webbrowser.open(papers[0].yonsei_openlink)

        return 0

    except urllib.error.HTTPError as exc:
        print(f"HTTP error: {exc.code} {exc.reason}", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"Network error: {exc.reason}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
