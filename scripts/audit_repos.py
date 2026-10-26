#!/usr/bin/env python3
"""Audit the live settings of the GitLab project and of the GitHub mirror.

Compares what the forges report today with the baseline documented in
docs/repository-settings.md and prints one PASS/FAIL line per control, so an audit
(or a drift after a manual change in a web UI) is answered in one command.

Usage:
    GITLAB_TOKEN=... GITHUB_TOKEN=... python3 scripts/audit_repos.py

Tokens are read from the environment only; read access is enough. A missing token
skips that forge. Exit 1 if any control fails.
"""

import json
import os
import sys
import urllib.error
import urllib.request

GITLAB = "https://gitlab.com/api/v4/projects/jeanmichel4121%2Fnetwork-protocols-expert"
GITHUB = "https://api.github.com/repos/jeanmichel4121/network-protocols-expert"

# (control id, description, path in the project JSON, expected value)
GITLAB_PROJECT = [
    ("GL-01", "project is private", "visibility", "private"),
    ("GL-02", "default branch is main", "default_branch", "main"),
    ("GL-03", "fast-forward merges (linear history)", "merge_method", "ff"),
    ("GL-04", "squash always", "squash_option", "always"),
    ("GL-05", "merge only on a green pipeline", "only_allow_merge_if_pipeline_succeeds", True),
    ("GL-06", "skipped pipelines do not count as green", "allow_merge_on_skipped_pipeline", False),
    (
        "GL-07",
        "merge only when every thread is resolved",
        "only_allow_merge_if_all_discussions_are_resolved",
        True,
    ),
    ("GL-08", "source branch deleted on merge", "remove_source_branch_after_merge", True),
    ("GL-09", "shared runners disabled", "shared_runners_enabled", False),
    ("GL-10", "group runners disabled", "group_runners_enabled", False),
    ("GL-11", "pipelines not public", "public_jobs", False),
    ("GL-12", "pipeline variables restricted", "restrict_user_defined_variables", True),
    (
        "GL-13",
        "nobody may override pipeline variables",
        "ci_pipeline_variables_minimum_override_role",
        "no_one_allowed",
    ),
    ("GL-14", "job token cannot push to the repository", "ci_push_repository_for_job_token_allowed", False),
    ("GL-15", "older deployments cannot overwrite newer ones", "ci_forward_deployment_enabled", True),
    ("GL-16", "separated caches for protected branches", "ci_separated_caches", True),
    ("GL-17", "pipelines kept one year", "ci_delete_pipelines_in_seconds", 31536000),
    ("GL-18", "Auto DevOps disabled", "auto_devops_enabled", False),
    ("GL-19", "access requests disabled", "request_access_enabled", False),
    ("GL-20", "forking disabled", "forking_access_level", "disabled"),
    ("GL-21", "wiki disabled (docs live in the repository)", "wiki_enabled", False),
    ("GL-22", "snippets disabled", "snippets_enabled", False),
    ("GL-23", "container registry disabled", "container_registry_enabled", False),
    ("GL-24", "package registry disabled", "packages_enabled", False),
    ("GL-25", "GitLab Pages disabled (site served by the NAS)", "pages_access_level", "disabled"),
    ("GL-26", "Service Desk disabled", "service_desk_enabled", False),
    ("GL-27", "LFS disabled (not used)", "lfs_enabled", False),
    ("GL-28", "auto-close referenced issues", "autoclose_referenced_issues", True),
    ("GL-29", "warn about unwanted Unicode characters", "warn_about_potentially_unwanted_characters", True),
    ("GL-30", "authorization checks on uploads", "enforce_auth_checks_on_uploads", True),
    (
        "GL-31",
        "squash commit carries the MR reference",
        "squash_commit_template",
        "%{title}\n\nSee merge request %{reference}",
    ),
]

GITHUB_REPO = [
    ("GH-01", "repository is public", "visibility", "public"),
    ("GH-02", "pull requests disabled (read-only mirror)", "has_pull_requests", False),
    ("GH-03", "issues enabled (public feedback channel)", "has_issues", True),
    ("GH-04", "wiki disabled", "has_wiki", False),
    ("GH-05", "projects disabled", "has_projects", False),
    ("GH-06", "discussions disabled", "has_discussions", False),
    ("GH-07", "homepage is the published site", "homepage", "https://learning.cuvelier.tech"),
    ("GH-08", "secret scanning enabled", "security_and_analysis.secret_scanning.status", "enabled"),
    (
        "GH-09",
        "secret scanning push protection enabled",
        "security_and_analysis.secret_scanning_push_protection.status",
        "enabled",
    ),
]


