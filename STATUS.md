# Status

**This file is the single source of current status for the hub.** Decisions and their rationale live
only in [`docs/decisions.md`](docs/decisions.md); the plan lives in
[`docs/implementation-plan.md`](docs/implementation-plan.md).

**Updated:** 2026-11-09
**Phase:** Phases 1 to 5 complete; Phase 6 not started and needs an owner decision.
**State:** The sample book is published at `v0.2.2` and this catalog change lists that release.
`v0.2.1` is superseded and its release page is removed after the portal shows `v0.2.2`, under
`HUB-DEC-023`. The Owner accepted P5-GATE on 2026-11-09. Changes reach `main` only through pull
requests (`HUB-DEC-018`).

## Current facts

| Item | State |
| --- | --- |
| `main` | `ecd1878a34635d4669a7c78ff001a82251b6d233`; protected by pull request and CI, also for administrators (`HUB-DEC-018`). Phase 5 closing record merged as PR 7. This catalog change is unmerged |
| GitHub repositories | [hub](https://github.com/cesarcastrocuba/handbooks-hub) and [sample](https://github.com/cesarcastrocuba/handbook-sample-01), both public and active |
| Reference handbook | Read-only at `6a15cc211f65e148afdaa75c71a063a8084d1910` |
| Sample repository | `v0.2.2` is the current release. `v0.1.0` to `v0.2.0` are withdrawn and keep their tags (`HUB-DEC-021`). `v0.2.1` remains published until the portal shows `v0.2.2`; then its release page and assets are deleted and its tag kept (`HUB-DEC-023`). Introduction, 8 chapters, 3 appendices and References |
| Toolkit | `0.5.0`, tag `toolkit-v0.5.0`, 203 unit tests. Sample `v0.2.2` was built with it |
| CI | Sample `v0.2.2` release run 42621799383 succeeded. Catalog dry run 42622072835 reported `v0.2.1` to `v0.2.2` and `release verification: OK`. Real run 42622209774 succeeded and pushed this catalog branch, the first real automation run |
| Standard profile | `1.0.0`, **Approved** 2026-11-06; `0.2.0` remains resolvable |
| Licensing | CC BY-SA 4.0 content, MIT code. Bundled third-party render resources reviewed and replaced where in doubt (`HUB-DEC-020`). Sample `v0.2.2` names Franz César Castro Cuba and includes a third-party notices page |
| Catalog | This change lists `handbook-authoring-and-publishing` `v0.2.2`. `main` still lists `v0.2.1` until this change merges |
| Publication | Reading site live at https://cesarcastrocuba.github.io/handbook-sample-01/ |
| Portal | Live at https://cesarcastrocuba.github.io/handbooks-hub/ and currently shows `v0.2.1`; it shows `v0.2.2` after this change merges and `portal-pages` runs |
| Migration of existing handbook | Deferred; separate owner decision (`HUB-DEC-012`) |

## Next actions

1. Merge this catalog change, run `portal-pages`, and confirm the portal shows `v0.2.2`.
2. Delete the `v0.2.1` release page and assets, keeping its Git tag.
3. Phase 6: migration evaluation of `solutions-architecture-handbook`, including its copies of the replaced fonts and DOCX reference; needs an owner decision.

## Blockers and open owner decisions

- This catalog change is unmerged, so the portal still shows `v0.2.1`.
- Withdrawal of `v0.2.1` waits until the portal shows `v0.2.2`.
- Phase 6 has not started and needs an owner decision.
