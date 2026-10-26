## Release vX.Y.Z

<!-- MAJOR = template change for every page, MINOR = new protocol or section,
PATCH = corrections. Explain the choice in one line. -->

## Changes in this release

<!-- Copy of the new CHANGELOG section. -->

## Checks before merge

- [ ] `[Unreleased]` entries moved to `## [X.Y.Z] - YYYY-MM-DD` in `CHANGELOG.md`, comparison links updated
- [ ] Every issue of the milestone closed or moved to the next milestone
- [ ] Pipeline green on this MR

## After merge (maintainer, with explicit approval)

- [ ] Tag `main`: `git tag -a vX.Y.Z -m "vX.Y.Z" && git push origin vX.Y.Z`
- [ ] Tag pipeline green: release created with notes, website link, SBOM and GitHub source links
- [ ] Tag mirrored to GitHub
- [ ] Milestone closed

/label ~"type::chore"
/assign me
