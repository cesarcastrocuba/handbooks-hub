# Status

**This file is the single source of current status for the hub.** Decisions and their rationale live
only in [`docs/decisions.md`](docs/decisions.md); the plan lives in
[`docs/implementation-plan.md`](docs/implementation-plan.md).

**Updated:** 2026-11-09
**Phase:** Phases 1 to 4 complete; Phase 5 delivered and awaiting P5-GATE; Phase 6 not started.
**State:** The sample book is published at `v0.2.1` and the catalog and portal list that release.
Phase 5 adapters, catalog automation, the clean-clone matrix and the operations runbook are merged;
P5-GATE remains the Owner's decision. The sample book's corrected attribution and third-party notices
are being prepared for release `v0.2.2`. Changes reach `main` only through pull requests (`HUB-DEC-018`).

## Current facts

| Item | State |
| --- | --- |
| `main` | `ad1f5b89f03a28cd4921a1e7adb6c9b40720253e`; protected by pull request and CI, also for administrators (`HUB-DEC-018`). Phase 5 integration merged (#3, #4, #5, #6) under `HUB-DEC-022` |
| GitHub repositories | [hub](https://github.com/cesarcastrocuba/handbooks-hub) and [sample](https://github.com/cesarcastrocuba/handbook-sample-01), both public and active |
| Reference handbook | Read-only at `6a15cc211f65e148afdaa75c71a063a8084d1910` |
| Sample repository | `v0.2.1` is the only release; `v0.1.0` to `v0.2.0` are withdrawn and keep their tags (`HUB-DEC-021`). Introduction, 8 chapters, 3 appendices and References |
| Toolkit | `0.5.0`, tag `toolkit-v0.5.0`, 203 unit tests. Sample `v0.2.1` was built with it |
| CI | Clean-clone run 42612951277 succeeded on `ubuntu-24.04` and `macos-15` at `ad1f5b8`. Catalog-update dry run 42613085588 succeeded as a no-op and skipped publish. No real, non-dry catalog update has run |
| Standard profile | `1.0.0`, **Approved** 2026-11-06; `0.2.0` remains resolvable |
| Licensing | CC BY-SA 4.0 content, MIT code. Bundled third-party render resources reviewed and replaced where in doubt (`HUB-DEC-020`). The sample author was confirmed by the Owner on 2026-11-09; corrected attribution and third-party notices await release `v0.2.2` |
| Catalog | 1 approved release: `handbook-authoring-and-publishing` `v0.2.1` (`HUB-DEC-021`) |
| Publication | Reading site live at https://cesarcastrocuba.github.io/handbook-sample-01/ |
| Portal | Live at https://cesarcastrocuba.github.io/handbooks-hub/ |
| Migration of existing handbook | Deferred; separate owner decision (`HUB-DEC-012`) |

## Next actions

1. Owner decides P5-GATE from the clean-clone evidence and the reviewed Phase 5 records.
2. Owner authorizes release `v0.2.2` of the sample book, with the confirmed author and the third-party notices.
3. Phase 6: migration evaluation of `solutions-architecture-handbook`, including its copies of the replaced fonts and DOCX reference.

## Blockers and open owner decisions

- P5-GATE has not been accepted by the Owner.
- The sample book's published HTML carries a Quarto library with no license text in its file and the
  site has no third-party notices page; the PDF author is still the placeholder from
  `publishing/metadata.yaml`. The Owner confirmed the author on 2026-11-09; both fixes wait for `v0.2.2`.
- No real, non-dry catalog update has been run.
- Phase 6 remains outside the Phase 5 authorization and needs an owner decision.
