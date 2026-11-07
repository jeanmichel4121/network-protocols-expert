# Web and learning standards

The rules every page of the library follows, why, and where each one comes from.
`CLAUDE.md` holds the authoring rules; this file holds the web, accessibility and
learning-design standards behind them. The reference implementation is
[`templates/protocol-template.html`](../templates/protocol-template.html).
Rules marked **[CI]** are enforced by the pipeline.

Last reviewed: 2026-10-25.

## 1. Publication: one URL per language

- Source pages keep the four languages in one file and switch in place, so a page still
  opens offline by double-click.
- The build (`scripts/build_site.py`) publishes each page four times:
  `/fr/<slug>/`, `/en/<slug>/`, `/nl/<slug>/`, `/de/<slug>/`. Google recommends
  "different URLs for each language version of a page" rather than switching content
  with cookies or scripts, which it "might not find and crawl" [G1].
- Each URL carries its own `<html lang>`, `<title>`, description, `canonical`,
  `hreflang` for the four languages plus `x-default`, Open Graph tags and JSON-LD
  (`LearningResource` for protocol pages, `WebSite` for the home page) [G1][S1]. **[CI]**
- The language switch stays instant: it changes the language in place and rewrites the
  URL to the matching `/xx/` path (`history.replaceState`), without a reload. **[CI]**
- Each protocol page is also published as chapters (ADR 0009): the overview
  `/<lang>/<slug>/` (header and one card per chapter), and one URL per section
  `/<lang>/<slug>/<section id>/`. A chapter page keeps the shared CSS and JS, so it stays self-contained; it
  gets the chapter list, a breadcrumb, previous/next links (`rel="prev"`/`"next"`), its
  own title and description, and JSON-LD `isPartOf` the overview, which lists `hasPart`.
  Links to an anchor that moved to another chapter are rewritten to that chapter. A
  learner-paced segment at a time follows Mayer's segmenting principle [L4]. **[CI]**
  (`check_site.py`: links, anchors, every chapter linked from its overview)
- The chapter list and the overview cards mark the chapters a reader has already opened, only
  if the reader ticked "remember on this device" (privacy page, ADR 0011): a per-viewer
  convenience, the page works without it.
- A step-by-step diagram shows the steps not reached yet faintly, so the reader sees where
  the exchange goes before pressing Play.
- The sample packets of a section are tabs (`NPE.pktset`): one packet shown at a time,
  a link to a field or heading inside a packet opens its tab; every packet is shown
  without JavaScript and in print.
- `/` is a language chooser (`x-default`) that sends a returning visitor to their saved
  language, else their browser language. `sitemap.xml` lists every URL with its
  alternates (chapters included); `robots.txt` points to it;
  `404.html` is served for unknown paths.
- Page metadata lives in `<script type="application/json" id="page-meta">`: `title` and
  `description` (≤ 200 characters) in the four languages, `name`, `tags`, `standards`,
  `updated`. **[CI]**

## 2. Accessibility: WCAG 2.2 level AA

Target: WCAG 2.2 AA [W1]. axe-core checks every built page in the light and the dark
theme and at 360 px (tags `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa`, `wcag22aa`). **[CI]**

| Criterion | What it means here |
|---|---|
| 2.4.11 Focus Not Obscured (AA, new in 2.2) | The header is sticky: `scroll-padding-top` keeps the focused element below it. |
| 2.5.8 Target Size (AA, new in 2.2) | Every control ≥ 24 × 24 CSS px; buttons are 36 to 44 px high. Reference links `[n]` are 24 px boxes. **[CI]** |
| 2.5.7 Dragging Movements (AA, new in 2.2) | No drag interaction without a single-click alternative. |
| 2.5.3 Label in Name | A control's accessible name contains its visible text (no `aria-label` that rewords it). **[CI]** |
| 1.4.3 Contrast | Text ≥ 4.5:1 in both themes (palette tokens are checked by axe in light and dark). **[CI]** |
| 1.4.1 Use of Color | Colour is always paired with text, a symbol (✓ ✗ ▶) or a line style (solid / dashed / dotted). |
| 1.4.4 / 1.4.10 Resize, Reflow | Relative units, no horizontal page scroll at 360 px; wide diagrams scroll inside their own container. **[CI]** |
| 2.1.1 Keyboard (scroll areas) | Every container that can scroll on its own (tables, code blocks, diagrams on small screens) has `tabindex="0"` so keyboard users can scroll it. **[CI]** |
| 2.1.1 Keyboard | Every widget works with the keyboard: roving tabindex + arrow keys in the bit diagram, the Wireshark tree and the tabs (WAI-ARIA APG pattern). |
| 2.4.1 Bypass Blocks | "Skip to content" link. |
| 3.1.1 / 3.1.2 Language | `<html lang>` follows the switch; translated blocks carry their own `lang`. |
| 4.1.3 Status Messages | Field details, animation step and quiz feedback are announced through `aria-live="polite"` without moving focus [H1]. |

