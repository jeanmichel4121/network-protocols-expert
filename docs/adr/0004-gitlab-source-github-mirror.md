# ADR 0004: GitLab as source of truth, GitHub as read-only mirror

- Status: accepted
- Date: 2026-10-26

## Context

Work happens on GitLab (CI, issues, MRs). The Claude app and public readers need a GitHub repository.

## Decision

GitLab.com stays private and authoritative. A GitLab push mirror (SSH deploy key, protected branches and tags) feeds a public GitHub repository where pull requests are disabled and rulesets let only the deploy key write. GitHub issues are the public feedback channel.

## Consequences

One place to work, one place to read. Everything committed becomes public, history included, so the confidentiality rules apply to every commit.
