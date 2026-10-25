# CLAUDE.md — Network Protocols (expert learning library)

## Role and goal
I am a network & security engineer (multi-vendor: Cisco, Check Point, F5, Palo Alto,
NetScaler, FortiGate). This project builds an **expert-level (CCIE) learning library**:
one self-contained HTML page per network protocol, all pages built from the same template,
each page available in **French, English, Dutch and German**.
- Chat with me in **French**: structured, direct, technically precise.
- Page content: the 4 languages (see "Multilingual rules").
- Before writing a page, ask me which protocol and, if relevant, which scope
  (e.g. OSPFv2 only or OSPFv2 + v3, BGP base or + EVPN/VPNv4). Otherwise do not ask:
  state your assumption and proceed.

## Repository layout
```
/
├── CLAUDE.md
├── README.md
├── .gitlab-ci.yml                  # pipeline: build → validate → deploy (GitLab Pages)
├── index.html                      # home page: list of all protocols (same 4-language switch)
├── templates/
│   └── protocol-template.html      # the reference page — every protocol page copies it
├── protocols/
│   └── <protocol-slug>/            # lowercase, e.g. ospf, bgp, tcp, ipsec-ikev2
│       ├── index.html              # the page (self-contained)
│       └── sources.md              # every source used, with section numbers and links
├── tools/
│   └── packet-builder.py           # builds sample packets, computes checksums/lengths
├── scripts/                        # CI scripts: check_pages, smoke_test (browser),
│                                   # check_commits, release_notes, create_release
├── requirements/                   # pinned CI tooling (ci.in → ci.txt with hashes)
├── infra/
│   └── nas-runner/                 # docker-compose for the self-hosted runner (no secrets)
├── .gitlab/                        # MR/issue templates, CODEOWNERS
├── CHANGELOG.md · CONTRIBUTING.md · SECURITY.md
└── .pre-commit-config.yaml · .yamllint.yml · pyproject.toml (ruff) · .editorconfig
```
- When a page is created or renamed, update `index.html` in the same change.
- Changes to the shared layout go into `templates/protocol-template.html` first,
  then are propagated to every existing page (list the pages updated).

## Git hosting, CI/CD and publication
- GitLab.com, **private** project "Network Protocols Expert" (`jeanmichel4121/network-protocols-expert`), default branch `main`.
- All CI jobs run on my **self-hosted runner on my home NAS** (ARM64, Docker executor,
  tag `nas`). Shared GitLab runners are disabled. Every CI image must exist for
  `linux/arm64` (use official multi-arch images: python, alpine, node…).
- Pipeline stages: `lint` (yamllint, ruff, Conventional Commits) → `test` (packet-builder
  self-test, static page checks) → `security` (gitleaks) → `build` (assemble `public/`)
  → `verify` (Playwright: no external request, no console error, 4 languages, 360 px)
  → `deploy` (GitLab Pages, `main` only, environment `production`) → `release` (tags).
  Pages access = project members only.
- `main` is protected: **no direct push**. Workflow: branch `<type>/<name>` → merge request
  (Default template) → green pipeline + resolved threads → squash merge.
  A page is "done" only when it is published by a green `main` pipeline.
- Commits: **Conventional Commits** in English, scope = protocol slug or area
  (e.g. `feat(ospf): add LSU packet views`, `fix(bgp): correct hold timer default`,
  `ci(pipeline): pin playwright image`).
- Every MR adds a line to `CHANGELOG.md` under `[Unreleased]` (Keep a Changelog).
  Releases: SemVer tags `vX.Y.Z` on `main` (MAJOR = template change for all pages,
  MINOR = new protocol/section, PATCH = corrections); the pipeline creates the release.
- Pin everything: CI images by tag + `@sha256` digest (must support `linux/arm64`),
  Python tools in `requirements/ci.txt` with hashes, pre-commit hooks frozen to SHAs.
