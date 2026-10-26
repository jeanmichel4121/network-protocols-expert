# CLAUDE.md - Network Protocols (expert learning library)

## Role and goal
I am a network & security engineer (multi-vendor: Cisco, Check Point, F5, Palo Alto,
NetScaler, FortiGate). This repository builds an **expert-level (CCIE) learning library**:
one self-contained HTML page per network protocol, all pages built from the same template,
each page available in **French, English, Dutch and German**.
The sole purpose: learn every network protocol in depth and pass expert-level
certifications (CCIE for Cisco and the equivalent expert level for the other vendors:
Check Point CCSM / CCSM Elite, Palo Alto Networks Network Security Architect,
Fortinet NSE 8, F5 Certified Solution Expert, NetScaler Expert; see README.md).

- Chat with me in **French**: structured, direct, technically precise.
- Page content: the 4 languages (see "Multilingual rules").
- Before writing a page, ask me which protocol and, if relevant, which scope
  (e.g. OSPFv2 only or OSPFv2 + v3, BGP base or + EVPN/VPNv4). Otherwise do not ask:
  state your assumption and proceed.

## Repository layout
```
/
├── CLAUDE.md
├── README.md  CONTRIBUTING.md  SECURITY.md  CODE_OF_CONDUCT.md  CHANGELOG.md  CITATION.cff
├── LICENSE  LICENSES/  REUSE.toml  # MIT (code), CC BY-SA 4.0 (content), Cisco icons terms
├── .gitlab-ci.yml                  # CI pipeline, runs on the self-hosted runners (NAS)
├── .gitlab/                        # MR and issue templates, CODEOWNERS
├── .github/                        # issue forms, SUPPORT.md, labels.yml (both forges)
├── index.html                      # home page: list of all protocols (same 4-language switch)
├── templates/
│   └── protocol-template.html      # the reference page - every protocol page copies it
├── protocols/
│   └── <protocol-slug>/            # lowercase, e.g. ospf, bgp, tcp, ipsec-ikev2
│       ├── index.html              # the page (self-contained)
│       └── sources.md              # every source used, with section numbers and links
├── tools/
│   ├── packet-builder.py           # builds sample packets, computes checksums/lengths
│   ├── sync-shared.py              # copies the template's shared blocks into every page
│   ├── landing-topology.py         # draws the home-page topology
│   └── icons/cisco/                # unaltered Cisco topology icons (own terms)
├── scripts/                        # build_site, check_pages, check_site, smoke_test,
│                                   # check_commits, check_updates, sync_labels,
│                                   # audit_repos, releases
├── docs/                           # web-standards.md, repository-settings.md (forge
│                                   # baseline for audits), adr/ (decisions), assets/
└── requirements/                   # pinned CI tooling (ci.in -> ci.txt with hashes)
```
- When a page is created or renamed, update `index.html` in the same change.
- Changes to the shared layout go into `templates/protocol-template.html` first,
  then are propagated to every existing page with `python3 tools/sync-shared.py`
  (list the pages updated). CI fails if a page drifts from the template.

## Git and GitLab workflow
- Remote: private GitLab.com project `jeanmichel4121/network-protocols-expert`
  (source of truth). CI/CD runs on self-hosted GitLab Runners on my NAS
  (tag `nas`; tag `nas-deploy` for the deploy, protected branches only, official
  `alpine` images only). Shared runners are disabled.
- Public read-only mirror on GitHub (`jeanmichel4121/network-protocols-expert`), fed by a
  GitLab push mirror (protected branches and tags, SSH deploy key). Pull requests are
  disabled there; GitHub issues are the public feedback channel (issue forms). Never push
  or commit on GitHub. Everything committed becomes public, history included.
- Trunk-based development: `main` is the only long-lived branch, protected (no direct push).
  Never commit directly to `main`. One short-lived branch per change:
  `feat/<protocol-slug>`, `fix/<protocol-slug>-<topic>`, `chore/<topic>`, `docs/<topic>`.
  CI rejects other branch names.
- Commit messages follow Conventional Commits, in English:
  `feat(ospf): add LSA type 5 packet views`, `fix(bgp): correct OPEN hold time default`.
  The MR title must follow the same format: it becomes the squash commit on `main`
  (fast-forward merge, linear history).
- One protocol page (or one template change and its propagation) per merge request.
  The MR description lists: pages touched, sources added, and the "Definition of done"
  checklist with each box ticked or explained (template `Protocol-page`).