def get(url, headers):
    req = urllib.request.Request(url, headers={"User-Agent": "npe-audit", **headers})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 (fixed https URLs)
            raw = resp.read()
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as exc:
        return exc.code, None


def dig(data, path):
    for key in path.split("."):
        data = (data or {}).get(key)
    return data


class Report:
    def __init__(self):
        self.failed = 0

    def check(self, cid, desc, ok, got=None):
        self.failed += not ok
        detail = "" if ok or got is None else f" (got {got!r})"
        print(f"{'PASS' if ok else 'FAIL'} {cid} {desc}{detail}")


def audit_gitlab(rep, token):
    h = {"PRIVATE-TOKEN": token}
    _, project = get(GITLAB, h)
    for cid, desc, path, want in GITLAB_PROJECT:
        got = dig(project, path)
        rep.check(cid, desc, got == want, got)
    _, user = get("https://gitlab.com/api/v4/user", h)
    rep.check("GL-40", "maintainer account has 2FA", bool(user and user.get("two_factor_enabled")))
    _, main = get(f"{GITLAB}/protected_branches/main", h)
    push = [a["access_level"] for a in (main or {}).get("push_access_levels", [])]
    rep.check("GL-41", "main protected: no direct push", push == [0], push)
    rep.check("GL-42", "main protected: no force push", main is not None and not main["allow_force_push"])
    _, tags = get(f"{GITLAB}/protected_tags", h)
    rep.check("GL-43", "release tags v* protected", any(t["name"] == "v*" for t in tags or []))
    _, scope = get(f"{GITLAB}/job_token_scope", h)
    rep.check("GL-44", "CI job token inbound allowlist enabled", bool(scope and scope.get("inbound_enabled")))
    _, members = get(f"{GITLAB}/members/all", h)
    rep.check("GL-45", "single member (the maintainer)", len(members or []) == 1, len(members or []))
    _, hooks = get(f"{GITLAB}/hooks", h)
    rep.check("GL-46", "no webhooks", hooks == [], len(hooks or []))
    for cid, what in (("GL-47", "deploy_keys"), ("GL-48", "deploy_tokens"), ("GL-49", "variables")):
        _, items = get(f"{GITLAB}/{what}", h)
        rep.check(cid, f"no {what.replace('_', ' ')}", items == [], len(items or []))
    _, runners = get(f"{GITLAB}/runners", h)
    rep.check(
        "GL-50",
        "only the two project runners",
        sorted(r["runner_type"] for r in runners or []) == ["project_type"] * 2,
    )
    for r in runners or []:
        _, d = get(f"https://gitlab.com/api/v4/runners/{r['id']}", h)
        rep.check(
            "GL-51",
            f"runner {r['id']} locked and tagged only",
            bool(d and d["locked"] and not d["run_untagged"]),
        )
        if d and "nas-deploy" in d["tag_list"]:
            rep.check(
                "GL-52",
                "deploy runner runs protected refs only",
                d["access_level"] == "ref_protected",
                d["access_level"],
            )
    _, mirrors = get(f"{GITLAB}/remote_mirrors", h)
    m = (mirrors or [{}])[0]
    rep.check(
        "GL-53",
        "push mirror to GitHub enabled, protected branches only",
        bool(m.get("enabled") and m.get("only_protected_branches")),
    )
    rep.check("GL-54", "last mirror update succeeded", m.get("last_error") in (None, ""), m.get("last_error"))
    _, envs = get(f"{GITLAB}/environments", h)
    rep.check("GL-55", "production environment tracked", any(e["name"] == "production" for e in envs or []))
    _, labels = get(f"{GITLAB}/labels?per_page=100", h)
    rep.check("GL-56", "label taxonomy present", len(labels or []) >= 40, len(labels or []))
    _, boards = get(f"{GITLAB}/boards", h)
    rep.check("GL-57", "workflow board present", any(b["name"] == "Workflow" for b in boards or []))
    _, scheds = get(f"{GITLAB}/pipeline_schedules", h)
    rep.check("GL-58", "weekly pipeline schedule active", any(s["active"] for s in scheds or []))