- Run `pre-commit run --all-files` before pushing.
- Never commit secrets: no tokens, no runner token, no real IPs/hostnames.
  `infra/nas-runner/.env` is git-ignored.

## Document library (Google Drive)
- Reference sources (RFC PDFs, vendor guides) live in Google Drive (connector available):
  `Network Protocoles` (folder ID `1V20Pia8gMlZ3u5afBkAnVMDgtGKQUPKm`), plus existing
  vendor folders `Cisco` (`1GzcQeZbEjAh4yB9j-dlWiZiE0Oln6Ga_`),
  `Checkpoint` (`1OQx9c5jh2m_l9M2B_lclAOOs6YxVZ6Xu`), `BIG-IP` (`1tl-aUfvyWEZ2fUxkJJ-nmTLzeYQEhSLp`).
- Search scoped by folder: `parentId = '<folder ID>' and fullText contains '<term>'`.
- Search order: Drive library → official web sources (RFC Editor, IANA, vendor docs).
  Cite the document used (title + link) and its version.

## HTML technical rules (mandatory)
- **One self-contained file per page**: CSS, JS and SVG inline. No CDN, no external
  font, no external image, no network call. The page must open offline by double-click.
- Vanilla HTML/CSS/JS only (no framework, no build step).
- Light and dark mode (`prefers-color-scheme` + manual toggle).
- Responsive down to 360 px wide, no horizontal page scroll (wide tables/grids scroll
  inside their own container).
- `localStorage` only for per-viewer conveniences (chosen language, theme), always wrapped
  in try/catch; the page must work without it.
- Accessible: semantic headings, `alt`/`aria-label`, keyboard-usable interactive elements,
  visible focus, WCAG AA contrast.
- Printable: a print stylesheet that shows the current language only and expands all
  collapsible sections.

## Multilingual rules
- **One page, a language switch FR | EN | NL | DE** in the header. The four language
  versions are all inside the page (e.g. `<span lang="fr">…</span>` blocks or an inline
  JS dictionary); switching language never reloads the page.
- Default language: the browser language if it is fr/en/nl/de, else EN.
  Remember the choice in `localStorage`. Set `<html lang>` on switch.
- **Always kept in English in all 4 languages**: protocol field names (Router ID,
  Packet length…), states and events (2-Way, ExStart, Established…), message names
  (Hello, LSU, OPEN…), RFC terms, CLI commands and device output, Wireshark filter names.
  The explanations around them are translated.
- The 4 versions must have **identical content**: same sections, same examples, same
  values. A section is never left untranslated or summarised in one language only.
- Quality: native technical register in each language (not literal translation).
  NL = Netherlands/Flemish neutral standard Dutch; DE = standard German.

## Page structure (same order on every page)
1. **Header**: protocol name, one-line definition, OSI layer, transport/encapsulation
   (IP protocol number, TCP/UDP port, EtherType), governing standards (RFC/IEEE numbers),
   language switch, theme toggle, table of contents.
2. **Concepts**: purpose, where it sits in the stack, terminology, design trade-offs,
   versions/variants and their differences.
3. **Packet formats — every message type** (see "Packet representation").
4. **Operation (animated)**: state machine(s) and message exchanges, step by step
   (①②③…), with play / pause / next / previous controls. Timers and their defaults.
5. **Advanced behaviour (expert)**: edge cases, interoperability issues, scaling limits,
   security (attacks and protections), tuning, convergence, known RFC ambiguities.
6. **Multi-vendor configuration and verification** (see "Vendor rules").
7. **Troubleshooting**: yes/no decision tree ending in verification commands per vendor;
   table of common faults (symptom → cause → command → expected output → fix).
8. **Quiz**: at least 15 CCIE-level questions (scenario-based, packet-reading,
   "what breaks if…"), each with explanation and the RFC/vendor reference.
9. **Sources**: full list (also in `sources.md`).

Sections 5–8 can be collapsible but are open by default on screen.

