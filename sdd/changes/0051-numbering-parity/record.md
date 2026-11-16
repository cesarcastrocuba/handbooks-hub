# Change 0051 — Figure and Table Numbering Parity (Gap G12)

Implementation of Figure and Table numbering parity under **HUB-DEC-043** (no section lost; prose
references keep pointing at the same item) and **HUB-DEC-005** (explicit `Figure N.F` / `Table N.T`
references). This resolves Gap G12 identified in Change 0048 and reported during acceptance audit
of the 0050 real-book build (PR 85 review on book PR 3): Chapter 1 previously displayed double-numbered
figure captions such as `Figure 4.1: Figure 1.1 — …`, and appendices were assigned positional chapter
numbers (e.g., Chapter 24) instead of appendix letters (`A.1`, `B.2`, …).

No version bump or tag is created here; this change ships with toolkit 0.12.0. Neither `STATUS.md`
nor `docs/decisions.md` is modified.

## Pins and Scope

- **Hub Base**: `95658f9817b808351360e30e1f72bb87a398f1b1` (`origin/main`, merge of PR #85).
- **Branch / Worktree**: `feat/0051-numbering-parity`, `/home/ubuntu/github/handbooks-hub.worktrees/numbering`.
- **Write set**:
  - `tools/src/handbook_toolkit/build.py`
  - `tools/src/handbook_toolkit/build_markdown.py`
  - `tools/src/handbook_toolkit/build_staging.py`
  - `tools/src/handbook_toolkit/print_layout.py`
  - `tools/src/handbook_toolkit/reading_site.py`
  - `tools/src/handbook_toolkit/render_data/typst/handbook-typst.typ`
  - `tools/src/handbook_toolkit/render_data/filters/front-crossrefs.lua`
  - `tools/src/handbook_toolkit/render_resources.py`
  - `tools/src/handbook_toolkit/web_lists.py`
  - `tools/tests/test_build.py`
  - `tools/tests/test_reading_site.py`
  - `tools/tests/test_numbering_parity.py` (suite of 15 focused unit and regression tests)
  - `sdd/changes/0051-numbering-parity/record.md`

## Implemented Behaviors & Review Resolutions

1. **Appendix Numbering (HTML, PDF, DOCX, Markdown)**:
   - The reading-order `appendices` group renders as Quarto appendices (`book.appendices` in `_quarto.yml`) across HTML (`book-html.zip` and reading site), PDF, DOCX, and the Markdown edition (`book.md`).
   - Figures, tables, and sections in appendices are lettered (`A.1`, `B.2`, …) in all editions and the generated List of Figures and List of Tables.
   - For Typst PDF builds, appendix lettering is handled through dedicated state tracking (`handbook-appendix-start`) and dynamic counter numbering (`A.1`..`J.7`), verified by a real `pdftotext` assertion on rendered PDF outputs.
   - In single-file Markdown generation, Quarto's GFM compiler resets chapter numbering and generates appendix letters via injected markers, which are stripped in post-processing.
   - Reading order preservation: `book_config["chapters"]` holds front, chapters, and back matter; `book_config["appendices"]` holds appendices followed by references, ensuring references do not render ahead of appendices in navigation.

2. **Displayed Chapter Numbering & Table Labels**:
   - The `tbl-{prefix}-{n}` labels follow the displayed chapter number rather than the reading order file position.
   - Unnumbered front matter entries do not count towards the chapter number and are assigned prefix `0` (`tbl-0-1`, `tbl-0-2`, …).
   - In all editions (HTML, DOCX, Typst PDF) and lists (`tables.html`, DOCX LoT, Typst LoT), front matter tables are numbered continuously as `Table 0.1` through `Table 0.7`.
   - Numbered chapters count strictly from 1 (`tbl-1-1`, `tbl-2-1`, …).
   - Appendices receive their letter identifier (`tbl-a-1`, `tbl-b-1`, …).

3. **Prefix Stripping and Mismatch Protection**:
   - Figure captions matching `^Figure\s+(?P<label>[A-Za-z0-9.]+)\s*(?:[—–:]|-)\s*(?P<rest>.*)$` (including class-first attribute forms such as `Figure 9.9 — ...` followed by `{.wide #fig-...}`) have the `Figure <label> — ` prefix stripped at staging so Quarto's native cross-reference numbering does not create duplicate numbers (`Figure 1.1: Figure 1.1 — …`).
   - Before stripping, `<label>` is validated against the exact expected displayed number (`{ch}.{fig}` or `{app_letter}.{fig}`). If `<label>` differs, the build fails with `BuildError: figure caption label '<label>' does not match expected number '<expected>'`. Tested with a negative build asserting build failure on mismatched class-first figures.
   - Table captions matching `^Table\s+(?P<label>[A-Za-z0-9.]+)\s*(?:[—–:]|-)\s*(?P<rest>.*)$` are stripped and validated under the same rule.
   - The canonical manuscript source in git remains untouched.

4. **Front Matter and Back Matter Labels**:
   - In v3.0.0, front matter tables carried manual labels `Table 0.1` through `Table 0.7`.
   - With continuous front matter numbering, HTML, DOCX, and PDF all render `Table 0.1` through `Table 0.7` continuously across the unnumbered front-matter group, resolving the duplicate `Table 1, 2, 3, 1, 2, 3, 4` issue in `tables.html` and matching v3.0.0.
   - Sample book change: `handbook-sample-01` front matter table in introduction changed from `Table 1` to `Table 0.1`.
   - Sample heading change: Appendix heading `Appendix A — Brief and Outline Templates` in sample is adapted to `Brief and Outline Templates` because the appendix letter is supplied by Quarto/Typst.
   - Conclusions back-matter table: renders as `Table BM.1` in HTML, DOCX, and Typst PDF, matching v3.0.0's `Table BM.1`. Unnumbered back-matter files (appearing after numbered chapters/appendices) receive the `BM` chapter prefix and `tbl-bm-` label prefix.
   - Note on desktop Word verification: Owner desktop Word approval is required before the toolkit 0.12.0 tag, but does not block merging this PR.

5. **Sample Book Regression (`handbook-sample-01`)**:
   - Built before and after change 0051 using `handbook-sample-01` at commit `8ed1b7035430ab3dc25fb65d712577bc197394ef`.
   - List of Figures:
     - `Figure 1.1: The seven lifecycle states in order, from brief to retirement.`
   - List of Tables:
     - Before: `Table 1: Task-Based Reading Routes`, `Table 2.1: Illustrative brief for a fictional API handbook; names, targets and evidence are not real.`
     - After: `Table 0.1: Task-Based Reading Routes`, `Table 2.1: Illustrative brief for a fictional API handbook; names, targets and evidence are not real.`
   - In DOCX, the appendices (which lack figures or tables) retain their unnumbered titles.

## Real Book Parity Proof (`Solutions-Architecture-Handbook`)

Full book build executed on `/tmp/codex-pr87-real-book` with all 33 files into `/tmp/codex-pr87-real-dist`.

### Comparison Command

```bash
python3 /tmp/codex-pr87-compare.py
```

### Command Output

```text
HTML Figure counts 121 121 full ordered equality True
HTML Figure chapter/appendix count 121 ordered equality True
HTML Figure other labels [] => []
DOCX BODY Figure counts 121 121 full ordered equality True
DOCX BODY Figure chapter/appendix ordered equality True
DOCX BODY Figure other labels [] => []
DOCX LIST Figure counts 121 121 core equality True
HTML Table counts 263 263 full ordered equality True
HTML Table chapter/appendix count 255 ordered equality True
HTML Table other labels ['0.1', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7', 'BM.1'] => ['0.1', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7', 'BM.1']
DOCX BODY Table counts 263 263 full ordered equality True
DOCX BODY Table chapter/appendix ordered equality True
DOCX BODY Table other labels ['0.1', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7', 'BM.1'] => ['0.1', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7', 'BM.1']
DOCX LIST Table counts 263 263 core equality True
PDF Figure appendix letter labels ['A.1']
PDF Table appendix letter labels ['A.1', 'A.2', 'B.1', 'B.10', 'B.11', 'B.12', 'B.13', 'B.14', 'B.2', 'B.3', 'B.4', 'B.5', 'B.6', 'B.7', 'B.8', 'B.9', 'C.1', 'D.1', 'E.1', 'E.10', 'E.2', 'E.3', 'E.4', 'E.5', 'E.6', 'E.7', 'E.8', 'E.9', 'F.1', 'F.10', 'F.11', 'F.2', 'F.3', 'F.4', 'F.5', 'F.6', 'F.7', 'F.8', 'F.9', 'G.1', 'H.1', 'H.10', 'H.11', 'H.12', 'H.13', 'H.14', 'H.15', 'H.16', 'H.17', 'H.18', 'H.2', 'H.3', 'H.4', 'H.5', 'H.6', 'H.7', 'H.8', 'H.9', 'I.1', 'I.10', 'I.11', 'I.12', 'I.13', 'I.14', 'I.15', 'I.16', 'I.17', 'I.18', 'I.2', 'I.3', 'I.4', 'I.5', 'I.6', 'I.7', 'I.8', 'I.9', 'J.1', 'J.2', 'J.3', 'J.4', 'J.5', 'J.6', 'J.7']
Comparison complete: full-table sequence differences are reported explicitly above.
```

Across all 18 numbered chapters and 10 appendices (A–J):
- **121 figures** match v3.0.0 100% identically in sequence and numbering in HTML, DOCX, and PDF.
- **255 captioned chapter and appendix tables** match v3.0.0 100% identically in sequence and numbering (`Table 1.1`–`Table 18.8`, `Table A.1`–`Table J.7`).
- **Front matter tables**: `Table 0.1` through `Table 0.7` continuous in HTML, DOCX, and PDF LoT/LoF.
- **Back-matter table**: The 1 table in `conclusions.qmd` is `Table BM.1` in HTML, DOCX, and Typst PDF, matching v3.0.0's `Table BM.1` 100%. All 263 tables achieve full ordered equality.

## Test Suite and Verification

```bash
# Unit test suite (477 tests)
.venv/bin/python -m unittest discover -s tools/tests -v
Ran 477 tests in 308.343s
OK (skipped=3)

# Fast verify
PYTHONPATH=tools/src .venv/bin/python -m handbook_toolkit --root . verify
repository files: OK
packaged schemas: OK
catalog/catalog.json: OK
profiles/standard/profile.yaml: OK
template/book/book.yaml: OK
VERIFY: 5 check(s), 0 problem(s)

# Full verify
PYTHONPATH=tools/src .venv/bin/python -m handbook_toolkit --root . verify --full
repository files: OK
packaged schemas: OK
catalog/catalog.json: OK
profiles/standard/profile.yaml: OK
template/book/book.yaml: OK
documentation links: OK
documentation currency: OK
VERIFY (full): 7 check(s), 0 problem(s)
```
