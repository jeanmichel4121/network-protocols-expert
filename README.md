# Network Protocols Expert

[![pipeline](https://gitlab.com/jeanmichel4121/network-protocols-expert/badges/main/pipeline.svg)](https://gitlab.com/jeanmichel4121/network-protocols-expert/-/pipelines?ref=main)
[![release](https://gitlab.com/jeanmichel4121/network-protocols-expert/-/badges/release.svg)](https://gitlab.com/jeanmichel4121/network-protocols-expert/-/releases)

> **Source of truth: GitLab.com.** [github.com/jeanmichel4121/network-protocols-expert](https://github.com/jeanmichel4121/network-protocols-expert)
> is a read-only push mirror of the protected branches; changes pushed there are overwritten.
> The site is published at <https://learning.cuvelier.tech>.

Learning library for network protocols at expert level, aimed at CCIE and the equivalent
expert certifications of other vendors. One self-contained HTML page per protocol, available
in French, English, Dutch and German. Each page contains:

- RFC-style bit diagrams and Wireshark-style trees for every message type
- Animated state machines and message exchanges
- Configuration, verification and troubleshooting for Cisco, Check Point, F5 BIG-IP,
  Palo Alto, NetScaler and FortiGate, each command sourced from vendor documentation
- A CCIE-level quiz per protocol

| Document | Content |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | Authoring rules: page structure, packet views, sources, visuals |
| [`docs/web-standards.md`](docs/web-standards.md) | Web, accessibility and learning-design standards, with sources |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Branches, Conventional Commits, merge requests, releases |
| [`CHANGELOG.md`](CHANGELOG.md) | Version history |
| [`SECURITY.md`](SECURITY.md) | Secrets and confidentiality rules |

## Pipeline

| Stage | Checks |
|---|---|
| lint | YAML (yamllint), Python (ruff), commit messages (Conventional Commits) |
| test | packet-builder self-test, static page checks |
| security | secret scanning (gitleaks) |
| build | one URL per language (`/fr/` `/en/` `/nl/` `/de/`), hreflang, sitemap, 404 |
| verify | headless browser: axe WCAG 2.2 AA (light + dark), CLS, reduced motion, hreflang, 360 px, no external request |
| deploy | https://learning.cuvelier.tech (public), from `main` only, smoke-tested |
| release | GitLab release from a `vX.Y.Z` tag |

Published at **https://learning.cuvelier.tech** (public, no authentication).
All jobs run on self-hosted ARM64 runners (tags `nas`, `nas-deploy`), see [`infra/nas-runner`](infra/nas-runner).
Images are pinned by digest and Python tools by hash.

## Local checks

```sh
pip install pre-commit
pre-commit install --install-hooks -t pre-commit -t commit-msg
pre-commit run --all-files
```
