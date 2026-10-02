from __future__ import annotations

import argparse
import html
import re
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--identity-name", required=True)
    parser.add_argument("--publisher", required=True)
    parser.add_argument("--publisher-display-name", required=True)
    parser.add_argument("--display-name", default="Yonsei Paper Downloader")
    parser.add_argument("--version", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not re.fullmatch(r"\d+\.\d+\.\d+\.\d+", args.version):
        raise SystemExit("MSIX version must use four numeric parts, e.g. 1.0.0.0")

    replacements = {
        "{{IDENTITY_NAME}}": args.identity_name,
        "{{PUBLISHER}}": args.publisher,
        "{{PUBLISHER_DISPLAY_NAME}}": args.publisher_display_name,
        "{{DISPLAY_NAME}}": args.display_name,
        "{{VERSION}}": args.version,
    }

    text = Path(args.template).read_text(encoding="utf-8")

    for key, value in replacements.items():
        text = text.replace(key, html.escape(value, quote=True))

    Path(args.output).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
