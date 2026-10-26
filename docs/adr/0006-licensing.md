# ADR 0006: MIT for code, CC BY-SA 4.0 for content, REUSE

- Status: accepted
- Date: 2026-10-26

## Context

The repository is public and mixes code, learning content and third-party icons with their own terms.

## Decision

Code, tooling and the template under MIT; pages and documentation under CC BY-SA 4.0; Cisco icons unaltered under Cisco's terms. Licensing per file in `REUSE.toml`, checked by `reuse lint`.

## Consequences

Anyone may reuse the content with attribution and share-alike. New folders may need an annotation, or CI fails.