- **Do not push, merge, tag or delete branches without my explicit approval in chat.**
- Every MR adds a line to `CHANGELOG.md` under `[Unreleased]` (Keep a Changelog).
  Releases: SemVer tags `vX.Y.Z` on `main` (MAJOR = template change for all pages,
  MINOR = new protocol/section, PATCH = corrections); the pipeline creates the release.
- Labels: taxonomy in `.github/labels.yml`, applied to both forges with
  `scripts/sync_labels.py`. A new protocol page adds its `protocol::<slug>` label there.
- Forge settings: baseline and reasons in `docs/repository-settings.md`, checked by
  `scripts/audit_repos.py`. A settings change updates that file in the same MR.
  Significant decisions get an ADR in `docs/adr/`.
- Templates: MR `Protocol-page`, `Correction`, `Template-change`, `Release`, `Default`;
  issues `New-protocol`, `Correction`, `Bug`, `Feature`, `Security` (confidential),
  `Release`; GitHub issue forms in `.github/ISSUE_TEMPLATE/`.
- Never commit secrets, tokens, runner registration keys, real configs or captures
  from production. `.gitignore` excludes `*.pcap`, `*.pcapng`, `.env`, editor files.
- Pin everything: CI images by tag + `@sha256` digest (must support `linux/arm64`),
  Python tools in `requirements/ci.txt` with hashes, pre-commit hooks frozen to SHAs.
  Run `pre-commit run --all-files` before pushing.
- The pipeline must pass before merge. CI jobs (keep them lightweight, no external
  network calls from the pages themselves):
  - offline check: no `http://` / `https://` resource loads (src, href to CSS/JS/fonts,
    fetch, XHR) in any page (`check_pages.py`, plus the browser test);
  - HTML validation and link check between pages (`check_site.py` on the built site);
  - language completeness: every translatable block exists in fr, en, nl and de;
  - `tools/packet-builder.py` runs and its outputs match the values embedded in pages;
  - `index.html` lists every folder under `protocols/` (`check_site.py`);
  - also: YAML, ruff, Conventional Commits, branch name, MR title, REUSE licensing,
    gitleaks, axe WCAG 2.2 AA (light, dark, mobile), layout shift, reduced motion.
- Publication: a green `main` pipeline deploys the site **publicly, without
  authentication**, at **https://learning.cuvelier.tech** (one URL per language,
  built by `scripts/build_site.py`). The CSP allows inline JS/CSS and forbids network
  calls (`connect-src 'none'`).

## HTML technical rules (mandatory)
Full rationale and sources: [`docs/web-standards.md`](docs/web-standards.md). Start every
page from `templates/protocol-template.html`; its shared blocks are copied verbatim.
- **One self-contained file per page**: CSS, JS and SVG inline. No CDN, no external
  font, no external image, no network call. The page must open offline by double-click.
- Vanilla HTML/CSS/JS only (no framework, no build step).
- Light and dark mode (`prefers-color-scheme` + manual toggle).
- Responsive down to 360 px wide, no horizontal page scroll (wide tables/grids scroll
  inside their own container).
- `localStorage` only for per-viewer conveniences (chosen language, theme), always wrapped
  in try/catch; the page must work without it.
- Accessible, **WCAG 2.2 AA** (axe-core in CI): semantic headings, `alt`/`aria-label`,
  keyboard-usable interactive elements (roving tabindex + arrow keys), visible focus not
  hidden by the sticky header, targets at least 24x24 px, accessible name = visible text,
  live regions for feedback, contrast at least 4.5:1 in both themes.
- Motion: Play always has Pause; `prefers-reduced-motion` turns animation off.
- No layout shift (CLS < 0.1): theme/language set in `<head>` before paint.
- Printable: a print stylesheet that shows the current language only and expands all
  collapsible sections.

## Multilingual rules
- **One page, a language switch FR | EN | NL | DE** in the header. The four language
  versions are all inside the page (`data-l="fr|en|nl|de"` blocks plus the template's
  inline JS dictionary); switching language never reloads the page.
- Default language: the browser language if it is fr/en/nl/de, else EN.
  Remember the choice in `localStorage`. Set `<html lang>` on switch.
  On the published site each language also has its own URL (`/fr/<slug>/`...) with
  `hreflang`, canonical, Open Graph and JSON-LD; there the URL's language wins and the
  switch rewrites the URL. Title and description per language live in `#page-meta`.
- **Always kept in English in all 4 languages**: protocol field names (Router ID,
  Packet length...), states and events (2-Way, ExStart, Established...), message names
  (Hello, LSU, OPEN...), RFC terms, CLI commands and device output, Wireshark filter names.
  The explanations around them are translated.
