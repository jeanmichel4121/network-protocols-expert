#!/usr/bin/env python3
"""Assemble the published site in public/ — one URL per language.

Each source page holds the four languages and switches in place (CLAUDE.md). Search
engines index one language per URL (Google: "use different URLs for each language
version"), so every page is written four times:

    public/<lang>/index.html            home, <html lang> = <lang>
    public/<lang>/<slug>/index.html     protocol pages

Each copy gets <html lang>, <title>, description, canonical, hreflang alternates
(+ x-default), Open Graph and JSON-LD for its language, taken from the page's
<script type="application/json" id="page-meta">. Also written: a root language
chooser (/), 404.html, sitemap.xml, robots.txt and version.txt.

Usage: build_site.py [OUT_DIR]   (env SITE_URL, default https://learning.cuvelier.tech)
Standard library only.
"""

import html
import json
import os
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = os.environ.get("SITE_URL", "https://learning.cuvelier.tech").rstrip("/")
LANGS = ("fr", "en", "nl", "de")
NATIVE = {"fr": "Français", "en": "English", "nl": "Nederlands", "de": "Deutsch"}
OG_LOCALE = {"fr": "fr_BE", "en": "en_GB", "nl": "nl_BE", "de": "de_DE"}
BRAND = "Network Protocols Expert"
META_RE = re.compile(r'<script type="application/json" id="page-meta">\s*(.*?)\s*</script>', re.S)


def meta_of(text: str, src: pathlib.Path) -> dict:
    m = META_RE.search(text)
    if not m:
        sys.exit(f"{src}: missing <script type=application/json id=page-meta>")
    meta = json.loads(m.group(1))
    for key in ("title", "description"):
        missing = [lang for lang in LANGS if not meta.get(key, {}).get(lang)]
        if missing:
            sys.exit(f"{src}: page-meta {key} missing for {', '.join(missing)}")
    return meta


def url(lang: str, path: str) -> str:
    return f"{SITE}/{lang}/{path}"


