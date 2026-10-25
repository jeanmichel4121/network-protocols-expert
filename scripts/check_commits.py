#!/usr/bin/env python3
"""Check that commit messages follow Conventional Commits 1.0.0.

    <type>(<optional scope>)<optional !>: <description>

Usage:
    check_commits.py <base-sha> [<head-ref>]   check base..head (merges excluded), used in CI
    check_commits.py --msg-file <file>         check one message, used by the commit-msg hook
"""

import pathlib
import re
import subprocess
import sys

TYPES = ("feat", "fix", "docs", "style", "refactor", "perf", "test", "build", "ci", "chore", "revert")
PATTERN = re.compile(rf"^({'|'.join(TYPES)})(\([a-z0-9][a-z0-9._/-]*\))?!?: \S.{{0,99}}$")


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    if sys.argv[1] == "--msg-file":
        subject = pathlib.Path(sys.argv[2]).read_text(encoding="utf-8").splitlines()[0].strip()
        if PATTERN.match(subject):
            return 0
        print(f"Commit message must follow Conventional Commits: {subject!r}")
        return 1
    rng = f"{sys.argv[1]}..{sys.argv[2] if len(sys.argv) > 2 else 'HEAD'}"
    out = subprocess.run(
        ["git", "log", "--no-merges", "--format=%h%x09%s", rng], check=True, capture_output=True, text=True
    ).stdout
    bad = 0
    for line in filter(None, out.splitlines()):
        sha, subject = line.split("\t", 1)
        if PATTERN.match(subject):
            print(f"OK   {sha} {subject}")
        else:
            bad += 1
            print(f"FAIL {sha} {subject}")
    if bad:
        print(
            f"\n{bad} commit(s) do not follow Conventional Commits: "
            f"<type>(scope): description  — types: {', '.join(TYPES)}"
        )
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
