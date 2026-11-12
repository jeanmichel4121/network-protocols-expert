# Cisco network topology icons

Source: Cisco Brand Center, *Network Topology Icons*, "PMS 3015 print icons" (EPS),
https://www.cisco.com/c/en/us/about/brand-center/network-topology-icons.html
(downloaded 2026-10-25; `workgroup-switch.svg` and `pc.svg` on 2026-11-11).

Terms stated on that page: "You may use them freely, but you may not alter them."
So these files are a **format conversion only** (EPS → PDF with Ghostscript `-dSAFER`
→ SVG with `pdftocairo -svg`): same drawing, same colours. Pages may scale them
uniformly; never recolour, crop, skew or redraw them.

| File | Cisco icon |
|---|---|
| `router.svg` | router |
| `firewall.svg` | firewall |
| `content-switch.svg` | content switch (used for load balancers) |
| `fileserver.svg` | fileserver |
| `branch-office.svg` | branch office |
| `workgroup-switch.svg` | workgroup switch |
| `pc.svg` | PC |

Embedded in `index.html` by `tools/landing-topology.py --update index.html`, and in the
diagrams of a protocol page by `tools/page-icons.py --update protocols/<slug>/index.html`
(the page lists the icons it uses in its `<!--ICONS:...-->` marker).
