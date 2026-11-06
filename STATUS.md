# Status

**This file is the single source of current status for the hub.** Decisions and their rationale live
only in [`docs/decisions.md`](docs/decisions.md); the plan lives in
[`docs/implementation-plan.md`](docs/implementation-plan.md).

**Updated:** 2026-11-06
**Phase:** Phase 1 integrated; Phase 2 closure ready for the owner gate; Phase 4 local publication build in progress
**State:** Phase 1 foundation, dual-license defaults, setup docs, manuscript/reference validation,
packaged profiles and shared render resources are integrated on `main`. The `feat/phase2-closure`
branch adds standard profile `1.0.0`, template `1.0.0`, toolkit `0.4.0` and the Typst chapter-title
fix. Pilot approval, publication and release are **not** authorized.

## Current facts

| Item | State |
| --- | --- |
| `main` | `66d0581689e1e9c91913da25b5cb4a7723f3ec5c`; Phase 1, setup docs, manuscript validation, packaged profiles, portal, references and shared render resources integrated |
| Publication branch | `feat/phase2-closure`; Phase 2 profile/template/toolkit closure on top of the integrated build |
| GitHub repositories | [hub](https://github.com/cesarcastrocuba/handbooks-hub) and [sample](https://github.com/cesarcastrocuba/handbook-sample-01), both public |
| Reference handbook | Read-only at `6a15cc211f65e148afdaa75c71a063a8084d1910` |
| Sample repository | Branch `feat/pinned-toolkit-integration`; separate lane; no writes from this session |
| Toolkit | `0.4.0`, 160 unit tests; build, manuscript, reference, catalog, profile and book validators; bundled schemas and render resources |
| CI | The branch CI is reported after push; integrated `main` has passed its prior checks |
| Standard profile | `1.0.0`, **Approved** 2026-11-06; `0.2.0` remains resolvable |
| Licensing | CC BY-SA 4.0 content, MIT code; approved 2026-11-06 |
| Catalog | Empty; no approved release exists |
| Publication | Local build implemented on this branch; no publication, release or deployment authorized |
| Migration of existing handbook | Deferred; separate owner decision (`HUB-DEC-012`) |

## Next actions

1. Root independently reviews `feat/phase2-closure` and the owner approves the Phase 2 gate.
2. Keep the portal/catalog work in its separate root-owned branch.
3. Await explicit owner authorization before pilot approval, publication or release.

## Blockers and open owner decisions

- Pilot approval is not authorized.
- Release and publication are not authorized.
- Phase 2 and the Phase 4 build remain on an unmerged branch until the owner gate.
