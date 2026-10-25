#!/usr/bin/env python3
"""Generate the isometric network drawing of the landing page.

The scene is described on a ground plane (u to the right, v towards the viewer) and
projected isometrically: X = (u - v) * cos 30°, Y = (u + v) * sin 30° - z. Zones are
3D slabs; devices are the official Cisco network topology icons (tools/icons/cisco,
used unaltered as Cisco requires: embedded as <symbol>, placed upright with <use>,
uniform scale only). Nodes are drawn back to front so nearer ones overlap farther ones.

Each node carries data-x / data-y: the projected point where its links attach; the
page library (NPE.network) moves the packets along those links.

Usage:
    python3 tools/landing-topology.py --update index.html   # rewrite the TOPOLOGY block
    python3 tools/landing-topology.py                       # print the SVG
"""

import argparse
import json
import math
import pathlib
import re
import sys

C, S = math.cos(math.radians(30)), 0.5
OX, OY = 212, 92
SLAB = 18  # slab thickness

ZONES = [
    # (id, u0, u1, v0, v1, class, labels)
    (
        "sites",
        0,
        112,
        0,
        224,
        "z-site",
        {"fr": "Sites distants", "en": "Remote sites", "nl": "Externe sites", "de": "Außenstandorte"},
    ),
    (
        "core",
        150,
        334,
        0,
        224,
        "z-core",
        {"fr": "Cœur de réseau", "en": "Core backbone", "nl": "Core-backbone", "de": "Core-Backbone"},
    ),
    ("dc1", 372, 604, 0, 96, "z-dc", "DC1"),
    ("dc2", 372, 604, 128, 224, "z-dc", "DC2"),
]
ICON_DIR = pathlib.Path(__file__).resolve().parent / "icons" / "cisco"
ICONS = {
    # kind: (file, rendered height in SVG units)
    "router": ("router.svg", 34),
    "ce": ("router.svg", 28),
    "fw": ("firewall.svg", 50),
    "lb": ("content-switch.svg", 48),
    "srv": ("fileserver.svg", 42),
    "branch": ("branch-office.svg", 58),
}
DECOR = [
    # (kind, u, v): buildings behind the CE routers of the remote sites
    ("branch", 30, 26),
    ("branch", 30, 138),
]
NODES = [
    # (id, kind, u, v, label, sub)
    ("CE-A", "ce", 62, 70, "CE-A", "Site A"),
    ("CE-B", "ce", 62, 182, "CE-B", "Site B"),
    ("P1", "router", 196, 56, "P1", None),
    ("P2", "router", 288, 56, "P2", None),
    ("P4", "router", 196, 168, "P4", None),
    ("P3", "router", 288, 168, "P3", None),
    ("FW-1", "fw", 410, 48, "FW-1", None),
    ("LB-1", "lb", 478, 48, "LB-1", None),
    ("S1", "srv", 556, 20, "S1", None),
    ("S2", "srv", 556, 48, "S2", None),
    ("S3", "srv", 556, 76, "S3", None),
    ("FW-2", "fw", 410, 176, "FW-2", None),
    ("LB-2", "lb", 478, 176, "LB-2", None),
    ("S4", "srv", 556, 148, "S4", None),
    ("S5", "srv", 556, 176, "S5", None),
    ("S6", "srv", 556, 204, "S6", None),
]
LINKS = [
    ("CE-A", "P1"),
    ("CE-A", "P4"),
    ("CE-B", "P4"),
    ("CE-B", "P1"),
    ("P1", "P2"),
    ("P2", "P3"),
    ("P3", "P4"),
    ("P4", "P1"),
    ("P1", "P3"),
    ("P2", "FW-1"),
    ("P3", "FW-2"),
    ("FW-1", "FW-2"),
    ("FW-1", "LB-1"),
    ("FW-2", "LB-2"),
    ("LB-1", "S1"),
    ("LB-1", "S2"),
    ("LB-1", "S3"),
    ("LB-2", "S4"),
    ("LB-2", "S5"),
    ("LB-2", "S6"),
]
FLOWS = [
    {
        "kind": "tcp",
        "path": ["CE-A", "P1", "P2", "FW-1", "LB-1"],
        "pool": ["S1", "S2", "S3"],
        "label": "TLS, Site A → LB-1 → {s}, TCP 443, round robin",
    },
    {"kind": "ospf", "path": ["P1", "P2"], "label": "OSPF Hello, P1 → 224.0.0.5, IP 89"},
    {"kind": "esp", "path": ["CE-B", "P4", "P3", "FW-2"], "label": "IPsec ESP, CE-B → FW-2, IP 50"},
    {
        "kind": "tcp",
        "path": ["CE-B", "P4", "P3", "FW-2", "LB-2"],
        "pool": ["S4", "S5", "S6"],
        "label": "TLS, Site B → LB-2 → {s}, TCP 443, round robin",
    },
    {"kind": "bgp", "path": ["P1", "P3"], "label": "BGP UPDATE, P1 → P3, TCP 179"},
    {"kind": "ospf", "path": ["P3", "P4"], "label": "OSPF Hello, P3 → 224.0.0.5, IP 89"},
    {"kind": "esp", "path": ["CE-A", "P1", "P2", "FW-1"], "label": "IPsec ESP, CE-A → FW-1, IP 50"},
    {
        "kind": "tcp",
        "path": ["CE-B", "P1", "P2", "FW-1", "LB-1"],
        "pool": ["S1", "S2", "S3"],
        "label": "TLS, Site B → LB-1 → {s}, TCP 443, round robin",
    },
    {"kind": "ospf", "path": ["P2", "P3"], "label": "OSPF Hello, P2 → 224.0.0.5, IP 89"},
    {
        "kind": "tcp",
        "path": ["CE-A", "P4", "P3", "FW-2", "LB-2"],
        "pool": ["S4", "S5", "S6"],
        "label": "TLS, Site A → LB-2 → {s}, TCP 443, round robin",
    },
    {"kind": "ospf", "path": ["P4", "P1"], "label": "OSPF Hello, P4 → 224.0.0.5, IP 89"},
]
LANGS = ("fr", "en", "nl", "de")

