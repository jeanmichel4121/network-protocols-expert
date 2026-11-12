#!/usr/bin/env python3
"""Assemble the published site in public/, one URL per language.

Each source page holds the four languages and switches in place (CLAUDE.md). Search
engines index one language per URL (Google: "use different URLs for each language
version"), so every page is written four times. A protocol page is also split into its
chapters, one URL each (ADR 0009), so a reader gets one chapter at a time:

    public/<lang>/index.html                  home, <html lang> = <lang>
    public/<lang>/<slug>/index.html           overview: header, chapter cards
    public/<lang>/<slug>/<chapter>/index.html one section (concepts, packets, ...)
    public/<lang>/<page>/index.html           an information page of pages/ (legal notice,
                                              terms of use, privacy, accessibility), whole

Chapter pages keep the page's shared CSS/JS (they stay self-contained), get the chapter
list and previous/next links, and every #anchor that moved to another chapter is
rewritten to that chapter's URL. Each copy gets <html lang>, <title>, description,
canonical, hreflang alternates (+ x-default), Open Graph and JSON-LD for its language,
taken from the page's <script type="application/json" id="page-meta">. Also written: a
root language chooser (/), 404.html, sitemap.xml, robots.txt, version.txt,
security.txt (RFC 9116) and /.well-known/tdmrep.json. Every page carries the text and
data mining reservation (TDMRep, W3C community report) stated in the terms of use, and
robots.txt asks the AI training crawlers to stay away (ADR 0011).

Usage: build_site.py [OUT_DIR]   (env SITE_URL, default https://learning.cuvelier.tech)
Standard library only.
"""

