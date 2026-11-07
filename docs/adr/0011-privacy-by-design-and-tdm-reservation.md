# ADR 0011: no visitor data kept, storage on consent, text and data mining reserved

- Status: accepted
- Date: 2026-11-07

## Context

The owner asked for the standard legal pages of a website (terms, GDPR) on 2026-11-07. The site
is published from Belgium by a private individual, free and without any economic activity, so
the e-commerce information duties of the Belgian Code of economic law (book XII, information
society services "normally provided for remuneration") do not apply; the GDPR does, because a
public website is not a purely personal activity (CJEU C-101/01 Lindqvist, para. 47). Two facts
found while checking what the site really processes:

- Traefik's access log, shared by every service of the host, kept the IP address of every
  visitor with no retention limit (4.6 GB since 2026-05-15).
- The pages wrote reading progress (chapters opened, last chapter, quiz score) to
  `localStorage` without being asked. The Belgian Data Protection Authority treats local
  storage like cookies and exempts an interface preference for the duration of a session
  only (directive 2002/58/EC art. 5(3); WP29 Opinion 04/2012).

## Decision

1. **No visitor IP is written.** Homelab stack `learning`: Traefik access log off for the
   `learning` router; nginx log format without the client address (homelab/stacks!38).
2. **Storage on consent.** By default a preference (language, theme, chapter menu) stays in
   the tab (`sessionStorage`) and reading progress is not kept. A "remember on this device"
   switch (footer and privacy page, unticked by default) moves preferences to `localStorage`
   and enables progress; unticking it or "delete this site's data" removes every key. The
   smoke test fails if a page writes `localStorage` without consent.
3. **Text and data mining reserved** (Directive (EU) 2019/790 art. 4(3), Belgian Code of
   economic law art. XI.190, 20°, which accepts only machine-readable means for online
   content): `<meta name="tdm-reservation" content="1">` on every page,
   `/.well-known/tdmrep.json` (W3C TDMRep), and `robots.txt` rules for the AI training
   crawlers that document a token (GPTBot, ClaudeBot, Google-Extended, Applebot-Extended,
   CCBot, Meta-ExternalAgent). Search engines stay allowed.
4. **Four information pages** in `pages/`: legal notice, terms of use, privacy,
   accessibility (voluntary statement: the Web Accessibility Directive covers public bodies,
   the European Accessibility Act listed services such as e-commerce).

## Consequences

- The privacy page states facts that live in another repository (the homelab stack): a
  change there must update the page, and the stack README says so.
- Progress marks and the "Resume" link now need one tick from the reader.
- `robots.txt` and TDMRep are requests: they bind providers of general-purpose AI models
  through Regulation (EU) 2024/1689 art. 53(1)(c), not every crawler.
- Not done here: the entries already in Traefik's global access log (other services too)
  and a retention policy for it. That log belongs to the whole homelab, and deleting from it
  is the owner's decision.
