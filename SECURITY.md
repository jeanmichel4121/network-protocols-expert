# Security

- This repository must never contain secrets, real addresses, hostnames, customer data or ticket IDs
  (see `CLAUDE.md` → Confidentiality). Examples use RFC 5737 / RFC 3849 documentation ranges only.
- Secret scanning (`gitleaks`) runs on every commit (pre-commit) and every pipeline.
- CI runs only on the owner's self-hosted runner; shared runners are disabled.
- To report a problem, open a confidential issue.
