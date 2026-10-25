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

### Changed
- Deploy publishes the site publicly on https://learning.cuvelier.tech (NAS, atomic
  releases, smoke test) instead of GitLab Pages; the runners now live in the homelab
  stack `learning` (`infra/nas-runner` is a pointer).

## [0.1.0] - 2026-10-25

### Added
- Project scaffold, `CLAUDE.md` authoring rules, home page in FR · EN · NL · DE.
- `tools/packet-builder.py` with OSPFv2 Hello sample and RFC 1071 checksum self-test.
- Self-hosted GitLab Runner setup for the NAS (`infra/nas-runner`).
