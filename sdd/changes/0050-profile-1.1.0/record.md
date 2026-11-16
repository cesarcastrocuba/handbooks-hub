# Change 0050 — Standard Profile 1.1.0 for Reference Books

Implementation of Standard Profile 1.1.0 under Owner decision **HUB-DEC-044** (parts 1 and 2),
approved 2026-11-16. This change enhances the editorial profile and manuscript validator to support
production reference books (addressing inventory failure classes 1–3 and Gaps G2 and G3 from change
0048) while maintaining 100% backward compatibility for existing profile 1.0.0 books.

No toolkit version bump or tag is created here; this change ships with toolkit 0.12.0.

## Pins and Scope

- **Hub Base**: `12b83f1bf2c20f9af7dc95ccda16e9da7a2769a7` (`origin/main`, merge of PR #84).
- **Branch / Worktree**: `feat/0050-profile-1.1.0`, `/home/ubuntu/github/handbooks-hub.worktrees/profile110`.
- **Write set**:
  - `profiles/standard/profile.yaml` (canonical profile updated to version 1.1.0)
  - `tools/src/handbook_toolkit/profile_data/standard-1.1.0.yaml` (new packaged snapshot; 1.0.0 and 0.2.0 remain resolvable and unchanged)
  - `tools/src/handbook_toolkit/manuscript.py`
  - `tools/src/handbook_toolkit/build_staging.py`
  - `tools/src/handbook_toolkit/profiles.py`
  - `tools/src/handbook_toolkit/cli.py`
  - `docs/editorial-contract.md`
  - `docs/profile-distribution.md`
  - `CHANGELOG.md`
  - `tools/tests/test_profile_110.py` (new test suite with 14 focused regression tests)
  - `tools/tests/test_profile.py`
  - `tools/tests/test_build.py`
  - `tools/tests/test_profile_resources.py`
  - `sdd/changes/0050-profile-1.1.0/record.md`

`STATUS.md`, `docs/decisions.md`, and `tools/pyproject.toml` are deliberately not edited.
The template's `book.yaml` keeps profile 1.0.0 for now.

## Implemented Behaviors (Profile Standard 1.1.0)

1. **Qualified Titles (G3)**:
   - Under profile 1.1.0, required callout titles match when qualifying words precede them on word boundaries (e.g. `Architecture Review Checklist — Requirements` satisfies `Review Checklist`).
   - Standard separators (` —`, ` –`, ` -`, `:`) continue to apply following the title.
   - Word boundaries prevent accidental prefixes (e.g. `Pre-Review Checklist` is strictly rejected).
   - Under profile 1.0.0, strict title matching is preserved unchanged.

2. **Dedicated Appendix Rule (G2)**:
   - In chapter mode and appendix mode under profile 1.1.0, appendices are validated by an appendix rule rather than textbook chapter anatomy:
     - Exactly one H1 heading with a meaningful title.
     - Non-empty body.
     - General profile constraints (figures, tables, cross-references).
     - Chapter textbook elements (When to Use, Key Takeaway, Worked Example, Review Checklist, Further Reading, unit labels) are not required.
   - In chapter mode under profile 1.0.0, prior behavior is preserved.

3. **Unit Relaxations (Failure Class 3)**:
   - Under profile 1.1.0:
     - A unit may contain multiple closing elements of the same kind (e.g. two `**Example.**` paragraphs in `ch03` and `ch17`).
     - A label body may be a block list following the label paragraph (e.g. `**What it includes.**` followed by bullet items in `ch06`).
     - The unit scanner ignores text inside table cells for structural-label detection while preserving table content for callout and appendix body presence (e.g. table-only callouts or appendices).
     - Bold paragraph labels inside matching heading sections (e.g. `**Worked example.**` narrative inside `## 17.5 Worked Example`) are recognized as section body prose rather than wrong-form headings. **Note:** This fourth relaxation is beyond the three named in `HUB-DEC-044 (2)` and needs Owner confirmation before the toolkit 0.12.0 tag.
   - Under profiles 1.0.0 and 0.2.0, strict unit rules remain unchanged (verified via differential regression tests). Mode "appendix" is rejected as unsupported under 1.0.0/0.2.0, and untitled non-callout containers retain their malformed diagnostic across all profile versions.

4. **Version Resolution & Distribution**:
   - `profile: standard@1.1.0` and `profile: {id: standard, version: "1.1.0"}` resolve from the filesystem and packaged assets.
   - Profiles `1.0.0` and `0.2.0` remain resolvable.
   - Updated editorial and distribution documentation describing 1.1.0 features.

## Proof Against Real Reference Book (Scratch Verification)

In `/tmp/agy-sa/book` (at commit `80e1a978e902d234840b00dfaae8b94e83120fcc`), profile pinned to `standard@1.1.0`, Review Checklist titles adapted across all 18 chapters:

1. **Manuscript Validation**:
   ```bash
   # Chapters 1-18 in chapter mode:
   handbook-toolkit validate-manuscript manuscript/chapters/*.qmd --mode chapter --profile profiles/standard/profile.yaml
   # Appendices A-J in appendix mode:
   handbook-toolkit validate-manuscript manuscript/appendices/*.qmd --mode appendix --profile profiles/standard/profile.yaml
   ```
   **Result: All 18 chapters and all 10 appendices (28 files) passed cleanly with 0 issues (exit code 0).**

2. **Reference Validation**:
   ```bash
   handbook-toolkit --root /tmp/agy-sa/book validate-references /tmp/agy-sa/book/book.yaml
   ```
   **Result: `/tmp/agy-sa/book/book.yaml: OK` (exit code 0).**

3. **Full Rendered Build (No Bypass)**:
   ```bash
   handbook-toolkit build-book --repo /tmp/agy-sa/book --commit 80e1a978e902d234840b00dfaae8b94e83120fcc --output /tmp/agy-sa/dist-0050 --mode chapter
   ```
   **Result: `/tmp/agy-sa/dist-0050: OK` (exit code 0).**
   All 7 verified publication payloads produced without any bypass patches:
   - `book-html.zip` (18 MB)
   - `book-source.zip` (16 MB)
   - `book.docx` (16 MB)
   - `book.md` (1.2 MB)
   - `book.pdf` (21 MB)
   - `publication-manifest.json` (1.9 KB)
   - `SHA256SUMS.txt` (479 bytes)

## Sample Book Regression Verification

In `/home/ubuntu/github/handbook-sample-01` (at commit `8ed1b7035430ab3dc25fb65d712577bc197394ef`):
1. `make check`: 15 unit tests OK, `check_repo.py` OK (all gate checks green), `validate-book book.yaml`: OK (exit code 0).
2. `build-book --mode chapter`: Build succeeded cleanly, all 7 payloads verified (exit code 0).

## Hub Verification Evidence

In worktree `/home/ubuntu/github/handbooks-hub.worktrees/profile110` using dedicated virtual environment built from `requirements-dev.txt` (`.venv/bin/python`):
- **Unit & Integration Tests**:
  `make test PYTHON=.venv/bin/python`
  **Ran 454 tests in 308.066s, OK (skipped=3)**.
- **Fast Gate Verification**:
  `make verify PYTHON=.venv/bin/python`
  **VERIFY: 5 check(s), 0 problem(s)**.
- **Full Gate Verification**:
  `make verify-full PYTHON=.venv/bin/python`
  **VERIFY (full): 7 check(s), 0 problem(s)**.
- **Whitespace / Formatting**:
  `git diff --check`: **Clean, exit code 0**.

## What Was NOT Run

- Quarto portal live browser tests requiring Playwright (installed in CI `edition-preview` job).
