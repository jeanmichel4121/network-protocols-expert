## What

<!-- The change to templates/protocol-template.html and why. -->

## Pages propagated

<!-- Output of `python3 tools/sync-shared.py`: every page updated. -->

- `templates/protocol-template.html`
- `index.html`

## Visual check

<!-- Attach screenshots or describe what was checked. -->

- [ ] Light theme, dark theme
- [ ] Desktop (1280 px) and mobile (360 px), no horizontal page scroll
- [ ] Print preview (current language only, sections expanded)
- [ ] Keyboard only: focus visible, not hidden by the sticky header
- [ ] Reduced motion: no animation

## Checks

- [ ] `python3 tools/sync-shared.py` run, `scripts/check_pages.py` green
- [ ] Every UI string added in the 4 languages (template dictionary)
- [ ] `docs/web-standards.md` updated if a standard or rule changed
- [ ] Release impact noted in `CHANGELOG.md` (a change to every page is MAJOR)
- [ ] Writing style rules respected (no AI-looking typography)
- [ ] Pipeline green, including `verify:browser` and `verify:site`

/label ~"type::template"
/assign me
