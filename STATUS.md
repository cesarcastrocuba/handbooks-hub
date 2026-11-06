# Status

**This file is the single source of current status for the hub.** Decisions and their rationale live
only in [`docs/decisions.md`](docs/decisions.md); the plan lives in
[`docs/implementation-plan.md`](docs/implementation-plan.md).

**Updated:** 2026-11-06
**Phase:** Phases 1, 2, 3 and 4 complete and integrated on `main`. Phases 5 and 6 deferred.
**State:** Phase 1 foundation, Phase 2 contracts (standard profile `1.0.0`, template `1.0.0`, toolkit `0.4.0`),
Phase 3 sample book ("Handbook Authoring and Publishing" complete draft, Gates 1–3d approved),
and Phase 4 publication (release `v0.1.0` published with exact six verified assets on GitHub Releases,
live reading site deployed on GitHub Pages, catalog entry verified online, and static portal generated)
are integrated and complete.

## Current facts

| Item | State |
| --- | --- |
| `main` | Phase 1, Phase 2 (`1.0.0`/`0.4.0`), Phase 4 catalog and portal integrated |
| GitHub repositories | [hub](https://github.com/cesarcastrocuba/handbooks-hub) and [sample](https://github.com/cesarcastrocuba/handbook-sample-01), both public and active |
| Reference handbook | Read-only at `6a15cc211f65e148afdaa75c71a063a8084d1910` |
| Sample repository | `v0.1.0` release published on GitHub Releases and Pages; 8 chapters, front/back matter, appendices complete |
| Toolkit | `0.4.0`, 160 unit tests; build, manuscript, reference, catalog, profile and book validators; bundled schemas and render resources |
| CI | Green on hub and sample repositories |
| Standard profile | `1.0.0`, **Approved** 2026-11-06; `0.2.0` remains resolvable |
| Licensing | CC BY-SA 4.0 content, MIT code; approved 2026-11-06 |
| Catalog | 1 approved release: `handbook-authoring-and-publishing` `v0.1.0` verified online |
| Publication | Published and verified end-to-end; reading site live at https://cesarcastrocuba.github.io/handbook-sample-01/ |
| Portal | Generated static portal verified; workflow ready for Pages deployment |
| Migration of existing handbook | Deferred; separate owner decision (`HUB-DEC-012`) |

## Next actions

1. Phase 5: Agent adapters, automation and stabilization (scheduled for next session).
2. Phase 6: Migration evaluation of `solutions-architecture-handbook` (deferred to next session).

## Blockers and open owner decisions

- None for Phases 1–4. Phases 1–4 are completely fulfilled.
- Phases 5 and 6 deferred to the next session as requested by owner.
