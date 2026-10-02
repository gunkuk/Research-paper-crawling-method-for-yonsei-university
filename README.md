# Research Paper Crawling Method for Yonsei University

A small, reproducible helper for **paper metadata discovery** and **individual article access through Yonsei University Library's off-campus OpenLink**.

> This repository does **not** crawl publisher websites or automate subscription full-text downloads. Yonsei University Library and publishers such as IEEE restrict automated/systematic downloading of licensed electronic resources.

## What it does

1. Searches scholarly metadata through the public **Crossref REST API**.
2. Normalizes DOI metadata and optionally exports results to CSV.
3. Generates a Yonsei University **OpenLink** URL for an individual DOI/article URL.
4. Optionally opens that individual OpenLink URL in your browser, where normal Yonsei authentication can occur.

This separates **automatable public metadata collection** from **licensed full-text access**, which should remain an individual, user-initiated action.

## Requirements

- Python 3.10+
- A network connection
- For subscribed full text: an eligible Yonsei University Library account

No third-party Python packages are required.

## Quick start

Clone the repository and move into it:

```bash
git clone https://github.com/gunkuk/Research-paper-crawling-method-for-yonsei-university.git
cd Research-paper-crawling-method-for-yonsei-university
```

### 1. Search by title or keywords

```bash
python paper_search.py --query "deep residual learning image recognition" --rows 5
```

Example fields:

- title
- authors
- publication year
- venue
- DOI
- normal DOI URL
- Yonsei OpenLink URL

### 2. Look up one DOI

```bash
python paper_search.py --doi 10.1109/CVPR.2016.90
```

You can also supply a DOI URL:

```bash
python paper_search.py --doi https://doi.org/10.1109/CVPR.2016.90
```

### 3. Open one paper through Yonsei OpenLink

```bash
python paper_search.py --doi 10.1109/CVPR.2016.90 --open
```

Your browser opens the generated Yonsei OpenLink. If authentication is needed, complete it in the browser. The script does not store IDs, passwords, cookies, or publisher PDFs.

### 4. Convert an existing article URL to a Yonsei OpenLink

```bash
python paper_search.py --url "https://doi.org/10.1109/CVPR.2016.90"
```

Add `--open` to open it immediately:

```bash
python paper_search.py --url "https://doi.org/10.1109/CVPR.2016.90" --open
```

### 5. Export metadata

```bash
python paper_search.py --query "construction robotics" --rows 20 --out papers.csv
```

JSON output is also available:

```bash
python paper_search.py --query "construction robotics" --rows 5 --json
```

## Tests

```bash
python -m unittest discover -s tests -v
```

## Why full-text crawling is intentionally excluded

Yonsei University Library's electronic-resource fair-use notice identifies **automated downloading / web crawling of licensed e-resources** and excessive downloading as misuse. IEEE Xplore likewise prohibits robots or intelligent agents from systematically accessing or downloading its subscribed content.

For that reason, this project automates only public bibliographic metadata and URL preparation. Access to a subscribed article is performed individually in the user's browser through the institution's normal authentication path.

## Yonsei off-campus access

Yonsei's own guidance has documented OpenLink URLs in the form:

```text
https://openlink.access.yonsei.ac.kr/link.n2s?url=<target-url>
```

If Yonsei changes its proxy/OpenLink system, use the current route shown by the Yonsei University Library rather than hard-coding credentials or attempting to bypass authentication.

## Sources / policy references

- Yonsei University Department of Mathematics, paper-search guidance (off-campus OpenLink example):  
  https://math.yonsei.ac.kr/math/math/notice.do?articleNo=131640&mode=view
- Yonsei University Library e-resource fair-use notice (automated downloading / web crawling restrictions):  
  https://git.yonsei.ac.kr/git/news/academic.do?article.offset=210&articleLimit=10&articleNo=126987&mode=view
- IEEE Xplore legal information and bot policy:  
  https://ieeexplore.ieee.org/Xplorehelp/overview-of-ieee-xplore/legal-information
- Crossref REST API:  
  https://api.crossref.org/

## License

MIT. See [LICENSE](LICENSE).
