# Change 0060 — Appendices and Document Control (Owner Review Round 3)

Regression fix addressing Owner review findings on appendices and Document Control from change 0051.

No version bump or tag is created here. Commits carry the required provenance trailer.
Neither `STATUS.md` nor `docs/decisions.md` is modified.

## Pins and Scope

- **Hub Base**: `4773684` (`origin/main`, merge of template 1.8.0 release PR #95).
- **Branch / Worktree**: `fix/0060-appendices-document-control`, `/home/ubuntu/github/handbooks-hub.worktrees/0060-appendices-document-control`.
- **Write set**:
  - `tools/src/handbook_toolkit/print_layout.py`
  - `tools/src/handbook_toolkit/build.py`
  - `tools/src/handbook_toolkit/build_staging.py`
  - `tools/src/handbook_toolkit/reading_site.py`
  - `tools/src/handbook_toolkit/render_data/typst/typst-show.typ`
  - `tools/src/handbook_toolkit/render_data/typst/handbook-typst.typ`
  - `tools/tests/test_appendices_document_control.py`
  - `sdd/changes/0060-appendices-document-control/record.md`
  - `CHANGELOG.md`

## Problem & Root Causes

1. **PDF Standalone Appendices Page**: Quarto native `book.appendices` in `_render_config` emitted a part page holding only "Appendices". Fixed by suppressing the part page in `typst-show.typ` (`#let part(title) = if title != "Appendices" { heading(level: 1, numbering: none)[#title] }`).
2. **Appendix L1 Headings in PDF**: Appendix L1 headings read "A. Title" instead of literal "Appendix A — Title". Fixed by updating Typst `handbook-numbering` so that for level 1 appendix headings (`parts.len() == 1 and ch >= app-start`), it renders `"Appendix " + numbering("A", app-idx) + " — "`.
3. **HTML Sidebar Nesting**: References (and Index) were nested inside "Appendices" because `reading_site.py` appended references to `bc["appendices"]`, and `build.py` appended the Index to `appendices`. Fixed by keeping Quarto's native crossref numbering for `appendices`, and post-processing the generated HTML files in `_adjust_html_sidebar` to unnest `references` and `analytic-index` into top-level sidebar items directly following the Appendices section.
4. **Sample DOCX Missing "Appendix A —"**: The sample book source uses `{.unnumbered}` on appendix headings. Fixed in `_transform_chapter` by stripping `.unnumbered` during staging so Quarto and Pandoc apply standard appendix numbering across HTML, PDF, and DOCX without double-prefixing. In Markdown edition (`strip_heading_numbers=False`), literal "Appendix X — Title" is preserved.
5. **Document Control Validation**: When a book already provides its own `# Document Control` table (such as the Solutions Architecture Handbook), the toolkit leaves the table untouched and validates that the `Version` row contains the edition version (or `major.minor` for final `x.y.0`). Books without their own table (sample, template) continue having the table injected.

## Verification Evidence

### 1. Focused Unit Tests (6/6 Passed)

```bash
PYTHONPATH=tools/src:tools/tests .venv/bin/python -m unittest test_appendices_document_control -v
```

Output:
```
test_end_to_end_synthetic_book_with_appendices_and_document_control (test_appendices_document_control.AppendicesDocumentControlIntegrationTests.test_end_to_end_synthetic_book_with_appendices_and_document_control) ... ok
test_extract_document_control_version (test_appendices_document_control.AppendicesDocumentControlUnitTests.test_extract_document_control_version) ... ok
test_has_document_control_table (test_appendices_document_control.AppendicesDocumentControlUnitTests.test_has_document_control_table) ... ok
test_inject_document_control_preserves_existing_table_and_validates (test_appendices_document_control.AppendicesDocumentControlUnitTests.test_inject_document_control_preserves_existing_table_and_validates) ... ok
test_transform_chapter_appendix_l1_and_l2_formatting (test_appendices_document_control.AppendicesDocumentControlUnitTests.test_transform_chapter_appendix_l1_and_l2_formatting) ... ok
test_validate_document_control_version (test_appendices_document_control.AppendicesDocumentControlUnitTests.test_validate_document_control_version) ... ok

----------------------------------------------------------------------
Ran 6 tests in 23.884s

OK
```

### 2. Full Test Suite & Repository Validators

```bash
make full PYTHON=.venv/bin/python
```

Output:
```
----------------------------------------------------------------------
Ran 529 tests in 479.642s

OK (skipped=3)
PYTHONPATH=tools/src .venv/bin/python -m handbook_toolkit --root . verify
repository files: OK
packaged schemas: OK
/home/ubuntu/github/handbooks-hub.worktrees/0060-appendices-document-control/catalog/catalog.json: OK
/home/ubuntu/github/handbooks-hub.worktrees/0060-appendices-document-control/profiles/standard/profile.yaml: OK
/home/ubuntu/github/handbooks-hub.worktrees/0060-appendices-document-control/template/book/book.yaml: OK
VERIFY: 5 check(s), 0 problem(s)
PYTHONPATH=tools/src .venv/bin/python -m handbook_toolkit --root . verify --full
repository files: OK
packaged schemas: OK
/home/ubuntu/github/handbooks-hub.worktrees/0060-appendices-document-control/catalog/catalog.json: OK
/home/ubuntu/github/handbooks-hub.worktrees/0060-appendices-document-control/profiles/standard/profile.yaml: OK
/home/ubuntu/github/handbooks-hub.worktrees/0060-appendices-document-control/template/book/book.yaml: OK
documentation links: OK
documentation currency: OK
VERIFY (full): 7 check(s), 0 problem(s)
```

### 3. Real Book Build: Solutions Architecture Handbook

Built commit `ba9e1df1c985a48d1b5dedb98e2b982101d03fbb` via:
```bash
handbook-toolkit build-book --repo /home/ubuntu/github/handbook-solutions-architecture --commit ba9e1df1c985a48d1b5dedb98e2b982101d03fbb --output /tmp/sa-0060-dist-final --mode chapter --require-page-numbers
```

Command result:
- Exit code: 0
- Version: `3.1.0-rc.1`
- Epoch: `1794853569`
- Payload files and sizes:
  - `SHA256SUMS.txt`: 479 bytes
  - `book-html.zip`: 14,093,836 bytes
  - `book-source.zip`: 16,235,065 bytes
  - `book.docx`: 12,460,774 bytes
  - `book.md`: 1,556,060 bytes
  - `book.pdf`: 24,352,539 bytes
  - `publication-manifest.json`: 1,895 bytes

Parity and quality checks:
- **PDF Standalone page**: 0 standalone "Appendices" pages found (`pdftotext` search yields `[]`).
- **PDF Contents & Bookmarks**: Contents lists literal `Appendix A — Worked Architecture Cases . . . . . 418`.
- **HTML Sidebar**: Appendices section contains only Appendices A through J (`appendix-a-worked-architecture-cases.html` through `appendix-j-pattern-catalog.html`). References (`references.html`) and Index (`analytic-index.html`) are top-level navigation items directly after Appendices.
- **HTML Index**: Exactly 529 table rows (1 header + 528 data rows), 3,497 location links, 466 term links.
- **DOCX**: 0 missing bookmarks (`Missing bookmarks in DOCX: 0`). Headings and TOC show literal `Appendix A — Worked Architecture Cases`.
- **Document Control**: 3 book-owned tables preserved in `document-control.html`; no redundant table injected.

### 4. Sample Book Build: `handbook-sample-01`

Built commit `8ed1b7035430ab3dc25fb65d712577bc197394ef` via:
```bash
python tools/scripts/edition_preview.py --repo /home/ubuntu/github/handbook-sample-01 --output /tmp/sample-0060-dist
```

Command result:
- Exit code: 0
- Version: `0.5.2-preview`
- Sample DOCX: Displays literal `Appendix A — Brief and Outline Templates`, `Appendix B — Gate and Review Checklists`, `Appendix C — Glossary`.
- Sample PDF: 0 standalone "Appendices" pages found (`[]`). Contents lists `Appendix A`, `Appendix B`, `Appendix C`.
- Sample Document Control: Book has no owned table; toolkit successfully injected standard Document Control table into `title.html`.
