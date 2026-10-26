## What

<!-- One or two sentences: what this MR changes and why. The MR title is the squash
commit on main: <type>(<scope>): <description>, Conventional Commits, in English. -->

## Type

- [ ] Template change (propagated to every page, listed below)
- [ ] Site, tooling or CI/CD
- [ ] Dependency update (tag and digest changed together, `scripts/check_updates.py` green)
- [ ] Security fix
- [ ] Repository documentation
- [ ] Other:

## Pages touched

<!-- Every HTML page changed, e.g. index.html, templates/protocol-template.html.
Write "none" if no page changed. -->

## Checks

- [ ] One subject per MR (one page, or one template change and its propagation)
- [ ] `pre-commit run --all-files` passes locally
- [ ] `CHANGELOG.md` updated under `[Unreleased]`
- [ ] Writing style rules respected (CLAUDE.md, no AI-looking typography)
- [ ] Pipeline green

/assign me
