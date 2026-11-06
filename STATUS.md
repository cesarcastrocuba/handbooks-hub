# Status

**This file is the single source of current status for the hub.** Decisions and their rationale live
only in [`docs/decisions.md`](docs/decisions.md); the plan lives in
[`docs/implementation-plan.md`](docs/implementation-plan.md).

**Updated:** 2026-11-06
**Phase:** Phase 1 integrated on `main`; Phase 2 next
**State:** Phase 1 foundation, dual-license defaults and standard profile `0.2.0` are integrated on
`main`. The `docs/hub-setup` branch adds onboarding/setup documentation for review. Pilot approval,
publication and release are **not** authorized.

## Current facts

| Item | State |
| --- | --- |
| `main` | `8ee28a081399155a250ea8bc45d8492245ab2377`; Phase 1 integrated |
| Docs branch | `docs/hub-setup`; onboarding and pinned-toolkit setup instructions |
| GitHub repositories | [hub](https://github.com/cesarcastrocuba/handbooks-hub) and [sample](https://github.com/cesarcastrocuba/handbook-sample-01), both public |
| Reference handbook | Read-only at `6a15cc211f65e148afdaa75c71a063a8084d1910` |
| Sample repository | Branch `feat/pinned-toolkit-integration` at `e3b7f288`; separate lane; no writes from this session |
| Toolkit | `0.1.0`, catalog/profile/book validators, bundled schemas, 52 unit tests |
| CI | Hub `ci` passed on `main` `8ee28a0` (run [42277955794](https://github.com/cesarcastrocuba/handbooks-hub/actions/runs/42277955794)); sample `repository-check` passed at `e3b7f28` |
| Standard profile | `0.2.0`, **Approved** 2026-11-06 |
| Licensing | CC BY-SA 4.0 content, MIT code; approved 2026-11-06 |
| Catalog | Empty; no approved release exists |
| Publication | Not implemented; no pilot approval or release authorized |
| Migration of existing handbook | Deferred; separate owner decision (`HUB-DEC-012`) |

## Next actions

1. Root independently reviews and integrates `docs/hub-setup`.
2. After integration, start the next scoped Phase 2 task.
3. Await explicit owner authorization before pilot approval, publication or release.

## Blockers and open owner decisions

- Pilot approval is not authorized.
- Release and publication are not authorized.
- Phase 2 implementation has not started.
