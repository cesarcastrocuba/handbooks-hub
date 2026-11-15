# Change 0048 — Solutions Architecture Handbook Onboarding Inventory & Dry Run

Phase 6, Stage 0: Read-only inventory, section-mapping parity proof, feature matrix, licensing audit,
and scratch scaffold dry run for onboarding the Solutions Architecture Handbook to the platform under
`HUB-DEC-043`. This change establishes full content preservation, complete feature matrix mapping,
rendered parity baselines against v3.0.0 release assets, and defines the platform gap backlog
before any manuscript file is imported.

The Implementer (Agy) executes this change in a dedicated worktree and submits it for independent
review by Codex. The Implementer does not review or merge their own work, does not touch `STATUS.md`,
`docs/decisions.md`, `tools/`, `template/`, or `catalog/`, and never modifies the frozen reference
repository `solutions-architecture-handbook`.

## Pins and Scope

- **Hub base**: `fe439a2a3edfb69e0de0227f5b9e40be3f84a3bf` (`origin/main`, PR 81 merged). Governed by Owner decision `HUB-DEC-043`.
- **Source repository pin**: `cesarcastrocuba/solutions-architecture-handbook` (private reference), tag `v3.0.0`, peeled commit `13d295bfb266c6fb03b8d244666ebbf0e056e6cd` (annotated tag object `0516d8b`).
- **Hub template pin**: `template-v1.6.0` (peeled commit `8a6d5aeefdb5401f3f69a3378975003b9083a50b`).
- **Hub toolkit pin**: `0.11.0` (commit `d4bef53af4c70f86fecdb13d1924c79353dde32f`).
- **Worktree**: `/home/ubuntu/github/handbooks-hub.worktrees/sa-onboarding` on branch `docs/0048-sa-onboarding`.
- **Write set (exclusive)**:
  - `sdd/changes/0048-sa-onboarding/record.md` (this change record)
  - `sdd/changes/0048-sa-onboarding/inventory.md` (comprehensive 8-section report)
  - `sdd/changes/0048-sa-onboarding/inventory.py` (reproducible deterministic counter & generator, supporting `--src` and `--out`)
  - `sdd/changes/0048-sa-onboarding/metrics.json` (raw repository, per-file byte inventory, directory breakdown & manuscript metrics)
  - `sdd/changes/0048-sa-onboarding/source_files.csv` (itemized 479-file per-file byte-size inventory)
  - `sdd/changes/0048-sa-onboarding/section_map.csv` (itemized 626-row source-to-target mapping with real anchors and producers)
  - `sdd/changes/0048-sa-onboarding/per_chapter_metrics.csv` (per-file element counts including pipe, captioned, and uncaptioned tables)
  - `sdd/changes/0048-sa-onboarding/feature_matrix.csv` (feature classifications & rationales)

No manuscript prose, figures, or `.dot`/`.png` files are copied into the hub repository.

## Inventory Findings & Parity Summary

1. **Corpus Scope**:
   - Reference repository tree: Exactly 479 files, 25,004,001 bytes (~25.0 MB) derived from the repository tree:
     `assets/` (244 files, 17,627,471 B), `baseline/` (4 files, 1,813,080 B), `checklists/` (61 files, 393,707 B), `docs/` (2 files, 41,531 B), `manuscript/` (34 files, 1,211,401 B), `publishing/` (23 files, 2,313,201 B), root files (11 files, 65,727 B), `scripts/` (33 files, 378,731 B), `sdd/` (67 files, 1,159,152 B).
   - Manuscript: Exactly 33 `.qmd` files (3 front-matter, 18 chapters, 10 appendices, 2 back-matter), 184,551 words, 11,577 lines.
   - Diagrams: Exactly 121 Graphviz `.dot` sources and 121 rendered `.png` diagrams (17.5 MB). All diagrams are original author works.
   - Tables: 376 total pipe-table separators outside code blocks (263 captioned tables, 113 uncaptioned data/fiche tables).
   - Checklists: 18 chapter review checklists in manuscript and 18 canonical checklist YAML definitions with multi-format assessment exports.
   - Published release assets (v3.0.0): HTML bundle (36 pages, 14.1 MB), Word edition (624 headings, 121 figures, 263 tables, 12.4 MB), Typst PDF (570 pages, 16.0 MB), SHA256SUMS.