import datetime
import functools
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
AUTHOR = "Jean-Michel Cuvelier"
LICENSE_URL = "https://creativecommons.org/licenses/by-nc-sa/4.0/"
# Training crawlers asked not to collect the site (terms of use, section "Text and data
# mining"): tokens of crawlers that collect for AI training or training datasets, as their
# operators document them. Search engines (Googlebot, Bingbot, Applebot...) and fetches a
# person asks for are not concerned. __usage_ai-training is the shared AI training preference
# token (IETF individual draft draft-kelley-aipref-training-preference-signal), which the *
# group does not cover.
AI_TRAINING_BOTS = (
    "__usage_ai-training",
    "GPTBot",
    "ClaudeBot",
    "Google-Extended",
    "Applebot-Extended",
    "CCBot",
    "Meta-ExternalAgent",
    "Bytespider",
    "cohere-training-data-crawler",
    "AI2Bot",
    "Ai2Bot-Dolma",
    "PanguBot",
    "Webzio-Extended",
)
# Consent to keep data on this device (privacy page, ADR 0011) lasts six months, 183 days;
# "1" is the undated consent of v0.7.0, which the page library dates on the next page view.
CONSENT_MS = 183 * 86_400_000
KEPT = (
    f'(function (c) {{ return c === "1" || Date.now() - c < {CONSENT_MS}; }})'
    '(localStorage.getItem("npe-remember"))'
)
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
    if meta.get("kind") == "info":
        ld = {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": title,
            "description": meta["description"][lang],
            "url": url(lang, path),
            "inLanguage": lang,
            "isPartOf": {"@type": "WebSite", "name": BRAND, "url": f"{SITE}/"},
        }
        if meta.get("updated"):
            ld["dateModified"] = meta["updated"]
    elif meta.get("kind") == "home":
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
    ld["license"] = LICENSE_URL
    ld["author"] = {"@type": "Person", "name": AUTHOR, "url": "https://about.cuvelier.tech"}
    ld["copyrightHolder"] = ld["author"]
    tags.append('<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + "</script>")
    tags.append(TDM_META)
    return "\n".join(tags)


# Text and data mining reservation (Directive (EU) 2019/790 art. 4(3), Belgian Code of economic
# law art. XI.190, 20°) in the TDMRep form: the same signal is in /.well-known/tdmrep.json.
TDM_META = '<meta name="tdm-reservation" content="1">'


def tdmrep() -> str:
    return json.dumps([{"location": "/", "tdm-reservation": 1}], indent=2) + "\n"


def robots() -> str:
    blocked = "".join(f"User-agent: {bot}\nDisallow: /\n\n" for bot in AI_TRAINING_BOTS)
    return (
        "# Search engines are welcome. AI training crawlers are not: see the terms of use,\n"
        f"# {SITE}/en/terms/ (text and data mining reservation, also in /.well-known/tdmrep.json).\n"
        f"{blocked}User-agent: *\nAllow: /\n"
        "# AI usage preference of the IETF aipref working group (draft-ietf-aipref-attach).\n"
        f"Content-Usage: train-ai=n\n\nSitemap: {SITE}/sitemap.xml\n"
    )


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
        "Contact: mailto:jm@cuvelier.tech\n"
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
    if meta.get("kind") == "chapter":
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

    # A link to another protocol page (../<slug>/index.html in the source) goes to that page's
    # overview in the same language, whatever the depth of the page being built.
    # A fragment that names a chapter of that page goes to the chapter's own URL (ADR 0009).
    def other_page(m):
        slug, frag = m.group(1), m.group(2)
        if frag[1:] in chapter_ids(slug):
            return f'href="{home_href}{slug}/{frag[1:]}/"'
        return f'href="{home_href}{slug}/{frag}"'

    body = re.sub(r'href="\.\./([a-z0-9-]+)/index\.html((?:#[^"]*)?)"', other_page, body)
    sha = os.environ.get("CI_COMMIT_SHA", "local")[:8]
    body = body.replace("<code data-version>local</code>", f"<code data-version>{esc(sha)}</code>")
    return pre + sep + head + sep2 + body


@functools.cache
def chapter_ids(slug: str) -> frozenset:
    """Section ids of a protocol page: each one is published as a chapter."""
    src = ROOT / "protocols" / slug / "index.html"
    if not src.is_file():
        return frozenset()
    return frozenset(re.findall(r'<section class="sec" id="([^"]+)"', src.read_text(encoding="utf-8")))


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
    "seen": {
        "fr": "(déjà ouvert)",
        "en": "(already opened)",
        "nl": "(al geopend)",
        "de": "(bereits geöffnet)",
    },
    "resume": {"fr": "Reprendre :", "en": "Resume:", "nl": "Verdergaan:", "de": "Fortsetzen:"},
    "score": {"fr": "Quiz :", "en": "Quiz:", "nl": "Quiz:", "de": "Quiz:"},
    "menu": {
        "fr": "Liste des chapitres",
        "en": "Chapter list",
        "nl": "Lijst met hoofdstukken",
        "de": "Kapitelliste",
    },
    "prev": {"fr": "Précédent", "en": "Previous", "nl": "Vorige", "de": "Zurück"},
    "next": {"fr": "Suivant", "en": "Next", "nl": "Volgende", "de": "Weiter"},
}
PIN_ICON = (
    '<svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M9 4v16"/></svg>'
)
# Wide screens: the chapter list is open, and its button folds it away (choice kept in this tab,
# or on this device if the reader asked so: privacy page, ADR 0011; applied here, before the
# chapter is painted). Folded, pointing at the left edge shows the list; right after the click
# it stays away until the pointer has left.
PIN_SCRIPT = """(function () {
  var root = document.documentElement, nav = document.currentScript.parentNode;
  var pin = document.getElementById("toc-pin"), off = false;
  if (matchMedia("(min-width: 64rem)").matches) document.getElementById("toc").open = true;
  function box() {
    try { return __KEPT__ ? localStorage : sessionStorage; }
    catch (e) { return null; }
  }
  try { off = box().getItem("npe-nav") === "off"; } catch (e) {}
  function set() {
    root.classList.toggle("nav-off", off);
    pin.setAttribute("aria-expanded", String(!off));
  }
  set();
  pin.addEventListener("click", function () {
    off = !off;
    root.classList.toggle("nav-quiet", off);
    set();
    try { box().setItem("npe-nav", off ? "off" : "on"); } catch (e) {}
  });
  nav.addEventListener("mouseleave", function () { root.classList.remove("nav-quiet"); });
})();""".replace("__KEPT__", KEPT)
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
        item = f'<li><a href="{up}{sid}/" data-ch="{sid}"{cur if sid == here else ""}>'
        item += f'<span class="n">{num}</span>{label}</a>'
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
        '<nav class="toc" aria-labelledby="toc-h">\n'
        '  <button type="button" class="toc-pin icon-btn" id="toc-pin" aria-expanded="true" '
        f'aria-controls="toc">{PIN_ICON}<span class="sr-only">{spans(WORDS["menu"])}</span></button>\n'
        '  <details id="toc">\n'
        f'    <summary id="toc-h">{spans(of)}</summary>\n'
        f"    <ol>{''.join(items)}</ol>\n"
        "  </details>\n"
        f"  <script>{PIN_SCRIPT}</script>\n"
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


