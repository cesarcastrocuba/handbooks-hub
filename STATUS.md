# Status

**This file is the single source of current status for the hub.** Decisions and their rationale live
only in [`docs/decisions.md`](docs/decisions.md); the plan lives in
[`docs/implementation-plan.md`](docs/implementation-plan.md).

**Updated:** 2026-11-06
**Phase:** Phase 1 integrated; Phase 2 manuscript validation integrated; Phase 4 local publication build in progress
**State:** Phase 1 foundation, dual-license defaults, standard profile `0.2.0`, setup docs and
structural manuscript validation are integrated on `main`. The `feat/publication-build` branch adds
a staged, verified local build. Pilot approval, publication and release are **not** authorized.

## Current facts

| Item | State |
| --- | --- |
| `main` | `9ef28d7d7c06de7ec8af926ede2083a8ba487a2e`; Phase 1, setup docs and manuscript validation integrated |
| Publication branch | `feat/publication-build`; local staged build on the publication dependency stack |
| GitHub repositories | [hub](https://github.com/cesarcastrocuba/handbooks-hub) and [sample](https://github.com/cesarcastrocuba/handbook-sample-01), both public |
| Reference handbook | Read-only at `6a15cc211f65e148afdaa75c71a063a8084d1910` |
| Sample repository | Branch `feat/pinned-toolkit-integration`; separate lane; no writes from this session |
| Toolkit | `0.3.0`, 116 unit tests; build, manuscript, catalog, profile and book validators; bundled schemas |
| CI | The branch CI is reported after push; integrated `main` has passed its prior checks |
| Standard profile | `0.2.0`, **Approved** 2026-11-06 |
| Licensing | CC BY-SA 4.0 content, MIT code; approved 2026-11-06 |
| Catalog | Empty; no approved release exists |
| Publication | Local build implemented on this branch; no publication, release or deployment authorized |
| Migration of existing handbook | Deferred; separate owner decision (`HUB-DEC-012`) |

## Next actions

1. Root independently reviews and integrates `feat/publication-build` after the publication dependency review.
2. Keep the portal/catalog work in its separate root-owned branch.
3. Await explicit owner authorization before pilot approval, publication or release.

## Blockers and open owner decisions

- Pilot approval is not authorized.
- Release and publication are not authorized.
- Phase 4 publication build is on an unmerged dependency stack.