2. **Section Preservation**:
   - **Source sections**: 625 headings (620 manuscript headings + 5 generated sections: Cover, Contents, List of Figures, List of Tables, Analytic Index) + 1 checklist exports entry = **626 mapped items**.
   - **Target sections**: 626 (all 626 mapped 1-to-1 to target files with real anchors matching `scripts/build_book.py:heading_id`, e.g. `1.1 Functional Requirements` -> `sec-1-1`).
   - **Unmapped sections**: **0** (zero content lost).
   - **Theme-only replaced items**: Learn CSS (`handbook.css`), Selawik font, Cascadia Code font, Learn accent palette. These are replaced by hub design tokens and packaged typography: **Source Sans 3**, **Source Serif 4**, and **JetBrains Mono** under SIL Open Font License 1.1 (`template/book/NOTICE.md`, `render_resources.py`).
3. **Licensing**:
   - CC BY-SA 4.0 for content, diagrams, checklists, documentation (`LICENSE`).
   - MIT for code and build configuration (`LICENSE-CODE`).
   - SIL Open Font License 1.1 fonts (Selawik/Cascadia) are excluded and not imported.
   - The `IN-04` customer security requirements annex was never stored in the reference repository and is completely excluded.
4. **Dry Run Executions**:
   - `make check` (`validate-book --full` + `validate-references book.yaml`): **PASSED** (exit code 0).
   - `make full` (`build-book --mode chapter`): Failed with exit code 1 due to `title="Review Checklist"` callout attribute expectation.
   - Diagnostic chapter audit across all 18 chapters with `handbook-toolkit validate-manuscript <file> --profile profiles/standard/profile.yaml`: all 18 failed on missing `title="Review Checklist"` attribute (exit code 1).
   - Second diagnostic dry run with checklist titles added: **14 of 18 chapters (77.8%) passed 100% cleanly** (exit code 0). Exactly 4 chapters exhibited single-line issues: `ch03` (lines 167/169), `ch06` (line 273), `ch16` (lines 462/481/487), `ch17` (lines 171/225). At the heading unit level, **321 of 325 chapter units (98.8%)** passed profile conformance out-of-the-box. Non-destructive adaptations proposed keeping every author word.
   - Diagnostic appendix audit: All 10 appendices fail in chapter mode because `build_staging.py` enforces chapter textbook anatomy on appendices (Gap G2).
   - Third dry run (full rendered build on commit `a7e00d7be960a7bd5ce38b7dde5fb09359dd6653` with `--version 3.1.0-preview`): **PASSED** (exit code 0). All publication payloads produced: `book-html.zip` (17.8 MB), `book.docx` (16.2 MB), `book.pdf` (21.4 MB), `book.md` (1.2 MB), `book-source.zip` (16.0 MB), `publication-manifest.json`, `SHA256SUMS.txt`.
5. **Rendered Parity Baseline vs Frozen v3.0.0 Release Assets**:
   - **PDF Pages**: 490 pages (Typst 0.15.1 with Hub design tokens) vs 570 pages in v3.0.0 (-80 pages due to tighter hub typography tokens).
   - **DOCX Total Headings**: 624 headings vs 625 in v3.0.0. Exact 100% parity across all 620 manuscript headings (Title: 1, H1: 33, H2: 261, H3: 322, H4: 4). Difference is exactly 1 heading: missing TOCHeading for Index (Gap G4).
   - **Figures / Drawings**: Exactly 121 in preview DOCX vs 121 in v3.0.0 DOCX (100% match). List of Figures present in both (`figures.html` vs `list-of-figures.html`).
   - **Tables**: 263 captioned tables in source (100% match). List of Tables present in both (`tables.html` vs `list-of-tables.html`). TableCaption custom style count in DOCX is 0 in preview because `annotate_tables` was not run (tables rendered with native Quarto captions).
   - **HTML Page Count**: Exactly 36 HTML pages in preview zip vs 36 in v3.0.0 release zip.
   - **Glossary Links (Appendix G)**: 41 explicit author links in preview vs 509 links in v3.0.0 (468 term links added by `rewrite_glossary_hrefs` absent; Gap G9). Appendix G definition backlinks ("Defined in Section X.Y") absent in preview (Gap G9).
   - **Prose Cross-References**: 673 explicit prose references linked in v3.0.0 via `link_references`, plain text in preview (Gap G8).
   - **Analytic Index**: Present in v3.0.0 (`analytic-index.html`, 487 KB), absent in preview (Gap G4). Definite platform home is `handbook-toolkit`.