# One line icon per chapter (24 px grid, stroke only), drawn on the overview cards.
CHAPTER_ICONS = {
    "concepts": "M12 3a6 6 0 0 0-3.5 10.9V16h7v-2.1A6 6 0 0 0 12 3ZM9.5 19h5M10.5 22h3",
    "packets": "M3 5h18v14H3zM3 10h18M3 15h18M9 5v5M15 10v5",
    "operation": "M3 4h7v6H3zM14 14h7v6h-7zM10 7h5.5a2 2 0 0 1 2 2v5M14.5 11l3 3 3-3",
    "advanced": "M12 3l8 3v6c0 4.5-3.2 7.8-8 9-4.8-1.2-8-4.5-8-9V6zM9 12l2.2 2.2L15.5 10",
    "vendors": "M3 5h18v14H3zM7 10l3 2.5L7 15M12.5 15H17",
    "troubleshooting": (
        "M14.5 5.5a4 4 0 0 0-5.2 5.2L4 16v4h4l5.3-5.3a4 4 0 0 0 5.2-5.2l-2.7 2.7-2.6-.7-.7-2.6z"
    ),
    "quiz": (
        "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18ZM9.6 9.3a2.5 2.5 0 1 1 3.6 2.3c-.8.5-1.2 1-1.2 1.9M12 16.8v.1"
    ),
    "sources": "M6 3h12v18l-6-4-6 4zM9.5 8h5M9.5 11.5h5",
}
ICON = (
    '<span class="ci"><svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true" fill="none" '
    'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="{path}"/></svg></span>'
)


def chapter_icon(sid: str) -> str:
    path = CHAPTER_ICONS.get(sid)
    return ICON.format(path=path) if path else ""


def overview_cards(parts: dict) -> str:
    cards = []
    for sid, sec in parts["sections"]:
        num, label = parts["labels"][sid]
        desc = CHAPTER_DESC.get(sid)
        cd = spans({lang: desc[lang][0].upper() + desc[lang][1:] for lang in LANGS}) if desc else ""
        cc = count_label(sid, sec)
        cards.append(
            f'<li><a href="{sid}/" data-ch="{sid}">{chapter_icon(sid)}'
            f'<span class="ct"><span class="n">{num}</span>'
            f"<span>{label}</span></span>"
            + (f'<span class="cd">{cd}</span>' if cd else "")
            + (f'<span class="cc">{cc}</span>' if cc else "")
            + "</a></li>"
        )
    return (
        '<section class="sec" id="chapters" aria-labelledby="h-chapters">\n'
        f'<h2 id="h-chapters">{spans(WORDS["chapters"])}</h2>\n'
        f'<ol class="chap-cards">{"".join(cards)}</ol>\n'
        "</section>"
    )


