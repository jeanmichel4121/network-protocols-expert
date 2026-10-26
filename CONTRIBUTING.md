# Contributing

Authoring rules for the pages are in [`CLAUDE.md`](CLAUDE.md), the web and accessibility
standards in [`docs/web-standards.md`](docs/web-standards.md). This file covers the workflow.

## From outside: issues on GitHub

The GitHub repository is a read-only mirror: pull requests are disabled. To help:

- report an error with the **Correction** form, with the authoritative source;
- suggest a protocol with the **New protocol** form;
- report a layout or accessibility problem with the **Site problem** form;
- report a vulnerability privately, see [`SECURITY.md`](SECURITY.md).

Accepted reports are carried over to the GitLab project, where the work happens.

## Branches: trunk-based

`main` is the only long-lived branch. It is protected (no direct push), always deployable,
and every merge to it is published. Work happens on short-lived branches cut from `main`:

| Branch | Use |
|---|---|
| `feat/<protocol-slug>` | a new protocol page or a new section |
| `fix/<protocol-slug>-<topic>` | a correction (`fix/site-<topic>` for the site itself) |
| `chore/<topic>` | tooling, CI, dependencies, template changes |
| `docs/<topic>` | repository documentation |

Lowercase letters, digits, dots and hyphens only. CI rejects any other name.
Releases are tags (`vX.Y.Z`) on `main`, not branches.

## Commits and merge requests

1. Open or pick an issue (templates: *New-protocol*, *Correction*, *Bug*, *Feature*,
   *Security* (created confidential), *Release*). Triage on the *Workflow* board.
2. Branch from `main`, commit with **Conventional Commits** in English:
   `<type>(<scope>): <description>`
   - types: `feat` `fix` `docs` `style` `refactor` `perf` `test` `build` `ci` `chore` `revert`
   - scope = protocol slug or area: `feat(ospf): add LSU packet views`, `ci(pipeline): pin images`
3. Open a merge request with the matching template: *Protocol-page* (new page),
   *Correction* (fix in a page), *Template-change* (shared layout), *Release*, or *Default*.
   The MR description lists the pages touched, the sources added and the Definition of
   done, each box ticked or explained.
4. The **MR title** is a Conventional Commit too: the MR is squashed and merged
   fast-forward, so the title becomes the single commit on `main`.
5. One subject per MR: one protocol page, or one template change and its propagation.
6. Merge only with a green pipeline and every discussion resolved. The branch is
   deleted on merge.

## Labels

Defined once in [`.github/labels.yml`](.github/labels.yml) and applied to both forges
with `scripts/sync_labels.py`. One value per scope:

| Scope | Values |
|---|---|
| `type::` | page, correction, bug, feature, template, docs, ci, security, chore |
| `priority::` | high, medium, low |
| `status::` | needs-triage, confirmed, in-progress, needs-source, blocked, wont-fix, duplicate |
| `area::` | concepts, packets, operation, advanced, vendors, troubleshooting, quiz, sources, landing, accessibility, i18n |
| `lang::` | fr, en, nl, de (a problem in one language version only) |
| `vendor::` | cisco, checkpoint, f5, paloalto, netscaler, fortinet |
| `protocol::` | one per protocol page (added with the page) |

## Working on pages

New protocol page: copy `templates/protocol-template.html` to `protocols/<slug>/index.html`,
fill `#page-meta`, replace every `TEMPLATE` block, add the packet samples to
`tools/packet-builder.py`, then run `python3 tools/packet-builder.py --update protocols/<slug>/index.html`.
Preview the published layout with `python3 scripts/build_site.py public`.
Changed the template's styles, page library, header or footer? Run `python3 tools/sync-shared.py`.
Changed the home-page drawing? Edit `tools/landing-topology.py`, then run it with `--update index.html`.

## Local checks (same as CI)

```sh
pip install pre-commit
pre-commit install --install-hooks -t pre-commit -t commit-msg
pre-commit run --all-files
python3 scripts/build_site.py public
python3 scripts/check_site.py public    # needs html5lib (requirements/ci.txt)
python3 scripts/smoke_test.py public    # needs Playwright (requirements/browser.txt)
```

## Releases

1. Move the `[Unreleased]` entries of `CHANGELOG.md` to a new `## [X.Y.Z] - YYYY-MM-DD` section (via MR).
2. Tag `main`: `git tag -a vX.Y.Z -m "vX.Y.Z" && git push origin vX.Y.Z` (tags `v*` are protected).
3. The pipeline creates the GitLab release with the CHANGELOG notes; the tag is mirrored to GitHub.

## Updating pinned dependencies

`python3 scripts/check_updates.py` lists what is outdated (also run weekly by the
`security:dependencies` job: orange means an update is due).

- **CI images** (`.gitlab-ci.yml`): update the tag *and* the `@sha256:` digest together; the image
  must provide `linux/arm64` (the runner is ARM64).
- **Python tools**: edit `requirements/ci.in`, then
  `pip-compile --generate-hashes --strip-extras --allow-unsafe -o requirements/ci.txt requirements/ci.in`.
- **pre-commit hooks**: `pre-commit autoupdate --freeze`.

## Repository settings

The settings of both forges are documented in [`docs/repository-settings.md`](docs/repository-settings.md).
After any change in a web UI, run `scripts/audit_repos.py` (read-only tokens in the
environment) and update that file in the same MR. Significant decisions get an ADR in
[`docs/adr/`](docs/adr/README.md).

## Licensing

Code is MIT, content CC BY-SA 4.0 (see [`REUSE.toml`](REUSE.toml)). By contributing you
agree that your contribution is published under the licence of the files you change.

## Secrets

Never commit tokens, keys, real IPs or hostnames. `gitleaks` runs in pre-commit and in CI.
If a secret is pushed: revoke it first, then clean history (the GitHub mirror is public).
