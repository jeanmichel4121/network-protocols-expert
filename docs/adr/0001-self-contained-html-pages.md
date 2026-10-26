# ADR 0001: Self-contained HTML pages, no framework

- Status: accepted
- Date: 2026-10-26

## Context

Readers study offline, on exam preparation laptops and in labs without internet. Pages must last for years without a toolchain.

## Decision

One HTML file per protocol with inline CSS, JavaScript and SVG; vanilla code only; no CDN, font, image or network call. Shared layout comes from `templates/protocol-template.html` and is copied verbatim by `tools/sync-shared.py`.

## Consequences

A page opens by double-click and never breaks because of a dependency. Shared code is duplicated in every page, so CI (`check_pages.py`) fails when a page drifts from the template.
