#!/usr/bin/env python3
"""Write the information pages (legal notice, terms of use, privacy, accessibility) from the
page template: same head, header, footer and library as a protocol page, with their own
crumbs, hero, sections and contents, in the four languages.

The pages are generated, never edited by hand: change the text here, then run
    python3 tools/info-pages.py            # rewrites pages/<slug>/index.html
    python3 tools/info-pages.py --check    # CI: fails if a page differs from this script
Run it again after a template change (tools/sync-shared.py only copies the shared blocks).
"""

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
TPL = (ROOT / "templates" / "protocol-template.html").read_text(encoding="utf-8")
L = ("fr", "en", "nl", "de")
UPDATED = "2026-11-08"
# Typography that looks machine-written (CLAUDE.md, writing style): dashes, ellipsis, curly quotes.
BAD = ("\u2014", "\u2013", "\u2026", "\u2018", "\u2019", "\u201c", "\u201d")
MAIL = '<a href="mailto:jm@cuvelier.tech">jm@cuvelier.tech</a>'
GH = "https://github.com/jeanmichel4121/network-protocols-expert"


def need(ok, what):
    """Stop the build on a writing-rule or structure error (not an assert: always checked)."""
    if not ok:
        sys.exit(f"info-pages: {what}")


def plain(*t):
    for x in t:
        for b in BAD:
            need(b not in x, f"typography {b!r} in {x[:80]!r}")
    return t


def sp(*t):
    need(len(t) == 4, f"four languages expected: {t!r}")
    return "".join(f'<span data-l="{lang}">{x}</span>' for lang, x in zip(L, plain(*t), strict=True))


def per(fmt, **kw):
    """One string per language from a dict of 4-tuples."""
    return tuple(fmt[lang].format(**{k: v[i] for k, v in kw.items()}) for i, lang in enumerate(L))


def P(*t, cls=""):
    c = f' class="{cls}"' if cls else ""
    return f"<p{c}>" + sp(*t) + "</p>\n"


def UL(items):
    return "<ul>" + "".join("<li>" + sp(*i) + "</li>" for i in items) + "</ul>\n"


def DL(rows):
    return (
        '<dl class="fields">'
        + "".join(f"<div><dt>{dt}</dt><dd>{sp(*dd)}</dd></div>" for dt, dd in rows)
        + "</dl>\n"
    )


def H3(*t):
    return "<h3>" + sp(*t) + "</h3>\n"


ICON = {
    "info": '<circle cx="12" cy="12" r="9.5"></circle><path d="M12 11v6M12 7.5v.5" stroke-linecap="round"></path>',
    "ok": '<circle cx="12" cy="12" r="9.5"></circle><path d="M7.5 12.5l3 3 6-6.5" stroke-linecap="round" stroke-linejoin="round"></path>',
    "lock": '<rect x="5" y="11" width="14" height="9.5" rx="2"></rect><path d="M8.5 11V8a3.5 3.5 0 0 1 7 0v3" stroke-linecap="round"></path>',
}


def CALLOUT(kind, icon, label, body):
    """A coloured box (template .callout): icon, bold label, then the body (paragraphs or a list)."""
    return (
        f'<div class="callout {kind}"><svg aria-hidden="true" fill="none" height="20" stroke="currentColor" '
        f'stroke-width="2" viewBox="0 0 24 24" width="20">{ICON[icon]}</svg><div>'
        f'<span class="label">{sp(*label)}</span>\n{body}</div></div>\n'
    )


def a(href, text):
    return f'<a href="{href}">{text}</a>'


def history(slug):
    return f"{GH}/commits/main/pages/{slug}/index.html"


DATE = ("8 novembre 2026", "8 November 2026", "8 november 2026", "8. November 2026")
DEED = {lang: f"https://creativecommons.org/licenses/by-nc-sa/4.0/deed.{lang}" for lang in L}
CODE = {lang: f"https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.{lang}" for lang in L}
APD_URL = (
    "https://www.autoriteprotectiondonnees.be/",
    "https://www.dataprotectionauthority.be/",
    "https://www.gegevensbeschermingsautoriteit.be/",
    "https://www.datenschutzbehorde.be/",
)
GDPR = "https://eur-lex.europa.eu/eli/reg/2016/679/oj"
EPRIVACY = "https://eur-lex.europa.eu/eli/dir/2002/58/oj"
DSM = "https://eur-lex.europa.eu/eli/dir/2019/790/oj"
AIACT = "https://eur-lex.europa.eu/eli/reg/2024/1689/oj"
TDMREP = "https://www.w3.org/community/reports/tdmrep/CG-FINAL-tdmrep-20240510/"
AIPREF = "https://datatracker.ietf.org/wg/aipref/about/"
WCAG = "https://www.w3.org/TR/WCAG22/"
SECTXT = "https://learning.cuvelier.tech/.well-known/security.txt"

# =============================================================================== legal notice
LEGAL = {
    "slug": "legal",
    "version": 2,
    "title": ("Mentions légales", "Legal notice", "Wettelijke vermeldingen", "Impressum"),
    "description": (
        "Éditeur, indépendance, contact, hébergement, rédaction, code source et marques du site Network Protocols Expert.",
        "Publisher, independence, contact, hosting, writing, source code and trademarks of the Network Protocols Expert site.",
        "Uitgever, onafhankelijkheid, contact, hosting, redactie, broncode en merken van de site Network Protocols Expert.",
        "Herausgeber, Unabhängigkeit, Kontakt, Hosting, Redaktion, Quellcode und Marken der Website Network Protocols Expert.",
    ),
    "lede": (
        "Qui publie ce site, qui le finance, comment joindre l'éditeur et où le site est hébergé.",
        "Who publishes this site, who funds it, how to reach the publisher and where the site is hosted.",
        "Wie deze site uitgeeft, wie ze financiert, hoe u de uitgever bereikt en waar de site gehost wordt.",
        "Wer diese Website herausgibt, wer sie finanziert, wie Sie den Herausgeber erreichen und wo die Website gehostet wird.",
    ),
    "sections": [
        (
            "publisher",
            ("Éditeur", "Publisher", "Uitgever", "Herausgeber"),
            P(
                "Network Protocols Expert est le site personnel de Jean-Michel Cuvelier, personne physique établie en Belgique. Le site est gratuit, sans publicité, sans compte et sans activité commerciale.",
                "Network Protocols Expert is the personal site of Jean-Michel Cuvelier, a private individual based in Belgium. The site is free, has no advertising, no account and no commercial activity.",
                "Network Protocols Expert is de persoonlijke site van Jean-Michel Cuvelier, natuurlijke persoon gevestigd in België. De site is gratis, zonder reclame, zonder account en zonder commerciële activiteit.",
                "Network Protocols Expert ist die private Website von Jean-Michel Cuvelier, einer in Belgien ansässigen Privatperson. Die Website ist kostenlos, werbefrei, ohne Konto und ohne gewerbliche Tätigkeit.",
            )
            + DL(
                [
                    (
                        sp("Éditeur", "Publisher", "Uitgever", "Herausgeber"),
                        (
                            "Jean-Michel Cuvelier, Belgique",
                            "Jean-Michel Cuvelier, Belgium",
                            "Jean-Michel Cuvelier, België",
                            "Jean-Michel Cuvelier, Belgien",
                        ),
                    ),
                    (
                        sp(
                            "Responsable de la publication",
                            "Responsible for the content",
                            "Verantwoordelijk voor de inhoud",
                            "Verantwortlich für den Inhalt",
                        ),
                        ("Jean-Michel Cuvelier",) * 4,
                    ),
                    (sp("Contact", "Contact", "Contact", "Kontakt"), (MAIL,) * 4),
                    (sp("Site", "Site", "Site", "Website"), ("https://learning.cuvelier.tech",) * 4),
                ]
            ),
        ),
        (
            "independence",
            ("Indépendance", "Independence", "Onafhankelijkheid", "Unabhängigkeit"),
            CALLOUT(
                "ok",
                "ok",
                (
                    "Aucune participation commerciale d'un tiers",
                    "No commercial involvement of any third party",
                    "Geen commerciële betrokkenheid van derden",
                    "Keine geschäftliche Beteiligung Dritter",
                ),
                P(
                    "Pas de sponsor, pas de publicité, pas de lien d'affiliation, pas de contenu payé ou commandé, pas de partenariat. Personne d'autre que l'auteur ne finance le site, et le site ne génère aucun revenu.",
                    "No sponsor, no advertising, no affiliate link, no paid or commissioned content, no partnership. Nobody but the author funds the site, and the site earns no revenue.",
                    "Geen sponsor, geen reclame, geen affiliatelinks, geen betaalde of bestelde inhoud, geen partnerschap. Niemand anders dan de auteur financiert de site, en de site brengt geen inkomsten op.",
                    "Kein Sponsor, keine Werbung, keine Affiliate-Links, keine bezahlten oder beauftragten Inhalte, keine Partnerschaft. Niemand außer dem Autor finanziert die Website, und sie erzielt keine Einnahmen.",
                ),
            )
            + P(
                "Les constructeurs traités (Cisco, Check Point, F5, Palo Alto Networks, NetScaler, Fortinet) n'ont ni financé, ni commandé, ni relu, ni approuvé le contenu. Ils sont présentés parce qu'on les rencontre souvent dans les réseaux d'entreprise, et leurs produits sont décrits d'après leur documentation publique.",
                "The vendors covered (Cisco, Check Point, F5, Palo Alto Networks, NetScaler, Fortinet) have not funded, commissioned, reviewed or approved the content. They are covered because they are common in enterprise networks, and their products are described from their public documentation.",
                "De behandelde vendors (Cisco, Check Point, F5, Palo Alto Networks, NetScaler, Fortinet) hebben de inhoud niet gefinancierd, besteld, nagelezen of goedgekeurd. Ze komen aan bod omdat ze vaak in bedrijfsnetwerken voorkomen, en hun producten worden beschreven op basis van hun openbare documentatie.",
                "Die behandelten Hersteller (Cisco, Check Point, F5, Palo Alto Networks, NetScaler, Fortinet) haben den Inhalt weder finanziert noch beauftragt, geprüft oder freigegeben. Sie werden behandelt, weil man sie in Unternehmensnetzen häufig antrifft, und ihre Produkte werden nach ihrer öffentlichen Dokumentation beschrieben.",
            ),
        ),
        (
            "contact",
            ("Contact", "Contact", "Contact", "Kontakt"),
            P(
                f"Pour toute question, écrivez à {MAIL}. Pour signaler une erreur dans une page, vous pouvez aussi ouvrir un ticket public sur {a(GH + '/issues/new/choose', 'GitHub')} (un compte GitHub est nécessaire). Une faille de sécurité se signale de manière confidentielle, selon le fichier {a(SECTXT, 'security.txt')}.",
                f"For any question, write to {MAIL}. To report an error in a page, you can also open a public issue on {a(GH + '/issues/new/choose', 'GitHub')} (a GitHub account is needed). A security issue is reported privately, as described in the {a(SECTXT, 'security.txt')} file.",
                f"Voor elke vraag kunt u schrijven naar {MAIL}. Een fout in een pagina kunt u ook melden met een openbaar ticket op {a(GH + '/issues/new/choose', 'GitHub')} (daarvoor is een GitHub-account nodig). Een beveiligingsprobleem meldt u vertrouwelijk, zoals beschreven in het bestand {a(SECTXT, 'security.txt')}.",
                f"Bei Fragen schreiben Sie an {MAIL}. Einen Fehler auf einer Seite können Sie auch mit einem öffentlichen Ticket auf {a(GH + '/issues/new/choose', 'GitHub')} melden (dafür ist ein GitHub-Konto nötig). Eine Sicherheitslücke melden Sie vertraulich, wie in der Datei {a(SECTXT, 'security.txt')} beschrieben.",
            ),
        ),
        (
            "hosting",
            ("Hébergement", "Hosting", "Hosting", "Hosting"),
            P(
                "Le site est hébergé par l'éditeur lui-même, sur un serveur situé en Belgique. Les serveurs DNS du domaine cuvelier.tech sont fournis par OVHcloud. Le certificat HTTPS est délivré par Let's Encrypt. Aucun réseau de diffusion de contenu (CDN) ni aucun service tiers n'intervient dans l'affichage des pages.",
                "The site is hosted by the publisher, on a server located in Belgium. The DNS servers of the cuvelier.tech domain are provided by OVHcloud. The HTTPS certificate is issued by Let's Encrypt. No content delivery network (CDN) and no third-party service takes part in displaying the pages.",
                "De site wordt door de uitgever zelf gehost, op een server in België. De DNS-servers van het domein cuvelier.tech worden geleverd door OVHcloud. Het HTTPS-certificaat wordt uitgegeven door Let's Encrypt. Geen content delivery network (CDN) en geen dienst van derden komt tussen bij het tonen van de pagina's.",
                "Die Website wird vom Herausgeber selbst auf einem Server in Belgien gehostet. Die DNS-Server der Domain cuvelier.tech stellt OVHcloud bereit. Das HTTPS-Zertifikat stellt Let's Encrypt aus. Kein Content Delivery Network (CDN) und kein Drittanbieter ist an der Anzeige der Seiten beteiligt.",
            ),
        ),
        (
            "source",
            (
                "Rédaction, contenu et code source",
                "Writing, content and source code",
                "Redactie, inhoud en broncode",
                "Redaktion, Inhalt und Quellcode",
            ),
            P(
                "Les textes sont rédigés avec l'aide d'outils d'IA, puis relus et vérifiés par l'auteur sur les sources citées. L'auteur en assume la responsabilité éditoriale.",
                "The texts are written with the help of AI tools, then reviewed and checked by the author against the cited sources. The author holds editorial responsibility for them.",
                "De teksten worden geschreven met hulp van AI-tools en daarna door de auteur nagelezen en getoetst aan de vermelde bronnen. De auteur draagt er de redactionele verantwoordelijkheid voor.",
                "Die Texte werden mit Hilfe von KI-Werkzeugen verfasst und anschließend vom Autor anhand der angegebenen Quellen geprüft. Der Autor trägt dafür die redaktionelle Verantwortung.",
            )
            + P(
                f"Le contenu est publié sous licence {a(DEED['fr'], 'CC BY-NC-SA 4.0')} et le code sous licence MIT. Les deux sont consultables dans un {a(GH, 'miroir public en lecture seule sur GitHub')}. Ce que vous pouvez en faire est précisé dans les {a('../terms/index.html', 'conditions d&#x27;utilisation')}.",
                f"The content is published under the {a(DEED['en'], 'CC BY-NC-SA 4.0')} licence and the code under the MIT licence. Both can be read in a {a(GH, 'public read-only mirror on GitHub')}. What you may do with them is set out in the {a('../terms/index.html', 'terms of use')}.",
                f"De inhoud wordt gepubliceerd onder de licentie {a(DEED['nl'], 'CC BY-NC-SA 4.0')} en de code onder de MIT-licentie. Beide staan in een {a(GH, 'openbare, alleen-lezen mirror op GitHub')}. Wat u ermee mag doen, staat in de {a('../terms/index.html', 'gebruiksvoorwaarden')}.",
                f"Der Inhalt steht unter der Lizenz {a(DEED['de'], 'CC BY-NC-SA 4.0')}, der Code unter der MIT-Lizenz. Beide sind in einem {a(GH, 'öffentlichen, schreibgeschützten Spiegel auf GitHub')} einsehbar. Was Sie damit tun dürfen, regeln die {a('../terms/index.html', 'Nutzungsbedingungen')}.",
            ),
        ),
        (
            "trademarks",
            ("Marques", "Trademarks", "Merken", "Marken"),
            P(
                "Cisco, IOS, NX-OS, Check Point, Gaia, F5, BIG-IP, Palo Alto Networks, PAN-OS, NetScaler, Fortinet, FortiGate, FortiOS et Wireshark sont des marques de leurs propriétaires respectifs. Elles ne sont citées que pour désigner les produits décrits. Ce site n'est ni affilié à ces entreprises, ni approuvé, ni financé par elles.",
                "Cisco, IOS, NX-OS, Check Point, Gaia, F5, BIG-IP, Palo Alto Networks, PAN-OS, NetScaler, Fortinet, FortiGate, FortiOS and Wireshark are trademarks of their respective owners. They are named only to identify the products described. This site is not affiliated with, endorsed by or funded by these companies.",
                "Cisco, IOS, NX-OS, Check Point, Gaia, F5, BIG-IP, Palo Alto Networks, PAN-OS, NetScaler, Fortinet, FortiGate, FortiOS en Wireshark zijn merken van hun respectieve eigenaars. Ze worden alleen genoemd om de beschreven producten aan te duiden. Deze site is niet verbonden met deze bedrijven en wordt niet door hen goedgekeurd of gefinancierd.",
                "Cisco, IOS, NX-OS, Check Point, Gaia, F5, BIG-IP, Palo Alto Networks, PAN-OS, NetScaler, Fortinet, FortiGate, FortiOS und Wireshark sind Marken ihrer jeweiligen Inhaber. Sie werden nur genannt, um die beschriebenen Produkte zu bezeichnen. Diese Website ist mit diesen Unternehmen nicht verbunden und wird von ihnen weder empfohlen noch finanziert.",
            )
            + P(
                "Les icônes de topologie réseau de la page d'accueil sont des icônes officielles de Cisco, utilisées sans modification selon les conditions de Cisco.",
                "The network topology icons of the home page are official Cisco icons, used unaltered under Cisco's terms.",
                "De netwerktopologie-iconen van de startpagina zijn officiële iconen van Cisco, ongewijzigd gebruikt volgens de voorwaarden van Cisco.",
                "Die Netzwerktopologie-Symbole der Startseite sind offizielle Symbole von Cisco, unverändert nach den Bedingungen von Cisco verwendet.",
            ),
        ),
    ],
}

