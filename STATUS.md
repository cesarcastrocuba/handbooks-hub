# Status

**This file is the single source of current status for the hub.** Decisions and their rationale live
only in [`docs/decisions.md`](docs/decisions.md); the plan lives in
[`docs/implementation-plan.md`](docs/implementation-plan.md).

**Updated:** 2026-11-09
**Phase:** Phases 1 to 5 complete; Phase 6 not started and needs an owner decision.
**State:** The sample book is published at `v0.2.4`. This catalog change lists it; the portal shows it
after this change merges and `portal-pages` deploys.
`v0.2.3` was published by mistake without the corrections and is withdrawn with its tag kept (sample
`DEC-019`); `v0.2.1` is withdrawn with its tag kept (`HUB-DEC-023`). The Owner accepted P5-GATE on 2026-11-09. Changes reach `main` only through pull
requests (`HUB-DEC-018`).

## Current facts

| Item | State |
| --- | --- |
| `main` | `5b7d28625e5ba474cf25bd53e3653c493688cc16`; protected by pull request and CI, also for administrators (`HUB-DEC-018`). Catalog listing and P5-GATE record merged as PR 8 |
| GitHub repositories | [hub](https://github.com/cesarcastrocuba/handbooks-hub) and [sample](https://github.com/cesarcastrocuba/handbook-sample-01), both public and active |
| Reference handbook | Read-only at `6a15cc211f65e148afdaa75c71a063a8084d1910` |
| Sample repository | `v0.2.4` is the current release; `v0.2.2` stays published as the previous edition. `v0.2.3` is withdrawn and keeps its tag (sample `DEC-019`). `v0.1.0` to `v0.2.0` are withdrawn and keep their tags (`HUB-DEC-021`). `v0.2.1` is withdrawn and keeps its tag (`HUB-DEC-023`). Introduction, 8 chapters, 3 appendices and References |
| Toolkit | `0.5.0`, tag `toolkit-v0.5.0`, 203 unit tests. Sample `v0.2.4` was built with it |
| CI | Sample `v0.2.4` release run 42810374270 succeeded from `cd99d7a`. Catalog dry run 42810626248 reported `v0.2.2` to `v0.2.4` and `release verification: OK`; real run 42810762259 pushed this catalog branch. `portal-pages` deploys automatically when this change reaches `main` (`HUB-DEC-024`) |
| Standard profile | `1.0.0`, **Approved** 2026-11-06; `0.2.0` remains resolvable |
| Licensing | CC BY-SA 4.0 content, MIT code. Bundled third-party render resources reviewed and replaced where in doubt (`HUB-DEC-020`). Sample `v0.2.2` names Franz César Castro Cuba and includes a third-party notices page |
| Catalog | This change lists `handbook-authoring-and-publishing` `v0.2.4` (sample `DEC-019`); `main` lists `v0.2.2` until it merges |
| Publication | Reading site live at https://cesarcastrocuba.github.io/handbook-sample-01/ |
| Portal | Live at https://cesarcastrocuba.github.io/handbooks-hub/ and shows `v0.2.2` until this change merges and the automatic deployment runs |
| Migration of existing handbook | Deferred; separate owner decision (`HUB-DEC-012`) |

## Next actions

1. Phase 6: migration evaluation of `solutions-architecture-handbook`, including its copies of the replaced fonts and DOCX reference; needs an owner decision.

## Blockers and open owner decisions

- Phase 6 has not started and needs an owner decision.