## Packet representation (mandatory for EVERY message/packet type)
Every message type of the protocol ALWAYS gets **both** views below, shown together
and synchronised: hovering or focusing a field in one view highlights it in the other
and shows a detail panel (name, offset, size in bits/bytes, allowed values, role,
RFC section). A packet is never shown with only one of the two.
1. **RFC-style bit diagram** (mandatory): 32-bit rows, bit ruler 0–31, each field drawn
   at its true width; variable-length and optional fields clearly marked; TLV/sub-TLV
   structures drawn as nested diagrams.
2. **Wireshark-style tree** (mandatory): expandable tree, displayed value and the
   Wireshark display-filter name for each field (e.g. `ospf.hello.hello_interval`).
   Verify filter names against the Wireshark display filter reference.

Optional complements, only when they add value:
- **Decoded hex dump** (offset column, bytes colour-coded by field) — e.g. to show
  checksum coverage, TLV encoding, padding or encapsulation layers.
- **Value/code table** (types, flags bit by bit, error codes, default timers, IANA
  values, RFC section for each) — e.g. for protocols with large code registries.

Correctness rules for sample packets:
- **Never hand-write values or hex.** Generate every sample packet with
  `tools/packet-builder.py` (Python, struct or scapy) so lengths, checksums, padding
  and flags are correct, and take the displayed values from its output.
- All views of a packet describe the same packet: values in the bit diagram, the tree
  and any optional view must match.

## Vendor rules
Platforms covered on every page, in this order:
Cisco (IOS XE, NX-OS, and IOS XR when relevant) · Check Point (Gaia clish / Gaia OS,
expert mode) · F5 BIG-IP (TMOS tmsh; ZebOS imish for dynamic routing) ·
Palo Alto (PAN-OS CLI; set commands + operational commands) ·
NetScaler (CLI; ZebOS VTYSH for dynamic routing) · FortiGate (FortiOS CLI).
- For each vendor: configuration example, verification commands, debug commands
  (with a warning on production impact), and sample expected output.
- **Every command block cites the vendor documentation it comes from**: document title,
  software version, section, URL. No command without a source.
- State the software version the commands were checked against (e.g. "PAN-OS 11.1",
  "FortiOS 7.4", "TMOS 17.1", "Gaia R81.20"). Flag syntax that changes between versions.
- If a vendor does not support the protocol or a feature, say so explicitly with the
  source ("not supported on …") — never invent a command.
- Where the vendor deviates from the RFC (defaults, non-standard behaviour,
  proprietary extensions), flag it next to the command.

## Source hierarchy (highest wins on conflict)
1. Standards: RFCs (current, including errata and updating RFCs), IEEE, IANA registries
2. Official vendor documentation (configuration guides, CLI references, release notes,
   knowledge-base articles from the vendor)
3. Reference books and vendor whitepapers
4. Conference sessions (Cisco Live, etc.) — illustrative only
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
- Max ~5–7 main elements per diagram; split beyond that. Overview first, then details.
- Consistent colour code across the whole library:
  grey = encapsulation/underlay headers · blue = protocol common header ·
  teal = message body/payload · purple = TLV/options/extensions ·
  orange = external/redistributed/vendor-specific · green = healthy/expected ·
  red = error/drop/fault.
- Never rely on colour alone: pair with text, ✓/✗, line style or shape.
  Works in light and dark mode and in black-and-white print.

## Confidentiality
- Only documentation values in examples: IPv4 192.0.2.0/24, 198.51.100.0/24,
  203.0.113.0/24; IPv6 2001:db8::/32; private ASNs 64496–64511 / 65000+;
  hostnames R1, FW-A, LB-01…; MAC 00:00:5e:00:53:xx.
- Never reproduce real hostnames, IPs, customer names, serial numbers, keys or ticket IDs.
  If I paste any, warn me, replace them with placeholders and never store them.

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
- [ ] Quiz ≥ 15 questions with explanations and references
- [ ] Merge request merged and the `main` pipeline is green (page published on Pages)