def head_tags(meta: dict, lang: str, path: str) -> str:
    esc = lambda s: html.escape(s, quote=True)  # noqa: E731
    title = full_title(meta, lang)
    tags = [f'<link rel="canonical" href="{url(lang, path)}">']
    tags += [f'<link rel="alternate" hreflang="{alt}" href="{url(alt, path)}">' for alt in LANGS]
    # x-default: the language chooser for the home page, English for content pages.
    tags.append(
        f'<link rel="alternate" hreflang="x-default" href="{url("en", path) if path else SITE + "/"}">'
    )
    tags += [
        '<meta property="og:type" content="website">',
        f'<meta property="og:site_name" content="{BRAND}">',
        f'<meta property="og:title" content="{esc(title)}">',
        f'<meta property="og:description" content="{esc(meta["description"][lang])}">',
        f'<meta property="og:url" content="{url(lang, path)}">',
        f'<meta property="og:locale" content="{OG_LOCALE[lang]}">',
    ]
    tags += [f'<meta property="og:locale:alternate" content="{OG_LOCALE[o]}">' for o in LANGS if o != lang]
    if meta.get("kind") == "home":
        ld = {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": BRAND,
            "url": url(lang, ""),
            "inLanguage": lang,
            "description": meta["description"][lang],
        }
    else:
        ld = {
            "@context": "https://schema.org",
            "@type": "LearningResource",
            "name": title,
            "description": meta["description"][lang],
            "url": url(lang, path),
            "inLanguage": lang,
            "learningResourceType": "reference",
            "educationalLevel": "Expert",
            "teaches": meta.get("name", ""),
            "keywords": ", ".join(meta.get("tags", [])),
            "isPartOf": {"@type": "WebSite", "name": BRAND, "url": f"{SITE}/"},
        }
        if meta.get("updated"):
            ld["dateModified"] = meta["updated"]
    tags.append('<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + "</script>")
    return "\n".join(tags)


def full_title(meta: dict, lang: str) -> str:
    t = meta["title"][lang]
    return t if meta.get("kind") == "home" else f"{t} | {BRAND}"


def localise(text: str, meta: dict, lang: str, path: str, home_href: str) -> str:
    esc = lambda s: html.escape(s, quote=True)  # noqa: E731
    # Only touch real markup: comments above <head> may mention the same tags.
    pre, sep, rest = text.partition("<head>")
    pre = re.sub(r"<html lang=\"[a-z]{2}\">", f'<html lang="{lang}" data-built>', pre, count=1)
    head, sep2, body = rest.partition("</head>")
    head = re.sub(
        r"<title>.*?</title>",
        lambda _: f"<title>{esc(full_title(meta, lang))}</title>",
        head,
        count=1,
        flags=re.S,
    )
    head = re.sub(
        r'<meta name="description" content="[^"]*">',
        lambda _: (
            f'<meta name="description" content="{esc(meta["description"][lang])}">\n'
            + head_tags(meta, lang, path)
        ),
        head,
        count=1,
    )
    body = re.sub(r'href="[^"]*" data-home', f'href="{home_href}" data-home', body)
    return pre + sep + head + sep2 + body


def card(meta: dict, slug: str) -> str:
    def per_lang(key, cls):
        return "".join(
            f'<span class="{cls}" data-l="{lang}" lang="{lang}">{html.escape(meta[key][lang])}</span>'
            for lang in LANGS
        )

    tags = "".join(f"<span>{html.escape(t)}</span>" for t in meta.get("tags", []) + meta.get("standards", []))
    return (
        f'      <li><a class="pcard" href="{slug}/">'
        f'<span class="pname">{html.escape(meta.get("name", slug))}</span>'
        f'{per_lang("title", "pt")}{per_lang("description", "pd")}<span class="tags">{tags}</span></a></li>'
    )


def shared_blocks(home: str) -> dict:
    head = home[home.find("<head>") :]
    grab = lambda rx: re.search(rx, head, re.S).group(0)  # noqa: E731
    return {
        "early": grab(r"<script>\n/\* Runs before first paint.*?</script>"),
        "style": grab(r"<style>.*?</style>"),
        "icon": grab(r'<link rel="icon"[^>]*>'),
    }


def chooser(blocks: dict) -> str:
    """Root page (x-default): sends a returning visitor to their language, else lists the four."""
    links = "\n".join(
        f'    <li><a href="{lang}/" hreflang="{lang}" lang="{lang}"><strong>{NATIVE[lang]}</strong>'
        f"<span>{lang.upper()}</span></a></li>"
        for lang in LANGS
    )
    alts = "\n".join(f'<link rel="alternate" hreflang="{lang}" href="{url(lang, "")}">' for lang in LANGS)
    return f"""<!doctype html>
<html lang="en" data-built>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>{BRAND}</title>
<meta name="description" content="CCIE-level network protocol library in French, English, Dutch and German.">
<link rel="canonical" href="{SITE}/">
{alts}
<link rel="alternate" hreflang="x-default" href="{SITE}/">
{blocks["icon"]}
<script>
(function () {{
  var l = null;
  try {{ l = localStorage.getItem("lang"); }} catch (e) {{}}
  if (!l) l = (navigator.language || "en").slice(0, 2).toLowerCase();
  if (["fr", "en", "nl", "de"].indexOf(l) < 0) l = "en";
  location.replace(l + "/");
}})();
</script>
{blocks["early"]}
{blocks["style"]}
<style data-page>
.choose {{ min-height: 100dvh; display: grid; place-content: center; gap: 1.5rem;
  padding: 2rem 1rem; text-align: center; }}
.choose ul {{ list-style: none; padding: 0; margin: 0; display: grid;
  grid-template-columns: repeat(auto-fit, minmax(10rem, 1fr)); gap: 0.75rem; }}
.choose a {{ display: grid; gap: 0.2rem; padding: 1rem 1.25rem; border: 1px solid var(--line);
  border-radius: var(--radius); background: var(--surface); text-decoration: none; color: var(--fg); }}
.choose a:hover {{ border-color: var(--accent); }}
.choose a span {{ color: var(--muted); font: 600 0.8125rem var(--mono); }}
</style>
</head>
<body>
<main class="choose">
  <h1>{BRAND}</h1>
  <ul>
{links}
  </ul>
</main>
</body>
</html>
"""


def not_found(blocks: dict) -> str:
    def L(fr, en, nl, de):
        return (
            f'<span data-l="fr">{fr}</span><span data-l="en">{en}</span>'
            f'<span data-l="nl">{nl}</span><span data-l="de">{de}</span>'
        )

    back = L(
        "Retour à la bibliothèque",
        "Back to the library",
        "Terug naar de bibliotheek",
        "Zurück zur Bibliothek",
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<meta name="robots" content="noindex">
<title>404 | {BRAND}</title>
{blocks["icon"]}
{blocks["early"]}
<script>
(function () {{
  var m = location.pathname.match(/^\\/(fr|en|nl|de)\\//);
  if (m) document.documentElement.lang = m[1];
}})();
</script>
{blocks["style"]}
<style data-page>
.nf {{ min-height: 100dvh; display: grid; place-content: center; gap: 1rem;
  padding: 2rem 1rem; text-align: center; }}
.nf .code {{ font: 700 clamp(4rem, 12vw, 7rem)/1 var(--mono); color: var(--accent); }}
</style>
</head>
<body>
<main class="nf">
  <p class="code" aria-hidden="true">404</p>
  <h1>{L("Page introuvable", "Page not found", "Pagina niet gevonden", "Seite nicht gefunden")}</h1>
  <p><a href="/">{back}</a></p>
</main>
</body>
</html>
"""


def sitemap(pages: list) -> str:
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">',
    ]
    for path, meta in pages:
        for lang in LANGS:
            out.append(f"  <url><loc>{url(lang, path)}</loc>")
            if meta.get("updated"):
                out.append(f"    <lastmod>{meta['updated']}</lastmod>")
            for alt in LANGS:
                out.append(f'    <xhtml:link rel="alternate" hreflang="{alt}" href="{url(alt, path)}"/>')
            out.append("  </url>")
    out.append("</urlset>")
    return "\n".join(out) + "\n"


def main() -> int:
    out = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "public").resolve()
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    home_src = ROOT / "index.html"
    home = home_src.read_text(encoding="utf-8")
    home_meta = meta_of(home, home_src)
    protocols = []
    for src in sorted((ROOT / "protocols").glob("*/index.html")):
        text = src.read_text(encoding="utf-8")
        protocols.append((src.parent.name, text, meta_of(text, src)))

    cards = "\n".join(card(meta, slug) for slug, _, meta in protocols)
    if cards:
        home = re.sub(r"<!--PROTOCOLS-->.*?<!--/PROTOCOLS-->", lambda _: cards, home, flags=re.S)

    pages = [("", home_meta)]
    for lang in LANGS:
        target = out / lang / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(localise(home, home_meta, lang, "", "./"), encoding="utf-8")
    for slug, text, meta in protocols:
        pages.append((f"{slug}/", meta))
        for lang in LANGS:
            target = out / lang / slug / "index.html"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(localise(text, meta, lang, f"{slug}/", "../"), encoding="utf-8")

    blocks = shared_blocks(home)
    (out / "index.html").write_text(chooser(blocks), encoding="utf-8")
    (out / "404.html").write_text(not_found(blocks), encoding="utf-8")
    (out / "sitemap.xml").write_text(sitemap(pages), encoding="utf-8")
    (out / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8"
    )
    (out / "version.txt").write_text(os.environ.get("CI_COMMIT_SHA", "local") + "\n", encoding="utf-8")

    for f in sorted(out.rglob("*")):
        if f.is_file():
            print(f.relative_to(out).as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main())