Component patterns:
- **SVG diagrams**: `role="img"` + `aria-labelledby` pointing to visible text (the figure
  title and the current step). `<title>`/`<desc>` alone are read inconsistently by screen
  readers [A1][A2]. Purely decorative icons get `aria-hidden="true"`.
- **Packet views**: the Wireshark tree is the text alternative of the bit diagram; the
  hex dump is supplementary (`aria-hidden`), its content is in the tree.
- **Quiz**: one `<fieldset>` + `<legend>` per question, native radios with `<label>`,
  feedback in a live region; never `aria-hidden` on feedback text [H1].
- **Tabs**: WAI-ARIA tabs pattern; panels are rendered hidden in HTML (no layout shift)
  and shown by `<noscript>` CSS when scripts are off, and all shown in print.

## 3. Motion

- Auto-advancing content (the animation's Play) has a visible Pause and stops at the
  end: WCAG 2.2.2 Pause, Stop, Hide (A) [W2].
- `prefers-reduced-motion: reduce` turns transitions and animations off (W3C technique
  C39); content never depends on motion [W2]. **[CI]** (no animation runs at load).
- Smooth scrolling only under `prefers-reduced-motion: no-preference`.

## 4. Performance and stability

- Core Web Vitals "good" thresholds, 75th percentile: LCP ≤ 2.5 s, INP ≤ 200 ms,
  CLS ≤ 0.1 [P1]. Self-contained pages make LCP trivial; the risks are CLS and INP.
- No layout shift: theme and language are applied by a tiny script in `<head>` before the
  first paint; each interactive component is rendered by an inline call placed right
  after its markup; tab panels start `hidden`. What a script would add above a packet's
  figure (the chips line) and the packet tab lists are written in the markup by
  `tools/packet-builder.py --update`: a page that a slow link renders progressively
  does not shift either. CLS < 0.1 on every page, and on the packets chapters also over a
  64 KB/s link, which makes the browser paint the page in parts. **[CI]**
- Interactions do small DOM updates only (class toggles, one panel re-render) to keep INP
  well under 200 ms.
- No external request of any kind. **[CI]**

## 5. HTML and CSS baseline

- Use features that are Baseline "widely available"; newer "newly available" features
  only as progressive enhancement with a fallback [B1].
- Used: `:has()`, `color-mix()`, `light-dark()` with `color-scheme` [B2],
  CSS grid, `clamp()`, `text-wrap: balance|pretty`, `<details>`, `dvh`.
  `light-dark()` follows `color-scheme`, so the manual theme toggle only sets
  `color-scheme` on `<html>` [B2].
- Not used yet: anchor positioning, `@scope`, cross-document view transitions
  (not widely available at last review) [B1].
- Vanilla HTML/CSS/JS, no framework, no build step for the page itself.

## 6. Typography and layout

- Body text 16 to 17 px (`clamp`), line height 1.6, prose limited to ~70 characters per line
  (`max-width: 72ch`); 45 to 75 characters is the readable range [T1][T2].
- System font stack and a system monospace stack: no web font, nothing to download.
- Documentation layout: sticky header, content column, table of contents on the right
  from 64 rem (collapsible block above the content on smaller screens). The TOC
  highlights the section in view with `IntersectionObserver` (not a scroll handler) and
  its entries are real links that work without JavaScript [D1].
- Sections 4 to 7 are `<details open>`: collapsible, open by default.

## 7. Colour and theming

- Light and dark themes from one set of tokens (`light-dark()`). Dark is the default (owner's
  choice, 2026-11-06), also without JavaScript; the manual toggle to light is remembered in
  the tab (`sessionStorage`), or on the device once the reader agreed (wrapped in try/catch).
- Library colour code (CLAUDE.md): grey = encapsulation, blue = protocol header,
  teal = message body, purple = TLV/options, orange = vendor-specific, green = expected,
  red = error. Fields also differ by border style (solid / dashed / dotted) so the
  diagrams survive black-and-white print.

## 8. Learning design

| Principle | Evidence | How the template applies it |
|---|---|---|
| Explanatory feedback beats "correct/incorrect" | Elaborated feedback helps higher-order learning and transfer more than knowledge of the correct response [L1][L2] | Every quiz answer reveals an explanation and its RFC/vendor reference, whichever option was chosen. |
| Predict, then observe | Explorable explanations work because the reader commits to a prediction and checks it against the model [L3] | Animation steps carry "Predict: …" prompts revealed on demand. |
| Worked examples first, retrieval after | Worked examples help early skill acquisition; retrieval practice consolidates [L4][L5] | Packet sections are decoded examples; the quiz forces recall and packet reading. |
| Cut extraneous load | Multimedia/cognitive-load principles: remove what does not serve the goal, put words next to the graphic they describe [L4] | One precise sentence beside each diagram, ≤ 5 to 7 elements per diagram, details on demand (field panel). |
| Pages that stand alone | Readers arrive anywhere and leave anytime [L6] | Each section is self-contained; the TOC and stable anchors (`#packets`, `#quiz`…) support deep links. |

## 8b. Writing style

Page text avoids the typography readers associate with generated text: no em dash,
no en dash or middle dot used as a separator, no decorative arrows on buttons. Colons,
commas, parentheses and short sentences instead. Arrows remain only as notation
(`R1 → R2`, state transitions); ✓ / ✗ remain where they back up colour (WCAG 1.4.1).

## 9. Print

`@media print`: light colours, only the current language, header/TOC/controls hidden,
every `<details>` opened before printing and closed after, all tab panels and quiz
explanations shown, source URLs printed after each source.

## 10. What the pipeline enforces

| Check | Job / script |
|---|---|
| No external resource, four languages, balanced translations, page-meta complete | `test:pages-static`, `scripts/check_pages.py` |
| Shared style block and page library identical to the template | `test:pages-static` |
| Every diagram has a title and a legend | `test:pages-static` |
| Sample packets identical to `tools/packet-builder.py` output | `test:pages-static` (fix with `--update`) |
| No `TEMPLATE` placeholder in a published page | `test:pages-static` |
| Field map tiles the packet exactly; checksums verify | `test:packet-builder` |
| axe WCAG 2.2 AA light + dark, CLS < 0.1, reduced motion, hreflang/canonical, URL switch, 360 px, no external request, no console error | `verify:browser`, `scripts/smoke_test.py` |
| No `localStorage` write without the reader's consent; the privacy page's switch and delete button work | `verify:browser`, `scripts/smoke_test.py` |

## 11. Privacy, licence and rights

- Legal pages in `pages/<slug>/index.html` (legal notice, terms of use, privacy,
  accessibility), built from the template and published at `/<lang>/<slug>/`; every page
  links them from the footer. They state facts that live elsewhere: keep them true in the
  same change (ADR 0010, ADR 0011).
- No cookie, no tracker, no third-party resource (CSP `default-src 'self'`,
  `connect-src 'none'`) [R1]. No visitor IP is written: Traefik writes no access log for the
  `learning` router and nginx logs without the client address (homelab stack `learning`,
  README "Privacy").
- Browser storage [R2]: a choice (language, theme, chapter menu) stays in the tab
  (`sessionStorage`), which the ePrivacy rule allows for an interface preference kept for
  the session; reading progress and longer storage need consent, the "remember on this
  device" switch (`npe-remember`, unticked by default). Unticking or "delete" removes every
  key of the site.
- Content under CC BY-NC-SA 4.0 [R3]; commercial use on written permission. Text and data
  mining is reserved under Directive (EU) 2019/790 art. 4(3) and the Belgian Code of economic
  law art. XI.190, 20° [R4], in machine-readable form: `<meta name="tdm-reservation"
  content="1">` on every page and `/.well-known/tdmrep.json` (TDMRep [R5]), plus
  `robots.txt` rules for the documented AI training crawlers (GPTBot, ClaudeBot,
  Google-Extended, Applebot-Extended, CCBot, Meta-ExternalAgent).

## Sources

- [G1] Google Search Central: Managing multi-regional and multilingual sites. https://developers.google.com/search/docs/specialty/international/managing-multi-regional-sites
- [S1] Google Search Central: Education Q&A (Quiz) structured data. https://developers.google.com/search/docs/appearance/structured-data/education-qa
- [W1] W3C: What's New in WCAG 2.2. https://www.w3.org/WAI/standards-guidelines/wcag/new-in-22/
- [W2] W3C: Understanding SC 2.3.3 Animation from Interactions. https://w3c.github.io/wcag/understanding/animation-from-interactions.html
- [H1] Harvard Digital Accessibility: Form feedback with live regions. https://accessibility.huit.harvard.edu/technique-form-feedback-live-regions
- [A1] Smashing Magazine: Accessible SVGs: perfect patterns for screen reader users (2021). https://smashingmagazine.com/2021/05/accessible-svg-patterns-comparison/
- [A2] data.europa.eu: Accessible SVG and ARIA. https://data.europa.eu/apps/data-visualisation-guide/accessible-svg-and-aria
- [P1] Core Web Vitals thresholds (LCP, INP, CLS). https://corewebvitals.io/core-web-vitals
- [B1] web.dev: Baseline 2026. https://web.dev/baseline/2026
- [B2] MDN: `light-dark()`. https://developer.mozilla.org/docs/Web/CSS/color_value/light-dark
- [T1] UXPin: Optimal line length for readability. https://www.uxpin.com/studio/blog/optimal-line-length-for-readability/
- [T2] Canada GCWeb design system: Typography. https://design.cra-arc.alpha.canada.ca/en/design-systems/gcweb/typography/index.html
- [D1] 21st.dev: Docs site components (TOC scroll-spy with IntersectionObserver). https://21st.dev/blog/docs-site-components
- [L1] Butler, Godbole & Marsh (2013): Explanation feedback is better than correct answer feedback for promoting transfer of learning. Journal of Educational Psychology 105(2).
- [L2] Van der Kleij, Feskens & Eggen (2015): Effects of feedback in a computer-based learning environment on students' learning outcomes: a meta-analysis. Review of Educational Research 85(4).
- [L3] Explorable explanation (Bret Victor, 2011). https://en.wikipedia.org/wiki/Explorable_explanation
- [L4] Mayer: Applying the science of learning: evidence-based principles for the design of multimedia instruction (2008). https://pressbooks.pub/learningenvironmentsdesign/chapter/mayer-applying-the-science-of-learning-evidence-based-principles-for-the-design-of-multimedia-instruction/
- [L5] UBC: Design principles for multimedia. https://wiki.ubc.ca/Documentation:Design_Principles_for_Multimedia
- [L6] Red Blob Games: notes on interactive explanations. https://redblobgames.com/x/2306-educ432
- [R1] Regulation (EU) 2016/679 (GDPR), art. 5, 6(1)(f), 13, 15-21. https://eur-lex.europa.eu/eli/reg/2016/679/oj
- [R2] Directive 2002/58/EC art. 5(3); Article 29 Working Party, Opinion 04/2012 on cookie consent exemption (WP194), user-interface customisation; Belgian Data Protection Authority, cookies page. https://www.autoriteprotectiondonnees.be/citoyen/themes/internet/cookies
- [R3] Creative Commons BY-NC-SA 4.0 legal code. https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.en
- [R4] Directive (EU) 2019/790 art. 4(3) and recital 18; Belgian law of 19 June 2022, art. 13 (Code of economic law art. XI.190, 20°); Regulation (EU) 2024/1689 art. 53(1)(c). https://eur-lex.europa.eu/eli/dir/2019/790/oj
- [R5] W3C TDM Reservation Protocol (TDMRep), community group final report, 2024-05-10. https://www.w3.org/community/reports/tdmrep/CG-FINAL-tdmrep-20240510/
