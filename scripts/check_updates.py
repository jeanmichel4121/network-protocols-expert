#!/usr/bin/env python3
"""Report outdated pins: the dependency-update check of this repository.

Pull requests are disabled on the GitHub mirror and no bot holds a token, so instead
of Dependabot/Renovate a scheduled CI job runs this script every week and turns
orange when something should be updated (see CONTRIBUTING.md, "Updating pinned
dependencies"). It checks:

- Python tools pinned in requirements/*.in against the latest release on PyPI;
- CI images (tag@sha256) against the digest the registry serves today for the same
  tag (a new digest means the image was rebuilt, usually with security fixes);
- pre-commit hooks (`# frozen: vX`) against the latest GitHub release or tag;
- axe-core (scripts/smoke_test.py) against the latest version on npm;
- the Playwright image tag against the Playwright Python package pin.

Usage: python3 scripts/check_updates.py      (exit 1 if anything is outdated)
Network access to pypi.org, registries, api.github.com and registry.npmjs.org is needed.
"""

import json
import pathlib
import re
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
INDEX_TYPES = ", ".join(
    [
        "application/vnd.oci.image.index.v1+json",
        "application/vnd.docker.distribution.manifest.list.v2+json",
        "application/vnd.oci.image.manifest.v1+json",
        "application/vnd.docker.distribution.manifest.v2+json",
    ]
)


def fetch(url, headers=None, method="GET"):
    req = urllib.request.Request(
        url, method=method, headers={"User-Agent": "npe-check-updates", **(headers or {})}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 (fixed https registries)
        return resp.headers, resp.read()


def fetch_json(url, headers=None):
    return json.loads(fetch(url, headers)[1])


def python_pins():
    for path in sorted((ROOT / "requirements").glob("*.in")):
        for line in path.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^([A-Za-z0-9_.-]+)(\[[^\]]+\])?==([^\s#]+)", line.strip())
            if not m:
                continue
            name, pinned = m.group(1), m.group(3)
            latest = fetch_json(f"https://pypi.org/pypi/{name}/json")["info"]["version"]
            yield f"{path.name}: {name}", pinned, latest


def registry_digest(image, tag):
    if "." in image.split("/")[0]:
        host, repo = image.split("/", 1)
        base, headers = f"https://{host}/v2/{repo}", {}
    else:
        repo = image if "/" in image else f"library/{image}"
        token = fetch_json(
            f"https://auth.docker.io/token?service=registry.docker.io&scope=repository:{repo}:pull"
        )["token"]
        base, headers = f"https://registry-1.docker.io/v2/{repo}", {"Authorization": f"Bearer {token}"}
    resp_headers, _ = fetch(f"{base}/manifests/{tag}", {**headers, "Accept": INDEX_TYPES}, method="HEAD")
    return resp_headers["Docker-Content-Digest"].split(":", 1)[1]


def images():
    text = (ROOT / ".gitlab-ci.yml").read_text(encoding="utf-8")
    for image, tag, digest in sorted(set(re.findall(r"([\w.\-/]+):([\w.\-]+)@sha256:([0-9a-f]{64})", text))):
        current = registry_digest(image, tag)
        yield f"image {image}:{tag}", digest[:12], current[:12]


def hooks():
    text = (ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    for owner_repo, frozen in re.findall(
        r"repo: https://github\.com/([\w.-]+/[\w.-]+)\s+rev: [0-9a-f]{40}\s+# frozen: (\S+)", text
    ):
        try:
            latest = fetch_json(f"https://api.github.com/repos/{owner_repo}/releases/latest")["tag_name"]
        except urllib.error.HTTPError:
            latest = fetch_json(f"https://api.github.com/repos/{owner_repo}/tags?per_page=1")[0]["name"]
        yield f"pre-commit {owner_repo}", frozen, latest


def axe():
    text = (ROOT / "scripts" / "smoke_test.py").read_text(encoding="utf-8")
    pinned = re.search(r'AXE_VERSION = "([^"]+)"', text).group(1)
    yield (
        "axe-core (smoke_test.py)",
        pinned,
        fetch_json("https://registry.npmjs.org/axe-core/latest")["version"],
    )


def playwright_consistency():
    ci = (ROOT / ".gitlab-ci.yml").read_text(encoding="utf-8")
    image = re.search(r"playwright/python:v([\d.]+)-", ci).group(1)
    pkg = re.search(r"^playwright==([\d.]+)", (ROOT / "requirements" / "browser.in").read_text(), re.M).group(
        1
    )
    yield "playwright image tag = package pin", image, pkg


def main() -> int:
    outdated = errors = 0
    for check in (python_pins, images, hooks, axe, playwright_consistency):
        try:
            for name, pinned, latest in check():
                ok = pinned.lstrip("v") == latest.lstrip("v")
                outdated += not ok
                print(f"{'OK  ' if ok else 'OLD '} {name}: {pinned}{'' if ok else f' -> {latest}'}")
        except (urllib.error.URLError, KeyError, ValueError, AttributeError) as exc:
            errors += 1
            print(f"ERR  {check.__name__}: {exc}")
    print(f"\n{outdated} outdated, {errors} check(s) failed to run")
    return 1 if outdated or errors else 0


if __name__ == "__main__":
    sys.exit(main())