def seen_marks(slug: str, here: str, name: str, labels: dict) -> str:
    """Per-reader conveniences of a protocol's pages, kept in localStorage only when the reader
    ticked "remember on this device" (npe-remember, privacy page; the pages work without): marks
    the chapters already opened (chapter list and overview cards), remembers the chapter being
    read (the home page offers to resume it) and the last quiz score (shown on the quiz card)."""
    word = json.dumps(f'<span class="sr-only"> {spans(WORDS["seen"])}</span>')
    last = json.dumps({"slug": slug, "ch": here, "name": name, "labels": labels}, ensure_ascii=False)
    score = json.dumps(f'<span class="cc score">{spans(WORDS["score"])} </span>')
    return (
        "<script>(function () {\n"
        "  try {\n"
        f'    var key = "npe-seen:{slug}", here = "{here}", store = localStorage;\n'
        f"    if (!{KEPT}) return;\n"
        '    var seen = JSON.parse(store.getItem(key) || "[]");\n'
        "    if (here) {\n"
        "      if (seen.indexOf(here) < 0) { seen.push(here); store.setItem(key, JSON.stringify(seen)); }\n"
        f'      store.setItem("npe-last", JSON.stringify({last}));\n'
        "    }\n"
        '    document.querySelectorAll("a[data-ch]").forEach(function (a) {\n'
        "      if (a.dataset.ch === here || seen.indexOf(a.dataset.ch) < 0) return;\n"
        f'      a.classList.add("seen"); a.insertAdjacentHTML("beforeend", {word});\n'
        "    });\n"
        f'    var quiz = store.getItem("npe-quiz:{slug}");\n'
        "    var card = document.querySelector('.chap-cards a[data-ch=\"quiz\"]');\n"
        "    if (quiz && /^\\d+ \\/ \\d+$/.test(quiz) && card) {\n"
        f'      card.insertAdjacentHTML("beforeend", {score});\n'
        "      card.lastElementChild.appendChild(document.createTextNode(quiz));\n"
        "    }\n"
        '    document.addEventListener("npe:quiz", function (e) {\n'
        f'      store.setItem("npe-quiz:{slug}", e.detail.ok + " / " + e.detail.total);\n'
        "    });\n"
        "  } catch (e) { /* storage unavailable: no marks */ }\n"
        "})();</script>"
    )


def resume_link() -> str:
    """Home page: a link back to the chapter this reader had open last (set by seen_marks)."""
    return (
        f'<p class="resume" id="resume" hidden>{spans(WORDS["resume"])} <a></a></p>\n'
        "<script>(function () {\n"
        "  try {\n"
        f"    if (!{KEPT}) return;\n"
        '    var last = JSON.parse(localStorage.getItem("npe-last") || "null");\n'
        '    var box = document.getElementById("resume");\n'
        "    if (!last || !/^[a-z0-9-]+$/.test(last.slug) || !/^[a-z0-9-]+$/.test(last.ch)) return;\n"
        '    var a = box.querySelector("a");\n'
        '    a.href = last.slug + "/" + last.ch + "/";\n'
        '    ["fr", "en", "nl", "de"].forEach(function (l) {\n'
        '      var s = document.createElement("span"); s.dataset.l = l;\n'
        '      s.textContent = last.name + ", " + ((last.labels || {})[l] || last.ch); a.appendChild(s);\n'
        "    });\n"
        "    box.hidden = false;\n"
        "  } catch (e) { /* storage unavailable: no link */ }\n"
        "})();</script>\n"
    )


TEXT_SKIP = re.compile(r"(<(script|style|pre|code|textarea)\b.*?</\2>|<[^>]+>)", re.S)


def french_spaces(page: str) -> str:
    """French puts a space before : ; ? ! and inside « »: make it a no-break space, so the mark
    never starts a line on its own. Text only; scripts, styles and code are left as they are."""
    parts = TEXT_SKIP.split(page)
    for k in range(0, len(parts), 3):
        parts[k] = re.sub(r" ([:;?!»])", "\u00a0\\1", parts[k]).replace("« ", "«\u00a0")
    return "".join(parts[k] for k in range(len(parts)) if k % 3 != 2)


PACKET_DATA = re.compile(r'<script type="application/json" data-packet="([a-z0-9-]+)">.*?</script>', re.S)


def with_packet_data(sec: str, data: dict) -> str:
    """A component may use a packet shown in another chapter (NPE.csum: data-packet, data-after):
    the chapter page gets a copy of that packet's JSON block, before the component runs."""
    present = set(PACKET_DATA.findall(sec))
    tags = re.findall(r"<(?!script)[a-z][^>]*>", sec)
    needed = {k for tag in tags for k in re.findall(r'\sdata-(?:packet|after)="([a-z0-9-]+)"', tag)} - present
    return "".join(data[k] for k in sorted(needed) if k in data) + sec


