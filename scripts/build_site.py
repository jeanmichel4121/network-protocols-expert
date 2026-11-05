#!/usr/bin/env python3
"""Assemble the published site in public/, one URL per language.

Each source page holds the four languages and switches in place (CLAUDE.md). Search
engines index one language per URL (Google: "use different URLs for each language
version"), so every page is written four times. A protocol page is also split into its
chapters, one URL each (ADR 0009), so a reader gets one chapter at a time:

    public/<lang>/index.html                  home, <html lang> = <lang>
    public/<lang>/<slug>/index.html           overview: header, chapter cards
    public/<lang>/<slug>/<chapter>/index.html one section (concepts, packets, ...)
    public/<lang>/<slug>/all/index.html       the whole page, for print (noindex)

Chapter pages keep the page's shared CSS/JS (they stay self-contained), get the chapter
list and previous/next links, and every #anchor that moved to another chapter is
rewritten to that chapter's URL. Each copy gets <html lang>, <title>, description,
canonical, hreflang alternates (+ x-default), Open Graph and JSON-LD for its language,
taken from the page's <script type="application/json" id="page-meta">. Also written: a
root language chooser (/), 404.html, sitemap.xml, robots.txt, version.txt and
security.txt (RFC 9116).

Usage: build_site.py [OUT_DIR]   (env SITE_URL, default https://learning.cuvelier.tech)
Standard library only.
"""

import datetime
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
        # Chapters belong to their protocol overview, which lists them.
        if meta.get("part_of"):
            name, ppath = meta["part_of"][lang], meta["part_of_path"]
            ld["isPartOf"] = {"@type": "LearningResource", "name": name, "url": url(lang, ppath)}
        if meta.get("parts"):
            ld["hasPart"] = [
                {"@type": "LearningResource", "name": p["title"][lang], "url": url(lang, p["path"])}
                for p in meta["parts"]
            ]
        if meta.get("updated"):
            ld["dateModified"] = meta["updated"]
    ld["license"] = "https://creativecommons.org/licenses/by-sa/4.0/"
    ld["author"] = {"@type": "Person", "name": "Jean-Michel Cuvelier", "url": "https://about.cuvelier.tech"}
    tags.append('<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + "</script>")
    return "\n".join(tags)


def full_title(meta: dict, lang: str) -> str:
    t = meta["title"][lang]
    return t if meta.get("kind") == "home" else f"{t} | {BRAND}"


def security_txt() -> str:
    """RFC 9116 file; Expires is renewed by every deploy (180 days, under the 1-year limit)."""
    now = datetime.datetime.now(datetime.UTC).replace(microsecond=0)
    expires = now + datetime.timedelta(days=180)
    repo = "https://github.com/jeanmichel4121/network-protocols-expert"
    return (
        f"Contact: {repo}/security/advisories/new\n"
        f"Expires: {expires.isoformat().replace('+00:00', 'Z')}\n"
        "Preferred-Languages: fr, en, nl, de\n"
        f"Canonical: {SITE}/.well-known/security.txt\n"
        f"Policy: {repo}/blob/main/SECURITY.md\n"
    )


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
            + ('<meta name="robots" content="noindex">\n' if meta.get("noindex") else "")
            + head_tags(meta, lang, path)
        ),
        head,
        count=1,
    )
    if meta.get("kind") in ("chapter", "all"):
        # The in-page language switch retitles the page from #page-meta: give it this page's titles.
        js_meta = {k: meta[k] for k in ("slug", "name", "kind", "title", "description") if k in meta}
        head = META_RE.sub(
            lambda _: (
                '<script type="application/json" id="page-meta">\n'
                + json.dumps(js_meta, ensure_ascii=False)
                + "\n</script>"
            ),
            head,
            count=1,
        )
    body = re.sub(
        r'href="[^"#]*((?:#[^"]*)?)" data-home', lambda m: f'href="{home_href}{m.group(1)}" data-home', body
    )
    sha = os.environ.get("CI_COMMIT_SHA", "local")[:8]
    body = body.replace("<code data-version>local</code>", f"<code data-version>{esc(sha)}</code>")
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


# ----- Chapters (ADR 0009) ------------------------------------------------------------------