## Platform Gap Backlog

- **G1**: Template release workflow tag regex rejects `-rc.N` pre-releases (`release.yml:47`). Home: Hub repository `template/book/` (small).
- **G2**: Profile validator enforces chapter anatomy on appendices in `--mode chapter`. Home: `handbook-toolkit` (medium).
- **G3**: Review Checklist callout attribute title vs bold lead-in recognition. Home: `handbook-toolkit` / book import (small).
- **G4**: Analytic Index generation from index vocabulary. Home: `handbook-toolkit` (medium).
- **G5**: Automated catalog appendices generation from callouts. Home: book repository `handbook-solutions-architecture` (small).
- **G6**: Canonical checklist parity & multi-format assessment exports distribution. Published as extra release assets (`checklists/*.csv`, `*.json`) and checked into book repository under `checklists/exports/`. Home: book repository `handbook-solutions-architecture` (small).
- **G7**: Web landing & Document Control presentation (preserving 11-version history table without dropping content). Home: `handbooks-template` / `handbook-toolkit` (small).
- **G8**: Cross-reference hyperlinking for prose numbers (`Section X.Y`, `Figure X.Y`, `Table X.Y`, `Chapter X`, `Appendix X`). Home: `handbook-toolkit` (medium).
- **G9**: Appendix G glossary body hyperlinks (`rewrite_glossary_hrefs`) & definition backlinks (`annotate_glossary_entries`). Home: `handbook-toolkit` (medium).
- **G10**: Template CI job name mismatch (`Fast checks` in workflow vs `ci` in `docs/author-guide.md`). Home: Hub repository `template/book/` (small).
- **G11**: Book initializer updates only README title, leaving template body text. Home: Hub repository `template/book/` (small).

## Verification Evidence

- In worktree `/home/ubuntu/github/handbooks-hub.worktrees/sa-onboarding`:
  - `python3 tools/src/handbook_toolkit/cli.py verify`: ran unit tests and validators.
  - `make full PYTHON=/tmp/codex-pr82-venv/bin/python`: verified all 7 hub repository checks with 0 problems (`Ran 435 tests in 394.559s, OK (skipped=3); VERIFY (full): 7 check(s), 0 problem(s)`).
  - `git diff --check`: clean (no whitespace or conflict artifacts).
- In scratch workspace `/tmp/agy-sa/`:
  - `inventory.py --src /tmp/agy-sa/src --out sdd/changes/0048-sa-onboarding`: executed deterministically, regenerating `metrics.json`, `source_files.csv`, `section_map.csv`, `per_chapter_metrics.csv`, `feature_matrix.csv`, and `inventory.md` without discrepancies.
  - Initial fast checks: `handbook-toolkit --root /tmp/agy-sa/book validate-book --full` (exit 0) and `validate-references book.yaml` (exit 0).
  - Diagnostic manuscript audit: `handbook-toolkit validate-manuscript <file> --profile profiles/standard/profile.yaml` (18/18 chapters fail on checklist title).
  - Second diagnostic pass with checklist title added: 14/18 chapters exit 0, 4 chapters fail on specific single lines.
  - Third dry run (full build with `--version 3.1.0-preview`): exit code 0 (`/tmp/agy-sa/dist: OK`).

## What Was NOT Run

- No content was committed to or imported into `cesarcastrocuba/handbook-solutions-architecture` (Stage 0 is strictly a read-only inventory).
- No Git tag or release was published.
- `solutions-architecture-handbook` was accessed read-only; no branch, push, PR, or issue was created on it.

## Rollback Boundary

Revert or delete branch `docs/0048-sa-onboarding` and remove `sdd/changes/0048-sa-onboarding/`. No hub code, template assets, catalog entries, or external repositories are affected.