def old_anchors(owner: dict) -> str:
    """The overview URL was the whole page before ADR 0009: a link to one of its anchors
    (/fr/ethernet/#h-pkt-eth-ii) is sent on to the chapter that now holds that id."""
    moved = {i: sid for i, sid in owner.items() if sid}
    return (
        '<script type="application/json" id="anchor-map">'
        + json.dumps(moved, separators=(",", ":"), sort_keys=True)
        + "</script>\n<script>(function () {\n"
        + "  var id = decodeURIComponent(location.hash.slice(1));\n"
        + "  if (!id || document.getElementById(id)) return;\n"
        + '  var to = JSON.parse(document.getElementById("anchor-map").textContent)[id];\n'
        + '  if (to) location.replace(to + "/#" + encodeURIComponent(id));\n'
        + "})();</script>"
    )


def protocol_pages(slug: str, text: str, meta: dict, src: str) -> list:
    """[(path, meta, html)] for the overview and every chapter of one page."""
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
                old_anchors(owner)
                + "\n"
                + parts["crumbs"]
                + "\n"
                + relink(parts["hero"], "", owner)
                + "\n"
                + overview_cards(parts)
                + "\n"
                + seen_marks(slug, "", name, {}),
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
        content = (
            crumbs_to(parts["crumbs"], label)
            + "\n"
            + body
            + "\n"
            + pager(parts, sid)
            + "\n"
            + seen_marks(slug, sid, name, label_text[sid])
        )
        out.append((f"{slug}/{sid}/", cmeta, page(chapter_nav(parts, name, sid), content)))
    return out


def shared_blocks(home: str) -> dict:
    head = home[home.find("<head>") :]
    grab = lambda rx: re.search(rx, head, re.S).group(0)  # noqa: E731
    return {
        "early": grab(r"<script>\n/\* Runs before first paint.*?</script>"),
        "style": grab(r"<style>.*?</style>"),
        "icon": grab(r'<link rel="icon"[^>]*>'),
    }


# The information pages, as the footer of every other page names them.
INFO_PAGES = {
    "legal": dict(
        zip(LANGS, ("Mentions légales", "Legal notice", "Wettelijke vermeldingen", "Impressum"), strict=True)
    ),
    "terms": dict(
        zip(
            LANGS,
            ("Conditions d'utilisation", "Terms of use", "Gebruiksvoorwaarden", "Nutzungsbedingungen"),
            strict=True,
        )
    ),
    "privacy": dict(zip(LANGS, ("Vie privée", "Privacy", "Privacy", "Datenschutz"), strict=True)),
    "accessibility": dict(
        zip(LANGS, ("Accessibilité", "Accessibility", "Toegankelijkheid", "Barrierefreiheit"), strict=True)
    ),
}
INFO_CSS = """.legal { list-style: none; display: flex; flex-wrap: wrap; justify-content: center;
  gap: 0.25rem 1.25rem; padding: 0; margin: 0; font-size: 0.875rem; }
.legal a { display: inline-block; min-height: 24px; padding: 0.15rem 0; color: var(--muted); }"""


