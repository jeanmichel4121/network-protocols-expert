# ADR 0013: Small screens: diagrams open full size, wide tables become cards

- Status: accepted
- Date: 2026-11-17

## Context

On a phone (360 px) the pages kept the laptop layout squeezed into the screen. Every
schematic had a minimum width of 30 to 40 rem: the frame showed 51 to 68 % of the drawing and
its text came out at 5.5 to 8.5 px. Wide tables showed two or three columns and cut the
others, with no sign that they scroll. In the header the logo slid under the About link at
360 px, and at 320 px the page scrolled sideways by 27 px. The owner asked for a review of
the site for mobile that leaves the laptop view as it is.

## Decision

- Every small-screen rule sits in a media query (under 40 rem, 48 rem for diagrams) or
  behind `(hover: none)`. At 48 rem and above nothing changes: checked by comparing
  full-page screenshots pixel by pixel at 1024, 1280 and 1440 px, dark and light themes.
- **Diagrams** fit their frame on a phone, so the whole drawing is visible, and open in a
  full-screen `<dialog>` at their own size through an Enlarge button or a tap. The drawing
  (and an animation's controls) is moved into the dialog and put back on close, so an
  animation keeps its state; Escape, Close and the Back button close it. A separate portrait
  drawing for each diagram was set aside: it would double every diagram in four languages
  and let the two versions drift apart.
- **Tables** wider than their frame become one card per row, each cell headed by its column
  label, written by the library from the header row and hidden from screen readers;
  explicit ARIA roles keep the table semantics. A table with merged cells keeps scrolling.
- **Frames that still scroll** fade, or show a shadow, on the side where more content waits.
- The header fits 320 px, the packet panel says "tap" on touch screens and long inline code
  wraps. The smoke test checks 320 px as well as 360 px.

## Consequences

- A new page gets this behaviour from the template; nothing to write in the page.
- A table header must name its column on its own, because it becomes the label of each
  cell on a phone.
- On a phone a reader sees a whole diagram small, then reads it full size; the field list
  under each diagram stays its text alternative.
