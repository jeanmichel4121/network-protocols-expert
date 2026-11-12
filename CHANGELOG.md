# Changelog

All notable changes to this project are documented in this file.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Versioning rules for this library:
- **MAJOR**: template or page structure change that affects every page
- **MINOR**: new protocol page or new section
- **PATCH**: corrections (facts, commands, translations, typos)

## [Unreleased]

## [0.9.0] - 2026-11-12

### Added
- Template: layers view of a frame (`data-view="layers"`: bit diagram coloured by OSI layer,
  layer strip, detail panel), flowchart (`ol.flow`), documented sample outputs
  (`details.outs`) and an icon sprite for page diagrams (`tools/page-icons.py`, checked in
  CI); Cisco icons `pc` and `workgroup-switch` (ADR 0012).
- OSI and TCP/IP: an HTTP request frame (`osi-http`) with its payload read layer by layer,
  the DNS payload detailed, a switch in the encapsulation animation, an end-to-end HTTP
  journey (client, switch, two routers, firewall, load balancer, server) showing what each
  device reads and rewrites, expected outputs under the verification commands of the six
  vendors, a layer 1 to 7 troubleshooting flowchart.

### Changed
- OSI and TCP/IP: the frames of chapter 2 keep the layers view only; the Wireshark tree, hex
  dump, guided tour and field list are read on the Ethernet and IPv4 pages. The "next layer"
  field, the DNS journey and "what changes at each hop" are redrawn with topology icons and
  a table tied to the diagram. The fault table marks its key words. The quiz is rewritten
  (17 questions). Sources renumbered (103).

### Removed
- OSI and TCP/IP: cross-layer protocols, tunnels, MTU and MSS, and layer interactions leave
  the "Advanced behaviour" chapter; each gets its own article later.

## [0.8.0] - 2026-11-08

### Added
- Legal notice: independence (no commercial involvement of any third party: no sponsor,
  advertising, affiliate link, paid content or partnership), and the texts written with AI
  tools, reviewed by the author, who holds editorial responsibility.
- Terms of use: an "in short" summary (free use, what needs written permission); linking to
  the site or showing it in a course is always allowed; proper use and vulnerability reports;
  the French version prevails.
- Privacy page: a diagram of what a visit sends and keeps, with its legend and parts list;
  links to other sites; the versions of the page. Every information page shows its version
  and links its history.
- `robots.txt`: the shared `__usage_ai-training` token (IETF individual draft, backed by
  Google, Microsoft, OpenAI and Anthropic), `Content-Usage: train-ai=n` (IETF aipref) and six
  more AI training crawlers. `security.txt` also gives an email contact.
- The 404 page and the root language chooser link the four information pages.
- `tools/info-pages.py` writes the information pages in the four languages; CI fails if a page
  differs from it.

### Changed
- Consent to keep data on the device lasts six months, as the Belgian Data Protection
  Authority recommends: `npe-remember` holds the date of the consent, and an expired consent
  deletes what it kept. The footer says so under the switch, with a link to the details.
- Privacy page: the right to object shown on its own (GDPR art. 21(4)); emails deleted at the
  latest 12 months after the last exchange; the Belgian rule cited (art. 10/2 of the Act of
  30 July 2018); the abuse limits named (requests per address, blocklist).
- Footer: "No advertising, no sponsor".

### Fixed
- On a phone, a diagram wider than the screen was cut on the right (Ethernet and OSI
  concepts). It now scrolls inside its frame, which the keyboard can reach (WCAG 1.4.10 and
  2.1.1), as the accessibility statement says.

## [0.7.0] - 2026-11-07

### Added
- Legal pages, in four languages, linked from every page: legal notice, terms of use, privacy
  (GDPR, browser storage, rights, Belgian Data Protection Authority) and a voluntary
  accessibility statement (`pages/`, published at `/<lang>/legal/`, `/terms/`, `/privacy/`,
  `/accessibility/`).
- Privacy: a "remember my choices and progress on this device" switch (footer and privacy
  page, unticked by default) and a "delete this site's data" button. The smoke test fails if a
  page writes `localStorage` without the reader's consent.
- Text and data mining reservation (Directive (EU) 2019/790 art. 4(3), Belgian Code of economic
  law art. XI.190, 20°) in machine-readable form: `tdm-reservation` meta tag on every page,
  `/.well-known/tdmrep.json` (TDMRep), and `robots.txt` rules for the AI training crawlers.
- ADR 0010 (content licence) and ADR 0011 (privacy by design, text and data mining reservation).

### Changed
- Content licence: CC BY-NC-SA 4.0 instead of CC BY-SA 4.0 (ADR 0010). Commercial use needs
  written permission. Releases up to v0.6.0 stay available under CC BY-SA 4.0.
- Browser storage: language, theme and the chapter menu stay in the tab by default
  (`sessionStorage`); reading progress (chapters opened, "Resume" link, quiz scores) is kept
  only with the reader's consent.
- Footer: a "Legal" column, the new licence, copyright holder Jean-Michel Cuvelier; JSON-LD
  `license` and `copyrightHolder`.

