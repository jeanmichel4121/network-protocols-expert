# ADR 0003: Self-hosted ARM64 runners and hosting on the NAS

- Status: accepted
- Date: 2026-10-26

## Context

The project needs CI and a public website without recurring cost, and the maintainer already operates an ARM64 NAS behind Traefik.

## Decision

Two GitLab runners on the NAS: `nas` for every job, `nas-deploy` for the deploy only (protected refs, official `alpine` images). nginx serves atomic releases at https://learning.cuvelier.tech, publicly, without authentication.

## Consequences

No vendor lock-in or bill. Every CI image must support `linux/arm64`. The site's availability depends on the home connection, which is acceptable for a learning library.
