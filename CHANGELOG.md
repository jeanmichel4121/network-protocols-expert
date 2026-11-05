# Changelog

All notable changes to this project are documented in this file.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Versioning rules for this library:
- **MAJOR**: template or page structure change that affects every page
- **MINOR**: new protocol page or new section
- **PATCH**: corrections (facts, commands, translations, typos)

## [Unreleased]

### Added
- Links to an anchor of a former full page (`/fr/ethernet/#h-pkt-eth-ii`) are sent on to the
  chapter that now holds it (map written by `build_site.py` in each overview).
- IPv4 page (`protocols/ipv4/`): full header, DS field (DSCP, ECN), fragmentation and PMTUD,
  every IP option (registry with the RFC 7126 advice and the layout of each option); ten sample
  packets from `tools/packet-builder.py` (checksums, fragments and the RFC 1624 update checked by the
  self-test), field-by-field reference, value tables (DSCP, ECN, protocol numbers, special-purpose
  addresses, ICMP), checksum walk-through, three step-by-step animations, six platforms with sourced
  commands, decision tree, 20 quiz questions, 109 sources in `sources.md`. Listed on the home page;
  label `protocol::ipv4`.
- Published chapters (ADR 0009): every protocol page is also published as an overview
  (header and one card per chapter), one URL per section with the chapter list,
  breadcrumb and previous/next links (no full-page version: it was dropped before the
  first release, the chapters are the way to read a protocol). The source
  stays one self-contained file; links to anchors in another chapter are rewritten, the
  sitemap lists every chapter and `check_site.py` checks that each one is linked.
- Template packet set (`NPE.pktset`): the sample packets of a section are tabs, one packet
  shown at a time (the Ethernet formats go from about 20,000 px to 8,000 px); a link into a
  packet opens its tab; all packets are shown without JavaScript and in print. The tab list
  and each packet's chips line are written in the page by `tools/packet-builder.py --update`
  (checked by `check_pages.py`), so a page rendered progressively over a slow link does not
  shift (the Ethernet formats chapter measured a CLS of 0.28 that way).
- Template components (needed by IPv4): nested Wireshark tree groups (`ws_groups`,
  `ws_group`), the value Wireshark prints when it differs from the raw one (`ws_value`), its
  generated lines (`ws_pre`, `ws_more`) and long data fields drawn on a few rows only
  (`rows`, cut mark), a bit diagram that starts at a given bit (`grid_from`: the IPv4 header on
  its own 32-bit rows, Ethernet kept in the tree and hex dump); structure diagrams without sample
  values for TLVs and options (`NPE.struct`); a checksum walk-through computed from the builder bytes
  (`NPE.csum`, RFC 1071, incremental update per RFC 1624); collapsible field reference
  cards (`.fref`); one page-wide block of field docs shared by every packet (`data-field-docs="*"`);
  green and measured-span lines (`ln-ok`, `ln-span`), text halo and a green `.tag.ok`. A chapter
  page gets a copy of the packet data its components use (`data-packet`, `data-after`). The template
  shows them on an OSPF LLS TLV and the Hello checksum.
- Ethernet page (`protocols/ethernet/`): Ethernet II, IEEE 802.3 LLC and SNAP, IEEE 802.1Q
  C-TAG and Q-in-Q, MAC Control PAUSE and PFC; eight sample frames from
  `tools/packet-builder.py` (FCS and CRC residue checked), three step-by-step animations,
  MTU accounting per vendor, six platforms with sourced commands, decision tree, 17 quiz
  questions, sources in `sources.md`. Listed on the home page.
- Footer: source code, report an error and content licence (CC BY-SA 4.0) links;
  licence and author in the JSON-LD of every page.
- Public repository setup: MIT (code) and CC BY-SA 4.0 (content) licences with REUSE
  per-file licensing, code of conduct, security policy with private reporting,
  citation file, GitHub issue forms and support page, shared label taxonomy
  (`.github/labels.yml`, `scripts/sync_labels.py`), professional README.
- CI: branch-name and merge-request-title checks (trunk-based), REUSE lint, and
  `verify:site` (HTML validation, links between pages, protocol index, security.txt).
- `security.txt` (RFC 9116) published by the site build.
- Audit baseline of both forges (`docs/repository-settings.md`) with a live check
  (`scripts/audit_repos.py`), architecture decision records (`docs/adr/`), weekly
  dependency report (`scripts/check_updates.py`), CycloneDX SBOM linked from releases,
  MR templates (Correction, Template-change, Release) and issue templates (Feature,
  Security, Release), GitHub improvement form and PR notice.

### Changed
- UX review of the published site:
  - step-by-step diagrams show every step faintly from the initial state (the IPv4 flowchart
    started as an empty frame) and use the full width;
  - on a narrow screen the packet tabs are one row that scrolls sideways (10 tabs took four
    rows) and the selected tab stays in view;
  - a quiz question sits inside its card instead of across the border; lighter header facts;
  - the chapter list and the overview cards mark the chapters already opened (kept in
    `localStorage`, per reader);
  - the home page offers to resume the chapter read last, and the quiz card shows the last
    score (both per reader, in `localStorage`);
  - French text gets a no-break space before `: ; ? !` and inside guillemets, so a mark never
    starts a line (`build_site.py`).
- CI tooling: ruff 0.17.3 (package and pre-commit hook), reuse 6.3.0 and cyclonedx-bom 8.0.1,
  as reported by the weekly dependency check; pins recompiled with hashes for Python 3.12.
