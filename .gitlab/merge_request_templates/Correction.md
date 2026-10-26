## What

<!-- The error corrected and the issue it closes, e.g. "OSPF Hello: RouterDeadInterval default is 40 s. Closes #12". -->

## Pages touched

- `protocols/<slug>/index.html`
- `protocols/<slug>/sources.md` (if a source was added)

## Before / after

| | Text or value |
|---|---|
| Before | |
| After | |

## Source

<!-- The authoritative source that proves the correction: RFC and section, IEEE clause,
or vendor document title, software version, section and URL. -->

## Checks

- [ ] The correction is applied in all 4 languages (FR, EN, NL, DE), same values everywhere
- [ ] Every view of the same fact is updated (bit diagram, Wireshark tree, hex dump, tables, quiz, animation)
- [ ] Sample packets regenerated with `tools/packet-builder.py --update` if a value changed
- [ ] `sources.md` and the Sources section updated if a new source is cited
- [ ] `CHANGELOG.md` updated under `[Unreleased]` (### Fixed)
- [ ] Writing style rules respected (no AI-looking typography)
- [ ] Pipeline green

/label ~"type::correction"
/assign me
