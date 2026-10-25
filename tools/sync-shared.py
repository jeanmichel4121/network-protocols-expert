#!/usr/bin/env python3
"""Propagate the template's shared blocks to every page.

CLAUDE.md: layout changes go into templates/protocol-template.html first, then are
propagated to every existing page. This copies, verbatim, from the template into
index.html and protocols/*/index.html:
  - the pre-paint script (theme + language before first paint),
  - the shared style block (first <style>),
  - the page library (window.NPE),
  - the site header and footer, keeping each page's path to the home page.
scripts/check_pages.py fails when a page drifts from the template.

Usage: python3 tools/sync-shared.py        (prints the pages updated)
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "templates" / "protocol-template.html"
BLOCKS = [
    re.compile(r"<script>\n/\* Runs before first paint.*?</script>", re.S),
    re.compile(r"<style>.*?</style>", re.S),
    re.compile(r"<script>\n/\* ===== Page library.*?</script>", re.S),
    re.compile(r'<header class="site-header">.*?</header>', re.S),
    re.compile(r'<footer class="site-footer">.*?</footer>', re.S),
]
# Home links keep the page's own path to the home page and the template's #fragment.
HOME_LINK = re.compile(r'href="([^"#]*)((?:#[^"]*)?)" data-home')


def split_head(text: str):
    i = text.find("<head>")
    return text[:i], text[i:]


def main() -> int:
    _, tpl = split_head(TEMPLATE.read_text(encoding="utf-8"))
    pages = [ROOT / "index.html", *sorted((ROOT / "protocols").glob("*/index.html"))]
    for page in pages:
        pre, text = split_head(page.read_text(encoding="utf-8"))
        old = text
        for rx in BLOCKS:
            src = rx.search(tpl).group(0)
            m = rx.search(text)
            if not m:
                print(f"{page.relative_to(ROOT)}: block not found: {rx.pattern[:40]}")
                return 1
            home = HOME_LINK.search(m.group(0))
            if home:
                base = home.group(1)
                src = HOME_LINK.sub(lambda h, base=base: f'href="{base}{h.group(2)}" data-home', src)
            text = text[: m.start()] + src + text[m.end() :]
        if text != old:
            page.write_text(pre + text, encoding="utf-8")
            print(f"updated {page.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
