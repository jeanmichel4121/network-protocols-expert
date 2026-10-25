#!/usr/bin/env python3
"""Print the CHANGELOG.md section of a version (Keep a Changelog format).

Usage: release_notes.py v1.2.0   -> prints the body of the "## [1.2.0]" section.
Exit code 1 if the section does not exist (a release must be documented first).
"""

import pathlib
import re
import sys


def main() -> int:
    version = sys.argv[1].lstrip("v")
    text = (pathlib.Path(__file__).resolve().parent.parent / "CHANGELOG.md").read_text(encoding="utf-8")
    m = re.search(rf"^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## \[|\Z)", text, re.M | re.S)
    if not m or not m.group(1).strip():
        print(f"CHANGELOG.md has no section for [{version}]", file=sys.stderr)
        return 1
    print(m.group(1).strip())
    return 0


if __name__ == "__main__":
    sys.exit(main())
