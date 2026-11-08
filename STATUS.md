# Status

**This file is the single source of current status for the hub.** Decisions and their rationale live
only in [`docs/decisions.md`](docs/decisions.md); the plan lives in
[`docs/implementation-plan.md`](docs/implementation-plan.md).

**Updated:** 2026-11-08
**Phase:** Phases 1 to 4 complete and post-Phase-4 remediation integrated. Phases 5 and 6 not started.
**State:** The sample book is published at `v0.2.1` and the catalog and portal list that release.
Changes reach `main` only through pull requests (`HUB-DEC-018`).

## Current facts

| Item | State |
| --- | --- |
| `main` | Protected: pull request and CI required, also for administrators (`HUB-DEC-018`) |
| GitHub repositories | [hub](https://github.com/cesarcastrocuba/handbooks-hub) and [sample](https://github.com/cesarcastrocuba/handbook-sample-01), both public and active |
| Reference handbook | Read-only at `6a15cc211f65e148afdaa75c71a063a8084d1910` |
| Sample repository | `v0.2.1` is the only release; `v0.1.0` to `v0.2.0` are withdrawn and keep their tags (`HUB-DEC-021`). Introduction, 8 chapters, 3 appendices and References |
| Toolkit | `0.5.0`, tag `toolkit-v0.5.0`, 167 unit tests. Sample `v0.2.1` was built with it |
| CI | Green on hub and sample `main` at the last runs |
| Standard profile | `1.0.0`, **Approved** 2026-11-06; `0.2.0` remains resolvable |
| Licensing | CC BY-SA 4.0 content, MIT code. Bundled third-party render resources reviewed and replaced where in doubt (`HUB-DEC-020`) |
| Catalog | 1 approved release: `handbook-authoring-and-publishing` `v0.2.1` (`HUB-DEC-021`) |
| Publication | Reading site live at https://cesarcastrocuba.github.io/handbook-sample-01/ |
| Portal | Live at https://cesarcastrocuba.github.io/handbooks-hub/ |
| Migration of existing handbook | Deferred; separate owner decision (`HUB-DEC-012`) |

## Next actions

1. Phase 5: agent adapters, automation and stabilization.
2. Phase 6: migration evaluation of `solutions-architecture-handbook`, including its copies of the replaced fonts and DOCX reference.

## Blockers and open owner decisions

- Phases 5 and 6 are outside the `HUB-DEC-016` delegation and need owner authorization.
