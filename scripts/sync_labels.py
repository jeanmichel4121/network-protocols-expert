#!/usr/bin/env python3
"""Apply .github/labels.yml to the GitLab project and to the GitHub mirror.

Creates missing labels and updates colour/description of existing ones. Labels that
are not in the file are listed, and deleted only with --prune.

Usage:
    GITLAB_TOKEN=... GITHUB_TOKEN=... python3 scripts/sync_labels.py [--prune] [--dry-run]

Tokens are read from the environment only (never pass them on the command line).
A missing token skips that forge.
"""

import json
import os
import pathlib
import sys
import urllib.parse
import urllib.request

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
GITLAB = "https://gitlab.com/api/v4/projects/jeanmichel4121%2Fnetwork-protocols-expert"
GITHUB = "https://api.github.com/repos/jeanmichel4121/network-protocols-expert"


def call(method, url, headers, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url, data=data, method=method, headers={**headers, "Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 (fixed https URLs)
        raw = resp.read()
        return json.loads(raw) if raw else None


def sync(forge, wanted, prune, dry):
    if forge == "gitlab":
        h = {"PRIVATE-TOKEN": os.environ["GITLAB_TOKEN"]}
        have = {x["name"]: x for x in call("GET", f"{GITLAB}/labels?per_page=100", h)}
    else:
        h = {"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}", "Accept": "application/vnd.github+json"}
        have = {x["name"]: x for x in call("GET", f"{GITHUB}/labels?per_page=100", h)}
    for lab in wanted:
        name, color, desc = lab["name"], lab["color"], lab["description"]
        cur = have.get(name)
        cur_color = cur and ("#" + cur["color"].lstrip("#")).lower()
        if cur and cur_color == color.lower() and (cur.get("description") or "") == desc:
            continue
        action = "update" if cur else "create"
        print(f"{forge}: {action} {name}")
        if dry:
            continue
        q = urllib.parse.quote(name, safe="")
        if forge == "gitlab":
            body = {"name": name, "color": color, "description": desc}
            call("PUT" if cur else "POST", f"{GITLAB}/labels/{q}" if cur else f"{GITLAB}/labels", h, body)
        else:
            body = {"name": name, "color": color.lstrip("#"), "description": desc}
            call("PATCH" if cur else "POST", f"{GITHUB}/labels/{q}" if cur else f"{GITHUB}/labels", h, body)
    names = {lab["name"] for lab in wanted}
    for extra in sorted(set(have) - names):
        print(f"{forge}: {'delete' if prune else 'not in labels.yml (kept)'} {extra}")
        if prune and not dry:
            q = urllib.parse.quote(extra, safe="")
            call("DELETE", f"{GITLAB}/labels/{q}" if forge == "gitlab" else f"{GITHUB}/labels/{q}", h)


def main() -> int:
    wanted = yaml.safe_load((ROOT / ".github" / "labels.yml").read_text(encoding="utf-8"))
    prune, dry = "--prune" in sys.argv, "--dry-run" in sys.argv
    for forge, var in (("gitlab", "GITLAB_TOKEN"), ("github", "GITHUB_TOKEN")):
        if os.environ.get(var):
            sync(forge, wanted, prune, dry)
        else:
            print(f"{forge}: {var} not set, skipped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
