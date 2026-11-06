# Status

**This file is the single source of current status for the hub.** Decisions and their rationale live
only in [`docs/decisions.md`](docs/decisions.md); the plan lives in
[`docs/implementation-plan.md`](docs/implementation-plan.md).

**Updated:** 2026-11-06
**Phase:** 1 — Foundation (hub portion)
**State:** Scaffold complete with the packaged-schema fix; independent review pending; no release,
deployment or GitHub repository creation.

## Current facts

| Item | State |
| --- | --- |
| Local hub repository | Initialized on branch `main` |
| Reference handbook | Inspected read-only at `6a15cc211f65e148afdaa75c71a063a8084d1910` (branch `release/v2.1-rc5`) |
| Sample repository | Empty at initial inspection (15:32); populated concurrently by a separate session (observed HEAD `bbcba3ef6fd2a3495de33dfcb1eac4ca5a697aa7`). This session made no writes to it. |
| Toolkit | `0.1.0`, catalog/profile/book validators, bundled schemas, 46 unit tests |
| Standard profile | `0.1.0`, **Proposed**; owner approval required |
| Catalog | Empty; no approved release exists |
| Publication | Not implemented; planned for Phase 4 |
| Migration of existing handbook | Deferred; separate owner decision (`DEC-009`) |

## Next actions

1. Independent reviewer checks the exact commit, re-runs `make full` and posts classified findings.
2. Owner reviews the plan, the proposed standard profile and the licensing/notice scope.
3. After Gate 1, review the sample-repository scaffold produced by the separate session in its own
   lane; do not treat this hub review as approval of that work.
4. Start Phase 2 (toolkit, profile and template) only after Gate 1 approval.

## Blockers and open owner decisions

- Approval of the proposed standard editorial profile.
- Confirmation of the dual-license scope in `NOTICE.md`.
- Approval of the Phase 1 gate and the separate sample-repository lane.
- Approval to create GitHub repositories at a later, explicitly authorized step.
