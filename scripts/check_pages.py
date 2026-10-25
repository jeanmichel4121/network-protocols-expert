#!/usr/bin/env python3
"""CI checks for every source page (CLAUDE.md "HTML technical rules", docs/web-standards.md).

- Self-contained: no external script, stylesheet, font, image or fetch.
- Four languages: language buttons for fr, en, nl, de, and the same number of
  data-l blocks in each language (a block is never left untranslated).
- page-meta: title and description in the four languages (used by build_site.py).
- Shared blocks (first <style>, page library) identical to the template's, so a
  layout change is always made in the template first and then propagated.
- Every <figure class="diagram"> has a title (figcaption) and a legend.
- Sample packets: every data-packet JSON block equals tools/packet-builder.py output.
- Published protocol pages contain no TEMPLATE placeholder.
Exit code 1 if any page fails.
"""

import importlib.util
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "templates" / "protocol-template.html"
LANGS = ("fr", "en", "nl", "de")

EXTERNAL = [
    (re.compile(r"<script[^>]+src\s*=\s*[\"']?(https?:)?//", re.I), "external <script src>"),
    (
        re.compile(
            r"<link[^>]+rel\s*=\s*[\"']?(stylesheet|preload|icon|modulepreload)[^>]+href\s*=\s*[\"']?(https?:)?//",
            re.I,
        ),
        "external <link> resource",
    ),
    (
        re.compile(r"<(img|source|video|audio|iframe)[^>]+src\s*=\s*[\"']?(https?:)?//", re.I),
        "external media",
    ),
    (re.compile(r"@import\s+(url\()?[\"']?(https?:)?//", re.I), "CSS @import of a remote file"),
    (re.compile(r"url\(\s*[\"']?(https?:)?//", re.I), "CSS url() to a remote file"),
    (re.compile(r"\bfetch\s*\(\s*[\"'`](https?:)?//", re.I), "fetch() to a remote URL"),
]
STYLE = re.compile(r"<style>.*?</style>", re.S)
LIBRARY = re.compile(r"<script>\n/\* ===== Page library.*?</script>", re.S)
META = re.compile(r'<script type="application/json" id="page-meta">\s*(.*?)\s*</script>', re.S)
PACKET = re.compile(r'<script type="application/json" data-packet="([a-z0-9-]+)">(.*?)</script>', re.S)
FIGURE = re.compile(r'<figure class="diagram[^"]*"[^>]*>(.*?)</figure>', re.S)


def builder():
    spec = importlib.util.spec_from_file_location("packet_builder", ROOT / "tools" / "packet-builder.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def pages():
    yield ROOT / "index.html"
    yield from sorted((ROOT / "protocols").glob("*/index.html"))
    yield TEMPLATE


def head_on(text: str) -> str:
    """Markup from <head> on: leading comments may quote tag names."""
    i = text.find("<head>")
    return text[i:] if i >= 0 else text


def check_languages(text: str) -> list:
    errs = []
    for lang in LANGS:
        if not re.search(rf"data-lang\s*=\s*[\"']{lang}[\"']", text):
            errs.append(f"language '{lang}' missing (no data-lang=\"{lang}\" button)")
    counts = {lang: len(re.findall(rf'data-l="{lang}"', text)) for lang in LANGS}
    if len(set(counts.values())) != 1:
        errs.append(f"unbalanced translations, data-l blocks per language: {counts}")
    return errs


def check_meta(text: str) -> list:
    m = META.search(text)
    if not m:
        return ["no <script type=application/json id=page-meta>"]
    try:
        meta = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        return [f"page-meta is not valid JSON: {e}"]
    errs = [
        f"page-meta {key} missing in '{lang}'"
        for key in ("title", "description")
        for lang in LANGS
        if not meta.get(key, {}).get(lang)
    ]
    errs += [
        f"page-meta description '{lang}' is {len(d)} chars (keep it under 200)"
        for lang, d in meta.get("description", {}).items()
        if len(d) > 200
    ]
    return errs


def check_shared(text: str, tpl: str) -> list:
    errs = []
    for name, rx in (("shared style block", STYLE), ("page library", LIBRARY)):
        a, b = rx.search(head_on(text)), rx.search(head_on(tpl))
        if not a or a.group(0) != b.group(0):
            errs.append(f"{name} differs from the template (change templates/ first, then propagate)")
    return errs


def check_figures(text: str) -> list:
    errs = []
    for i, fig in enumerate(FIGURE.findall(text), 1):
        if "<figcaption" not in fig:
            errs.append(f"diagram #{i} has no title (figcaption)")
        if 'class="legend"' not in fig:
            errs.append(f"diagram #{i} has no legend")
    return errs


def check_packets(text: str, path: pathlib.Path, pb) -> list:
    errs = []
    for sample, body in PACKET.findall(text):
        if sample not in pb.SAMPLES:
            errs.append(f"packet '{sample}' is not built by tools/packet-builder.py")
        elif body != pb.embed(sample):
            errs.append(
                f"packet '{sample}' differs from the builder output "
                f"(run: python3 tools/packet-builder.py --update {path.relative_to(ROOT)})"
            )
    return errs


def check(path: pathlib.Path, tpl: str, pb) -> list:
    text = path.read_text(encoding="utf-8")
    errs = [msg for rx, msg in EXTERNAL if rx.search(text)]
    errs += check_languages(text) + check_meta(text) + check_figures(text) + check_packets(text, path, pb)
    if path != TEMPLATE:
        errs += check_shared(text, tpl)
    if path.parent.parent == ROOT / "protocols" and ("data-tpl" in text or "⟨" in text):
        errs.append("TEMPLATE placeholder left in a published page (data-tpl or ⟨…⟩)")
    return errs


def main() -> int:
    tpl = TEMPLATE.read_text(encoding="utf-8")
    pb = builder()
    failed = 0
    for p in pages():
        if not p.exists():
            continue
        errs = check(p, tpl, pb)
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
