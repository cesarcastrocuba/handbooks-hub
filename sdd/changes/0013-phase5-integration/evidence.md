# Evidence — Phase 5 integration

**Decision:** `HUB-DEC-022`. **Main commit:** `ad1f5b89f03a28cd4921a1e7adb6c9b40720253e`.
**Recorded:** 2026-11-09.

## Delivered

| Work package | Delivery | Review |
| --- | --- | --- |
| P5-01, P5-02 | Adapter contract, `CLAUDE.md`, GitHub Copilot pointer and adapter drift test; hub PR 6 | Antigravity approved at `ecb38bf` |
| P5-03 | `catalog-update` workflow and catalog-automation documentation; hub PR 4 | Antigravity approved at `3ec04b8` |
| P5-04 | Clean-clone workflow, `docs/clean-clone.md`, and the sample book's portable `mktemp` fix; hub PR 3 and sample PR 3 | Antigravity approved at `3d92335`; Codex approved at `e7fa80e`, merged at `4e17627` |
| P5-05 | Operations runbook and rehearsal record; hub PR 5 | OpenCode approved after three review rounds at `99f173c` |

The Owner authorized these merges on 2026-11-09 for these pull requests only. P5-GATE remains the
Owner's decision.

Reviewer reports, Owner authorizations and the adapter loading check are in
[`reviews.md`](reviews.md).

## Post-merge runs

| Run | Commit | Result |
| --- | --- | --- |
| Clean-clone, 42612951277 | `ad1f5b8` | Success on `ubuntu-24.04` and `macos-15` |
| Catalog-update dry run, 42613085588 | `ad1f5b8` | Success; prepare reported no-op "handbook-authoring-and-publishing already lists v0.2.1"; publish job skipped |

No real, non-dry catalog update has been run.

## Verification

Commands run in this change:

```bash
make check
make full
```

- `make check`: 203 tests, 5 repository checks, 0 problems.
- `make full`: 203 tests, 6 repository checks, documentation links OK.

## Not run

- The Owner's P5-GATE acceptance.
- A real catalog update (`dry_run=false`).
- Copilot loading of its adapter and Codex native reading of `AGENTS.md`.
- Windows; the matrix covers `ubuntu-24.04` and `macos-15` only.
- Artifact builds in the clean-clone workflow; those belong to `publication-build` and the book's
  release workflow.

## Open items for the sample book

- Published HTML `v0.2.1` carries Quarto libraries; one of them (Tippy, MIT) has no license text in
  its file, and the site has no third-party notices page.
- The `v0.2.1` PDF shows the author `Handbook Sample Contributors (pending owner confirmation)` from
  `publishing/metadata.yaml`.
- The Owner confirmed the author, Franz César Castro Cuba, on 2026-11-09. Both fixes wait for release
  `v0.2.2`, which is in preparation and needs Owner authorization to publish.
- `solutions-architecture-handbook` still holds the files replaced under `HUB-DEC-020`; they are to
  be handled at migration under `HUB-DEC-012`.
