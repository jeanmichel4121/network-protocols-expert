#!/usr/bin/env python3
"""Create the GitLab release for the current tag, with notes from CHANGELOG.md.

Runs in CI on a protected tag (vMAJOR.MINOR.PATCH). Uses the CI job token:
no personal token is needed.
"""

import json
import os
import subprocess
import sys
import urllib.request


def main() -> int:
    tag = os.environ["CI_COMMIT_TAG"]
    notes = subprocess.run(
        [sys.executable, "scripts/release_notes.py", tag], check=True, capture_output=True, text=True
    ).stdout
    body = {
        "name": tag,
        "tag_name": tag,
        "description": notes,
        "assets": {
            "links": [
                {
                    "name": "Website (GitLab Pages)",
                    "url": os.environ.get("CI_PAGES_URL", ""),
                    "link_type": "other",
                }
            ]
        },
    }
    req = urllib.request.Request(
        f"{os.environ['CI_API_V4_URL']}/projects/{os.environ['CI_PROJECT_ID']}/releases",
        data=json.dumps(body).encode(),
        method="POST",
        headers={"JOB-TOKEN": os.environ["CI_JOB_TOKEN"], "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        print(f"release {tag} created (HTTP {resp.status})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
