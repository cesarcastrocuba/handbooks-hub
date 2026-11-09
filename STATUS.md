# Status

**This file is the single source of current status for the hub.** Decisions and their rationale live
only in [`docs/decisions.md`](docs/decisions.md); the plan lives in
[`docs/implementation-plan.md`](docs/implementation-plan.md).

**Updated:** 2026-11-09
**Phase:** Phases 1 to 5 complete; Phase 6 not started and needs an owner decision.
**State:** The sample book is published at `v0.2.2`, and the catalog and portal list that release.
`v0.2.1` is withdrawn: its release page and assets were deleted and its tag stays, under
`HUB-DEC-023`. The Owner accepted P5-GATE on 2026-11-09. Changes reach `main` only through pull
requests (`HUB-DEC-018`).

## Current facts

| Item | State |
| --- | --- |
| `main` | `5b7d28625e5ba474cf25bd53e3653c493688cc16`; protected by pull request and CI, also for administrators (`HUB-DEC-018`). Catalog listing and P5-GATE record merged as PR 8 |
| GitHub repositories | [hub](https://github.com/cesarcastrocuba/handbooks-hub) and [sample](https://github.com/cesarcastrocuba/handbook-sample-01), both public and active |
| Reference handbook | Read-only at `6a15cc211f65e148afdaa75c71a063a8084d1910` |
| Sample repository | `v0.2.2` is the current release. `v0.1.0` to `v0.2.0` are withdrawn and keep their tags (`HUB-DEC-021`). `v0.2.1` is withdrawn and keeps its tag (`HUB-DEC-023`). Introduction, 8 chapters, 3 appendices and References |
| Toolkit | `0.5.0`, tag `toolkit-v0.5.0`, 203 unit tests. Sample `v0.2.2` was built with it |
| CI | Sample `v0.2.2` release run 42621799383 succeeded. Catalog dry run 42622072835 reported `v0.2.1` to `v0.2.2` and `release verification: OK`. Real run 42622209774 succeeded and pushed the catalog branch merged as PR 8, the first real automation run. Portal run 42667021558 deployed `v0.2.2` from `5b7d286` |
| Standard profile | `1.0.0`, **Approved** 2026-11-06; `0.2.0` remains resolvable |
| Licensing | CC BY-SA 4.0 content, MIT code. Bundled third-party render resources reviewed and replaced where in doubt (`HUB-DEC-020`). Sample `v0.2.2` names Franz César Castro Cuba and includes a third-party notices page |
| Catalog | 1 approved release: `handbook-authoring-and-publishing` `v0.2.2` (`HUB-DEC-023`) |
| Publication | Reading site live at https://cesarcastrocuba.github.io/handbook-sample-01/ |
| Portal | Live at https://cesarcastrocuba.github.io/handbooks-hub/ and shows `v0.2.2` |
| Migration of existing handbook | Deferred; separate owner decision (`HUB-DEC-012`) |

## Next actions

1. Phase 6: migration evaluation of `solutions-architecture-handbook`, including its copies of the replaced fonts and DOCX reference; needs an owner decision.

## Blockers and open owner decisions

- Phase 6 has not started and needs an owner decision.
