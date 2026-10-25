# Changelog

All notable changes to this project are documented in this file.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) ·
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Versioning rules for this library:
- **MAJOR** — template or page structure change that affects every page
- **MINOR** — new protocol page or new section
- **PATCH** — corrections (facts, commands, translations, typos)

## [Unreleased]

### Added
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

### Changed
- Deploy publishes the site publicly on https://learning.cuvelier.tech (NAS, atomic
  releases, smoke test) instead of GitLab Pages; the runners now live in the homelab
  stack `learning` (`infra/nas-runner` is a pointer).

## [0.1.0] - 2026-10-25

### Added
- Project scaffold, `CLAUDE.md` authoring rules, home page in FR · EN · NL · DE.
- `tools/packet-builder.py` with OSPFv2 Hello sample and RFC 1071 checksum self-test.
- Self-hosted GitLab Runner setup for the NAS (`infra/nas-runner`).
