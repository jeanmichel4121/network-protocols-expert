# Contributing

Authoring rules for the pages are in [`CLAUDE.md`](CLAUDE.md), the web and accessibility
standards in [`docs/web-standards.md`](docs/web-standards.md). This file covers the workflow.

New protocol page: copy `templates/protocol-template.html` to `protocols/<slug>/index.html`,
fill `#page-meta`, replace every `TEMPLATE` block, add the packet samples to
`tools/packet-builder.py`, then run `python3 tools/packet-builder.py --update protocols/<slug>/index.html`.
Preview the published layout with `python3 scripts/build_site.py /tmp/site`.
Changed the template's styles, page library or header? Run `python3 tools/sync-shared.py`.
Changed the landing-page drawing? Edit `tools/landing-topology.py`, then run it with `--update index.html`.

## Workflow

1. Open or pick an issue (templates: *New-protocol*, *Correction*).
2. Create a branch from `main`: `<type>/<short-name>` — e.g. `feat/ospf`, `fix/bgp-timers`, `ci/cache`.
3. Commit with **Conventional Commits**: `<type>(<scope>): <description>`
   - types: `feat` `fix` `docs` `style` `refactor` `perf` `test` `build` `ci` `chore` `revert`
   - scope = protocol slug or area: `feat(ospf): add LSU packet views`, `ci(pipeline): pin images`
4. Push and open a merge request (template *Default*). `main` is protected: no direct push.
5. Merge only when the pipeline is green and every discussion is resolved.
   The MR is squashed and the branch deleted automatically.

## Local checks (same as CI)

```sh
pip install pre-commit
pre-commit install --install-hooks -t pre-commit -t commit-msg
pre-commit run --all-files
python3 scripts/smoke_test.py public   # after building public/ (needs Playwright)
```

## Releases

1. Move the `[Unreleased]` entries of `CHANGELOG.md` to a new `## [X.Y.Z] - YYYY-MM-DD` section (via MR).
2. Tag `main`: `git tag -a vX.Y.Z -m "vX.Y.Z" && git push origin vX.Y.Z` (tags `v*` are protected).
3. The pipeline creates the GitLab release with the CHANGELOG notes.

## Updating pinned dependencies

- **CI images** (`.gitlab-ci.yml`): update the tag *and* the `@sha256:` digest together; the image
  must provide `linux/arm64` (the runner is ARM64).
- **Python tools**: edit `requirements/ci.in`, then
  `pip-compile --generate-hashes --strip-extras --allow-unsafe -o requirements/ci.txt requirements/ci.in`.
- **pre-commit hooks**: `pre-commit autoupdate --freeze`.

## Secrets

Never commit tokens, keys, real IPs or hostnames. `gitleaks` runs in pre-commit and in CI.
If a secret is pushed: revoke it first, then clean history.
