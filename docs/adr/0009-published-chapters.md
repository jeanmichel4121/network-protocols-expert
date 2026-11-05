# ADR 0009: Each page published as chapters, one URL each

- Status: accepted
- Date: 2026-11-05

## Context

A complete protocol page is long. At 1280 px the Ethernet page measures about 50,000 px,
20,000 px of it for the packet formats (eight frames one after the other); the IPv4 draft
received from outside measures 43,000 px. The owner asked for the content not to be one
block: a reader studies one chapter at a time, links to it and comes back to it. Pages must
still open offline by double-click (ADR 0001), and one source file per protocol keeps the
CI checks as they are (language completeness, packets equal to the builder output).

## Decision

- The source stays one self-contained file per protocol: `protocols/<slug>/index.html`.
- `scripts/build_site.py` publishes it as an overview (`/<lang>/<slug>/`: header and one card
  per chapter) and one URL per `<section class="sec">` (`/<lang>/<slug>/<section id>/`).
  No full-page version is published (it was at first, as `/<lang>/<slug>/all/`, and was
  removed on 2026-11-05: the chapters are the way to read a protocol).
- A chapter page keeps the shared CSS and JavaScript inline, gets the chapter list (left
  column on wide screens), a breadcrumb, previous/next links, its own title, description,
  canonical, hreflang and JSON-LD (`isPartOf` the overview, which lists `hasPart`). Anchors
  that moved to another chapter are rewritten to that chapter's URL.
- The sample packets of a section are shown as tabs (`NPE.pktset`), one packet at a time;
  without JavaScript and in print every packet is shown.

Rejected alternatives: several thematic pages per protocol (each would need its own vendor,
troubleshooting and 15-question quiz sections, with duplicated content); one page that shows
one chapter at a time by script (still one heavy URL, a single indexed page).

## Consequences

- Every section must be listed in the page's table of contents (`nav.toc`): the build fails
  otherwise, and `check_site.py` checks that every chapter is linked from its overview.
- The site has about ten times more HTML files. The browser smoke test checks pages in
  parallel (`SMOKE_WORKERS`, one browser per worker thread).
- Printing a chapter prints that chapter (current language, sections expanded).
- A chapter starts with its own content, so what a script fills in after the first paint
  now moves the first screen (on the long page it was far below the fold). The packet chips
  line and the packet tab list are written in the markup by `tools/packet-builder.py
  --update`, and `check_pages.py` checks them.