def audit_github(rep, token):
    h = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    _, repo = get(GITHUB, h)
    for cid, desc, path, want in GITHUB_REPO:
        got = dig(repo, path)
        rep.check(cid, desc, got == want, got)
    _, user = get("https://api.github.com/user", h)
    rep.check("GH-20", "owner account has 2FA", bool(user and user.get("two_factor_authentication")))
    _, rules = get(f"{GITHUB}/rules/branches/main", h)
    types = sorted({r["type"] for r in rules or []})
    want = ["creation", "deletion", "non_fast_forward", "required_linear_history", "update"]
    rep.check("GH-21", "main: only the mirror may write (ruleset)", all(t in types for t in want), types)
    _, rulesets = get(f"{GITHUB}/rulesets", h)
    rep.check(
        "GH-22",
        "tag ruleset active",
        any(r["target"] == "tag" and r["enforcement"] == "active" for r in rulesets or []),
    )
    _, keys = get(f"{GITHUB}/keys", h)
    rep.check("GH-23", "single deploy key (GitLab push mirror)", len(keys or []) == 1, len(keys or []))
    _, collab = get(f"{GITHUB}/collaborators", h)
    rep.check("GH-24", "single collaborator (the owner)", len(collab or []) == 1, len(collab or []))
    _, hooks = get(f"{GITHUB}/hooks", h)
    rep.check("GH-25", "no webhooks", hooks == [], len(hooks or []))
    status, pvr = get(f"{GITHUB}/private-vulnerability-reporting", h)
    rep.check(
        "GH-26", "private vulnerability reporting enabled", status == 200 and bool(pvr and pvr.get("enabled"))
    )
    status, _ = get(f"{GITHUB}/vulnerability-alerts", h)
    rep.check("GH-27", "Dependabot alerts enabled", status == 204, status)
    _, cs = get(f"{GITHUB}/code-scanning/default-setup", h)
    rep.check(
        "GH-28",
        "CodeQL default setup configured",
        (cs or {}).get("state") == "configured",
        (cs or {}).get("state"),
    )
    _, act = get(f"{GITHUB}/actions/permissions", h)
    rep.check(
        "GH-29",
        "Actions: GitHub-owned only, SHA pinning required",
        bool(act and act["allowed_actions"] == "selected" and act.get("sha_pinning_required")),
    )
    _, wf = get(f"{GITHUB}/actions/permissions/workflow", h)
    rep.check(
        "GH-30",
        "workflow token read-only by default",
        (wf or {}).get("default_workflow_permissions") == "read",
    )
    _, lim = get(f"{GITHUB}/interaction-limits", h)
    rep.check("GH-31", "no interaction limit blocking public issues", not lim, lim)
    _, prof = get(f"{GITHUB}/community/profile", h)
    rep.check(
        "GH-32",
        "community profile complete",
        (prof or {}).get("health_percentage") == 100,
        (prof or {}).get("health_percentage"),
    )
    _, topics = get(f"{GITHUB}/topics", h)
    rep.check("GH-33", "topics set", len((topics or {}).get("names", [])) >= 10)
    _, labels = get(f"{GITHUB}/labels?per_page=100", h)
    rep.check("GH-34", "label taxonomy present", len(labels or []) >= 40, len(labels or []))
    _, alerts = get(f"{GITHUB}/code-scanning/alerts?state=open", h)
    rep.check("GH-35", "no open code scanning alert", alerts == [], len(alerts or []))
    _, dep = get(f"{GITHUB}/dependabot/alerts?state=open", h)
    rep.check("GH-36", "no open Dependabot alert", dep == [], len(dep or []))
    _, sec = get(f"{GITHUB}/secret-scanning/alerts?state=open", h)
    rep.check("GH-37", "no open secret scanning alert", sec == [], len(sec or []))


def main() -> int:
    rep = Report()
    for name, var, fn in (("GitLab", "GITLAB_TOKEN", audit_gitlab), ("GitHub", "GITHUB_TOKEN", audit_github)):
        print(f"== {name}")
        if os.environ.get(var):
            fn(rep, os.environ[var])
        else:
            print(f"SKIP {var} not set")
    print(f"\n{rep.failed} control(s) failed")
    return 1 if rep.failed else 0


if __name__ == "__main__":
    sys.exit(main())
