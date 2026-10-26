# Security policy

## Scope

- The published site <https://learning.cuvelier.tech> (static pages, HTTP headers, CSP).
- This repository: build and check scripts, CI configuration, pinned dependencies.
- Content that could harm a reader who applies it, for example a configuration example
  that disables a protection without saying so.

Out of scope: the vendor products and protocols themselves (report those to the vendor or
to the IETF), and denial-of-service tests against the site.

## Supported versions

Only the current `main` branch, which is what the site serves, receives fixes.

## Reporting a vulnerability

Report privately, never in a public issue:

1. Preferred: GitHub private vulnerability reporting, at
   <https://github.com/jeanmichel4121/network-protocols-expert/security/advisories/new>.
2. Otherwise: the contact details on <https://about.cuvelier.tech>.

Include the affected URL or file, the steps to reproduce and the impact you expect.
Reports in French, English, Dutch or German are welcome.

## What happens next

This is a project with a single maintainer; the targets below are best effort.

| Step | Target |
|---|---|
| Acknowledgement | 7 days |
| First assessment and severity | 14 days |
| Fix published (high or critical) | 30 days |
| Public disclosure | after the fix, coordinated with the reporter, at most 90 days after the report |

Reporters are credited in the advisory and the changelog, unless they prefer otherwise.

## How the project protects itself

- No secrets, real addresses, hostnames or customer data in the repository: examples use
  the documentation ranges of RFC 5737 and RFC 3849 only (see `CLAUDE.md`, Confidentiality).
- Secret scanning (gitleaks) runs before each commit and in every pipeline; GitHub secret
  scanning and push protection are enabled on the mirror.
- CI runs only on the maintainer's self-hosted runners; the deploy runner accepts only
  protected branches and official `alpine` images. Images are pinned by digest, Python
  tools by hash, pre-commit hooks by commit SHA.
- The pages load no external resource; the site's Content Security Policy forbids network
  calls (`connect-src 'none'`) and framing (`frame-ancestors 'none'`).
- The GitHub mirror accepts writes only from the GitLab push mirror's deploy key.
