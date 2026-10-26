# ADR 0005: Trunk-based development with squash and fast-forward merges

- Status: accepted
- Date: 2026-10-26

## Context

Every merge to `main` is deployed. A single maintainer gains nothing from long-lived release or develop branches.

## Decision

`main` is the only long-lived branch. Short-lived `feat/`, `fix/`, `chore/`, `docs/` branches; MRs are squashed and merged fast-forward; releases are `vX.Y.Z` tags. Branch names and MR titles are checked in CI.

## Consequences

Linear, readable history with one Conventional Commit per change. A broken `main` is fixed forward by a new MR.
