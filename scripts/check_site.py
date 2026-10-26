#!/usr/bin/env python3
"""Check the built site (public/): HTML validity, links between pages, protocol index.

- every .html file parses without error under the HTML5 parsing algorithm (html5lib, strict);
- every internal href/src points to an existing file, and every #fragment to an existing id;
- every protocol page /<lang>/<slug>/ is linked from the home page of the same language;
- security.txt is present with the RFC 9116 required fields.

Usage: python3 scripts/check_site.py public
"""

import pathlib
import re
import sys
import urllib.parse

import html5lib

LANGS = ("fr", "en", "nl", "de")
ATTR = re.compile(r'\s(?:href|src)="([^"]*)"')
ID = re.compile(r'\sid="([^"]+)"')
SKIP = ("http://", "https://", "mailto:", "data:", "tel:", "javascript:")


def strip_scripts(text: str) -> str:
    """Script and style bodies may contain markup in strings; they are not links."""
    return re.sub(r"<(script|style)\b[^>]*>.*?</\1>", "", text, flags=re.S)


def validate(path: pathlib.Path) -> list:
    parser = html5lib.HTMLParser(strict=True, namespaceHTMLElements=False)
    try:
        parser.parse(path.read_bytes())
    except html5lib.html5parser.ParseError as exc:
        return [f"HTML parse error: {exc}"]
    return []


def target_of(page: pathlib.Path, root: pathlib.Path, url: str):
    parts = urllib.parse.urlsplit(url)
    if not parts.path:
        return page, parts.fragment
    base = root if parts.path.startswith("/") else page.parent
    target = (base / urllib.parse.unquote(parts.path.lstrip("/"))).resolve()
    if target.is_dir() or parts.path.endswith("/"):
        target = target / "index.html"
    return target, parts.fragment


def ids_of(target: pathlib.Path, cache: dict) -> set:
    if target not in cache:
        cache[target] = set(ID.findall(target.read_text(encoding="utf-8")))
    return cache[target]


def check_links(page: pathlib.Path, root: pathlib.Path, cache: dict) -> list:
    errs = []
    for url in sorted(set(ATTR.findall(strip_scripts(page.read_text(encoding="utf-8"))))):
        if not url or url.startswith(SKIP):
            continue
        target, frag = target_of(page, root, url)
        if not target.is_file():
            errs.append(f"broken link {url!r}: target not found")
        elif frag and target.suffix == ".html" and frag not in ids_of(target, cache):
            errs.append(f"broken anchor {url!r}: no element with id={frag!r}")
    return errs


def check_index(root: pathlib.Path) -> list:
    errs = []
    for lang in LANGS:
        home = root / lang / "index.html"
        if not home.is_file():
            errs.append(f"missing home page /{lang}/")
            continue
        links = set(ATTR.findall(home.read_text(encoding="utf-8")))
        for page in sorted((root / lang).glob("*/index.html")):
            slug = re.escape(page.parent.name)
            if not any(re.fullmatch(rf"(\./)?{slug}/(index\.html)?", u) for u in links):
                errs.append(f"/{lang}/ does not link to the protocol page /{lang}/{page.parent.name}/")
    return errs


def check_security_txt(root: pathlib.Path) -> list:
    path = root / ".well-known" / "security.txt"
    if not path.is_file():
        return ["missing /.well-known/security.txt"]
    text = path.read_text(encoding="utf-8")
    return [f"security.txt: missing {field}" for field in ("Contact:", "Expires:") if field not in text]


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    root = pathlib.Path(sys.argv[1]).resolve()
    cache: dict = {}
    failed = 0
    for page in sorted(root.rglob("*.html")):
        errs = validate(page) + check_links(page, root, cache)
        rel = page.relative_to(root)
        if errs:
            failed += 1
            print(f"FAIL {rel}")
            for err in errs:
                print(f"     - {err}")
        else:
            print(f"OK   {rel}")
    site_errs = check_index(root) + check_security_txt(root)
    for err in site_errs:
        print(f"FAIL site: {err}")
    return 1 if failed or site_errs else 0


if __name__ == "__main__":
    sys.exit(main())
