## Release vX.Y.Z

- Milestone:
- Type (MAJOR / MINOR / PATCH) and reason:

## Steps

- [ ] Every issue of the milestone closed or moved
- [ ] `scripts/check_updates.py` reviewed (no critical pin left behind)
- [ ] Release MR (template *Release*) merged, pipeline green
- [ ] Tag `vX.Y.Z` pushed (explicit approval in chat)
- [ ] Release created by the tag pipeline (notes, website, SBOM, GitHub links)
- [ ] Site checked: https://learning.cuvelier.tech/version.txt matches the tag commit
- [ ] Milestone closed

/label ~"type::chore"
