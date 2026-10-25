#!/usr/bin/env python3
"""CI checks for every published HTML page (CLAUDE.md "HTML technical rules").

- The page is self-contained: no external script, stylesheet, font, image or fetch.
- The four languages are present: the page declares data-lang blocks or buttons
  for fr, en, nl and de.
Exit code 1 if any page fails.
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
LANGS = ("fr", "en", "nl", "de")

EXTERNAL = [
    (re.compile(r"<script[^>]+src\s*=\s*[\"']?(https?:)?//", re.I), "external <script src>"),
    (re.compile(r"<link[^>]+href\s*=\s*[\"']?(https?:)?//", re.I), "external <link href>"),
    (
        re.compile(r"<(img|source|video|audio|iframe)[^>]+src\s*=\s*[\"']?(https?:)?//", re.I),
        "external media",
    ),
    (re.compile(r"@import\s+(url\()?[\"']?(https?:)?//", re.I), "CSS @import of a remote file"),
    (re.compile(r"url\(\s*[\"']?(https?:)?//", re.I), "CSS url() to a remote file"),
    (re.compile(r"\bfetch\s*\(\s*[\"'`](https?:)?//", re.I), "fetch() to a remote URL"),
]


def pages():
    yield ROOT / "index.html"
    yield from sorted((ROOT / "protocols").glob("*/index.html"))
    tpl = ROOT / "templates" / "protocol-template.html"
    if tpl.exists():
        yield tpl


def check(path: pathlib.Path) -> list:
    text = path.read_text(encoding="utf-8")
    errs = [msg for rx, msg in EXTERNAL if rx.search(text)]
    for lang in LANGS:
        if not re.search(rf"data-lang\s*=\s*[\"']{lang}[\"']", text):
            errs.append(f"language '{lang}' missing (no data-lang=\"{lang}\")")
    return errs


def main() -> int:
    failed = 0
    for p in pages():
        if not p.exists():
            continue
        errs = check(p)
        rel = p.relative_to(ROOT)
        if errs:
            failed += 1
            for e in errs:
                print(f"FAIL {rel}: {e}")
        else:
            print(f"OK   {rel}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
