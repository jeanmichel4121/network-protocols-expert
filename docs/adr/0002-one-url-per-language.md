# ADR 0002: One URL per language, switch without reload

- Status: accepted
- Date: 2026-10-26

## Context

Content exists in French, English, Dutch and German. Search engines index one language per URL; readers want to switch language instantly.

## Decision

All four versions live in the same source page (`data-l` blocks). `scripts/build_site.py` publishes `/fr/`, `/en/`, `/nl/`, `/de/` with `hreflang`, canonical, Open Graph and JSON-LD per language; the switch rewrites the URL with `history.replaceState`.

## Consequences

Translations cannot drift apart (they are reviewed in one file) and each language is indexed. Pages are four times larger than a single-language page, which stays small for text.
