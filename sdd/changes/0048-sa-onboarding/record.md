# Change 0048 — Solutions Architecture Handbook Onboarding Inventory & Dry Run

Phase 6, Stage 0: Read-only inventory, section-mapping parity proof, feature matrix, licensing audit,
and scratch scaffold dry run for onboarding the Solutions Architecture Handbook to the platform under
`HUB-DEC-043`. This change establishes full content preservation and defines the platform gap backlog
before any manuscript file is imported.

The Implementer (Agy) executes this change in a dedicated worktree and submits it for independent
review by Codex. The Implementer does not review or merge their own work, does not touch `STATUS.md`,
`docs/decisions.md`, `tools/`, `template/`, or `catalog/`, and never modifies the frozen reference
repository `solutions-architecture-handbook`.

## Pins and Scope

- **Hub base**: `fe439a2f641a94254f3b7ceeaefd3eb470dfbf91` (`origin/main`, PR 81 merged). Governed by Owner decision `HUB-DEC-043`.
- **Source repository pin**: `cesarcastrocuba/solutions-architecture-handbook` (private reference), tag `v3.0.0`, peeled commit `13d295bfb266c6fb03b8d244666ebbf0e056e6cd` (annotated tag object `0516d8b`).
- **Hub template pin**: `template-v1.6.0` (commit `8a6d5ae5222ef2e53526017fece64be934c9c22e`).
- **Hub toolkit pin**: `0.11.0` (commit `d4bef53af4c70f86fecdb13d1924c79353dde32f`).
- **Worktree**: `/home/ubuntu/github/handbooks-hub.worktrees/sa-onboarding` on branch `docs/0048-sa-onboarding`.
- **Write set (exclusive)**:
  - `sdd/changes/0048-sa-onboarding/record.md` (this change record)
  - `sdd/changes/0048-sa-onboarding/inventory.md` (comprehensive 8-section report)
  - `sdd/changes/0048-sa-onboarding/inventory.py` (reproducible deterministic counter & generator)
  - `sdd/changes/0048-sa-onboarding/metrics.json` (raw repository & manuscript metrics)
  - `sdd/changes/0048-sa-onboarding/section_map.csv` (itemized 625-row source-to-target mapping)
  - `sdd/changes/0048-sa-onboarding/per_chapter_metrics.csv` (per-file element counts)
  - `sdd/changes/0048-sa-onboarding/feature_matrix.csv` (feature classifications & rationales)

No manuscript prose, figures, or `.dot`/`.png` files are copied into the hub repository.

## Inventory Findings & Parity Summary

1. **Corpus Scope**:
   - Reference repository tree: 479 files, 25,004,001 bytes (~25.0 MB).
   - Manuscript: Exactly 33 `.qmd` files (3 front-matter, 18 chapters, 10 appendices, 2 back-matter), 184,551 words, 11,577 lines.
   - Diagrams: Exactly 121 Graphviz `.dot` sources and 121 rendered `.png` diagrams (17.5 MB). All diagrams are original author works.
   - Tables: 263 captioned tables and 18 chapter review checklists.
   - Published release assets: HTML bundle (36 pages, 14.1 MB), Word edition (624 headings, 121 figures, 263 tables, 12.4 MB), Typst PDF (570 pages, 16.0 MB), SHA256SUMS.
2. **Section Preservation**:
   - **Source sections**: 625 (620 manuscript headings + 5 generated sections: Cover, Contents, List of Figures, List of Tables, Analytic Index).
   - **Target sections**: 625 (all 625 mapped 1-to-1 to target files).
   - **Unmapped sections**: **0** (zero content lost).
   - **Theme-only replaced items**: Learn CSS (`handbook.css`), Selawik font, Cascadia Code font, Learn accent palette. These are replaced by hub design tokens and packaged typography (Libertinus / Fira Code / Atkinson Hyperlegible).
3. **Licensing**:
   - CC BY-SA 4.0 for content, diagrams, checklists, documentation (`LICENSE`).
   - MIT for code and build configuration (`LICENSE-CODE`).
   - SIL Open Font License 1.1 fonts (Selawik/Cascadia) are excluded and not imported.
   - The `IN-04` customer security requirements annex was never stored in the reference repository and is completely excluded.
4. **Dry Run Executions**:
   - `make check` (`validate-book --full` + `validate-references book.yaml`): **PASSED** (exit code 0).
   - `make full` (`build-book --mode chapter`): Failed with exit code 1 due to `title="Review Checklist"` callout attribute expectation.
   - Diagnostic chapter audit: 18/18 chapters fail on Review Checklist callout attribute.
   - Second dry run with mechanical adaptation: 14/18 chapters pass 100% cleanly; 4 chapters have minor single-line content issues (duplicate `**Example.**` tags in ch03, ch16, ch17; empty `**What it includes.**` in ch06). 98.5% out-of-the-box profile conformance.
   - Diagnostic appendix audit: All 10 appendices fail in chapter mode because `build_staging.py` enforces chapter textbook anatomy on appendices.

## Platform Gap Backlog

- **G1**: Template release workflow tag regex rejects `-rc.N` pre-releases (`release.yml:47`). Home: `handbooks-template` (small).
- **G2**: Profile validator enforces chapter anatomy on appendices in `--mode chapter`. Home: `handbook-toolkit` (medium).
- **G3**: Review Checklist callout attribute title vs bold lead-in recognition. Home: `handbook-toolkit` / book import (small).
- **G4**: Analytic Index generation from index vocabulary. Home: `handbook-toolkit` (medium).
- **G5**: Automated catalog appendices generation from callouts. Home: book repository `handbook-solutions-architecture` (small).
- **G6**: Canonical checklist parity & multi-format assessment exports. Home: book repository `handbook-solutions-architecture` (small).
- **G7**: Web landing & Document Control presentation. Home: `handbooks-template` / `handbook-toolkit` (small).

## Verification Evidence

- In worktree `/home/ubuntu/github/handbooks-hub.worktrees/sa-onboarding`:
  - `python3 tools/src/handbook_toolkit/cli.py verify`: ran unit tests and validators.
  - `make full PYTHON=/home/ubuntu/github/handbooks-hub.worktrees/sa-onboarding/.venv/bin/python`: verified all 7 hub repository checks with 0 problems.
  - `git diff --check`: clean (no whitespace or conflict artifacts).
- In scratch workspace `/tmp/agy-sa/`:
  - `inventory.py`: executed deterministically, regenerating `metrics.json`, `section_map.csv`, `per_chapter_metrics.csv`, `feature_matrix.csv`, and `inventory.md` without discrepancies.
  - Scaffold `make check`: exit code 0.

## What Was NOT Run

- No content was committed to or imported into `cesarcastrocuba/handbook-solutions-architecture` (Stage 0 is strictly a read-only inventory).
- No Git tag or release was published.
- `solutions-architecture-handbook` was accessed read-only; no branch, push, PR, or issue was created on it.

## Rollback Boundary

Revert or delete branch `docs/0048-sa-onboarding` and remove `sdd/changes/0048-sa-onboarding/`. No hub code, template assets, catalog entries, or external repositories are affected.