# Shift each zone along v so that the zones line up left to right on screen
# (screen X grows with u - v, depth with u + v).
SHIFT = {"sites": 190, "core": 0, "dc1": -186, "dc2": -186}


def zone_of(u, v):
    if u < 130:
        return "sites"
    if u < 350:
        return "core"
    return "dc1" if v < 112 else "dc2"


ZONES = [(z, u0, u1, v0 + SHIFT[z], v1 + SHIFT[z], c, lab) for z, u0, u1, v0, v1, c, lab in ZONES]
DECOR = [(k, u, v + SHIFT[zone_of(u, v)]) for k, u, v in DECOR]
NODES = [(i, k, u, v + SHIFT[zone_of(u, v)], lab, sub) for i, k, u, v, lab, sub in NODES]


def p(u, v, z=0.0):
    return (OX + (u - v) * C, OY + (u + v) * S - z)


def pts(*points):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


def poly(cls, *points):
    return f'<polygon class="{cls}" points="{pts(*points)}"/>'


def symbols() -> str:
    """Each Cisco icon once, as a <symbol>; internal ids prefixed so icons cannot collide."""
    out = []
    for kind_file in sorted({f for f, _ in ICONS.values()}):
        name = kind_file[:-4]
        src = (ICON_DIR / kind_file).read_text(encoding="utf-8")
        vb = re.search(r'viewBox="([^"]+)"', src).group(1)
        body = re.search(r"<svg[^>]*>(.*)</svg>", src, re.S).group(1)
        body = re.sub(r'id="([^"]+)"', rf'id="ic-{name}-\1"', body)
        body = re.sub(r'(xlink:href|href)="#([^"]+)"', rf'\1="#ic-{name}-\2"', body)
        body = re.sub(r"url\(#([^)]+)\)", rf"url(#ic-{name}-\1)", body)
        out.append(f'<symbol id="ic-{name}" viewBox="{vb}">{body.strip()}</symbol>')
    return "<defs>" + "".join(out) + "</defs>"


def icon_size(kind):
    file, h = ICONS[kind]
    src = (ICON_DIR / file).read_text(encoding="utf-8")
    _, _, vw, vh = (float(x) for x in re.search(r'viewBox="([^"]+)"', src).group(1).split())
    return file[:-4], h * vw / vh, h


def icon_use(kind, u, v):
    """Icon standing on the ground point (u, v): bottom centre on the projected point."""
    name, w, h = icon_size(kind)
    x, y = p(u, v)
    return (
        f'<use href="#ic-{name}" x="{x - w / 2:.1f}" y="{y - h + 4:.1f}" width="{w:.1f}" height="{h:.1f}"/>',
        y - h + 4,
    )


def node_svg(node):
    nid, kind, u, v, label, sub = node
    ax, ay = p(u, v, 2)
    use, top = icon_use(kind, u, v)
    x, y = p(u, v)
    parts = [
        f'<ellipse class="shadow" cx="{x:.1f}" cy="{y + 2:.1f}" rx="{icon_size(kind)[1] * 0.55:.1f}" '
        'ry="5"/>',
        use,
        f'<text class="nl" x="{x:.1f}" y="{top - 5:.1f}">{label}</text>',
    ]
    if sub:
        parts.append(f'<text class="sub" x="{x:.1f}" y="{y + 20:.1f}">{sub}</text>')
    return (
        f'<g class="node n-{kind}" data-node="{nid}" data-x="{ax:.1f}" data-y="{ay:.1f}">'
        + "".join(parts)
        + "</g>"
    )