- The 4 versions must have **identical content**: same sections, same examples, same
  values. A section is never left untranslated or summarised in one language only.
- Quality: native technical register in each language (not literal translation).
  NL = Netherlands/Flemish neutral standard Dutch; DE = standard German.

## Writing style (all generated content)
- Avoid typography that makes text look machine-generated: no em dashes or en dashes
  used as punctuation (use a colon, comma, parentheses or a new sentence), no curly
  quotes, no decorative emoji, no ornamental arrows or bullets in prose.
- Functional symbols are allowed where they carry meaning: status markers in tables
  and diagrams (pass/fail), arrows inside diagrams, bit rulers.
- Plain, factual sentences. No filler, no marketing tone.
- Page titles use "Page | Network Protocols Expert".

## Page structure (same order on every page)
1. **Header**: protocol name, one-line definition, OSI layer, transport/encapsulation
   (IP protocol number, TCP/UDP port, EtherType), governing standards (RFC/IEEE numbers),
   language switch, theme toggle, table of contents.
2. **Concepts**: purpose, where it sits in the stack, terminology, design trade-offs,
   versions/variants and their differences.
3. **Packet formats - every message type** (see "Packet representation").
4. **Operation (animated)**: state machine(s) and message exchanges, numbered step by
   step (1, 2, 3...), with play / pause / next / previous controls. Timers and their
   defaults.
5. **Advanced behaviour (expert)**: edge cases, interoperability issues, scaling limits,
   security (attacks and protections), tuning, convergence, known RFC ambiguities.
6. **Multi-vendor configuration and verification** (see "Vendor rules").
7. **Troubleshooting**: yes/no decision tree ending in verification commands per vendor;
   table of common faults (symptom, cause, command, expected output, fix).
8. **Quiz**: at least 15 CCIE-level questions (scenario-based, packet-reading,
   "what breaks if..."), each with explanation and the RFC/vendor reference.
9. **Sources**: full list (also in `sources.md`).

Sections 5 to 8 can be collapsible but are open by default on screen.

## Packet representation (mandatory for EVERY message/packet type)
Every message type of the protocol ALWAYS gets **both** views below, shown together
and synchronised: hovering or focusing a field in one view highlights it in the other
and shows a detail panel (name, offset, size in bits/bytes, allowed values, role,
RFC section). A packet is never shown with only one of the two.
1. **RFC-style bit diagram** (mandatory): 32-bit rows, bit ruler 0-31, each field drawn
   at its true width; variable-length and optional fields clearly marked; TLV/sub-TLV
   structures drawn as nested diagrams.
2. **Wireshark-style tree** (mandatory): expandable tree, displayed value and the
   Wireshark display-filter name for each field (e.g. `ospf.hello.hello_interval`).
   Verify filter names against the Wireshark display filter reference.

Optional complements, only when they add value:
- **Decoded hex dump** (offset column, bytes colour-coded by field), e.g. to show
  checksum coverage, TLV encoding, padding or encapsulation layers.
- **Value/code table** (types, flags bit by bit, error codes, default timers, IANA
  values, RFC section for each), e.g. for protocols with large code registries.

Correctness rules for sample packets:
- **Never hand-write values or hex.** Generate every sample packet with
  `tools/packet-builder.py` (Python, struct or scapy) so lengths, checksums, padding
  and flags are correct, and take the displayed values from its output. The builder
  also emits the field map; embed it with
  `python3 tools/packet-builder.py --update protocols/<slug>/index.html`.
  CI fails if an embedded packet differs from the builder output.
- All views of a packet describe the same packet: values in the bit diagram, the tree
  and any optional view must match.

## Vendor rules
Platforms covered on every page, in this order:
1. Cisco (IOS XE, NX-OS, and IOS XR when relevant)
2. Check Point (Gaia clish / Gaia OS, expert mode)
3. F5 BIG-IP (TMOS tmsh; ZebOS imish for dynamic routing)
4. Palo Alto (PAN-OS CLI; set commands + operational commands)
5. NetScaler (CLI; ZebOS VTYSH for dynamic routing)
6. FortiGate (FortiOS CLI)

- For each vendor: configuration example, verification commands, debug commands
  (with a warning on production impact), and sample expected output.
- **Every command block cites the vendor documentation it comes from**: document title,
  software version, section, URL. No command without a source.