- `scripts/sync_labels.py` and `scripts/audit_repos.py` read `GITLAB_PERSONAL_ACCESS_TOKEN` and
  `GITHUB_PERSONAL_ACCESS_TOKEN` (the names used everywhere else) instead of `GITLAB_TOKEN` and
  `GITHUB_TOKEN`; the CI pipeline name and the docs no longer use a middle dot as separator.
- Template packet view: fields narrower than a byte (802.1Q PCP, DEI, VID), one Wireshark
  tree entry per protocol (`tree` key, optional `ws_root`), bit-mask prefix in tree lines,
  flag texts and widths, and an "Allowed values" row in the field details.
- Template diagrams: schematic SVG vocabulary (`svg.sch`, shapes `sh-*` and lines `ln-*` in
  the library colour code) and animation elements that appear at a step (`data-s`) and
  disappear after another (`data-until`).
- Template: inline markers `.tag.vend` (vendor deviation) and `.tag.err` (not supported or
  not documented), muted comments in command blocks.
- Browser smoke test: pages checked in parallel (`SMOKE_WORKERS`, default 4), one browser
  per worker thread; the CI job uses 2, as the NAS runner gives a job 1 GB of memory (4
  browsers crash there).
- Table of contents: a wrapped entry keeps its indent after the chapter number.


### Fixed
- Ethernet page: the vendor callouts use the template's `callout vendor` class (they were
  unstyled); spaced hyphens used as separators replaced in `sources.md`, the source list, the
  command comments and three diagram labels.
- IPv4 diagrams: two legend entries had lost their arrow symbol.
- Headings break a word that is longer than the line (German compounds in a chapter title
  overflowed by 8 px at 360 px).
- Template: animation control icons were drawn at the width of the diagram (480 px)
  instead of 18 px; packet comment without `--`, which is invalid inside an HTML comment.
- Template: example router IDs moved to the RFC 5737 range (198.51.100.1/2 instead of
  the public 1.1.1.1/2.2.2.2); straight quotes instead of curly ones and numbered steps
  (1, 2, 3) as required by the writing style rules.
- Release assets linked to a disabled GitLab Pages site; `.gitignore` now excludes
  captures, `.env` files and editor files as documented.
- Public read-only GitHub mirror (GitLab push mirror of protected branches), documented in
  README and CLAUDE.md.
- Site footer in columns (library links, method, project, version, documentation
  addresses) shared by every page; centred closing band on the home page.
- CI/CD pipeline: lint (YAML, Python, Conventional Commits), tests, secret scanning,
  site build, headless-browser verification, GitLab Pages deploy, tag-based releases.
- Repository governance: MR and issue templates, CODEOWNERS, contributing guide,
  pre-commit hooks, editor and lint configuration.

- Page template `templates/protocol-template.html`: the nine sections, synchronised RFC bit
  diagram + Wireshark tree + hex dump rendered from the packet builder's field map,
  step-by-step animation with prediction prompts, vendor tabs, decision tree, accessible
  quiz with explained answers, light/dark themes, print stylesheet (demo: OSPFv2 Hello).
- Redesigned home page sharing the template's design system.
- One URL per language (`/fr/`, `/en/`, `/nl/`, `/de/`) with hreflang, canonical, Open Graph,
  JSON-LD, sitemap, robots.txt, 404 and a root language chooser (`scripts/build_site.py`).
- `docs/web-standards.md`: sourced web, accessibility (WCAG 2.2 AA) and learning-design standards.
- CI: axe-core WCAG 2.2 AA in light and dark themes, CLS budget, reduced-motion,
  hreflang and language-URL checks; static checks for balanced translations, shared
  template blocks, diagram legends and builder-generated packets.
- `tools/packet-builder.py`: field map output and `--update` to embed samples in a page.
- Landing page: hero with an animated network topology (OSPF, BGP, TLS, IPsec packets between
  routers, firewall and load balancer; pausable, paused off-screen, still under reduced motion),
  key numbers, how a page teaches, platforms and an About band linking to about.cuvelier.tech.
- About link in the shared header; `tools/sync-shared.py` propagates the template's shared
  blocks (pre-paint script, styles, page library, header) to every page.
- CI: axe also runs at 360 px; script-driven animation must stay still under reduced motion.
- Landing topology: remote sites (CE-A, CE-B), a core backbone (P1 to P4), two data centers
  (firewall, load balancer, three servers each, DCI); TLS sessions spread round robin over the
  server pool, IPsec tunnels from the sites; nodes pulse when a packet reaches them.
- Landing topology in isometric 3D, generated by `tools/landing-topology.py`: zones as slabs,
  devices drawn with the official Cisco network topology icons (`tools/icons/cisco`, unaltered
  as Cisco's terms require), laid out left to right under the headline; CI checks the embedded
  scene matches the generator.

### Changed
- Page text no longer uses em dashes, middle-dot separators or decorative arrows
  (writing-style rule added to CLAUDE.md); page titles use "Page | Network Protocols Expert".

### Changed
- Deploy publishes the site publicly on https://learning.cuvelier.tech (NAS, atomic
  releases, smoke test) instead of GitLab Pages; the runners now live in the homelab
  stack `learning` (`infra/nas-runner` is a pointer).

## [0.1.0] - 2026-10-25

### Added
- Project scaffold, `CLAUDE.md` authoring rules, home page in French, English, Dutch and German.
- `tools/packet-builder.py` with OSPFv2 Hello sample and RFC 1071 checksum self-test.
- Self-hosted GitLab Runner setup for the NAS (`infra/nas-runner`).