WORDS = {
    "overview": {"fr": "Vue d'ensemble", "en": "Overview", "nl": "Overzicht", "de": "Überblick"},
    "chapters": {"fr": "Chapitres", "en": "Chapters", "nl": "Hoofdstukken", "de": "Kapitel"},
    "all": {
        "fr": "Version complète (une page)",
        "en": "Full version (one page)",
        "nl": "Volledige versie (één pagina)",
        "de": "Vollständige Fassung (eine Seite)",
    },
    "all_note": {
        "fr": "pour l'impression ou une lecture d'une traite",
        "en": "to print or to read in one go",
        "nl": "om af te drukken of in één keer te lezen",
        "de": "zum Drucken oder zum Lesen am Stück",
    },
    "all_short": {
        "fr": "version complète",
        "en": "full version",
        "nl": "volledige versie",
        "de": "vollständige Fassung",
    },
    "prev": {"fr": "Précédent", "en": "Previous", "nl": "Vorige", "de": "Zurück"},
    "next": {"fr": "Suivant", "en": "Next", "nl": "Volgende", "de": "Weiter"},
}
SEP = {"fr": " : ", "en": ": ", "nl": ": ", "de": ": "}
# What each chapter holds: the card text on the overview and the description of the chapter URL.
CHAPTER_DESC = {
    "concepts": {
        "fr": "rôle, place dans la pile, terminologie, compromis de conception et variantes.",
        "en": "purpose, place in the stack, terminology, design trade-offs and variants.",
        "nl": "doel, plaats in de stack, terminologie, ontwerpafwegingen en varianten.",
        "de": "Zweck, Einordnung im Stack, Terminologie, Designabwägungen und Varianten.",
    },
    "packets": {
        "fr": "chaque format de message en diagramme de bits RFC et en arbre Wireshark synchronisés, "
        "sur des paquets générés par script.",
        "en": "every message format as a synchronised RFC bit diagram and Wireshark tree, "
        "on script-generated packets.",
        "nl": "elk berichtformaat als gesynchroniseerd RFC-bitdiagram en Wireshark-boom, "
        "op door een script gegenereerde pakketten.",
        "de": "jedes Nachrichtenformat als synchronisiertes RFC-Bitdiagramm und Wireshark-Baum, "
        "an per Skript erzeugten Paketen.",
    },
    "operation": {
        "fr": "fonctionnement pas à pas en animations numérotées, temporisateurs et valeurs par défaut.",
        "en": "step-by-step operation in numbered animations, timers and defaults.",
        "nl": "werking stap voor stap in genummerde animaties, timers en standaardwaarden.",
        "de": "Funktionsweise Schritt für Schritt in nummerierten Animationen, Timer und Standardwerte.",
    },
    "advanced": {
        "fr": "cas limites, interopérabilité, sécurité, limites d'échelle et ambiguïtés des normes.",
        "en": "edge cases, interoperability, security, scaling limits and ambiguities in the standards.",
        "nl": "randgevallen, interoperabiliteit, beveiliging, schaalgrenzen en dubbelzinnigheden "
        "in de standaarden.",
        "de": "Grenzfälle, Interoperabilität, Sicherheit, Skalierungsgrenzen und Mehrdeutigkeiten "
        "der Standards.",
    },
    "vendors": {
        "fr": "configuration, vérification et debug sur Cisco, Check Point, F5, Palo Alto, NetScaler et "
        "FortiGate, chaque commande avec sa source.",
        "en": "configuration, verification and debug on Cisco, Check Point, F5, Palo Alto, NetScaler and "
        "FortiGate, every command with its source.",
        "nl": "configuratie, verificatie en debug op Cisco, Check Point, F5, Palo Alto, NetScaler en "
        "FortiGate, elk commando met zijn bron.",
        "de": "Konfiguration, Verifikation und Debugging auf Cisco, Check Point, F5, Palo Alto, "
        "NetScaler und "
        "FortiGate, jeder Befehl mit Quelle.",
    },
    "troubleshooting": {
        "fr": "arbre de décision oui/non et tableau des pannes fréquentes, "
        "avec les commandes de vérification.",
        "en": "yes/no decision tree and table of common faults, with the verification commands.",
        "nl": "ja/nee-beslisboom en tabel met veelvoorkomende fouten, met de verificatiecommando's.",
        "de": "Ja/Nein-Entscheidungsbaum und Tabelle häufiger Fehler, mit den Prüfbefehlen.",
    },
    "quiz": {
        "fr": "questions de niveau expert, avec explication et référence pour chaque réponse.",
        "en": "expert-level questions, with an explanation and a reference for every answer.",
        "nl": "vragen op expertniveau, met uitleg en referentie bij elk antwoord.",
        "de": "Fragen auf Expertenniveau, mit Erklärung und Referenz zu jeder Antwort.",
    },
    "sources": {
        "fr": "normes, registres et documentation des vendeurs utilisés, avec les sections citées.",
        "en": "standards, registries and vendor documents used, with the sections cited.",
        "nl": "gebruikte standaarden, registers en vendordocumentatie, met de geciteerde secties.",
        "de": "verwendete Standards, Register und Herstellerdokumente, mit den zitierten Abschnitten.",
    },
}
# Counts shown on the chapter cards: (marker counted in the section, singular, plural).
COUNTS = {
    "packets": (
        '<article class="packet"',
        {"fr": "format", "en": "format", "nl": "formaat", "de": "Format"},
        {"fr": "formats", "en": "formats", "nl": "formaten", "de": "Formate"},
    ),
    "operation": (
        '<figure class="diagram anim"',
        {"fr": "animation", "en": "animation", "nl": "animatie", "de": "Animation"},
        {"fr": "animations", "en": "animations", "nl": "animaties", "de": "Animationen"},
    ),
    "vendors": (
        '<div role="tabpanel"',  # not the noscript CSS selector [role="tabpanel"]
        {"fr": "plateforme", "en": "platform", "nl": "platform", "de": "Plattform"},
        {"fr": "plateformes", "en": "platforms", "nl": "platformen", "de": "Plattformen"},
    ),
    "quiz": (
        '<fieldset class="quiz-q"',
        {"fr": "question", "en": "question", "nl": "vraag", "de": "Frage"},
        {"fr": "questions", "en": "questions", "nl": "vragen", "de": "Fragen"},
    ),
    "sources": (
        '<li id="src-',
        {"fr": "source", "en": "source", "nl": "bron", "de": "Quelle"},
        {"fr": "sources", "en": "sources", "nl": "bronnen", "de": "Quellen"},
    ),
}
ID_RE = re.compile(r'\sid="([^"]+)"')