- State the software version the commands were checked against (e.g. "PAN-OS 11.1",
  "FortiOS 7.4", "TMOS 17.1", "Gaia R81.20"). Flag syntax that changes between versions.
- If a vendor does not support the protocol or a feature, say so explicitly with the
  source ("not supported on ..."). Never invent a command.
- Where the vendor deviates from the RFC (defaults, non-standard behaviour,
  proprietary extensions), flag it next to the command.

## Document library (Google Drive)
- Reference sources (RFC PDFs, vendor guides) live in Google Drive (connector available):
  `Network Protocoles` (folder ID `1V20Pia8gMlZ3u5afBkAnVMDgtGKQUPKm`), plus vendor
  folders `Cisco` (`1GzcQeZbEjAh4yB9j-dlWiZiE0Oln6Ga_`),
  `Checkpoint` (`1OQx9c5jh2m_l9M2B_lclAOOs6YxVZ6Xu`), `BIG-IP` (`1tl-aUfvyWEZ2fUxkJJ-nmTLzeYQEhSLp`).
- Search order: Drive library, then official web sources (RFC Editor, IANA, vendor docs).

## Source hierarchy (highest wins on conflict)
1. Standards: RFCs (current, including errata and updating RFCs), IEEE, IANA registries
2. Official vendor documentation (configuration guides, CLI references, release notes,
   knowledge-base articles from the vendor)
3. Reference books and vendor whitepapers
4. Conference sessions (Cisco Live, etc.), illustrative only

Rules:
- Cite RFCs with their section number (e.g. RFC 2328 §A.3.2). Mention when an RFC is
  obsoleted/updated and use the current one.
- When the vendor behaviour differs from the RFC, show both and say which one applies.
- Use web search/fetch to verify facts; never rely on memory alone for field layouts,
  code values, default timers or CLI syntax.
- Do not copy figures or long text from sources: redraw and rephrase, then cite.

## Visual standards (every diagram, animation and packet view)
- Title on every diagram stating type and scope; **legend on every diagram**
  explaining every colour, shape, line style, arrow and abbreviation.
- Labels carry information (field names, values, states, timers), never generic labels.
- Every arrow has a direction and states what flows (message type, encapsulation).
- Max about 5 to 7 main elements per diagram; split beyond that. Overview first,
  then details.
- Consistent colour code across the whole library:
  - grey: encapsulation/underlay headers
  - blue: protocol common header
  - teal: message body/payload
  - purple: TLV/options/extensions
  - orange: external/redistributed/vendor-specific
  - green: healthy/expected
  - red: error/drop/fault
- Never rely on colour alone: pair with text, pass/fail markers, line style or shape.
  Works in light and dark mode and in black-and-white print.

## Confidentiality
- Only documentation values in examples: IPv4 192.0.2.0/24, 198.51.100.0/24,
  203.0.113.0/24; IPv6 2001:db8::/32; private ASNs 64496-64511 / 65000+;
  hostnames R1, FW-A, LB-01...; MAC 00:00:5e:00:53:xx.
- Never reproduce real hostnames, IPs, customer names, serial numbers, keys or ticket IDs.
  If I paste any, warn me, replace them with placeholders and never store or commit them.
  (The public site name learning.cuvelier.tech is the one exception.)

## Licensing
- Code, tooling and the template: MIT. Learning content (pages, docs): CC BY-SA 4.0.
  Cisco topology icons: Cisco's own terms, used unaltered. Declared per file in
  `REUSE.toml`; `reuse lint` runs in pre-commit and CI. New file types or folders may
  need a `REUSE.toml` annotation.

## Tools
- Check the available tools/MCP connectors first and use the best fit
  (web search/fetch for RFCs and vendor docs, Python for packet building and checks,
  browser/preview to view pages).
- Ask me only when unsure of the request or when you lack the permission to do the task.

## Definition of done (check before saying a page is finished)
- [ ] Same section order as the template; all 4 languages complete and switchable
- [ ] Every message type has BOTH the RFC bit diagram and the Wireshark tree, synchronised;
      sample packet generated by script
- [ ] Every vendor covered (or explicitly "not supported" with source); versions stated
- [ ] Every command block and every RFC fact has a citation; `sources.md` updated
- [ ] Every diagram has a title and a complete legend; light/dark/print checked
- [ ] Page opens offline, no console error, no external request
- [ ] `index.html` updated
- [ ] Quiz has at least 15 questions with explanations and references
- [ ] Writing style rules respected (no AI-looking typography)
- [ ] Work is on a feature branch, CI pipeline green, MR opened with this checklist
