# network-protocols-expert

Expert-level (CCIE-grade) multi-vendor network protocol library.
One self-contained HTML page per protocol, in **FR · EN · NL · DE**, with:

- RFC-style bit diagrams and Wireshark-style trees for every message type
- Animated state machines and message exchanges
- Configuration, verification and troubleshooting for Cisco, Check Point, F5 BIG-IP,
  Palo Alto, NetScaler and FortiGate, each command sourced from vendor documentation
- CCIE-level quiz per protocol

Authoring rules: see [`CLAUDE.md`](CLAUDE.md).

## Pipeline

`build` (packet-builder self-test) → `validate` (`scripts/check_pages.py`) → `deploy` (GitLab Pages, members only).
All jobs run on a self-hosted ARM64 runner (tag `nas`) — see [`infra/nas-runner`](infra/nas-runner).

## Local checks

```sh
python3 tools/packet-builder.py --self-test
python3 scripts/check_pages.py
```
