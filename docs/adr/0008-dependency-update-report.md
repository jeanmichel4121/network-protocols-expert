# ADR 0008: Weekly dependency report instead of an update bot

- Status: accepted
- Date: 2026-10-26

## Context

Dependabot and Renovate open pull requests, which are disabled on the mirror; a bot on GitLab would need an extra long-lived token.

## Decision

`scripts/check_updates.py` runs weekly (pipeline schedule) and when pins change: Python tools, image digests, pre-commit hooks, axe-core. The job turns orange when an update is due; Dependabot alerts on the mirror report known vulnerabilities.

## Consequences

No extra credential. Updates are applied by hand in an MR, which keeps every change reviewed.