def decor_svg(kind, u, v):
    return '<g class="decor">' + icon_use(kind, u, v)[0] + "</g>"


def zone_svg(zone):
    _, u0, u1, v0, v1, cls, labels = zone
    slab = (
        poly("f-l", p(u0, v1, 0), p(u1, v1, 0), p(u1, v1, -SLAB), p(u0, v1, -SLAB))
        + poly("f-r", p(u1, v0, 0), p(u1, v1, 0), p(u1, v1, -SLAB), p(u1, v0, -SLAB))
        + poly("f-top", p(u0, v0), p(u1, v0), p(u1, v1), p(u0, v1))
    )
    # Zone name engraved on the front-left edge of the slab (x along u, y down the edge).
    x0, y0 = p(u0 + 10, v1, 0)
    m = f"matrix({C:.4f} {S} 0 1 {x0:.1f} {y0:.1f})"
    if isinstance(labels, dict):
        text = "".join(
            f'<text class="zl" data-l="{lang}" transform="{m}" y="12.5">{labels[lang]}</text>'
            for lang in LANGS
        )
    else:
        text = f'<text class="zl" transform="{m}" y="12.5">{labels}</text>'
    return f'<g class="zone {cls}">{slab}{text}</g>'


def svg() -> str:
    pos = {n[0]: (n[2], n[3]) for n in NODES}
    corners = [
        p(u, v, z) for _, u0, u1, v0, v1, *_ in ZONES for u in (u0, u1) for v in (v0, v1) for z in (0, -SLAB)
    ]
    corners += [p(n[2], n[3], ICONS[n[1]][1] + 18) for n in NODES] + [
        p(d[1], d[2], ICONS[d[0]][1] + 6) for d in DECOR
    ]
    x0, x1 = min(c[0] for c in corners) - 12, max(c[0] for c in corners) + 12
    y0, y1 = min(c[1] for c in corners) - 8, max(c[1] for c in corners) + 10
    out = [
        f'<svg viewBox="{x0:.0f} {y0:.0f} {x1 - x0:.0f} {y1 - y0:.0f}" '
        'role="img" aria-labelledby="net-t net-d">',
        '<title id="net-d">Site A, Site B (CE-A, CE-B); core P1 to P4; DC1 (FW-1, LB-1, S1 to S3); '
        "DC2 (FW-2, LB-2, S4 to S6)</title>",
        symbols(),
        '<g class="zones">' + "".join(zone_svg(z) for z in ZONES) + "</g>",
        '<g class="links">',
    ]
    for a, b in LINKS:
        (xa, ya), (xb, yb) = p(*pos[a], 2), p(*pos[b], 2)
        cls = ' class="dci"' if {a, b} == {"FW-1", "FW-2"} else ""
        out.append(f'<line{cls} x1="{xa:.1f}" y1="{ya:.1f}" x2="{xb:.1f}" y2="{yb:.1f}"/>')
    out.append("</g>")
    out.append('<g class="pkts"></g><g class="nodes">')
    items = [((d[1] + d[2], d[1]), decor_svg(*d)) for d in DECOR]
    items += [((n[2] + n[3], n[2]), node_svg(n)) for n in NODES]
    for _, markup in sorted(items, key=lambda t: t[0]):
        out.append(markup)
    out.append("</g></svg>")
    return "\n".join(out)


def block() -> str:
    flows = ",\n ".join(json.dumps(f, ensure_ascii=False) for f in FLOWS)
    return (
        f"<!--TOPOLOGY-->\n{svg()}\n<!--/TOPOLOGY-->",
        f'<script type="application/json" data-flows>\n[{flows}]\n</script>',
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--update", metavar="HTML", help="rewrite the TOPOLOGY and FLOWS blocks of a page")
    a = ap.parse_args()
    topo, flows = block()
    if not a.update:
        print(topo)
        return 0
    page = pathlib.Path(a.update)
    text = page.read_text(encoding="utf-8")
    text, n1 = re.subn(r"<!--TOPOLOGY-->.*?<!--/TOPOLOGY-->", lambda _: topo, text, flags=re.S)
    text, n2 = re.subn(
        r'<script type="application/json" data-flows>.*?</script>', lambda _: flows, text, flags=re.S
    )
    if n1 != 1 or n2 != 1:
        print(f"{page}: expected one TOPOLOGY block and one data-flows script, found {n1} and {n2}")
        return 1
    page.write_text(text, encoding="utf-8")
    print(f"{page}: topology updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