## [0.6.0] - 2026-11-07

### Added
- ICMP page (`protocols/icmp/`): ICMP for IPv4, every message type read bit by bit (eight sample
  packets built by `tools/packet-builder.py`: Echo Request and Reply, Fragmentation Needed, Port
  Unreachable, Time Exceeded, Redirect, extended Time Exceeded with an MPLS object, Timestamp),
  ping, traceroute and Path MTU Discovery as step-by-step animations, when an error must not be
  sent, rate limits, PMTUD black holes, NAT, redirects, security, commands on six platforms, 17 quiz
  questions; label `protocol::icmp`.
- ARP page (`protocols/arp/`): resolution on and off the subnet, ARP cache, gratuitous ARP, address
  conflict detection (RFC 5227), proxy ARP, ARP with NAT, spoofing and Dynamic ARP Inspection,
  ARP and MAC timer mismatch, six sample packets built by `tools/packet-builder.py` (Request, Reply,
  Probe, Announcement, gratuitous Reply, 802.1Q), three animations, commands on six platforms,
  17 quiz questions; label `protocol::arp`.
- IPv4 and OSI: same learning path as the Ethernet page. Every chapter states its goals; Concepts,
  Operation and Advanced are cut into numbered lessons that end with key points and, where it
  helps, a self-check; every sample packet lists its fields in order under the diagram.
- Packet views: a guided tour under every sample packet (previous field, next field) walks the
  fields in order, selects each one in the bit diagram and in the Wireshark tree and shows its
  detail. The bar is written in the page by `tools/packet-builder.py --update`.
- OSI: a step-by-step animation of encapsulation and decapsulation of the DNS query, next to the
  static diagram.
- IPv4: four addressing lessons in Concepts (address and prefix, subnetting and aggregation,
  local or remote decision, private and special addresses) with three diagrams, a table of common
  prefixes and a self-check each; sources RFC 4632, RFC 950, RFC 3021 and RFC 1918 added.
- Every diagram of the three pages now has, under its colour legend, a list that explains what the
  drawing contains: the eleven IP option layouts, the IPv4 header structure, the checksum
  computation, the eight animations, the layer and encapsulation diagrams, the physical-layer name.

### Changed
- IPv4: the note on the Wireshark preferences used for the trees is folded, so the chapter opens on
  the first packet; the labels of the encapsulation diagram are translated.
- Animations: the explanatory labels inside the eight step-by-step diagrams (Ethernet, IPv4, OSI)
  are translated in the four languages; field, state and message names stay in English. A badge
  that shows an explanation ("idle") is translated through the figure's `data-anim-i18n`
  dictionary and follows the language switch.

### Fixed
- OSI, Ethernet, IPv4: corrections from a review. Citations (DNS AD and CD bits to RFC 4035, default
  TTL 64 to the IANA registry, EtherType and DNS registries, HTTP/3 on UDP 443, MPLS shim to RFC 3032,
  TCP reserved bits and the ACK flag in a RST, X.200 editions), wording (tunnels, RFC 1122 and the
  upper layers, ARP cache timeout, TLS on layers 5-6), dead NetScaler links replaced by archived
  copies, three Cisco URLs, Palo Alto capture stages, IOS XR TCP MSS adjustment and Q-in-Any
  examples, and the Ethernet menu entry "Frame formats".
- Packet views: the bit diagram reserves its height before the page script draws it
  (`tools/packet-builder.py --update` writes the number of rows), so the panel below it no longer
  moves over a slow link (layout shift 0.110 on the English OSI packets chapter).

## [0.5.0] - 2026-11-06

### Added
- Template: learning-path blocks (`.goals`, `h3.lesson`, `.callout.recap`, `details.check`): chapter
  goals with time and prerequisites, numbered lessons, key points, and a self-check whose answer
  stays hidden until opened.
- Ethernet: every chapter states its goals and ends with key points; Concepts, Operation and
  Advanced are cut into numbered lessons with a self-check each; every frame of the Packet formats
  chapter lists its fields in order, with size and role, under the diagram.
- Build: a link to another protocol page (`../<slug>/index.html`) is rewritten to that page's
  overview in the same language.

### Changed
- Theme: dark by default on every page, also without JavaScript; the toggle to light is remembered.
  The smoke test checks the default and the stored light choice.

## [0.4.0] - 2026-11-06

### Added
- Ethernet, Concepts: the physical layers from 1BASE5 to 800GBASE (134 IEEE 802.3 types), with a
  diagram on how to read a name, the meaning of every letter, one collapsible table per rate and the
  names seen on optics that are not IEEE 802.3.
- Template: a field list under a diagram (`.fields-t`, `dl.fields`), one row per field with what it
  holds and what it is for; used under the seven diagrams of the Ethernet Concepts chapter.

### Changed
- Ethernet, Concepts: an envelope diagram under the first paragraph (host A sends host B a frame:
  to, from, contains, content and the FCS as the seal).
- Home page: the pages are listed in a suggested reading order (page-meta `order`): the layered
  model first, then each layer bottom-up, with one sentence saying so.
