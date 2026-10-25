# NAS runner + site hosting

The CI runners and the web server that publishes this library at
**https://learning.cuvelier.tech** run on the home NAS as the homelab stack
`learning` (homelab GitOps repo, deployed by Komodo). Nothing to run from here.

| Runner | Tag | Scope |
|---|---|---|
| `nas-arm64` | `nas` | every job except the deploy, any branch |
| `nas-arm64-deploy` | `nas-deploy` | protected branches only (`main`); official `alpine` images only; the only runner that can write the published site |

Runner tokens live in the operator's password vault, never in this repository.