def spans(words: dict) -> str:
    return "".join(f'<span data-l="{lang}">{html.escape(words[lang])}</span>' for lang in LANGS)


def text_of(fragment: str, lang: str) -> str:
    """Visible text of a fragment in one language (data-l blocks of the other languages dropped)."""
    other = "|".join(x for x in LANGS if x != lang)
    for _ in range(3):  # data-l blocks may nest one tag deep (<span data-l><code>...)
        fragment = re.sub(rf'<(\w+)[^>]*\sdata-l="(?:{other})"[^>]*>.*?</\1>', "", fragment, flags=re.S)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", fragment)).split())


def link_free(fragment: str) -> str:
    """A heading reused inside a link: no nested link, no duplicate id."""
    return ID_RE.sub("", re.sub(r"</?a\b[^>]*>", "", fragment))


def split_page(text: str, src: str) -> dict:
    main = re.search(r'<main id="main" tabindex="-1">(.*?)</main>', text, re.S)
    toc = re.search(r'<nav class="toc".*?</nav>\n?', text, re.S)
    if not main or not toc or toc.start() < main.end():
        sys.exit(f"{src}: expected <main id=main> followed by <nav class=toc>")
    inner = main.group(1)
    crumbs = re.search(r'<nav class="crumbs".*?</nav>', inner, re.S).group(0)
    hero = re.search(r'<header class="hero">.*?</header>', inner, re.S).group(0)
    sections = [
        (m.group(1), m.group(0))
        for m in re.finditer(r'<section class="sec" id="([a-z0-9-]+)"[^>]*>.*?</section>', inner, re.S)
    ]
    rest = inner.replace(crumbs, "").replace(hero, "")
    for _, sec in sections:
        rest = rest.replace(sec, "")
    if re.sub(r"<!--.*?-->|\s", "", rest, flags=re.S):
        sys.exit(f"{src}: content outside the hero and the <section class=sec> blocks: {rest.strip()[:80]}")
    labels = {
        m.group(1): (m.group(2), m.group(3))
        for m in re.finditer(
            r'<li><a href="#([a-z0-9-]+)"><span class="n">(\d+)</span>(.*?)</a></li>', toc.group(0)
        )
    }
    missing = [sid for sid, _ in sections if sid not in labels]
    if missing:
        sys.exit(f"{src}: sections missing from the table of contents: {', '.join(missing)}")
    return {
        "before": text[: main.start()],
        "between": text[main.end() : toc.start()],
        "after": text[toc.end() :],
        "toc": toc.group(0),
        "crumbs": crumbs,
        "hero": hero,
        "sections": sections,
        "labels": labels,
    }


