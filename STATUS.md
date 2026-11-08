# Status

**This file is the single source of current status for the hub.** Decisions and their rationale live
only in [`docs/decisions.md`](docs/decisions.md); the plan lives in
[`docs/implementation-plan.md`](docs/implementation-plan.md).

**Updated:** 2026-11-08
**Phase:** Phases 1 to 4 complete. Post-Phase-4 remediation in review. Phases 5 and 6 not started.
**State:** The sample book is published at `v0.2.0` and the catalog and portal list that release.
Changes reach `main` only through pull requests (`HUB-DEC-018`).

## Current facts

| Item | State |
| --- | --- |
| `main` | Protected: pull request and CI required, also for administrators (`HUB-DEC-018`) |
| GitHub repositories | [hub](https://github.com/cesarcastrocuba/handbooks-hub) and [sample](https://github.com/cesarcastrocuba/handbook-sample-01), both public and active |
| Reference handbook | Read-only at `6a15cc211f65e148afdaa75c71a063a8084d1910` |
| Sample repository | `v0.2.0` is the latest of four releases; Introduction, 8 chapters, 3 appendices and References |
| Toolkit | `0.5.0` in this change, 166 unit tests. Sample `v0.2.0` was built from hub `5f96202`, which reports `0.4.0` |
| CI | Green on hub and sample `main` at the last runs |
| Standard profile | `1.0.0`, **Approved** 2026-11-06; `0.2.0` remains resolvable |
| Licensing | CC BY-SA 4.0 content, MIT code. Bundled third-party render resources are under review (`HUB-DEC-020`) |
| Catalog | 1 approved release: `handbook-authoring-and-publishing` `v0.2.0` |
| Publication | Reading site live at https://cesarcastrocuba.github.io/handbook-sample-01/ |
| Portal | Live at https://cesarcastrocuba.github.io/handbooks-hub/ |
| Migration of existing handbook | Deferred; separate owner decision (`HUB-DEC-012`) |

## Next actions

1. Independent review and owner merge of change `0010-post-phase4-remediation`, using a merge commit.
2. Tag toolkit `0.5.0` on `main`, then move the sample-book pin to it in its own pull request.
3. Phase 5: agent adapters, automation and stabilization.
4. Phase 6: migration evaluation of `solutions-architecture-handbook`.

## Blockers and open owner decisions

- `HUB-DEC-019`: ratify the work integrated after the Phase 4 close.
- `HUB-DEC-020`: accept or replace the bundled render resources with open license questions.
- Phases 5 and 6 are outside the `HUB-DEC-016` delegation and need owner authorization.