- Site: no certification is named any more ("expert level" instead of "CCIE level") on the home
  page, in the page titles and descriptions, in the template and in the Ethernet quiz.

## [0.3.0] - 2026-11-06

### Added
- OSI and TCP/IP models page (`protocols/osi-tcpip-model/`): the seven OSI layers and the four
  TCP/IP layers, encapsulation read on two generated frames (DNS query over UDP, TCP SYN), two
  animations, per-layer verification commands on the six platforms, a bottom-up troubleshooting
  tree and a 16-question quiz. `tools/packet-builder.py` builds the two frames (`osi-dns`,
  `osi-syn`) and checks their IPv4, UDP and TCP checksums.

### Changed
- Ethernet, Concepts: three diagrams for the terminology (sizes, MAC address, VLAN tag) and one
  for the frame variants; the two reference tables are collapsible; the sizes table states its
  units, and its throughput formula has its multiplication signs back.

### Fixed
- Ethernet: 01-80-C2-00-00-08 is filtered by customer bridges too (802.1Q Table 8-1); 4092
  usable VLANs in the 0x003-0xFFE range; Q-in-Q adds 4 octets per tag; the IPv4 PMTUD message
  is "Fragmentation Needed".
- IPv4: comparison signs shown as `&lt;` and `&gt;`; one untranslated cell; IPComp is RFC 3173
  and SCTP RFC 9260; Timestamp overflow wording; CS3 usage per RFC 4594; Palo Alto counter
  command and description, NetScaler counter labels, as documented.

## [0.2.0] - 2026-11-05

### Changed
- Packet views: the whole 32-bit rows of a long field are folded into one row (a 64-byte
  field is no longer drawn as 16 identical rows), with its legend entry; the bit diagram
  always shows its 32 columns, with the field detail under it and the Wireshark tree below
  (side by side on very wide screens only).
- Ethernet: the seven value tables are collapsible cards, closed by default.
- Accent colour: night blue to cyan (logo, links, buttons, gradient) instead of indigo to
  violet, which was too close to the purple of TLVs in the diagrams.

## [0.1.0] - 2026-11-05

First release: the Ethernet and IPv4 pages, published as chapters, the page template and its
tooling, the CI pipeline and the public site.

### Added
- Chapter list: a button folds it away on wide screens, so the chapter gets the full width; the
  choice is kept per reader, and pointing at the left edge of the window shows the list again.
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
- Project scaffold, `CLAUDE.md` authoring rules, home page in French, English, Dutch and German.
- `tools/packet-builder.py` with OSPFv2 Hello sample and RFC 1071 checksum self-test.
- Self-hosted GitLab Runner setup for the NAS (`infra/nas-runner`).

### Changed
- Ethernet page, clarity pass: the Concepts chapter opens in plain language with a new diagram of
  the five fields of a frame, the stack diagram is redrawn as "what each layer adds", the CSMA/CD
  sequence is a numbered list, the packet and advanced chapters say where to start, and the ASCII
  arrows are gone from the prose (drawn arrows in diagrams and legends).
- Home page: plain wording in the four languages (hero, section headings, feature cards and the
  four steps), the key-numbers band is removed and the card no longer mentions a prediction step
  the pages do not have. IPv4 page: `...` replaces the ellipsis character in text and diagram
  labels, and the `⇒` shorthand and one vague adjective are written out in words.
- Visual refresh of every page: slate background with an indigo to violet accent (logo and
  favicon included), gradient on the primary buttons, the active language, chapter numbers and
  the selected packet tab, elevation (shadows, hover lift) on cards, diagrams, command blocks,
  tables and quiz questions, an icon per chapter on the overview cards, a reading progress bar
  under the header (scroll-driven, off with reduced motion), the current chapter highlighted
  in the chapter list, bolder headings and striped table rows. The packet colour code is
  unchanged. Contrast checked by axe in both themes.
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
- Browser smoke test: the packets chapters are also loaded over a 64 KB/s link, so a script
  that changes the first screen after a partial paint fails every time (the CLS check alone
  caught the Ethernet formats shift only when the runner was busy).
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
- Page text no longer uses em dashes, middle-dot separators or decorative arrows
  (writing-style rule added to CLAUDE.md); page titles use "Page | Network Protocols Expert".
- Deploy publishes the site publicly on https://learning.cuvelier.tech (NAS, atomic
  releases, smoke test) instead of GitLab Pages; the runners now live in the homelab
  stack `learning` (`infra/nas-runner` is a pointer).

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

[Unreleased]: https://github.com/jeanmichel4121/network-protocols-expert/compare/v0.9.0...main
[0.9.0]: https://github.com/jeanmichel4121/network-protocols-expert/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/jeanmichel4121/network-protocols-expert/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/jeanmichel4121/network-protocols-expert/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/jeanmichel4121/network-protocols-expert/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/jeanmichel4121/network-protocols-expert/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/jeanmichel4121/network-protocols-expert/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/jeanmichel4121/network-protocols-expert/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/jeanmichel4121/network-protocols-expert/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/jeanmichel4121/network-protocols-expert/tree/v0.1.0