def info_links(langs: tuple) -> str:
    """The pages without the site footer (root chooser, 404) still link the information pages."""
    lists = []
    for lang in langs:
        attr = f' data-l="{lang}"' if len(langs) > 1 else ""
        items = "".join(
            f'<li><a href="/{lang}/{slug}/" hreflang="{lang}">{html.escape(names[lang])}</a></li>'
            for slug, names in INFO_PAGES.items()
        )
        lists.append(f'<ul class="legal"{attr}>{items}</ul>')
    return f'<nav aria-label="Legal">{"".join(lists)}</nav>'


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
<meta name="color-scheme" content="dark">
<title>{BRAND}</title>
<meta name="description" content="Expert-level network protocols in French, English, Dutch and German.">
<link rel="canonical" href="{SITE}/">
{TDM_META}
{alts}
<link rel="alternate" hreflang="x-default" href="{SITE}/">
{blocks["icon"]}
<script>
(function () {{
  var l = null;
  try {{
    var keep = {KEPT};
    l = (keep ? localStorage : sessionStorage).getItem("lang");
  }} catch (e) {{}}
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
.choose .legal a {{ display: inline-block; padding: 0.15rem 0; border: 0; background: none;
  color: var(--muted); }}
{INFO_CSS}
</style>
</head>
<body>
<main class="choose">
  <h1>{BRAND}</h1>
  <ul>
{links}
  </ul>
  {info_links(("en",))}
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
<meta name="color-scheme" content="dark">
<meta name="robots" content="noindex">
{TDM_META}
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
{INFO_CSS}
</style>
</head>
<body>
<main class="nf">
  <p class="code" aria-hidden="true">404</p>
  <h1>{L("Page introuvable", "Page not found", "Pagina niet gevonden", "Seite nicht gefunden")}</h1>
  <p><a href="/">{back}</a></p>
  {info_links(LANGS)}
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


def info_pages(out: pathlib.Path) -> list:
    """pages/<slug>/index.html (legal notice, terms, privacy, accessibility): one whole page per
    language at /<lang>/<slug>/. Returns their (path, meta) for the sitemap."""
    done = []
    for src in sorted((ROOT / "pages").glob("*/index.html")):
        slug, text = src.parent.name, src.read_text(encoding="utf-8")
        meta = meta_of(text, src)
        if meta.get("kind") != "info":
            sys.exit(f"{src}: page-meta kind must be 'info'")
        done.append((f"{slug}/", meta))
        for lang in LANGS:
            target = out / lang / slug / "index.html"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(french_spaces(localise(text, meta, lang, f"{slug}/", "../")), encoding="utf-8")
    return done


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

    # Suggested reading order (page-meta "order"), then slug: the layered model first,
    # then each layer bottom-up.
    protocols.sort(key=lambda p: (p[2].get("order", 999), p[0]))
    cards = "\n".join(card(meta, slug) for slug, _, meta in protocols)
    if cards:
        home = re.sub(r"<!--PROTOCOLS-->.*?<!--/PROTOCOLS-->", lambda _: cards, home, flags=re.S)

    if home.count('    <ul class="pcards">\n') != 1:
        sys.exit("index.html: expected one <ul class=pcards>")
    home = home.replace('    <ul class="pcards">\n', resume_link() + '    <ul class="pcards">\n', 1)

    pages = [("", home_meta)]
    for lang in LANGS:
        target = out / lang / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(french_spaces(localise(home, home_meta, lang, "", "./")), encoding="utf-8")
    for slug, text, meta in protocols:
        for path, pmeta, page in protocol_pages(slug, text, meta, f"protocols/{slug}/index.html"):
            if not pmeta.get("noindex"):
                pages.append((path, pmeta))
            for lang in LANGS:
                target = out / lang / path / "index.html"
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(
                    french_spaces(localise(page, pmeta, lang, path, "../" * path.count("/"))),
                    encoding="utf-8",
                )

    pages += info_pages(out)

    blocks = shared_blocks(home)
    (out / "index.html").write_text(chooser(blocks), encoding="utf-8")
    (out / "404.html").write_text(not_found(blocks), encoding="utf-8")
    (out / "sitemap.xml").write_text(sitemap(pages), encoding="utf-8")
    (out / "robots.txt").write_text(robots(), encoding="utf-8")
    (out / "version.txt").write_text(os.environ.get("CI_COMMIT_SHA", "local") + "\n", encoding="utf-8")
    # RFC 9116, also at the top level for clients that do not look in /.well-known/.
    sec = security_txt()
    (out / ".well-known").mkdir()
    (out / ".well-known" / "security.txt").write_text(sec, encoding="utf-8")
    (out / "security.txt").write_text(sec, encoding="utf-8")
    (out / ".well-known" / "tdmrep.json").write_text(tdmrep(), encoding="utf-8")

    for f in sorted(out.rglob("*")):
        if f.is_file():
            print(f.relative_to(out).as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main())
