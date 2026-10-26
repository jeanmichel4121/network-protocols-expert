#!/usr/bin/env python3
"""Check that commit messages follow Conventional Commits 1.0.0.

    <type>(<optional scope>)<optional !>: <description>

Also checks the trunk-based branch names and the merge request title, which becomes the
squash commit subject on `main`.

Usage:
    check_commits.py <base-sha> [<head-ref>]   check base..head (merges excluded), used in CI
    check_commits.py --msg-file <file>         check one message, used by the commit-msg hook
    check_commits.py --branch <name>           check a branch name (CLAUDE.md, Git workflow)
    check_commits.py --title <text>            check a merge request title
"""

import pathlib
import re
import subprocess
import sys

TYPES = ("feat", "fix", "docs", "style", "refactor", "perf", "test", "build", "ci", "chore", "revert")
PATTERN = re.compile(rf"^({'|'.join(TYPES)})(\([a-z0-9][a-z0-9._/-]*\))?!?: \S.{{0,99}}$")
BRANCH_PREFIXES = ("feat", "fix", "chore", "docs")
BRANCH = re.compile(rf"^({'|'.join(BRANCH_PREFIXES)})/[a-z0-9][a-z0-9.-]{{1,60}}$")


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    if sys.argv[1] in ("--branch", "--title"):
        value = sys.argv[2] if len(sys.argv) > 2 else ""
        rx, what = (BRANCH, "Branch name") if sys.argv[1] == "--branch" else (PATTERN, "Merge request title")
        if rx.match(value):
            print(f"OK   {what}: {value}")
            return 0
        hint = (
            f"<{'|'.join(BRANCH_PREFIXES)}>/<lowercase-name>, e.g. feat/ospf, fix/bgp-timers, docs/readme"
            if rx is BRANCH
            else "<type>(scope): description, e.g. feat(ospf): add LSU packet views"
        )
        print(f"FAIL {what}: {value!r}\nExpected {hint}")
        return 1
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
            f"<type>(scope): description, types: {', '.join(TYPES)}"
        )
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