def heading_ids(sid: str, sec: str) -> str:
    """Give every visible <h3> of a chapter an id, so the chapter list can link to it."""
    seen = set(ID_RE.findall(sec))

    def add(m):
        attrs, body = m.group(1), m.group(2)
        if ' id="' in attrs or "sr-only" in attrs:
            return m.group(0)
        base = re.sub(r"[^a-z0-9]+", "-", text_of(body, "en").lower()).strip("-")[:40].strip("-")
        hid, k = f"{sid}-{base or 'part'}", 2
        while hid in seen:
            hid, k = f"{sid}-{base}-{k}", k + 1
        seen.add(hid)
        return f'<h3 id="{hid}"{attrs}>{body}</h3>'

    return re.sub(r"<h3\b([^>]*)>(.*?)</h3>", add, sec, flags=re.S)


def relink(fragment: str, here: str, owner: dict) -> str:
    """#anchors that live in another chapter point to that chapter's URL."""

    def fix(m):
        frag = m.group(1)
        target = owner.get(frag)
        if target is None or target == here:
            return m.group(0)
        dest = ("../" if here else "") + (f"{target}/" if target else "")
        return f'href="{dest or "./"}"' if frag == target else f'href="{dest}#{frag}"'

    return re.sub(r'href="#([^"]+)"', fix, fragment)


def chapter_nav(parts: dict, name: str, here: str) -> str:
    up = "../" if here else ""
    cur = ' aria-current="page"'
    items = [
        f'<li><a href="{up or "./"}"{cur if not here else ""}><span class="n"></span>'
        f"{spans(WORDS['overview'])}</a></li>"
    ]
    for sid, sec in parts["sections"]:
        num, label = parts["labels"][sid]
        item = f'<li><a href="{up}{sid}/"{cur if sid == here else ""}><span class="n">{num}</span>{label}</a>'
        if sid == here:
            subs = [
                f'<li><a href="#{hid}">{link_free(body)}</a></li>'
                for hid, body in re.findall(r'<h3 id="([^"]+)"[^>]*>(.*?)</h3>', sec, re.S)
                if not hid.startswith("h-pkt-")
            ]
            if subs:
                item += '<ol class="sub">' + "".join(subs) + "</ol>"
        items.append(item + "</li>")
    of = {lang: f"{WORDS['chapters'][lang]} ({name})" for lang in LANGS}
    return (
        '<nav class="toc" aria-labelledby="toc-h">\n  <details id="toc">\n'
        f'    <summary id="toc-h">{spans(of)}</summary>\n'
        f"    <ol>{''.join(items)}</ol>\n"
        f'    <p class="all"><a href="{up}all/">{spans(WORDS["all"])}</a></p>\n'
        "  </details>\n"
        '  <script>if (matchMedia("(min-width: 64rem)").matches) '
        'document.getElementById("toc").open = true;</script>\n'
        "</nav>\n"
    )


