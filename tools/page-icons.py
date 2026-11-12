#!/usr/bin/env python3
"""Embed the Cisco topology icons a protocol page uses in its diagrams.

A page lists the icons it needs in a marker placed in <body>, before the layout:

    <!--ICONS:pc,workgroup-switch,router--><!--/ICONS-->

This tool fills the marker with one hidden <svg class="sprite"> holding a <symbol id="ic-NAME">
per icon (tools/icons/cisco/NAME.svg, unaltered as Cisco requires: the drawing is copied as is,
only its internal ids are prefixed so two icons cannot collide). A diagram then places an icon
with <use href="#ic-NAME" x= y= width= height=>, keeping the icon's own aspect ratio.

Usage:
    python3 tools/page-icons.py --update protocols/<slug>/index.html
    python3 tools/page-icons.py --sizes pc,router      # viewBox of each icon, to place it
"""

import argparse
import pathlib
import re
import sys

ICON_DIR = pathlib.Path(__file__).resolve().parent / "icons" / "cisco"
BLOCK = re.compile(r"<!--ICONS:([a-z0-9,-]+)-->.*?<!--/ICONS-->", re.S)


def symbol(name: str) -> str:
    src = (ICON_DIR / f"{name}.svg").read_text(encoding="utf-8")
    vb = re.search(r'viewBox="([^"]+)"', src).group(1)
    body = re.search(r"<svg[^>]*>(.*)</svg>", src, re.S).group(1)
    body = re.sub(r'id="([^"]+)"', rf'id="ic-{name}-\1"', body)
    body = re.sub(r'(xlink:href|href)="#([^"]+)"', rf'\1="#ic-{name}-\2"', body)
    body = re.sub(r"url\(#([^)]+)\)", rf"url(#ic-{name}-\1)", body)
    return f'<symbol id="ic-{name}" viewBox="{vb}">{body.strip()}</symbol>'


def block(names: str) -> str:
    symbols = "".join(symbol(n) for n in names.split(","))
    return (
        f"<!--ICONS:{names}-->"
        f'<svg class="sprite" aria-hidden="true" focusable="false" xmlns:xlink="http://www.w3.org/1999/xlink">'
        f"<defs>{symbols}</defs></svg><!--/ICONS-->"
    )


def rewrite(text: str) -> str:
    """The page with its icon block rebuilt from the icon files (unchanged without a marker)."""
    return BLOCK.sub(lambda m: block(m.group(1)), text)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--update", metavar="PAGE", help="rewrite the icon block of that page")
    ap.add_argument("--sizes", metavar="NAMES", help="print the viewBox of each icon (comma separated)")
    args = ap.parse_args()
    if args.sizes:
        for name in args.sizes.split(","):
            src = (ICON_DIR / f"{name}.svg").read_text(encoding="utf-8")
            print(name, re.search(r'viewBox="([^"]+)"', src).group(1))
        return 0
    if not args.update:
        ap.print_help()
        return 2
    path = pathlib.Path(args.update)
    text = path.read_text(encoding="utf-8")
    if not BLOCK.search(text):
        print(f"{path}: no <!--ICONS:...--> marker", file=sys.stderr)
        return 1
    path.write_text(rewrite(text), encoding="utf-8")
    print(f"{path}: icons embedded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
