# Status

**This file is the single source of current status for the hub.** Decisions and their rationale live
only in [`docs/decisions.md`](docs/decisions.md); the plan lives in
[`docs/implementation-plan.md`](docs/implementation-plan.md).

**Updated:** 2026-11-06
**Phase:** 1 — Foundation: owner-approved; Phase 2 next
**State:** Phase 1 foundation approved. Dual-license defaults and standard profile `0.2.0` approved.
The reviewed `feat/topic-neutral-profile` branch is authorized for root review and integration.
Pilot approval and any release are **not** authorized. No merge has been performed here.

## Current facts

| Item | State |
| --- | --- |
| Local hub repository | Branch `feat/topic-neutral-profile`; `main` at `0e8d897`; no merge performed |
| GitHub repositories | [hub](https://github.com/cesarcastrocuba/handbooks-hub) and [sample](https://github.com/cesarcastrocuba/handbook-sample-01), both public, default branch `main` |
| Reference handbook | Read-only at `6a15cc211f65e148afdaa75c71a063a8084d1910` (branch `release/v2.1-rc5`) |
| Sample repository | GitHub branch `feat/pinned-toolkit-integration` at `e3b7f288`; separate lane; this session made no sample writes |
| Toolkit | `0.1.0`, catalog/profile/book validators, bundled schemas, 52 unit tests |
| CI | Hub `ci` passed on `main` `0e8d897` (run [42266553876](https://github.com/cesarcastrocuba/handbooks-hub/actions/runs/42266553876)) and on `feat/topic-neutral-profile` `ebdb42e` (run [42274376867](https://github.com/cesarcastrocuba/handbooks-hub/actions/runs/42274376867)); sample `repository-check` passed on `e3b7f28` (run [42276101707](https://github.com/cesarcastrocuba/handbook-sample-01/actions/runs/42276101707)) |
| Standard profile | `0.2.0`, **Approved** 2026-11-06; owner approval recorded in `HUB-DEC-015` |
| Licensing | CC BY-SA 4.0 for content, MIT for code; approved 2026-11-06 |
| Integration | `feat/topic-neutral-profile` authorized for root review/integration; not merged by the implementer |
| Catalog | Empty; no approved release exists |
| Publication | Not implemented; no pilot approval or release authorized |
| Migration of existing handbook | Deferred; separate owner decision (`HUB-DEC-012`) |

## Next actions

1. Root independently reviews and integrates `feat/topic-neutral-profile`; this branch must not be
   merged by the implementer.
2. After integration, start the next scoped Phase 2 task (toolkit/manuscript validation and template).
3. Await explicit owner authorization before any pilot approval, publication or release.

## Blockers and open owner decisions

- Pilot approval is not authorized.
- Release and publication are not authorized.
- Phase 2 implementation has not started.