# =============================================================================== terms of use
ATTR = "« Jean-Michel Cuvelier, Network Protocols Expert, https://learning.cuvelier.tech, CC BY-NC-SA 4.0 »"
ATTR_EN = '"Jean-Michel Cuvelier, Network Protocols Expert, https://learning.cuvelier.tech, CC BY-NC-SA 4.0"'
TRAIN = "<code>__usage_ai-training</code>"
USAGE = "<code>Content-Usage: train-ai=n</code>"
TERMS = {
    "slug": "terms",
    "version": 2,
    "title": ("Conditions d'utilisation", "Terms of use", "Gebruiksvoorwaarden", "Nutzungsbedingungen"),
    "description": (
        "Usage gratuit, licence CC BY-NC-SA 4.0, usage commercial sur autorisation, réserve de fouille de textes et d'entraînement d'IA, responsabilité.",
        "Free use, CC BY-NC-SA 4.0 licence, commercial use only with permission, text and data mining and AI training reserved, liability.",
        "Gratis gebruik, licentie CC BY-NC-SA 4.0, commercieel gebruik alleen met toestemming, voorbehoud voor tekst- en datamining en AI-training, aansprakelijkheid.",
        "Kostenlose Nutzung, Lizenz CC BY-NC-SA 4.0, kommerzielle Nutzung nur mit Erlaubnis, Vorbehalt für Text- und Data-Mining und KI-Training, Haftung.",
    ),
    "lede": (
        "Ce que vous pouvez faire avec ce site et son contenu, et ce qui demande une autorisation.",
        "What you may do with this site and its content, and what needs permission.",
        "Wat u met deze site en de inhoud mag doen, en waarvoor u toestemming nodig hebt.",
        "Was Sie mit dieser Website und ihrem Inhalt tun dürfen und wofür Sie eine Erlaubnis brauchen.",
    ),
    "sections": [
        (
            "summary",
            ("En bref", "In short", "In het kort", "Kurz gesagt"),
            '<div class="duo">\n'
            + CALLOUT(
                "ok",
                "ok",
                ("Libre et gratuit", "Free, no permission needed", "Vrij en gratis", "Frei und kostenlos"),
                UL(
                    [
                        (
                            "lire, apprendre et faire les quiz, y compris au travail ;",
                            "reading, learning and taking the quizzes, including at work;",
                            "lezen, leren en de quizzen maken, ook op het werk;",
                            "lesen, lernen und die Quizze lösen, auch bei der Arbeit;",
                        ),
                        (
                            "mettre un lien vers le site ou le montrer pendant un cours, même payant ;",
                            "linking to the site or showing it during a course, even a paid one;",
                            "naar de site linken of hem tonen tijdens een cursus, ook een betaalde;",
                            "auf die Website verlinken oder sie in einem Kurs zeigen, auch einem kostenpflichtigen;",
                        ),
                        (
                            "copier ou adapter le contenu sans but commercial, en citant la source, sous la même licence.",
                            "copying or adapting the content for a non-commercial purpose, with credit, under the same licence.",
                            "de inhoud kopiëren of bewerken zonder commercieel doel, met bronvermelding, onder dezelfde licentie.",
                            "den Inhalt ohne kommerziellen Zweck kopieren oder bearbeiten, mit Quellenangabe, unter derselben Lizenz.",
                        ),
                    ]
                ),
            )
            + CALLOUT(
                "vendor",
                "lock",
                (
                    "Sur autorisation écrite",
                    "Only with written permission",
                    "Alleen met schriftelijke toestemming",
                    "Nur mit schriftlicher Erlaubnis",
                ),
                UL(
                    [
                        (
                            "vendre le contenu ou l'intégrer dans un livre, un cours ou un support payants ;",
                            "selling the content or including it in a paid book, course or handout;",
                            "de inhoud verkopen of opnemen in een betaald boek, een betaalde cursus of syllabus;",
                            "den Inhalt verkaufen oder in ein kostenpflichtiges Buch, einen Kurs oder eine Unterlage aufnehmen;",
                        ),
                        (
                            "le republier sur un site ou dans une application financés par la publicité ou des abonnements ;",
                            "republishing it on a site or in an app funded by advertising or subscriptions;",
                            "hem opnieuw publiceren op een site of in een app die leeft van reclame of abonnementen;",
                            "ihn auf einer Website oder in einer App veröffentlichen, die sich durch Werbung oder Abonnements finanziert;",
                        ),
                        (
                            "le collecter pour entraîner un modèle d'intelligence artificielle commercial.",
                            "collecting it to train a commercial artificial intelligence model.",
                            "hem verzamelen om een commercieel AI-model te trainen.",
                            "ihn sammeln, um ein kommerzielles KI-Modell zu trainieren.",
                        ),
                    ]
                ),
            )
            + "</div>\n"
            + P(
                "Les sections suivantes donnent le détail. Elles seules font foi.",
                "The following sections give the details. They alone are binding.",
                "De volgende secties geven de details. Alleen zij zijn bindend.",
                "Die folgenden Abschnitte enthalten die Einzelheiten. Nur sie sind verbindlich.",
            ),
        ),
        (
            "scope",
            ("Objet", "Scope", "Toepassingsgebied", "Geltungsbereich"),
            P(
                "Ces conditions s'appliquent au site learning.cuvelier.tech et à son contenu. En utilisant le site, vous les acceptez. Le site est une bibliothèque d'apprentissage des protocoles réseau, gratuite et accessible sans compte.",
                "These terms apply to the learning.cuvelier.tech site and its content. By using the site, you accept them. The site is a learning library of network protocols, free and open without an account.",
                "Deze voorwaarden gelden voor de site learning.cuvelier.tech en de inhoud ervan. Door de site te gebruiken, aanvaardt u ze. De site is een leerbibliotheek over netwerkprotocollen, gratis en toegankelijk zonder account.",
                "Diese Bedingungen gelten für die Website learning.cuvelier.tech und ihren Inhalt. Mit der Nutzung der Website erkennen Sie sie an. Die Website ist eine Lernbibliothek über Netzwerkprotokolle, kostenlos und ohne Konto zugänglich.",
            ),
        ),
        (
            "free-use",
            ("Utilisation gratuite", "Free use", "Gratis gebruik", "Kostenlose Nutzung"),
            P(
                "Vous pouvez lire le site, apprendre, faire les quiz, imprimer des pages pour votre usage personnel et partager des liens, gratuitement, y compris dans le cadre de votre travail.",
                "You may read the site, learn, take the quizzes, print pages for your own use and share links, free of charge, including as part of your work.",
                "U mag de site lezen, leren, de quizzen maken, pagina's afdrukken voor eigen gebruik en links delen, gratis, ook in het kader van uw werk.",
                "Sie dürfen die Website lesen, lernen, die Quizze lösen, Seiten für den eigenen Gebrauch drucken und Links teilen, kostenlos, auch im Rahmen Ihrer Arbeit.",
            )
            + P(
                "Mettre un lien vers une page du site, ou la montrer en direct pendant une formation, même payante, est toujours permis : ce n'est pas une copie du contenu.",
                "Linking to a page of the site, or showing it live during a training session, even a paid one, is always allowed: it is not a copy of the content.",
                "Een link naar een pagina van de site plaatsen, of ze live tonen tijdens een opleiding, ook een betaalde, mag altijd: dat is geen kopie van de inhoud.",
                "Auf eine Seite der Website zu verlinken oder sie während einer Schulung live zu zeigen, auch einer kostenpflichtigen, ist immer erlaubt: Das ist keine Kopie des Inhalts.",
            ),
        ),
        (
            "licence",
            ("Licence du contenu", "Content licence", "Licentie van de inhoud", "Lizenz des Inhalts"),
            P(
                f"Le contenu (textes, schémas, animations, paquets d'exemple, quiz) est publié sous la licence {a(DEED['fr'], 'Creative Commons Attribution, Pas d&#x27;utilisation commerciale, Partage dans les mêmes conditions 4.0 International')} (CC BY-NC-SA 4.0). Vous pouvez le copier, le partager et l'adapter, à quatre conditions :",
                f"The content (texts, diagrams, animations, sample packets, quizzes) is published under the {a(DEED['en'], 'Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International')} licence (CC BY-NC-SA 4.0). You may copy, share and adapt it, on four conditions:",
                f"De inhoud (teksten, schema's, animaties, voorbeeldpakketten, quizzen) wordt gepubliceerd onder de licentie {a(DEED['nl'], 'Creative Commons Naamsvermelding-NietCommercieel-GelijkDelen 4.0 Internationaal')} (CC BY-NC-SA 4.0). U mag ze kopiëren, delen en bewerken, onder vier voorwaarden:",
                f"Der Inhalt (Texte, Diagramme, Animationen, Beispielpakete, Quizze) steht unter der Lizenz {a(DEED['de'], 'Creative Commons Namensnennung, Nicht kommerziell, Weitergabe unter gleichen Bedingungen 4.0 International')} (CC BY-NC-SA 4.0). Sie dürfen ihn kopieren, weitergeben und bearbeiten, unter vier Bedingungen:",
            )
            + UL(
                [
                    (
                        f"citer l'auteur, le site et la licence, par exemple : {ATTR} ;",
                        f"credit the author, the site and the licence, for example: {ATTR_EN};",
                        f"de auteur, de site en de licentie vermelden, bijvoorbeeld: {ATTR_EN};",
                        f"den Autor, die Website und die Lizenz nennen, zum Beispiel: {ATTR_EN};",
                    ),
                    (
                        "indiquer si vous avez modifié le contenu ;",
                        "state whether you changed the content;",
                        "aangeven of u de inhoud hebt gewijzigd;",
                        "angeben, ob Sie den Inhalt verändert haben;",
                    ),
                    (
                        "ne pas en faire un usage commercial (voir ci-dessous) ;",
                        "make no commercial use of it (see below);",
                        "er geen commercieel gebruik van maken (zie hieronder);",
                        "ihn nicht kommerziell nutzen (siehe unten);",
                    ),
                    (
                        "diffuser vos adaptations sous la même licence.",
                        "share your adaptations under the same licence.",
                        "uw bewerkingen onder dezelfde licentie verspreiden.",
                        "Ihre Bearbeitungen unter derselben Lizenz weitergeben.",
                    ),
                ]
            )
            + P(
                f"Le {a(CODE['fr'], 'texte juridique de la licence')} fait foi. Le code du site (scripts, outils, modèle de page) est publié sous licence MIT. La licence ne couvre ni les marques citées ni les icônes Cisco, qui gardent leurs propres conditions.",
                f"The {a(CODE['en'], 'legal code of the licence')} prevails. The site's code (scripts, tools, page template) is published under the MIT licence. The licence covers neither the trademarks named nor the Cisco icons, which keep their own terms.",
                f"De {a(CODE['nl'], 'juridische tekst van de licentie')} is bindend. De code van de site (scripts, tools, paginasjabloon) wordt gepubliceerd onder de MIT-licentie. De licentie dekt noch de genoemde merken, noch de iconen van Cisco, die hun eigen voorwaarden behouden.",
                f"Maßgeblich ist der {a(CODE['de'], 'Rechtstext der Lizenz')}. Der Code der Website (Skripte, Werkzeuge, Seitenvorlage) steht unter der MIT-Lizenz. Die Lizenz umfasst weder die genannten Marken noch die Cisco-Symbole, für die eigene Bedingungen gelten.",
            )
            + P(
                "Les versions publiées avant le 7 novembre 2026 l'ont été sous la licence CC BY-SA 4.0. Une licence Creative Commons ne se retire pas : les copies obtenues sous cette licence restent utilisables selon ses termes. Le contenu actuel n'est disponible que sous CC BY-NC-SA 4.0.",
                "Versions published before 7 November 2026 were released under the CC BY-SA 4.0 licence. A Creative Commons licence cannot be withdrawn: copies obtained under it remain usable on its terms. The current content is available only under CC BY-NC-SA 4.0.",
                "De versies die vóór 7 november 2026 verschenen, vielen onder de licentie CC BY-SA 4.0. Een Creative Commons-licentie kan niet worden ingetrokken: kopieën die onder die licentie werden verkregen, blijven bruikbaar volgens de voorwaarden ervan. De huidige inhoud is alleen beschikbaar onder CC BY-NC-SA 4.0.",
                "Vor dem 7. November 2026 veröffentlichte Versionen standen unter der Lizenz CC BY-SA 4.0. Eine Creative-Commons-Lizenz lässt sich nicht widerrufen: Unter ihr erhaltene Kopien bleiben nach ihren Bedingungen nutzbar. Der aktuelle Inhalt ist nur unter CC BY-NC-SA 4.0 verfügbar.",
            ),
        ),
        (
            "commercial",
            ("Usage commercial", "Commercial use", "Commercieel gebruik", "Kommerzielle Nutzung"),
            P(
                "Un usage commercial demande l'autorisation écrite préalable de l'auteur. La licence définit comme commercial un usage principalement destiné à obtenir un avantage commercial ou une rémunération. Par exemple :",
                "Commercial use needs the author's prior written permission. The licence defines as commercial a use primarily intended for or directed towards commercial advantage or monetary compensation. For example:",
                "Commercieel gebruik vereist de voorafgaande schriftelijke toestemming van de auteur. De licentie noemt commercieel: elk gebruik dat in de eerste plaats gericht is op commercieel voordeel of geldelijke vergoeding. Bijvoorbeeld:",
                "Eine kommerzielle Nutzung erfordert die vorherige schriftliche Erlaubnis des Autors. Die Lizenz versteht darunter eine Nutzung, die vorrangig auf einen geschäftlichen Vorteil oder eine Vergütung abzielt. Zum Beispiel:",
            )
            + UL(
                [
                    (
                        "vendre le contenu, ou l'intégrer dans un livre, un cours, une formation ou un support payants ;",
                        "selling the content, or including it in a paid book, course, training or handout;",
                        "de inhoud verkopen, of opnemen in een betaald boek, een betaalde cursus, opleiding of syllabus;",
                        "den Inhalt verkaufen oder in ein kostenpflichtiges Buch, einen Kurs, eine Schulung oder Unterlage aufnehmen;",
                    ),
                    (
                        "le republier sur un site ou dans une application qui vit de la publicité ou d'abonnements ;",
                        "republishing it on a site or in an app funded by advertising or subscriptions;",
                        "hem opnieuw publiceren op een site of in een app die leeft van reclame of abonnementen;",
                        "ihn auf einer Website oder in einer App veröffentlichen, die sich durch Werbung oder Abonnements finanziert;",
                    ),
                    (
                        "l'utiliser pour entraîner un modèle d'intelligence artificielle intégré à un produit ou à un service commercial.",
                        "using it to train an artificial intelligence model built into a commercial product or service.",
                        "hem gebruiken om een AI-model te trainen dat in een commercieel product of een commerciële dienst zit.",
                        "ihn zum Training eines KI-Modells verwenden, das in einem kommerziellen Produkt oder Dienst steckt.",
                    ),
                ]
            )
            + P(
                f"Lire le site pour apprendre, y compris au travail, n'est jamais un usage commercial au sens de ces conditions. En cas de doute, ou pour demander une autorisation, écrivez à {MAIL}.",
                f"Reading the site to learn, including at work, is never commercial use under these terms. If in doubt, or to ask for permission, write to {MAIL}.",
                f"De site lezen om te leren, ook op het werk, is nooit commercieel gebruik in de zin van deze voorwaarden. Bij twijfel, of om toestemming te vragen, schrijft u naar {MAIL}.",
                f"Die Website zum Lernen zu lesen, auch bei der Arbeit, ist nie eine kommerzielle Nutzung im Sinne dieser Bedingungen. Im Zweifel oder für eine Erlaubnis schreiben Sie an {MAIL}.",
            ),
        ),
        (
            "text-and-data-mining",
            (
                "Fouille de textes et de données, intelligence artificielle",
                "Text and data mining, artificial intelligence",
                "Tekst- en datamining, artificiële intelligentie",
                "Text- und Data-Mining, künstliche Intelligenz",
            ),
            P(
                f"L'auteur réserve expressément l'utilisation du contenu pour la fouille de textes et de données, au sens de l'article 4, paragraphe 3, de la {a(DSM, 'directive (UE) 2019/790')} et de l'article XI.190, 20°, du Code de droit économique belge. Cette réserve vise notamment la collecte du contenu pour entraîner des modèles d'intelligence artificielle.",
                f"The author expressly reserves the use of the content for text and data mining, within the meaning of Article 4(3) of {a(DSM, 'Directive (EU) 2019/790')} and Article XI.190, 20°, of the Belgian Code of Economic Law. This reservation covers in particular the collection of the content to train artificial intelligence models.",
                f"De auteur behoudt zich uitdrukkelijk het gebruik van de inhoud voor tekst- en datamining voor, in de zin van artikel 4, lid 3, van {a(DSM, 'richtlijn (EU) 2019/790')} en artikel XI.190, 20°, van het Belgische Wetboek van economisch recht. Dit voorbehoud geldt in het bijzonder voor het verzamelen van de inhoud om AI-modellen te trainen.",
                f"Der Autor behält sich die Nutzung des Inhalts für Text- und Data-Mining ausdrücklich vor, im Sinne von Artikel 4 Absatz 3 der {a(DSM, 'Richtlinie (EU) 2019/790')} und Artikel XI.190, 20°, des belgischen Wirtschaftsgesetzbuchs. Dieser Vorbehalt betrifft insbesondere das Sammeln des Inhalts zum Training von KI-Modellen.",
            )
            + P(
                f"La réserve est aussi exprimée par des moyens lisibles par machine, comme la loi le demande pour un contenu en ligne : la balise tdm-reservation de chaque page et le fichier /.well-known/tdmrep.json, selon le {a(TDMREP, 'protocole TDMRep')}, ainsi que le fichier robots.txt. Celui-ci demande aux robots d'entraînement connus de ne pas collecter le site et porte les deux signaux d'opposition à l'entraînement proposés à l'{a(AIPREF, 'IETF')} : le jeton commun {TRAIN} et la règle {USAGE}.",
                f"The reservation is also expressed by machine-readable means, as the law requires for online content: the tdm-reservation tag of every page and the /.well-known/tdmrep.json file, following the {a(TDMREP, 'TDMRep protocol')}, and the robots.txt file. That file asks the known training crawlers not to collect the site and carries the two AI training opt-out signals proposed at the {a(AIPREF, 'IETF')}: the shared {TRAIN} token and the {USAGE} rule.",
                f"Het voorbehoud wordt ook uitgedrukt met machineleesbare middelen, zoals de wet dat voor online inhoud vraagt: de tag tdm-reservation op elke pagina en het bestand /.well-known/tdmrep.json, volgens het {a(TDMREP, 'TDMRep-protocol')}, en het bestand robots.txt. Dat vraagt de bekende trainingsrobots de site niet te verzamelen en bevat de twee signalen tegen AI-training die bij de {a(AIPREF, 'IETF')} zijn voorgesteld: het gedeelde token {TRAIN} en de regel {USAGE}.",
                f"Der Vorbehalt ist auch maschinenlesbar erklärt, wie es das Gesetz für Online-Inhalte verlangt: mit dem Tag tdm-reservation auf jeder Seite und der Datei /.well-known/tdmrep.json nach dem {a(TDMREP, 'TDMRep-Protokoll')} sowie mit der Datei robots.txt. Sie bittet die bekannten Trainings-Crawler, die Website nicht zu sammeln, und enthält die beiden bei der {a(AIPREF, 'IETF')} vorgeschlagenen Signale gegen KI-Training: das gemeinsame Token {TRAIN} und die Regel {USAGE}.",
            )
            + P(
                f"Le {a(AIACT, 'règlement (UE) 2024/1689 sur l&#x27;intelligence artificielle')} (article 53, paragraphe 1, point c) oblige les fournisseurs de modèles d'IA à usage général à identifier et à respecter une telle réserve.",
                f"The {a(AIACT, 'Artificial Intelligence Act, Regulation (EU) 2024/1689')} (Article 53(1)(c)) requires providers of general-purpose AI models to identify and comply with such a reservation.",
                f"De {a(AIACT, 'AI-verordening (EU) 2024/1689')} (artikel 53, lid 1, punt c) verplicht aanbieders van AI-modellen voor algemene doeleinden zo een voorbehoud te herkennen en na te leven.",
                f"Die {a(AIACT, 'KI-Verordnung (EU) 2024/1689')} (Artikel 53 Absatz 1 Buchstabe c) verpflichtet Anbieter von KI-Modellen mit allgemeinem Verwendungszweck, einen solchen Vorbehalt zu ermitteln und einzuhalten.",
            )
            + P(
                "Cette réserve ne limite ni l'indexation par les moteurs de recherche, ni la fouille à des fins de recherche scientifique que la loi autorise, ni les usages non commerciaux permis par la licence.",
                "This reservation does not limit indexing by search engines, text and data mining for scientific research as allowed by law, or the non-commercial uses permitted by the licence.",
                "Dit voorbehoud beperkt niet de indexering door zoekmachines, niet de datamining voor wetenschappelijk onderzoek die de wet toestaat en niet het niet-commerciële gebruik dat de licentie toelaat.",
                "Dieser Vorbehalt schränkt weder die Indexierung durch Suchmaschinen noch das gesetzlich erlaubte Text- und Data-Mining für die wissenschaftliche Forschung noch die nicht kommerziellen Nutzungen ein, die die Lizenz erlaubt.",
            ),
        ),
        (
            "liability",
            (
                "Exactitude et responsabilité",
                "Accuracy and liability",
                "Juistheid en aansprakelijkheid",
                "Richtigkeit und Haftung",
            ),
            P(
                "Le contenu est rédigé avec soin et vérifié sur les sources citées (RFC, IEEE, IANA, documentation des constructeurs). Il est fourni à titre d'information et d'apprentissage, sans garantie d'exactitude, d'exhaustivité ni de mise à jour.",
                "The content is written with care and checked against the cited sources (RFC, IEEE, IANA, vendor documentation). It is provided for information and learning, with no guarantee of accuracy, completeness or currency.",
                "De inhoud is zorgvuldig geschreven en getoetst aan de vermelde bronnen (RFC, IEEE, IANA, documentatie van de vendors). Hij wordt aangeboden ter informatie en om te leren, zonder garantie op juistheid, volledigheid of actualiteit.",
                "Der Inhalt wird sorgfältig verfasst und anhand der angegebenen Quellen geprüft (RFC, IEEE, IANA, Herstellerdokumentation). Er dient der Information und dem Lernen, ohne Gewähr für Richtigkeit, Vollständigkeit oder Aktualität.",
            )
            + P(
                "Les commandes, en particulier les commandes de débogage et de capture, peuvent ralentir ou perturber un équipement en production. Vérifiez-les dans la documentation de votre version et essayez-les d'abord sur un équipement de test. Dans les limites permises par la loi, l'auteur ne répond pas des conséquences de l'utilisation du contenu.",
                "Commands, especially debug and capture commands, can slow down or disrupt a device in production. Check them in the documentation of your version and try them on a test device first. To the extent permitted by law, the author is not liable for the consequences of using the content.",
                "Commando's, vooral debug- en capturecommando's, kunnen een toestel in productie vertragen of verstoren. Controleer ze in de documentatie van uw versie en probeer ze eerst op een testtoestel. Binnen de grenzen van de wet is de auteur niet aansprakelijk voor de gevolgen van het gebruik van de inhoud.",
                "Befehle, vor allem Debug- und Mitschnittbefehle, können ein Gerät im Produktivbetrieb verlangsamen oder stören. Prüfen Sie sie in der Dokumentation Ihrer Version und testen Sie sie zuerst auf einem Testgerät. Soweit gesetzlich zulässig, haftet der Autor nicht für die Folgen der Nutzung des Inhalts.",
            ),
        ),
        (
            "links",
            (
                "Liens vers d'autres sites",
                "Links to other sites",
                "Links naar andere sites",
                "Links zu anderen Websites",
            ),
            P(
                "Les pages renvoient vers des sites externes (RFC Editor, IANA, IEEE, constructeurs, GitHub). L'auteur ne contrôle pas ces sites et ne répond pas de leur contenu. Leurs propres conditions et règles de confidentialité s'appliquent.",
                "The pages link to external sites (RFC Editor, IANA, IEEE, vendors, GitHub). The author does not control these sites and is not responsible for their content. Their own terms and privacy rules apply.",
                "De pagina's verwijzen naar externe sites (RFC Editor, IANA, IEEE, vendors, GitHub). De auteur heeft geen controle over die sites en is niet verantwoordelijk voor hun inhoud. Hun eigen voorwaarden en privacyregels zijn van toepassing.",
                "Die Seiten verweisen auf externe Websites (RFC Editor, IANA, IEEE, Hersteller, GitHub). Der Autor hat keinen Einfluss auf diese Websites und ist für ihren Inhalt nicht verantwortlich. Es gelten deren eigene Bedingungen und Datenschutzregeln.",
            ),
        ),
        (
            "availability",
            ("Disponibilité", "Availability", "Beschikbaarheid", "Verfügbarkeit"),
            P(
                "Le site est fourni tel quel. L'auteur peut le modifier, l'interrompre ou le retirer à tout moment, sans préavis.",
                "The site is provided as is. The author may change, suspend or withdraw it at any time, without notice.",
                "De site wordt aangeboden zoals hij is. De auteur kan hem op elk moment en zonder voorafgaande kennisgeving wijzigen, onderbreken of stopzetten.",
                "Die Website wird so bereitgestellt, wie sie ist. Der Autor kann sie jederzeit und ohne Vorankündigung ändern, unterbrechen oder einstellen.",
            ),
        ),
        (
            "conduct",
            (
                "Bon usage et sécurité",
                "Proper use and security",
                "Correct gebruik en beveiliging",
                "Ordnungsgemäße Nutzung und Sicherheit",
            ),
            P(
                f"N'essayez pas de contourner la sécurité du site ni de le surcharger, par exemple avec un robot trop rapide. Si vous découvrez une faille, signalez-la de manière confidentielle selon le fichier {a(SECTXT, 'security.txt')}, sans l'exploiter au-delà de ce qui est nécessaire pour la démontrer et sans la rendre publique avant sa correction.",
                f"Do not try to bypass the site's security or to overload it, for example with a crawler that is too fast. If you find a vulnerability, report it privately as described in the {a(SECTXT, 'security.txt')} file, without exploiting it beyond what is needed to demonstrate it and without making it public before it is fixed.",
                f"Probeer de beveiliging van de site niet te omzeilen en de site niet te overbelasten, bijvoorbeeld met een te snelle robot. Vindt u een kwetsbaarheid, meld die dan vertrouwelijk zoals beschreven in het bestand {a(SECTXT, 'security.txt')}, zonder ze verder te misbruiken dan nodig is om ze aan te tonen en zonder ze openbaar te maken voordat ze verholpen is.",
                f"Versuchen Sie nicht, die Sicherheit der Website zu umgehen oder sie zu überlasten, etwa mit einem zu schnellen Crawler. Wenn Sie eine Sicherheitslücke finden, melden Sie sie vertraulich, wie in der Datei {a(SECTXT, 'security.txt')} beschrieben, ohne sie weiter auszunutzen, als zum Nachweis nötig ist, und ohne sie vor ihrer Behebung zu veröffentlichen.",
            ),
        ),
        (
            "errors",
            ("Signaler une erreur", "Reporting an error", "Een fout melden", "Fehler melden"),
            P(
                f"Si vous trouvez une erreur, signalez-la à {MAIL} ou par un {a(GH + '/issues/new/choose', 'ticket public sur GitHub')}. Les corrections sont publiées avec la version suivante du site.",
                f"If you find an error, report it to {MAIL} or with a {a(GH + '/issues/new/choose', 'public issue on GitHub')}. Corrections are published with the next version of the site.",
                f"Vindt u een fout, meld die dan aan {MAIL} of met een {a(GH + '/issues/new/choose', 'openbaar ticket op GitHub')}. Correcties verschijnen in de volgende versie van de site.",
                f"Wenn Sie einen Fehler finden, melden Sie ihn an {MAIL} oder mit einem {a(GH + '/issues/new/choose', 'öffentlichen Ticket auf GitHub')}. Korrekturen erscheinen mit der nächsten Version der Website.",
            ),
        ),
        (
            "changes",
            (
                "Modification des conditions",
                "Changes to these terms",
                "Wijziging van de voorwaarden",
                "Änderung der Bedingungen",
            ),
            P(
                f"Ces conditions peuvent changer. La version en vigueur est celle publiée sur cette page, avec sa date et son numéro de version. Les versions précédentes restent consultables dans l'{a(history('terms'), 'historique public du dépôt')}.",
                f"These terms may change. The version in force is the one published on this page, with its date and version number. Earlier versions remain available in the {a(history('terms'), 'public history of the repository')}.",
                f"Deze voorwaarden kunnen wijzigen. De geldende versie is die op deze pagina, met haar datum en versienummer. Eerdere versies blijven raadpleegbaar in de {a(history('terms'), 'openbare geschiedenis van de repository')}.",
                f"Diese Bedingungen können sich ändern. Es gilt die auf dieser Seite veröffentlichte Fassung mit Datum und Fassungsnummer. Frühere Fassungen bleiben in der {a(history('terms'), 'öffentlichen Historie des Repositorys')} einsehbar.",
            ),
        ),
        (
            "law",
            ("Droit applicable", "Governing law", "Toepasselijk recht", "Anwendbares Recht"),
            P(
                "Ces conditions sont régies par le droit belge. Sous réserve des règles impératives qui vous protègent, tout litige relève des juridictions belges. Elles existent en français, en anglais, en néerlandais et en allemand ; en cas de divergence, la version française prévaut.",
                "These terms are governed by Belgian law. Subject to the mandatory rules that protect you, any dispute falls under the jurisdiction of the Belgian courts. They exist in French, English, Dutch and German; in case of discrepancy, the French version prevails.",
                "Op deze voorwaarden is het Belgische recht van toepassing. Onder voorbehoud van de dwingende regels die u beschermen, zijn de Belgische rechtbanken bevoegd voor elk geschil. Ze bestaan in het Frans, het Engels, het Nederlands en het Duits; bij verschillen heeft de Franse versie voorrang.",
                "Diese Bedingungen unterliegen belgischem Recht. Vorbehaltlich der zwingenden Vorschriften, die Sie schützen, sind für alle Streitigkeiten die belgischen Gerichte zuständig. Sie liegen auf Französisch, Englisch, Niederländisch und Deutsch vor; bei Abweichungen ist die französische Fassung maßgeblich.",
            ),
        ),
    ],
}


