# ADR 0010: content under CC BY-NC-SA 4.0, commercial use on permission

- Status: accepted
- Date: 2026-11-07
- Supersedes: the content part of [ADR 0006](0006-licensing.md)

## Context

The owner wants the site to stay free to use while forbidding the copy of the work for
profit ("on peut utiliser le site gratuitement mais on ne peut pas copier mon travail à des
fins lucratives", 2026-11-07). CC BY-SA 4.0 (ADR 0006) allows commercial reuse. The owner is
the only author of the content (every commit of the repository is his), so he can choose a
new licence for it. The Code of Conduct is a third-party text under CC BY-SA 4.0 and the
Cisco icons have their own terms: neither changes.

## Decision

- Content (protocol pages, information pages, home page, documentation, `sources.md`):
  **CC BY-NC-SA 4.0** from 2026-11-07. Commercial use needs the owner's written permission
  (terms of use, section "Commercial use"). Code, tooling and the template stay MIT.
- Text and data mining, AI training included, is reserved and signalled by machine-readable
  means (ADR 0011).
- `REUSE.toml`, `LICENSES/CC-BY-NC-SA-4.0.txt`, `CITATION.cff`, the README, the page footer and
  the JSON-LD `license` follow.

## Consequences

- A Creative Commons licence cannot be revoked (CC BY-SA 4.0 section 2(a)(1), irrevocable
  grant; CC FAQ "What if I change my mind about using a CC license?"). Copies obtained under
  CC BY-SA 4.0, that is releases v0.1.0 to v0.6.0 and the GitHub mirror history up to
  2026-11-07, stay usable under CC BY-SA 4.0, commercial use included. The terms of use say so.
- NonCommercial is judged on the purpose of the use, not on who uses it (CC FAQ). The terms
  give examples and invite readers to ask when in doubt.
- Outside contributions, if any are accepted later, are published under the licence of the
  files they change (CONTRIBUTING.md).
