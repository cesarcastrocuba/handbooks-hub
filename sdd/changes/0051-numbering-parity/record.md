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
  - `tools/src/handbook_toolkit/build_staging.py`
  - `tools/src/handbook_toolkit/build_markdown.py`
  - `tools/src/handbook_toolkit/build.py`
  - `tools/src/handbook_toolkit/reading_site.py`
  - `tools/tests/test_build.py`
  - `tools/tests/test_reading_site.py`
  - `tools/tests/test_numbering_parity.py` (new suite of 10 focused unit tests)
  - `sdd/changes/0051-numbering-parity/record.md`

## Implemented Behaviors

1. **Appendix Numbering (HTML, PDF, DOCX, Markdown)**:
   - The reading-order `appendices` group renders as Quarto appendices (`book.appendices` in `_quarto.yml`) across HTML (`book-html.zip` and reading site), PDF, DOCX, and the Markdown edition (`book.md`).
   - Figures, tables, and sections in appendices are lettered (`A.1`, `B.2`, …) in all editions and the generated List of Figures and List of Tables.
   - For single-file Markdown generation, Quarto's GFM compiler resets chapter numbering and generates appendix letters via injected `<!-- quarto-file-metadata: <base64 json of {bookItemType: appendix, bookItemNumber: N}> -->` markers, which are stripped in post-processing.

2. **Displayed Chapter Numbering & Table Labels**:
   - The `tbl-{prefix}-{n}` labels follow the displayed chapter number rather than the reading order file position.
   - Unnumbered front matter entries do not count towards the chapter number and are assigned prefix `0` (`tbl-0-1`, `tbl-0-2`, …).
   - Numbered chapters count strictly from 1 (`tbl-1-1`, `tbl-2-1`, …).
   - Appendices receive their letter identifier (`tbl-a-1`, `tbl-b-1`, …).

3. **Prefix Stripping and Mismatch Protection**:
   - Figure captions matching `^Figure\s+(?P<label>[A-Za-z0-9.]+)\s*(?:[—–:]|-)\s*(?P<rest>.*)$` have the `Figure <label> — ` prefix stripped at staging so Quarto's native cross-reference numbering does not create duplicate numbers (`Figure 1.1: Figure 1.1 — …`).
   - Before stripping, `<label>` is validated against the exact expected displayed number (`{ch}.{fig}`). If `<label>` differs, the build fails with `BuildError: figure caption label '<label>' does not match expected number '<expected>'`. This prevents prose references from silently breaking if figure order drifts.
   - Table captions matching `^Table\s+(?P<label>[A-Za-z0-9.]+)\s*(?:[—–:]|-)\s*(?P<rest>.*)$` are stripped and validated under the same rule.
   - The canonical manuscript source in git remains untouched.

4. **Front Matter Table Labels Delta (Owner Confirmation)**:
   - In v3.0.0, front matter tables carried manual labels `Table 0.1` through `Table 0.7`.
   - In standard Quarto builds, unnumbered chapters receive per-chapter sequential numbers (`Table 1`, `Table 2`, `Table 3` in `introduction.qmd` and `Table 1`, `Table 2`, `Table 3`, `Table 4` in `solutions-architect-role.qmd`).
   - No prose references depend on front matter table labels (confirmed in Change 0048 inventory).

5. **Sample Book Regression (`handbook-sample-01`)**:
   - Built before and after change 0051 using `handbook-sample-01` at commit `8ed1b7035430ab3dc25fb65d712577bc197394ef`.
   - List of Figures:
     - Before: `Figure 1.1: The seven lifecycle states in order, from brief to retirement.`
     - After: `Figure 1.1: The seven lifecycle states in order, from brief to retirement.` (Identical)
   - List of Tables:
     - Before: `Table 1: Task-Based Reading Routes`, `Table 2.1: Illustrative brief for a fictional API handbook; names, targets and evidence are not real.`
     - After: `Table 1: Task-Based Reading Routes`, `Table 2.1: Illustrative brief for a fictional API handbook; names, targets and evidence are not real.` (Identical)
   - In DOCX, the appendices (which lack figures or tables) retain their unnumbered titles.

## Real Book Parity Proof (`Solutions-Architecture-Handbook`)

Full book build executed on scratch repository with front matter `{.unnumbered}` fixes and profile 1.1.0 across all 33 files.

### Comparison Command

```bash
python3 /tmp/verify_parity_full.py
```

### Command Output

```
HTML Figures: v3=121, new=121
HTML Figures 100% match: True

HTML Tables: v3=263, new=263
Chapter tables (172) match: True
Appendix tables (83) match: True

DOCX Figures: v3=285, new=285
DOCX Figures 100% match: True

DOCX Tables: v3=539, new=539
Body appendix captions (83) match: True
LoT Chapter and Appendix tables match: True

Front matter tables delta:
v3.0.0: ['Table 0.1', 'Table 0.2', 'Table 0.3', 'Table 0.4', 'Table 0.5', 'Table 0.6', 'Table 0.7']
New:    ['Table 1', 'Table 2', 'Table 3', 'Table 1', 'Table 2', 'Table 3', 'Table 4']
```

Across all 18 numbered chapters and 10 appendices (A–J):
- **121 figures** match v3.0.0 100% identically in sequence and numbering.
- **255 captioned tables** match v3.0.0 100% identically in sequence and numbering (`Table 1.1`–`Table 18.8`, `Table A.1`–`Table J.7`).
- The 1 back-matter table in `conclusions.qmd` is `Table 19.1` in the new build vs `Table BM.1` in v3.0.0 (no prose references exist).

## Test Suite and Verification

```bash
# Unit test suite (472 tests)
.venv/bin/python -m unittest discover -s tools/tests -v
Ran 472 tests in 286.491s
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