# =============================================================================== privacy: diagram
def tx(x, y, t, cls, anchor="middle"):
    """One SVG text line: one tspan per language, or the same string in every language."""
    t = (t,) * 4 if isinstance(t, str) else plain(*t)
    return (
        f'<text class="{cls}" text-anchor="{anchor}" x="{x}" y="{y}">'
        + "".join(f'<tspan data-l="{lang}">{s}</tspan>' for lang, s in zip(L, t, strict=True))
        + "</text>"
    )


def arrow(x1, y1, x2, y2, kind):
    return f'<line class="ln-{kind}" marker-end="url(#pv-{kind})" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"></line>'


def box(x, y, w, h, cls, *, dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<rect class="{cls}" height="{h}" rx="6" width="{w}" x="{x}" y="{y}"{d}></rect>'


MARKERS = "".join(
    f'<marker id="pv-{k}" markerHeight="7" markerWidth="7" orient="auto" refX="9" refY="5" viewBox="0 0 10 10">'
    f'<path class="mk-{k}" d="M0,0 L10,5 L0,10 z"></path></marker>'
    for k in ("flow", "ok", "err")
)
SVG_STYLE = (
    "<style>svg.sch text.s-t{fill:var(--fg);font:600 13px var(--font)}"
    "svg.sch text.s-m{fill:var(--muted);font:12px var(--mono)}"
    "svg.sch text.s-k{fill:var(--muted);font:12px var(--font)}"
    "svg.sch text.s-ok{fill:var(--green);font:600 12px var(--font)}"
    "svg.sch text.s-err{fill:var(--red);font:600 12px var(--font)}</style>"
)
FLOW_SVG = (
    '<svg aria-labelledby="pv-t" class="sch" role="img" viewBox="0 0 960 310">\n'
    '<title id="pv-t">A visit: your browser sends the request through the firewall and Traefik, which keep the IP address in memory only, '
    "to the nginx web server, which writes one log line without the IP address and sends the page back. Nothing goes to a third party. "
    "The browser keeps its preferences for the tab, and the reading progress only with your consent, for six months at most.</title>\n"
    + SVG_STYLE
    + f"<defs>{MARKERS}</defs>\n"
    # your browser and its two storages
    + box(20, 40, 230, 252, "sh-ok")
    + tx(135, 64, ("Votre navigateur", "Your browser", "Uw browser", "Ihr Browser"), "s-t")
    + box(34, 84, 202, 82, "sh-box")
    + tx(135, 105, ("Stockage de session", "Session storage", "Sessieopslag", "Sitzungsspeicher"), "s-t")
    + tx(135, 125, "lang, theme, npe-nav", "s-m")
    + tx(
        135,
        151,
        (
            "effacé quand l'onglet se ferme",
            "erased when the tab closes",
            "gewist als het tabblad sluit",
            "gelöscht, wenn der Tab schließt",
        ),
        "s-k",
    )
    + box(34, 178, 202, 104, "sh-box", dash="5 3")
    + tx(135, 198, ("Stockage local", "Local storage", "Lokale opslag", "Lokaler Speicher"), "s-t")
    + tx(135, 216, "npe-seen, npe-last,", "s-m")
    + tx(135, 232, "npe-quiz, npe-remember", "s-m")
    + tx(
        135,
        254,
        ("seulement si vous cochez", "only if you tick", "alleen als u aanvinkt", "nur wenn Sie ankreuzen"),
        "s-k",
    )
    + tx(
        135,
        270,
        (
            "« Mémoriser », six mois au plus",
            '"Remember", six months at most',
            '"Onthouden", max. zes maanden',
            '"Speichern", max. sechs Monate',
        ),
        "s-k",
    )
    # firewall and reverse proxy
    + box(360, 40, 220, 120, "sh-enc")
    + tx(
        470,
        64,
        ("Pare-feu et Traefik", "Firewall and Traefik", "Firewall en Traefik", "Firewall und Traefik"),
        "s-t",
    )
    + tx(
        470,
        88,
        (
            "adresse IP en mémoire",
            "IP address in memory",
            "IP-adres in het geheugen",
            "IP-Adresse im Speicher",
        ),
        "s-k",
    )
    + tx(470, 108, ("liste de blocage,", "blocklist,", "blokkeerlijst,", "Sperrliste,"), "s-k")
    + tx(470, 124, ("limite de débit", "rate limit", "snelheidslimiet", "Ratenlimit"), "s-k")
    + tx(470, 148, ("✓ aucun journal", "✓ no log", "✓ geen logboek", "✓ kein Protokoll"), "s-ok")
    # web server
    + box(680, 40, 260, 120, "sh-enc")
    + tx(810, 64, ("Serveur web nginx", "Web server nginx", "Webserver nginx", "Webserver nginx"), "s-t")
    + tx(
        810,
        88,
        (
            "renvoie la page demandée",
            "sends the page back",
            "stuurt de pagina terug",
            "sendet die Seite zurück",
        ),
        "s-k",
    )
    + tx(
        810,
        108,
        (
            "reçoit l'IP dans un en-tête",
            "gets the IP in a header",
            "krijgt het IP in een header",
            "erhält die IP im Header",
        ),
        "s-k",
    )
    + tx(
        810,
        132,
        (
            "✓ ne l'écrit nulle part",
            "✓ writes it nowhere",
            "✓ schrijft het nergens weg",
            "✓ schreibt sie nirgends",
        ),
        "s-ok",
    )
    # the one thing written to disk
    + box(680, 205, 260, 87, "sh-body", dash="5 3")
    + tx(
        810, 229, ("Journal technique", "Technical log", "Technisch logboek", "Technisches Protokoll"), "s-t"
    )
    + tx(
        810,
        250,
        (
            "date, page, code, taille, User-Agent",
            "date, page, code, size, User-Agent",
            "datum, pagina, code, grootte, User-Agent",
            "Datum, Seite, Code, Größe, User-Agent",
        ),
        "s-k",
    )
    + tx(
        810,
        272,
        (
            "sans adresse IP, 30 Mo au plus",
            "no IP address, 30 MB at most",
            "zonder IP-adres, max. 30 MB",
            "ohne IP-Adresse, max. 30 MB",
        ),
        "s-k",
    )
    # third parties: nothing
    + box(360, 205, 220, 87, "sh-err", dash="6 4")
    + tx(470, 229, ("Sites tiers", "Third parties", "Derden", "Dritte"), "s-t")
    + tx(
        470,
        250,
        (
            "publicité, audience, CDN",
            "ads, analytics, CDN",
            "reclame, statistieken, CDN",
            "Werbung, Statistik, CDN",
        ),
        "s-k",
    )
    + tx(
        470,
        272,
        (
            "✗ rien ne leur est envoyé",
            "✗ nothing is sent to them",
            "✗ ze krijgen niets",
            "✗ sie erhalten nichts",
        ),
        "s-err",
    )
    # 1 to 4: the request and the page
    + arrow(250, 78, 356, 78, "flow")
    + tx(305, 70, ("1 requête", "1 request", "1 verzoek", "1 Anfrage"), "s-k")
    + tx(305, 94, ("IP, en-têtes", "IP, headers", "IP, headers", "IP, Header"), "s-m")
    + arrow(580, 78, 676, 78, "flow")
    + tx(630, 70, ("2 transmise", "2 passed on", "2 doorgegeven", "2 weiter"), "s-k")
    + arrow(810, 160, 810, 201, "flow")
    + tx(822, 186, ("3 une ligne", "3 one line", "3 één regel", "3 eine Zeile"), "s-k", "start")
    + arrow(680, 122, 584, 122, "ok")
    + tx(630, 114, ("4 la page", "4 the page", "4 de pagina", "4 die Seite"), "s-k")
    + arrow(360, 122, 254, 122, "ok")
    + tx(305, 114, ("4 la page", "4 the page", "4 de pagina", "4 die Seite"), "s-k")
    # nothing to third parties
    + arrow(250, 250, 356, 250, "err")
    + tx(305, 242, ("✗ aucun appel", "✗ no call", "✗ geen oproep", "✗ kein Aufruf"), "s-err")
    + arrow(680, 250, 584, 250, "err")
    + tx(630, 242, ("✗ rien", "✗ nothing", "✗ niets", "✗ nichts"), "s-err")
    + "\n</svg>"
)


def legend(rows):
    return (
        '<dl class="legend">'
        + "".join(f"<div><dt>{dt}</dt><dd>{sp(*dd)}</dd></div>" for dt, dd in rows)
        + "</dl>\n"
    )


FLOW = (
    '<figure class="diagram">\n<figcaption><span class="t">'
    + sp(
        "Schéma : le parcours d'une visite, de votre navigateur au serveur et retour, et ce qui est gardé à chaque étape",
        "Diagram: the path of a visit, from your browser to the server and back, and what is kept at each step",
        "Schema: het verloop van een bezoek, van uw browser naar de server en terug, en wat bij elke stap bewaard blijft",
        "Diagramm: der Weg eines Besuchs, von Ihrem Browser zum Server und zurück, und was bei jedem Schritt gespeichert wird",
    )
    + '</span></figcaption>\n<div class="body">\n'
    + FLOW_SVG
    + "\n</div>\n"
    + legend(
        [
            (
                '<span class="sw l-ok"></span>',
                (
                    "Reste sur votre appareil (vert)",
                    "Stays on your device (green)",
                    "Blijft op uw toestel (groen)",
                    "Bleibt auf Ihrem Gerät (grün)",
                ),
            ),
            (
                '<span class="sw l-encap"></span>',
                (
                    "Serveur de l'éditeur, en Belgique (gris)",
                    "The publisher's server, in Belgium (grey)",
                    "Server van de uitgever, in België (grijs)",
                    "Server des Herausgebers, in Belgien (grau)",
                ),
            ),
            (
                '<span class="sw l-body"></span>',
                (
                    "Seule donnée écrite sur disque (sarcelle, tirets)",
                    "Only data written to disk (teal, dashed)",
                    "Enige gegevens op schijf (teal, gestreept)",
                    "Einzige Daten auf der Festplatte (türkis, gestrichelt)",
                ),
            ),
            (
                '<span class="sw l-err"></span>',
                (
                    "Tiers : rien ne leur parvient (rouge, tirets, ✗)",
                    "Third parties: nothing reaches them (red, dashed, ✗)",
                    "Derden: er bereikt hen niets (rood, gestreept, ✗)",
                    "Dritte: nichts erreicht sie (rot, gestrichelt, ✗)",
                ),
            ),
            (
                "1 2 3",
                (
                    "Flèches bleues : votre requête, étape par étape",
                    "Blue arrows: your request, step by step",
                    "Blauwe pijlen: uw verzoek, stap voor stap",
                    "Blaue Pfeile: Ihre Anfrage, Schritt für Schritt",
                ),
            ),
            (
                "4",
                (
                    "Flèches vertes : la page qui vous revient",
                    "Green arrows: the page coming back to you",
                    "Groene pijlen: de pagina die naar u terugkomt",
                    "Grüne Pfeile: die Seite, die zu Ihnen zurückkommt",
                ),
            ),
        ]
    )
    + '<p class="fields-t">'
    + sp(
        "Les éléments du schéma",
        "The parts of the diagram",
        "De onderdelen van het schema",
        "Die Teile des Diagramms",
    )
    + "</p>"
    + DL(
        [
            (
                sp("Votre navigateur", "Your browser", "Uw browser", "Ihr Browser"),
                (
                    "envoie la requête (1) et reçoit la page (4). Il garde la langue, le thème et le menu le temps de l'onglet ; la progression, seulement si vous cochez « Mémoriser », et six mois au plus.",
                    'sends the request (1) and gets the page (4). It keeps the language, the theme and the menu for the tab; the progress only if you tick "Remember", and six months at most.',
                    'stuurt het verzoek (1) en krijgt de pagina (4). Hij bewaart taal, thema en menu zolang het tabblad open is; de voortgang alleen als u "Onthouden" aanvinkt, en hoogstens zes maanden.',
                    'sendet die Anfrage (1) und erhält die Seite (4). Er behält Sprache, Design und Menü für die Dauer des Tabs; den Fortschritt nur, wenn Sie "Speichern" ankreuzen, und höchstens sechs Monate.',
                ),
            ),
            (
                sp(
                    "Pare-feu et Traefik",
                    "Firewall and Traefik",
                    "Firewall en Traefik",
                    "Firewall und Traefik",
                ),
                (
                    "reçoivent votre adresse IP, la comparent à une liste d'adresses connues pour des attaques et limitent le nombre de requêtes par adresse. Tout se passe en mémoire : aucune ligne de journal n'est écrite pour ce site.",
                    "receive your IP address, compare it with a list of addresses known for attacks and limit the number of requests per address. All of it happens in memory: no log line is written for this site.",
                    "ontvangen uw IP-adres, vergelijken het met een lijst van adressen die bekendstaan om aanvallen en beperken het aantal verzoeken per adres. Alles gebeurt in het geheugen: voor deze site wordt geen logregel geschreven.",
                    "erhalten Ihre IP-Adresse, vergleichen sie mit einer Liste von Adressen, die für Angriffe bekannt sind, und begrenzen die Zahl der Anfragen pro Adresse. Alles geschieht im Arbeitsspeicher: Für diese Website wird keine Protokollzeile geschrieben.",
                ),
            ),
            (
                sp("nginx", "nginx", "nginx", "nginx"),
                (
                    "renvoie la page (4). Il reçoit votre adresse dans l'en-tête X-Forwarded-For, mais ne l'écrit nulle part.",
                    "sends the page back (4). It gets your address in the X-Forwarded-For header, but writes it nowhere.",
                    "stuurt de pagina terug (4). Hij krijgt uw adres in de header X-Forwarded-For, maar schrijft het nergens weg.",
                    "sendet die Seite zurück (4). Er erhält Ihre Adresse im Header X-Forwarded-For, schreibt sie aber nirgends.",
                ),
            ),
            (
                sp("Journal technique", "Technical log", "Technisch logboek", "Technisches Protokoll"),
                (
                    "une ligne par requête (3) : date, page, code de réponse, taille et User-Agent, sans adresse IP. 30 Mo au plus, effacé à chaque mise à jour du serveur.",
                    "one line per request (3): date, page, response code, size and User-Agent, without the IP address. 30 MB at most, erased at every update of the server.",
                    "één regel per verzoek (3): datum, pagina, antwoordcode, grootte en User-Agent, zonder IP-adres. Hoogstens 30 MB, gewist bij elke update van de server.",
                    "eine Zeile pro Anfrage (3): Datum, Seite, Antwortcode, Größe und User-Agent, ohne IP-Adresse. Höchstens 30 MB, gelöscht bei jeder Aktualisierung des Servers.",
                ),
            ),
            (
                sp("Sites tiers", "Third parties", "Derden", "Dritte"),
                (
                    "aucun : ni publicité, ni mesure d'audience, ni CDN, ni police ou script d'un autre site. La politique de sécurité du contenu bloque tout appel vers un autre site.",
                    "none: no advertising, no analytics, no CDN, no font or script from another site. The content security policy blocks any call to another site.",
                    "geen: geen reclame, geen bezoekersstatistieken, geen CDN, geen lettertype of script van een andere site. Het content security policy blokkeert elke oproep naar een andere site.",
                    "keine: keine Werbung, keine Reichweitenmessung, kein CDN, keine Schrift und kein Skript einer anderen Website. Die Content Security Policy blockiert jeden Aufruf einer anderen Website.",
                ),
            ),
        ]
    )
    + "</figure>\n"
)

# =============================================================================== privacy
KEEP = (
    "Mémoriser mes choix et ma progression sur cet appareil",
    "Remember my choices and progress on this device",
    "Mijn keuzes en voortgang op dit toestel onthouden",
    "Meine Auswahl und meinen Fortschritt auf diesem Gerät speichern",
)
FORGET = (
    "Effacer les données de ce site sur cet appareil",
    "Delete this site's data on this device",
    "De gegevens van deze site op dit toestel wissen",
    "Die Daten dieser Website auf diesem Gerät löschen",
)
CONTROLS = (
    '<div class="callout note store-box"><svg aria-hidden="true" fill="none" height="20" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" width="20"><circle cx="12" cy="12" r="9.5"></circle><path d="M12 11v6M12 7.5v.5" stroke-linecap="round"></path></svg><div>'
    + '<label class="remember"><input type="checkbox" data-remember> '
    + sp(*KEEP)
    + "</label>\n"
    + '<p><button type="button" class="btn" data-forget>'
    + sp(*FORGET)
    + "</button></p>\n"
    + '<p class="store-status" data-store-status role="status" aria-live="polite"></p>\n'
    + "</div></div>\n"
)
PRIVACY = {
    "slug": "privacy",
    "version": 2,
    "title": ("Vie privée", "Privacy", "Privacy", "Datenschutz"),
    "description": (
        "Ni cookie, ni traceur, ni mesure d'audience, ni adresse IP conservée : les rares données traitées, le stockage dans votre navigateur et vos droits (RGPD).",
        "No cookie, no tracker, no analytics, no IP address kept: the little data processed, what your browser stores and your rights (GDPR).",
        "Geen cookies, geen trackers, geen bezoekersstatistieken, geen IP-adres bewaard: de weinige verwerkte gegevens, wat uw browser opslaat en uw rechten (AVG).",
        "Keine Cookies, keine Tracker, keine Reichweitenmessung, keine gespeicherte IP-Adresse: die wenigen verarbeiteten Daten, die Speicherung im Browser und Ihre Rechte (DSGVO).",
    ),
    "lede": (
        "Ce site ne vous suit pas. Cette page décrit le peu de données qui existent, ce qui reste dans votre navigateur et vos droits.",
        "This site does not track you. This page describes the little data that exists, what stays in your browser and your rights.",
        "Deze site volgt u niet. Deze pagina beschrijft de weinige gegevens die bestaan, wat in uw browser blijft en uw rechten.",
        "Diese Website verfolgt Sie nicht. Diese Seite beschreibt die wenigen vorhandenen Daten, was in Ihrem Browser bleibt und Ihre Rechte.",
    ),
    "sections": [
        (
            "summary",
            ("En bref", "In short", "In het kort", "Kurz gesagt"),
            CALLOUT(
                "ok recap",
                "ok",
                ("L'essentiel", "The essentials", "Het belangrijkste", "Das Wichtigste"),
                UL(
                    [
                        (
                            "Aucun compte, aucun formulaire, aucune publicité.",
                            "No account, no form, no advertising.",
                            "Geen account, geen formulier, geen reclame.",
                            "Kein Konto, kein Formular, keine Werbung.",
                        ),
                        (
                            "Aucun cookie, aucun traceur, aucune mesure d'audience. Les pages ne chargent rien depuis un autre site.",
                            "No cookie, no tracker, no analytics. The pages load nothing from another site.",
                            "Geen cookies, geen trackers, geen bezoekersstatistieken. De pagina's laden niets van een andere site.",
                            "Keine Cookies, keine Tracker, keine Reichweitenmessung. Die Seiten laden nichts von einer anderen Website.",
                        ),
                        (
                            "Votre adresse IP n'est pas enregistrée.",
                            "Your IP address is not recorded.",
                            "Uw IP-adres wordt niet opgeslagen.",
                            "Ihre IP-Adresse wird nicht gespeichert.",
                        ),
                        (
                            "Vos préférences restent dans votre navigateur. Elles ne sont gardées après la fermeture de l'onglet que si vous le demandez, et six mois au plus.",
                            "Your preferences stay in your browser. They are kept after you close the tab only if you ask for it, and six months at most.",
                            "Uw voorkeuren blijven in uw browser. Ze worden na het sluiten van het tabblad alleen bewaard als u daarom vraagt, en hoogstens zes maanden.",
                            "Ihre Einstellungen bleiben in Ihrem Browser. Sie werden nach dem Schließen des Tabs nur gespeichert, wenn Sie das wünschen, und höchstens sechs Monate.",
                        ),
                        (
                            "Aucune donnée n'est vendue ni transmise à un tiers.",
                            "No data is sold or passed to a third party.",
                            "Geen enkel gegeven wordt verkocht of aan derden doorgegeven.",
                            "Keine Daten werden verkauft oder an Dritte weitergegeben.",
                        ),
                    ]
                ),
            )
            + FLOW,
        ),
        (
            "controller",
            ("Responsable du traitement", "Controller", "Verwerkingsverantwoordelijke", "Verantwortlicher"),
            P(
                f"Jean-Michel Cuvelier, Belgique, {MAIL}. L'éditeur n'a pas désigné de délégué à la protection des données : ce n'est pas obligatoire pour un site de ce type.",
                f"Jean-Michel Cuvelier, Belgium, {MAIL}. The publisher has not appointed a data protection officer: it is not required for a site of this kind.",
                f"Jean-Michel Cuvelier, België, {MAIL}. De uitgever heeft geen functionaris voor gegevensbescherming aangesteld: dat is voor een site van dit type niet verplicht.",
                f"Jean-Michel Cuvelier, Belgien, {MAIL}. Der Herausgeber hat keinen Datenschutzbeauftragten benannt: Für eine Website dieser Art ist das nicht vorgeschrieben.",
            ),
        ),
        (
            "visit",
            ("Lors d'une visite", "When you visit", "Bij een bezoek", "Bei einem Besuch"),
            P(
                "Pour vous envoyer une page, le serveur reçoit forcément votre adresse IP et les en-têtes envoyés par votre navigateur. Il les utilise en mémoire, le temps de répondre et de limiter les abus (nombre de requêtes par adresse, blocage des adresses connues pour des attaques), sans les enregistrer.",
                "To send you a page, the server necessarily receives your IP address and the headers your browser sends. It uses them in memory, while it answers and to limit abuse (number of requests per address, blocking of addresses known for attacks), without recording them.",
                "Om u een pagina te sturen, ontvangt de server noodzakelijk uw IP-adres en de headers die uw browser verstuurt. Hij gebruikt ze in het geheugen, zolang hij antwoordt en om misbruik te beperken (aantal verzoeken per adres, blokkering van adressen die bekendstaan om aanvallen), zonder ze op te slaan.",
                "Um Ihnen eine Seite zu senden, erhält der Server zwangsläufig Ihre IP-Adresse und die Header Ihres Browsers. Er nutzt sie im Arbeitsspeicher, solange er antwortet und um Missbrauch zu begrenzen (Zahl der Anfragen pro Adresse, Sperre von Adressen, die für Angriffe bekannt sind), ohne sie zu speichern.",
            )
            + P(
                "Le serveur web tient un journal technique, pour détecter les pannes et les attaques. Chaque ligne contient la date et l'heure, la page demandée, le code de réponse, la taille de la réponse et l'identifiant du navigateur (User-Agent). Elle ne contient pas votre adresse IP. Le journal est limité à 30 Mo (trois fichiers de 10 Mo, le plus ancien est écrasé) et il est effacé à chaque mise à jour du serveur.",
                "The web server keeps a technical log, to detect faults and attacks. Each line holds the date and time, the page requested, the response code, the size of the response and the browser identifier (User-Agent). It does not hold your IP address. The log is limited to 30 MB (three files of 10 MB, the oldest is overwritten) and is erased at every update of the server.",
                "De webserver houdt een technisch logboek bij, om storingen en aanvallen op te sporen. Elke regel bevat de datum en het tijdstip, de gevraagde pagina, de antwoordcode, de grootte van het antwoord en de browseridentificatie (User-Agent). Ze bevat uw IP-adres niet. Het logboek is beperkt tot 30 MB (drie bestanden van 10 MB, het oudste wordt overschreven) en wordt bij elke update van de server gewist.",
                "Der Webserver führt ein technisches Protokoll, um Störungen und Angriffe zu erkennen. Jede Zeile enthält Datum und Uhrzeit, die angeforderte Seite, den Antwortcode, die Größe der Antwort und die Browserkennung (User-Agent). Sie enthält Ihre IP-Adresse nicht. Das Protokoll ist auf 30 MB begrenzt (drei Dateien zu 10 MB, die älteste wird überschrieben) und wird bei jeder Aktualisierung des Servers gelöscht.",
            )
            + P(
                f"Base légale : l'intérêt légitime à faire fonctionner et à protéger le site (article 6, paragraphe 1, point f, du {a(GDPR, 'RGPD')}). Destinataires : personne. Le site est hébergé par l'éditeur, en Belgique, et ces données ne sont transmises à aucun tiers.",
                f"Legal basis: the legitimate interest in running and protecting the site (Article 6(1)(f) of the {a(GDPR, 'GDPR')}). Recipients: none. The site is hosted by the publisher, in Belgium, and this data is passed to no third party.",
                f"Rechtsgrond: het gerechtvaardigde belang om de site te laten werken en te beveiligen (artikel 6, lid 1, punt f, van de {a(GDPR, 'AVG')}). Ontvangers: niemand. De site wordt door de uitgever gehost, in België, en deze gegevens worden aan geen enkele derde doorgegeven.",
                f"Rechtsgrundlage: das berechtigte Interesse am Betrieb und am Schutz der Website (Artikel 6 Absatz 1 Buchstabe f der {a(GDPR, 'DSGVO')}). Empfänger: niemand. Die Website wird vom Herausgeber in Belgien gehostet, und diese Daten gehen an keinen Dritten.",
            ),
        ),
        (
            "device",
            ("Dans votre navigateur", "In your browser", "In uw browser", "In Ihrem Browser"),
            P(
                "Le site n'utilise pas de cookie. Il utilise le stockage web de votre navigateur, seulement pour vous rendre service. Ces données ne quittent jamais votre appareil :",
                "The site uses no cookie. It uses your browser's web storage, only to serve you. This data never leaves your device:",
                "De site gebruikt geen cookies. Hij gebruikt de webopslag van uw browser, alleen om u van dienst te zijn. Deze gegevens verlaten uw toestel nooit:",
                "Die Website verwendet keine Cookies. Sie nutzt den Webspeicher Ihres Browsers, nur für Sie. Diese Daten verlassen Ihr Gerät nie:",
            )
            + DL(
                [
                    (
                        "lang, theme, npe-nav",
                        (
                            "la langue choisie, le thème clair ou sombre et le menu des chapitres replié. Écrits quand vous cliquez sur le bouton concerné. Par défaut dans le stockage de session : effacés quand vous fermez l'onglet.",
                            "the chosen language, the light or dark theme and the folded chapter menu. Written when you click the matching button. By default in session storage: erased when you close the tab.",
                            "de gekozen taal, het lichte of donkere thema en het ingeklapte hoofdstukmenu. Geschreven wanneer u op de knop klikt. Standaard in de sessieopslag: gewist wanneer u het tabblad sluit.",
                            "die gewählte Sprache, das helle oder dunkle Design und das eingeklappte Kapitelmenü. Geschrieben, wenn Sie auf die jeweilige Schaltfläche klicken. Standardmäßig im Sitzungsspeicher: gelöscht, wenn Sie den Tab schließen.",
                        ),
                    ),
                    (
                        "npe-seen, npe-last, npe-quiz",
                        (
                            "les chapitres déjà ouverts, le dernier chapitre lu (lien « Reprendre » de l'accueil) et votre dernier score à chaque quiz. Écrits seulement si vous avez coché la case ci-dessous.",
                            'the chapters already opened, the last chapter read (the "Resume" link of the home page) and your last score at each quiz. Written only if you ticked the box below.',
                            'de al geopende hoofdstukken, het laatst gelezen hoofdstuk (de link "Verdergaan" op de startpagina) en uw laatste score per quiz. Alleen geschreven als u het vakje hieronder hebt aangevinkt.',
                            'die bereits geöffneten Kapitel, das zuletzt gelesene Kapitel (der Link "Fortsetzen" der Startseite) und Ihr letztes Ergebnis je Quiz. Nur geschrieben, wenn Sie das Kästchen unten angekreuzt haben.',
                        ),
                    ),
                    (
                        "npe-remember",
                        (
                            "la date de votre accord pour mémoriser. Présent seulement si vous avez coché la case.",
                            "the date of your consent to remember. Present only if you ticked the box.",
                            "de datum van uw toestemming om te onthouden. Alleen aanwezig als u het vakje hebt aangevinkt.",
                            "das Datum Ihrer Einwilligung zum Speichern. Nur vorhanden, wenn Sie das Kästchen angekreuzt haben.",
                        ),
                    ),
                ]
            )
            + P(
                "Si vous cochez la case, ces données passent dans le stockage local de votre navigateur. Elles y restent jusqu'à ce que vous décochiez la case ou effaciez les données, et six mois au plus : votre accord expire alors, les données sont effacées et la case se décoche. Vous pouvez la recocher quand vous voulez.",
                "If you tick the box, this data moves to your browser's local storage. It stays there until you untick the box or delete the data, and six months at most: your consent then expires, the data is deleted and the box is unticked. You can tick it again whenever you like.",
                "Als u het vakje aanvinkt, gaan deze gegevens naar de lokale opslag van uw browser. Ze blijven daar tot u het vakje uitvinkt of de gegevens wist, en hoogstens zes maanden: dan vervalt uw toestemming, worden de gegevens gewist en wordt het vakje uitgevinkt. U kunt het altijd opnieuw aanvinken.",
                "Wenn Sie das Kästchen ankreuzen, gehen diese Daten in den lokalen Speicher Ihres Browsers. Sie bleiben dort, bis Sie das Kreuz entfernen oder die Daten löschen, höchstens aber sechs Monate: Dann erlischt Ihre Einwilligung, die Daten werden gelöscht und das Kreuz verschwindet. Sie können es jederzeit wieder setzen.",
            )
            + P(
                "Retirer votre accord est aussi simple que le donner : décochez la case, ici ou en bas de n'importe quelle page, et tout ce qui était gardé sur l'appareil est effacé. Le bouton ci-dessous efface en plus les préférences de l'onglet en cours.",
                "Withdrawing your consent is as easy as giving it: untick the box, here or at the bottom of any page, and everything kept on the device is deleted. The button below also deletes the preferences of the current tab.",
                "Uw toestemming intrekken is even eenvoudig als ze geven: vink het vakje uit, hier of onderaan elke pagina, en alles wat op het toestel bewaard was, wordt gewist. De knop hieronder wist bovendien de voorkeuren van het huidige tabblad.",
                "Ihre Einwilligung zu widerrufen ist so einfach, wie sie zu erteilen: Entfernen Sie das Kreuz, hier oder unten auf jeder Seite, und alles, was auf dem Gerät gespeichert war, wird gelöscht. Die Schaltfläche unten löscht zusätzlich die Einstellungen des aktuellen Tabs.",
            )
            + CONTROLS
            + P(
                f"Règle appliquée : l'article 5, paragraphe 3, de la {a(EPRIVACY, 'directive 2002/58/CE')}, transposé en droit belge par l'article 10/2 de la loi du 30 juillet 2018 relative à la protection des personnes physiques à l'égard des traitements de données à caractère personnel, tel que l'{a(APD_URL[0], 'Autorité de protection des données')} l'explique pour les cookies et le stockage local. Une préférence d'interface gardée le temps de la session est nécessaire au service que vous demandez. Une conservation plus longue demande votre accord, d'où la case à cocher, décochée par défaut, et un accord valable six mois, la durée que l'Autorité juge en principe raisonnable pour garder un tel choix.",
                f"Rule applied: Article 5(3) of {a(EPRIVACY, 'Directive 2002/58/EC')}, transposed into Belgian law by Article 10/2 of the Act of 30 July 2018 on the protection of natural persons with regard to the processing of personal data, as the {a(APD_URL[1], 'Data Protection Authority')} explains it for cookies and local storage. An interface preference kept for the session is necessary for the service you ask for. Keeping it longer needs your consent, hence the box, unticked by default, and a consent valid for six months, the period the Authority considers reasonable in principle for keeping such a choice.",
                f"Toegepaste regel: artikel 5, lid 3, van {a(EPRIVACY, 'richtlijn 2002/58/EG')}, in Belgisch recht omgezet door artikel 10/2 van de wet van 30 juli 2018 betreffende de bescherming van natuurlijke personen met betrekking tot de verwerking van persoonsgegevens, zoals de {a(APD_URL[2], 'Gegevensbeschermingsautoriteit')} dat uitlegt voor cookies en lokale opslag. Een interfacevoorkeur die alleen voor de sessie wordt bewaard, is nodig voor de dienst die u vraagt. Langer bewaren vereist uw toestemming, vandaar het vakje, standaard niet aangevinkt, en een toestemming die zes maanden geldt, de termijn die de Autoriteit in principe redelijk acht om zo een keuze te bewaren.",
                f"Angewandte Regel: Artikel 5 Absatz 3 der {a(EPRIVACY, 'Richtlinie 2002/58/EG')}, ins belgische Recht umgesetzt durch Artikel 10/2 des Gesetzes vom 30. Juli 2018 über den Schutz natürlicher Personen hinsichtlich der Verarbeitung personenbezogener Daten, wie die {a(APD_URL[3], 'Datenschutzbehörde')} es für Cookies und lokalen Speicher erläutert. Eine Oberflächeneinstellung, die nur für die Sitzung gespeichert wird, ist für den angeforderten Dienst nötig. Eine längere Speicherung erfordert Ihre Einwilligung, daher das Kästchen, standardmäßig nicht angekreuzt, und eine Einwilligung, die sechs Monate gilt, die Frist, die die Behörde grundsätzlich für angemessen hält, um eine solche Wahl zu speichern.",
            ),
        ),
        (
            "email",
            (
                "Si vous écrivez à l'éditeur",
                "If you write to the publisher",
                "Als u de uitgever schrijft",
                "Wenn Sie dem Herausgeber schreiben",
            ),
            P(
                "Votre adresse e-mail et votre message servent seulement à vous répondre. Ils sont effacés au plus tard 12 mois après le dernier échange. Seule exception : une autorisation d'usage commercial est gardée tant qu'elle est valable, pour en conserver la preuve. Base légale : l'intérêt légitime à répondre aux personnes qui écrivent. Les e-mails sont reçus par Proton Mail (Proton AG, Suisse), un pays reconnu par la Commission européenne comme offrant une protection adéquate des données.",
                "Your email address and your message are used only to answer you. They are deleted at the latest 12 months after the last exchange. The one exception: a permission for commercial use is kept for as long as it is valid, as proof. Legal basis: the legitimate interest in answering people who write. Emails are received by Proton Mail (Proton AG, Switzerland), a country recognised by the European Commission as providing adequate data protection.",
                "Uw e-mailadres en uw bericht dienen alleen om u te antwoorden. Ze worden uiterlijk 12 maanden na de laatste uitwisseling gewist. Enige uitzondering: een toestemming voor commercieel gebruik wordt bewaard zolang ze geldig is, als bewijs. Rechtsgrond: het gerechtvaardigde belang om te antwoorden aan wie schrijft. De e-mails worden ontvangen door Proton Mail (Proton AG, Zwitserland), een land dat de Europese Commissie erkent als land met een passend beschermingsniveau.",
                "Ihre E-Mail-Adresse und Ihre Nachricht dienen nur dazu, Ihnen zu antworten. Sie werden spätestens 12 Monate nach dem letzten Austausch gelöscht. Einzige Ausnahme: Eine Erlaubnis zur kommerziellen Nutzung wird aufbewahrt, solange sie gilt, als Nachweis. Rechtsgrundlage: das berechtigte Interesse, Personen zu antworten, die schreiben. Die E-Mails empfängt Proton Mail (Proton AG, Schweiz), ein Land, dem die Europäische Kommission ein angemessenes Datenschutzniveau bescheinigt.",
            ),
        ),
        (
            "github",
            ("Tickets sur GitHub", "Issues on GitHub", "Tickets op GitHub", "Tickets auf GitHub"),
            P(
                f"Les tickets publics pour signaler une erreur sont hébergés par GitHub (GitHub, Inc., États-Unis). Leur contenu et votre nom d'utilisateur y sont publics, et la {a('https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement', 'déclaration de confidentialité de GitHub')} s'applique. Le site ne transmet aucune donnée à GitHub.",
                f"The public issues used to report errors are hosted by GitHub (GitHub, Inc., United States). Their content and your user name are public there, and the {a('https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement', 'GitHub privacy statement')} applies. The site sends no data to GitHub.",
                f"De openbare tickets om fouten te melden worden gehost door GitHub (GitHub, Inc., Verenigde Staten). Hun inhoud en uw gebruikersnaam zijn daar openbaar, en de {a('https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement', 'privacyverklaring van GitHub')} is van toepassing. De site stuurt geen gegevens naar GitHub.",
                f"Die öffentlichen Tickets zum Melden von Fehlern hostet GitHub (GitHub, Inc., USA). Ihr Inhalt und Ihr Benutzername sind dort öffentlich, und die {a('https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement', 'Datenschutzerklärung von GitHub')} gilt. Die Website übermittelt keine Daten an GitHub.",
            ),
        ),
        (
            "links",
            (
                "Liens vers d'autres sites",
                "Links to other sites",
                "Links naar andere sites",
                "Links zu anderen Websites",
            ),
            P(
                "Si vous suivez un lien vers un autre site (RFC Editor, IANA, constructeurs, GitHub), ce site reçoit votre adresse IP et ses propres règles s'appliquent. Votre navigateur lui indique seulement que vous venez de learning.cuvelier.tech, pas la page que vous lisiez.",
                "If you follow a link to another site (RFC Editor, IANA, vendors, GitHub), that site receives your IP address and its own rules apply. Your browser only tells it that you come from learning.cuvelier.tech, not which page you were reading.",
                "Volgt u een link naar een andere site (RFC Editor, IANA, vendors, GitHub), dan ontvangt die site uw IP-adres en gelden haar eigen regels. Uw browser meldt haar alleen dat u van learning.cuvelier.tech komt, niet welke pagina u las.",
                "Wenn Sie einem Link zu einer anderen Website folgen (RFC Editor, IANA, Hersteller, GitHub), erhält diese Website Ihre IP-Adresse, und es gelten ihre eigenen Regeln. Ihr Browser teilt ihr nur mit, dass Sie von learning.cuvelier.tech kommen, nicht welche Seite Sie gelesen haben.",
            ),
        ),
        (
            "rights",
            ("Vos droits", "Your rights", "Uw rechten", "Ihre Rechte"),
            P(
                f"Vous pouvez demander l'accès à vos données, leur rectification ou leur effacement, ou la limitation du traitement (articles 15 à 18 du RGPD). Écrivez à {MAIL} : une réponse vous est donnée dans un délai d'un mois. Comme le site n'enregistre pas votre adresse IP, il ne détient en général aucune donnée qui permette de vous identifier, en dehors des e-mails que vous avez envoyés (article 11 du RGPD).",
                f"You may ask for access to your data, its rectification or erasure, or the restriction of processing (Articles 15 to 18 of the GDPR). Write to {MAIL}: you get an answer within one month. As the site does not record your IP address, it usually holds no data that can identify you, apart from the emails you sent (Article 11 of the GDPR).",
                f"U kunt inzage in uw gegevens vragen, rectificatie of wissing ervan, of beperking van de verwerking (artikelen 15 tot 18 van de AVG). Schrijf naar {MAIL}: u krijgt binnen een maand een antwoord. Omdat de site uw IP-adres niet opslaat, bewaart hij in de regel geen gegevens waarmee u kunt worden geïdentificeerd, behalve de e-mails die u stuurde (artikel 11 van de AVG).",
                f"Sie können Auskunft über Ihre Daten, ihre Berichtigung oder Löschung oder die Einschränkung der Verarbeitung verlangen (Artikel 15 bis 18 DSGVO). Schreiben Sie an {MAIL}: Sie erhalten innerhalb eines Monats eine Antwort. Da die Website Ihre IP-Adresse nicht speichert, hat sie in der Regel keine Daten, mit denen Sie identifiziert werden können, außer den E-Mails, die Sie geschickt haben (Artikel 11 DSGVO).",
            )
            + CALLOUT(
                "note",
                "info",
                ("Droit d'opposition", "Right to object", "Recht van bezwaar", "Widerspruchsrecht"),
                P(
                    f"Vous pouvez vous opposer à tout moment, pour des raisons tenant à votre situation particulière, aux traitements fondés sur l'intérêt légitime décrits sur cette page (article 21 du RGPD). Écrivez à {MAIL}.",
                    f"You may object at any time, on grounds relating to your particular situation, to the processing based on legitimate interest described on this page (Article 21 of the GDPR). Write to {MAIL}.",
                    f"U kunt op elk moment, om redenen die verband houden met uw specifieke situatie, bezwaar maken tegen de verwerkingen op basis van het gerechtvaardigde belang die op deze pagina beschreven staan (artikel 21 van de AVG). Schrijf naar {MAIL}.",
                    f"Sie können jederzeit aus Gründen, die sich aus Ihrer besonderen Situation ergeben, der auf dieser Seite beschriebenen Verarbeitung auf Grundlage des berechtigten Interesses widersprechen (Artikel 21 DSGVO). Schreiben Sie an {MAIL}.",
                ),
            )
            + P(
                f"Vous pouvez aussi introduire une réclamation auprès de l'{a(APD_URL[0], 'Autorité de protection des données')}, rue de la Presse 35, 1000 Bruxelles, ou auprès de l'autorité de votre pays de résidence.",
                f"You may also lodge a complaint with the Belgian {a(APD_URL[1], 'Data Protection Authority')}, Rue de la Presse 35, 1000 Brussels, or with the authority of your country of residence.",
                f"U kunt ook een klacht indienen bij de {a(APD_URL[2], 'Gegevensbeschermingsautoriteit')}, Drukpersstraat 35, 1000 Brussel, of bij de autoriteit van het land waar u woont.",
                f"Sie können sich auch bei der belgischen {a(APD_URL[3], 'Datenschutzbehörde')}, Rue de la Presse 35, 1000 Brüssel, oder bei der Behörde Ihres Wohnsitzlandes beschweren.",
            ),
        ),
        (
            "security",
            ("Sécurité", "Security", "Beveiliging", "Sicherheit"),
            P(
                "Le site n'est servi qu'en HTTPS (HSTS). Une politique de sécurité du contenu stricte interdit aux pages de charger un script ou une ressource d'un autre site et de faire le moindre appel réseau. Le site ne prend aucune décision automatisée et ne fait aucun profilage.",
                "The site is served only over HTTPS (HSTS). A strict content security policy forbids the pages to load a script or a resource from another site and to make any network call. The site makes no automated decision and does no profiling.",
                "De site wordt alleen via HTTPS aangeboden (HSTS). Een strikt content security policy verbiedt de pagina's een script of bron van een andere site te laden en ook maar één netwerkoproep te doen. De site neemt geen geautomatiseerde beslissingen en doet niet aan profilering.",
                "Die Website wird nur über HTTPS ausgeliefert (HSTS). Eine strenge Content Security Policy verbietet den Seiten, ein Skript oder eine Ressource einer anderen Website zu laden und überhaupt einen Netzwerkaufruf zu machen. Die Website trifft keine automatisierten Entscheidungen und betreibt kein Profiling.",
            ),
        ),
        (
            "history",
            (
                "Versions de cette page",
                "Versions of this page",
                "Versies van deze pagina",
                "Fassungen dieser Seite",
            ),
            UL(
                [
                    (
                        "Version 2 du 8 novembre 2026 : accord limité à six mois, durée de conservation des e-mails, droit d'opposition présenté à part, schéma du parcours d'une visite.",
                        "Version 2 of 8 November 2026: consent limited to six months, retention period for emails, right to object shown separately, diagram of a visit.",
                        "Versie 2 van 8 november 2026: toestemming beperkt tot zes maanden, bewaartermijn voor e-mails, recht van bezwaar apart vermeld, schema van een bezoek.",
                        "Fassung 2 vom 8. November 2026: Einwilligung auf sechs Monate begrenzt, Speicherdauer für E-Mails, Widerspruchsrecht gesondert dargestellt, Diagramm eines Besuchs.",
                    ),
                    (
                        "Version 1 du 7 novembre 2026 : première publication.",
                        "Version 1 of 7 November 2026: first publication.",
                        "Versie 1 van 7 november 2026: eerste publicatie.",
                        "Fassung 1 vom 7. November 2026: erste Veröffentlichung.",
                    ),
                ]
            )
            + P(
                f"Le texte exact de chaque version reste public dans l'{a(history('privacy'), 'historique du dépôt')}.",
                f"The exact text of every version remains public in the {a(history('privacy'), 'history of the repository')}.",
                f"De precieze tekst van elke versie blijft openbaar in de {a(history('privacy'), 'geschiedenis van de repository')}.",
                f"Der genaue Text jeder Fassung bleibt in der {a(history('privacy'), 'Historie des Repositorys')} öffentlich.",
            ),
        ),
    ],
}

# =============================================================================== accessibility
ACCESS = {
    "slug": "accessibility",
    "version": 2,
    "title": ("Accessibilité", "Accessibility", "Toegankelijkheid", "Barrierefreiheit"),
    "description": (
        "Déclaration d'accessibilité : objectif WCAG 2.2 AA, contrôles faits à chaque publication, limites connues et contact.",
        "Accessibility statement: WCAG 2.2 AA target, checks run at every release, known limitations and contact.",
        "Toegankelijkheidsverklaring: doel WCAG 2.2 AA, controles bij elke publicatie, bekende beperkingen en contact.",
        "Erklärung zur Barrierefreiheit: Ziel WCAG 2.2 AA, Prüfungen bei jeder Veröffentlichung, bekannte Einschränkungen und Kontakt.",
    ),
    "lede": (
        "Le site vise le niveau AA des règles WCAG 2.2. Cette déclaration dit ce qui est vérifié, ce qui reste limité et comment signaler un problème.",
        "The site aims at level AA of the WCAG 2.2 guidelines. This statement says what is checked, what remains limited and how to report a problem.",
        "De site mikt op niveau AA van de WCAG 2.2-richtlijnen. Deze verklaring zegt wat gecontroleerd wordt, wat beperkt blijft en hoe u een probleem meldt.",
        "Die Website zielt auf Stufe AA der Richtlinien WCAG 2.2. Diese Erklärung sagt, was geprüft wird, was eingeschränkt bleibt und wie Sie ein Problem melden.",
    ),
    "sections": [
        (
            "target",
            ("Objectif", "Target", "Doel", "Ziel"),
            P(
                f"Le niveau AA des {a(WCAG, 'Web Content Accessibility Guidelines (WCAG) 2.2')} du W3C, sur toutes les pages, dans les quatre langues, en thème sombre comme en thème clair.",
                f"Level AA of the W3C {a(WCAG, 'Web Content Accessibility Guidelines (WCAG) 2.2')}, on every page, in the four languages, in the dark and the light theme.",
                f"Niveau AA van de {a(WCAG, 'Web Content Accessibility Guidelines (WCAG) 2.2')} van het W3C, op alle pagina's, in de vier talen, in het donkere en het lichte thema.",
                f"Stufe AA der {a(WCAG, 'Web Content Accessibility Guidelines (WCAG) 2.2')} des W3C, auf allen Seiten, in den vier Sprachen, im dunklen und im hellen Design.",
            ),
        ),
        (
            "status",
            ("État de conformité", "Compliance status", "Nalevingsstatus", "Stand der Vereinbarkeit"),
            P(
                "Auto-évaluation, sans audit externe. À chaque publication, chaque page est contrôlée automatiquement avec axe-core (règles WCAG 2.0, 2.1 et 2.2 de niveaux A et AA) en thème clair, en thème sombre et sur un écran de 360 pixels de large. Le même contrôle vérifie que la mise en page ne bouge pas au chargement, que rien ne s'anime quand le système demande moins de mouvement et que la page ne défile pas horizontalement. Une version qui échoue n'est pas mise en ligne.",
                "Self-assessment, with no external audit. At every release, every page is checked automatically with axe-core (WCAG 2.0, 2.1 and 2.2 rules, levels A and AA) in the light theme, the dark theme and on a 360-pixel-wide screen. The same check makes sure the layout does not move while loading, nothing animates when the system asks for less motion and the page does not scroll sideways. A version that fails is not published.",
                "Zelfbeoordeling, zonder externe audit. Bij elke publicatie wordt elke pagina automatisch gecontroleerd met axe-core (WCAG 2.0-, 2.1- en 2.2-regels, niveaus A en AA) in het lichte thema, het donkere thema en op een scherm van 360 pixels breed. Dezelfde controle gaat na dat de lay-out niet verspringt bij het laden, dat niets beweegt wanneer het systeem om minder beweging vraagt en dat de pagina niet horizontaal scrolt. Een versie die faalt, wordt niet gepubliceerd.",
                "Selbstbewertung, ohne externes Audit. Bei jeder Veröffentlichung wird jede Seite automatisch mit axe-core geprüft (Regeln der WCAG 2.0, 2.1 und 2.2, Stufen A und AA), im hellen und im dunklen Design und auf einem 360 Pixel breiten Bildschirm. Dieselbe Prüfung stellt sicher, dass sich das Layout beim Laden nicht verschiebt, dass sich nichts bewegt, wenn das System weniger Bewegung wünscht, und dass die Seite nicht seitlich scrollt. Eine Version, die durchfällt, wird nicht veröffentlicht.",
            )
            + P(
                "Les contrôles automatiques ne couvrent pas tous les critères. La conformité complète n'est donc pas déclarée.",
                "Automatic checks do not cover every criterion. Full compliance is therefore not claimed.",
                "Automatische controles dekken niet alle criteria. Volledige naleving wordt daarom niet verklaard.",
                "Automatische Prüfungen decken nicht alle Kriterien ab. Volle Vereinbarkeit wird daher nicht erklärt.",
            ),
        ),
        (
            "features",
            ("Ce qui est fait", "What is in place", "Wat er is", "Was umgesetzt ist"),
            UL(
                [
                    (
                        "Navigation complète au clavier, avec un focus toujours visible.",
                        "Full keyboard navigation, with an always visible focus.",
                        "Volledige navigatie met het toetsenbord, met een altijd zichtbare focus.",
                        "Vollständige Bedienung per Tastatur, mit stets sichtbarem Fokus.",
                    ),
                    (
                        "Contraste d'au moins 4,5:1 dans les deux thèmes.",
                        "Contrast of at least 4.5:1 in both themes.",
                        "Contrast van minstens 4,5:1 in beide thema's.",
                        "Kontrast von mindestens 4,5:1 in beiden Designs.",
                    ),
                    (
                        "Un titre, une légende et la liste de son contenu pour chaque schéma.",
                        "A title, a legend and a list of its content for every diagram.",
                        "Een titel, een legende en een lijst van de inhoud bij elk schema.",
                        "Ein Titel, eine Legende und eine Liste des Inhalts zu jedem Diagramm.",
                    ),
                    (
                        "Des animations pilotées par le lecteur, avec pause, et arrêtées quand le système demande moins de mouvement.",
                        "Animations driven by the reader, with pause, and stopped when the system asks for less motion.",
                        "Animaties die de lezer zelf bedient, met pauze, en stilgezet wanneer het systeem om minder beweging vraagt.",
                        "Animationen, die der Leser steuert, mit Pause, und angehalten, wenn das System weniger Bewegung wünscht.",
                    ),
                    (
                        "La langue déclarée sur chaque page et chaque passage.",
                        "The language declared on every page and passage.",
                        "De taal aangegeven op elke pagina en elke passage.",
                        "Die Sprache auf jeder Seite und in jeder Passage angegeben.",
                    ),
                    (
                        "Des cibles cliquables d'au moins 24 pixels, et une version imprimable de chaque page.",
                        "Click targets of at least 24 pixels, and a printable version of every page.",
                        "Klikdoelen van minstens 24 pixels en een afdrukbare versie van elke pagina.",
                        "Klickziele von mindestens 24 Pixeln und eine druckbare Fassung jeder Seite.",
                    ),
                ]
            ),
        ),
        (
            "limits",
            ("Limites connues", "Known limitations", "Bekende beperkingen", "Bekannte Einschränkungen"),
            UL(
                [
                    (
                        "Sur un petit écran, les grands schémas et tableaux défilent horizontalement dans leur cadre.",
                        "On a small screen, large diagrams and tables scroll sideways within their frame.",
                        "Op een klein scherm scrollen grote schema's en tabellen horizontaal binnen hun kader.",
                        "Auf kleinen Bildschirmen scrollen große Diagramme und Tabellen seitlich in ihrem Rahmen.",
                    ),
                    (
                        "Les diagrammes de bits et les arbres Wireshark sont denses. La liste des champs sous chaque paquet et la visite guidée en donnent une lecture pas à pas.",
                        "Bit diagrams and Wireshark trees are dense. The field list under each packet and the guided tour give a step-by-step reading.",
                        "Bitdiagrammen en Wireshark-bomen zijn dicht. De veldenlijst onder elk pakket en de rondleiding bieden een stapsgewijze lezing.",
                        "Bitdiagramme und Wireshark-Bäume sind dicht. Die Feldliste unter jedem Paket und die geführte Tour bieten eine schrittweise Lesart.",
                    ),
                    (
                        "Les noms de champs, de commandes et de messages restent en anglais dans toutes les langues, par choix pédagogique.",
                        "Field, command and message names stay in English in every language, by teaching choice.",
                        "Namen van velden, commando's en berichten blijven in alle talen in het Engels, als didactische keuze.",
                        "Namen von Feldern, Befehlen und Nachrichten bleiben in allen Sprachen englisch, aus didaktischen Gründen.",
                    ),
                ]
            ),
        ),
        (
            "framework",
            ("Cadre légal", "Legal framework", "Wettelijk kader", "Rechtsrahmen"),
            P(
                "La directive (UE) 2016/2102 vise les sites des organismes publics, et l'acte européen sur l'accessibilité (directive (UE) 2019/882) vise certains produits et services, comme le commerce en ligne. Ce site personnel et gratuit n'entre dans aucun de ces cadres : cette déclaration est volontaire.",
                "Directive (EU) 2016/2102 covers the websites of public sector bodies, and the European Accessibility Act (Directive (EU) 2019/882) covers certain products and services, such as e-commerce. This free personal site falls under neither: this statement is voluntary.",
                "Richtlijn (EU) 2016/2102 geldt voor de websites van overheidsinstanties, en de Europese toegankelijkheidsakte (richtlijn (EU) 2019/882) voor bepaalde producten en diensten, zoals e-commerce. Deze gratis persoonlijke site valt onder geen van beide: deze verklaring is vrijwillig.",
                "Die Richtlinie (EU) 2016/2102 gilt für Websites öffentlicher Stellen, der European Accessibility Act (Richtlinie (EU) 2019/882) für bestimmte Produkte und Dienstleistungen wie den Online-Handel. Diese kostenlose private Website fällt unter keinen der beiden Rahmen: Diese Erklärung ist freiwillig.",
            ),
        ),
        (
            "report",
            ("Signaler un problème", "Reporting a problem", "Een probleem melden", "Ein Problem melden"),
            P(
                f"Si une page vous pose un problème d'accès, écrivez à {MAIL} ou ouvrez un {a(GH + '/issues/new/choose', 'ticket sur GitHub')}. Indiquez la page, votre navigateur et, si vous en utilisez une, votre aide technique.",
                f"If a page gives you an access problem, write to {MAIL} or open an {a(GH + '/issues/new/choose', 'issue on GitHub')}. Say which page, which browser and, if you use one, which assistive technology.",
                f"Als een pagina u een toegankelijkheidsprobleem geeft, schrijf dan naar {MAIL} of open een {a(GH + '/issues/new/choose', 'ticket op GitHub')}. Vermeld de pagina, uw browser en, als u er een gebruikt, uw hulptechnologie.",
                f"Wenn Ihnen eine Seite ein Zugangsproblem bereitet, schreiben Sie an {MAIL} oder eröffnen Sie ein {a(GH + '/issues/new/choose', 'Ticket auf GitHub')}. Nennen Sie die Seite, Ihren Browser und, falls Sie eine nutzen, Ihre assistive Technologie.",
            )
            + P(
                "Si un contenu ne vous est pas accessible, vous pouvez aussi demander à le recevoir sous une autre forme, par exemple en texte.",
                "If some content is not accessible to you, you can also ask to receive it in another form, for example as text.",
                "Is bepaalde inhoud voor u niet toegankelijk, dan kunt u ook vragen om ze in een andere vorm te krijgen, bijvoorbeeld als tekst.",
                "Wenn Ihnen ein Inhalt nicht zugänglich ist, können Sie ihn auch in einer anderen Form anfordern, zum Beispiel als Text.",
            ),
        ),
    ],
}

EYEBROW = ("Informations légales", "Legal information", "Juridische informatie", "Rechtliche Hinweise")


def updated(page):
    v, h = page["version"], history(page["slug"])
    return per(
        {
            "fr": "Dernière mise à jour : {d} (version {v}). " + a(h, "Versions précédentes"),
            "en": "Last updated: {d} (version {v}). " + a(h, "Earlier versions"),
            "nl": "Laatst bijgewerkt: {d} (versie {v}). " + a(h, "Eerdere versies"),
            "de": "Zuletzt aktualisiert: {d} (Fassung {v}). " + a(h, "Frühere Fassungen"),
        },
        d=DATE,
        v=(v,) * 4,
    )


def build(page):
    """The page as text: the template with this page's head data, main content and contents."""
    slug, t = page["slug"], TPL
    meta = {
        "slug": slug,
        "name": page["title"][1],
        "kind": "info",
        "updated": UPDATED,
        "title": dict(zip(L, page["title"], strict=True)),
        "description": dict(zip(L, page["description"], strict=True)),
    }
    for lang in L:
        need(len(meta["description"][lang]) <= 200, f"{slug}: {lang} description over 200 characters")
    # head: comment, title, description, page-meta
    t = re.sub(
        r"<!--\n  Network Protocols Expert \u2014 reference page template\..*?-->",
        f"<!--\n  Network Protocols Expert: {page['title'][1]} ({slug}). Information page, written by\n"
        "  tools/info-pages.py from templates/protocol-template.html: edit that script, not this file.\n-->",
        t,
        count=1,
        flags=re.S,
    )
    t = re.sub(
        r"<title>.*?</title>", f"<title>{page['title'][1]} | Network Protocols Expert</title>", t, count=1
    )
    t = re.sub(
        r'<meta name="description" content="[^"]*">',
        f'<meta name="description" content="{page["description"][1]}">',
        t,
        count=1,
    )
    t = re.sub(
        r'<script type="application/json" id="page-meta">.*?</script>',
        lambda _: (
            '<script type="application/json" id="page-meta">\n'
            + json.dumps(meta, ensure_ascii=False)
            + "\n</script>"
        ),
        t,
        count=1,
        flags=re.S,
    )
    # main: crumbs, hero, sections
    secs, toc = "", ""
    for n, (sid, title, body) in enumerate(page["sections"], 1):
        secs += (
            f'\n  <section class="sec" id="{sid}" aria-labelledby="h-{sid}">\n'
            f'    <h2 id="h-{sid}"><span class="num">{n}</span>{sp(*title)}</h2>\n' + body + "  </section>\n"
        )
        toc += f'      <li><a href="#{sid}"><span class="n">{n}</span>{sp(*title)}</a></li>\n'
    main = (
        '<main id="main" tabindex="-1">\n\n'
        '  <nav class="crumbs" data-aria="crumbs" aria-label="Breadcrumb">\n    <ol>\n'
        '      <li><a href="../../index.html" data-home>'
        + sp("Bibliothèque", "Library", "Bibliotheek", "Bibliothek")
        + "</a></li>\n"
        f'      <li aria-current="page">{sp(*page["title"])}</li>\n    </ol>\n  </nav>\n\n'
        '  <header class="hero">\n'
        f'    <p class="eyebrow">{sp(*EYEBROW)}</p>\n'
        f"    <h1>{sp(*page['title'])}</h1>\n"
        f'    <p class="lede">{sp(*page["lede"])}</p>\n'
        f'    <p class="f-note">{sp(*updated(page))}</p>\n'
        "  </header>\n" + secs + "\n</main>"
    )
    t = re.sub(r'<main id="main" tabindex="-1">.*?</main>', lambda _: main, t, count=1, flags=re.S)
    nav = (
        '<nav class="toc" aria-labelledby="toc-h">\n  <details id="toc">\n'
        '    <summary id="toc-h">'
        + sp("Sur cette page", "On this page", "Op deze pagina", "Auf dieser Seite")
        + "</summary>\n"
        "    <ol>\n" + toc + "    </ol>\n  </details>\n"
        '  <script>if (matchMedia("(min-width: 64rem)").matches) document.getElementById("toc").open = true;</script>\n</nav>'
    )
    t = re.sub(r'<nav class="toc" aria-labelledby="toc-h">.*?</nav>', lambda _: nav, t, count=1, flags=re.S)
    need(
        "TEMPLATE" not in t.split("<body", 1)[1] and "data-tpl" not in t, f"{slug}: template placeholder left"
    )
    return t


def main(argv):
    check = argv[1:] == ["--check"]
    if argv[1:] and not check:
        sys.exit(__doc__)
    stale = []
    for page in (LEGAL, TERMS, PRIVACY, ACCESS):
        out, text = ROOT / "pages" / page["slug"] / "index.html", build(page)
        if check:
            if not out.exists() or out.read_text(encoding="utf-8") != text:
                stale.append(str(out.relative_to(ROOT)))
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"wrote {out.relative_to(ROOT)} ({len(text)} bytes)")
    if stale:
        sys.exit("out of date, run python3 tools/info-pages.py: " + ", ".join(stale))


if __name__ == "__main__":
    main(sys.argv)