def pager(parts: dict, here: str) -> str:
    ids = [sid for sid, _ in parts["sections"]]
    k = ids.index(here)
    links = []
    if k == 0:
        links.append(
            f'<a class="prev" href="../" rel="prev"><span class="pl">{spans(WORDS["prev"])}</span>'
            f"<span>{spans(WORDS['overview'])}</span></a>"
        )
    else:
        num, label = parts["labels"][ids[k - 1]]
        links.append(
            f'<a class="prev" href="../{ids[k - 1]}/" rel="prev">'
            f'<span class="pl">{spans(WORDS["prev"])}</span>'
            f"<span>{num}. {label}</span></a>"
        )
    if k + 1 < len(ids):
        num, label = parts["labels"][ids[k + 1]]
        links.append(
            f'<a class="next" href="../{ids[k + 1]}/" rel="next">'
            f'<span class="pl">{spans(WORDS["next"])}</span>'
            f"<span>{num}. {label}</span></a>"
        )
    return (
        f'<nav class="pager" data-aria="pager" aria-label="Previous and next chapter">{"".join(links)}</nav>'
    )


def as_chapter(sec: str) -> str:
    """The section heading becomes the page <h1>; a collapsible section is opened for good."""
    wrap = re.search(r"<details open>\s*<summary>\s*(<h2\b.*?</h2>)\s*</summary>", sec, re.S)
    if wrap:
        sec = sec[: wrap.start()] + wrap.group(1) + sec[wrap.end() :]
        sec, n = re.subn(r"</details>(\s*</section>)$", r"\1", sec)
        if n != 1 or sec.count("<details") != sec.count("</details>"):
            sys.exit("collapsible section: cannot find the closing </details> of its wrapper")
    return re.sub(r"<h2\b([^>]*)>(.*?)</h2>", r"<h1\1>\2</h1>", sec, count=1, flags=re.S)


def crumbs_to(crumbs: str, current: str) -> str:
    """Library / Protocol (link to the overview) / this page."""
    return re.sub(
        r'<li aria-current="page">(.*?)</li>',
        lambda m: f'<li><a href="../">{m.group(1)}</a></li><li aria-current="page">{current}</li>',
        crumbs,
        count=1,
        flags=re.S,
    )


def count_label(sid: str, sec: str) -> str:
    if sid not in COUNTS:
        return ""
    marker, one, many = COUNTS[sid]
    n = sec.count(marker)
    return spans({lang: f"{n} {(one if n == 1 else many)[lang]}" for lang in LANGS}) if n else ""


def overview_cards(parts: dict) -> str:
    cards = []
    for sid, sec in parts["sections"]:
        num, label = parts["labels"][sid]
        desc = CHAPTER_DESC.get(sid)
        cd = spans({lang: desc[lang][0].upper() + desc[lang][1:] for lang in LANGS}) if desc else ""
        cc = count_label(sid, sec)
        cards.append(
            f'<li><a href="{sid}/"><span class="ct"><span class="n">{num}</span><span>{label}</span></span>'
            + (f'<span class="cd">{cd}</span>' if cd else "")
            + (f'<span class="cc">{cc}</span>' if cc else "")
            + "</a></li>"
        )
    return (
        '<section class="sec" id="chapters" aria-labelledby="h-chapters">\n'
        f'<h2 id="h-chapters">{spans(WORDS["chapters"])}</h2>\n'
        f'<ol class="chap-cards">{"".join(cards)}</ol>\n'
        f'<p><a href="all/">{spans(WORDS["all"])}</a>, '
        f"{spans(WORDS['all_note'])}.</p>\n"
        "</section>"
    )


PACKET_DATA = re.compile(r'<script type="application/json" data-packet="([a-z0-9-]+)">.*?</script>', re.S)


def with_packet_data(sec: str, data: dict) -> str:
    """A component may use a packet shown in another chapter (NPE.csum: data-packet, data-after):
    the chapter page gets a copy of that packet's JSON block, before the component runs."""
    present = set(PACKET_DATA.findall(sec))
    tags = re.findall(r"<(?!script)[a-z][^>]*>", sec)
    needed = {k for tag in tags for k in re.findall(r'\sdata-(?:packet|after)="([a-z0-9-]+)"', tag)} - present
    return "".join(data[k] for k in sorted(needed) if k in data) + sec


