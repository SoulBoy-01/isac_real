from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from pypdf import PdfReader


KEYWORDS = (
    "abstract",
    "experiment",
    "measurement",
    "simulation",
    "displacement",
    "deformation",
    "phase",
    "frequency",
    "ghz",
    "accuracy",
    "resolution",
    "bridge",
    "field test",
    "conclusion",
)


def compact(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--pages", type=int, default=2)
    parser.add_argument("--context", type=int, default=280)
    parser.add_argument("--max-hits", type=int, default=30)
    parser.add_argument("--keywords", default="")
    args = parser.parse_args()

    reader = PdfReader(args.pdf)
    page_texts = [page.extract_text() or "" for page in reader.pages]
    print(f"FILE: {args.pdf.name}")
    print(f"PAGES: {len(page_texts)}")
    for page_index, text in enumerate(page_texts[: args.pages], start=1):
        print(f"\n--- FIRST PAGE {page_index} ---")
        print(compact(text)[:5000])

    keywords = tuple(
        item.strip().lower()
        for item in args.keywords.split(",")
        if item.strip()
    ) or KEYWORDS
    hits = 0
    seen: set[str] = set()
    for page_index, text in enumerate(page_texts, start=1):
        normalized = compact(text)
        lowered = normalized.lower()
        for keyword in keywords:
            start = 0
            while hits < args.max_hits:
                position = lowered.find(keyword, start)
                if position < 0:
                    break
                left = max(0, position - args.context)
                right = min(len(normalized), position + len(keyword) + args.context)
                excerpt = normalized[left:right]
                signature = excerpt[:160]
                if signature not in seen:
                    seen.add(signature)
                    print(f"\n--- HIT page={page_index} keyword={keyword} ---")
                    print(excerpt)
                    hits += 1
                start = position + len(keyword)
            if hits >= args.max_hits:
                break
        if hits >= args.max_hits:
            break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
