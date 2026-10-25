# Network Protocols Expert

[![pipeline](https://gitlab.com/jeanmichel4121/network-protocols-expert/badges/main/pipeline.svg)](https://gitlab.com/jeanmichel4121/network-protocols-expert/-/pipelines?ref=main)
[![release](https://gitlab.com/jeanmichel4121/network-protocols-expert/-/badges/release.svg)](https://gitlab.com/jeanmichel4121/network-protocols-expert/-/releases)

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
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Branches, Conventional Commits, merge requests, releases |
| [`CHANGELOG.md`](CHANGELOG.md) | Version history |
| [`SECURITY.md`](SECURITY.md) | Secrets and confidentiality rules |

## Pipeline

| Stage | Checks |
|---|---|
| lint | YAML (yamllint), Python (ruff), commit messages (Conventional Commits) |
| test | packet-builder self-test, static page checks |
| security | secret scanning (gitleaks) |
| build | assembles the site in `public/` |
| verify | headless browser: offline, no console error, 4 languages, 360 px |
| deploy | GitLab Pages, from `main` only |
| release | GitLab release from a `vX.Y.Z` tag |

All jobs run on a self-hosted ARM64 runner (tag `nas`), see [`infra/nas-runner`](infra/nas-runner).
Images are pinned by digest and Python tools by hash.

## Local checks

```sh
pip install pre-commit
pre-commit install --install-hooks -t pre-commit -t commit-msg
pre-commit run --all-files
```