def protocol_pages(slug: str, text: str, meta: dict, src: str) -> list:
    """[(path, meta, html)] for the overview, every chapter and the full version of one page."""
    parts = split_page(text, src)
    parts["sections"] = [(sid, heading_ids(sid, sec)) for sid, sec in parts["sections"]]
    owner = {i: "" for i in ID_RE.findall(parts["hero"])}
    for sid, sec in parts["sections"]:
        owner.update({i: sid for i in ID_RE.findall(sec)})
        owner[sid] = sid
    packet_data = {m.group(1): m.group(0) for m in PACKET_DATA.finditer(text)}
    name = meta.get("name", slug)
    label_text = {
        sid: {lang: text_of(lbl, lang) for lang in LANGS} for sid, (_, lbl) in parts["labels"].items()
    }

    if parts["before"].count('<div class="layout">\n') != 1:
        sys.exit(f"{src}: expected one <div class=layout> before <main>")

    def page(nav: str, content: str) -> str:
        before = parts["before"].replace('<div class="layout">\n', f'<div class="layout chap">\n{nav}', 1)
        return (
            before
            + '<main id="main" tabindex="-1">\n'
            + content
            + "\n</main>"
            + parts["between"]
            + parts["after"]
        )

    chapters = []
    for sid, _ in parts["sections"]:
        chapters.append(
            {"path": f"{slug}/{sid}/", "title": {lang: f"{label_text[sid][lang]} | {name}" for lang in LANGS}}
        )
    overview_meta = dict(meta, parts=chapters)
    out = [
        (
            f"{slug}/",
            overview_meta,
            page(
                chapter_nav(parts, name, ""),
                parts["crumbs"] + "\n" + relink(parts["hero"], "", owner) + "\n" + overview_cards(parts),
            ),
        )
    ]
    for sid, sec in parts["sections"]:
        label = parts["labels"][sid][1]
        cmeta = dict(
            meta,
            kind="chapter",
            title={lang: f"{label_text[sid][lang]} | {name}" for lang in LANGS},
            description={
                lang: f"{name}{SEP[lang]}{CHAPTER_DESC[sid][lang]}"
                if sid in CHAPTER_DESC
                else meta["description"][lang]
                for lang in LANGS
            },
            part_of=meta["title"],
            part_of_path=f"{slug}/",
        )
        cmeta.pop("parts", None)
        body = as_chapter(relink(with_packet_data(sec, packet_data), sid, owner)).replace(
            "<h1", f'<p class="eyebrow">{html.escape(name)}</p>\n<h1', 1
        )
        content = crumbs_to(parts["crumbs"], label) + "\n" + body + "\n" + pager(parts, sid)
        out.append((f"{slug}/{sid}/", cmeta, page(chapter_nav(parts, name, sid), content)))
    full = dict(
        meta,
        kind="all",
        noindex=True,
        title={lang: f"{meta['title'][lang]} ({WORDS['all_short'][lang]})" for lang in LANGS},
        part_of=meta["title"],
        part_of_path=f"{slug}/",
    )
    out.append(
        (
            f"{slug}/all/",
            full,
            text.replace(parts["crumbs"], crumbs_to(parts["crumbs"], spans(WORDS["all"])), 1),
        )
    )
    return out


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
        for path, pmeta, page in protocol_pages(slug, text, meta, f"protocols/{slug}/index.html"):
            if not pmeta.get("noindex"):
                pages.append((path, pmeta))
            for lang in LANGS:
                target = out / lang / path / "index.html"
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(
                    localise(page, pmeta, lang, path, "../" * path.count("/")), encoding="utf-8"
                )

    blocks = shared_blocks(home)
    (out / "index.html").write_text(chooser(blocks), encoding="utf-8")
    (out / "404.html").write_text(not_found(blocks), encoding="utf-8")
    (out / "sitemap.xml").write_text(sitemap(pages), encoding="utf-8")
    (out / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8"
    )
    (out / "version.txt").write_text(os.environ.get("CI_COMMIT_SHA", "local") + "\n", encoding="utf-8")
    # RFC 9116, also at the top level for clients that do not look in /.well-known/.
    sec = security_txt()
    (out / ".well-known").mkdir()
    (out / ".well-known" / "security.txt").write_text(sec, encoding="utf-8")
    (out / "security.txt").write_text(sec, encoding="utf-8")

    for f in sorted(out.rglob("*")):
        if f.is_file():
            print(f.relative_to(out).as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main())
