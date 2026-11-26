# Change 0060 — Appendices and Document Control (Owner review round 3)

Regression fix for the Owner findings on appendices and Document Control introduced by change `0051`.
Implemented by Agy until `b4d78f8`, then taken over by OpenCode after the review at that head: the
review's two Major findings (a standalone "Appendices" page in the PDF and a sidebar that nested
References inside Appendices) did not reproduce from the committed approach, which post-processed
rendered HTML with regular expressions. This revision fixes both structurally.

No version bump and no tag. `STATUS.md` and `docs/decisions.md` are not modified. Commits carry the
provenance trailer allowed by `HUB-DEC-025`.

## Scope

- **Hub base**: `39c524c` (`origin/main`, merge of PR 97 / change `0062`).
- **Branch / worktree**: `fix/0060-appendices-document-control`,
  `../handbooks-hub.worktrees/0060-appendices-document-control`.
- **Write set**:
  - `tools/src/handbook_toolkit/build.py`
  - `tools/src/handbook_toolkit/build_staging.py`
  - `tools/src/handbook_toolkit/print_layout.py`
  - `tools/src/handbook_toolkit/reading_site.py`
  - `tools/src/handbook_toolkit/render_data/filters/front-crossrefs.lua`
  - `tools/src/handbook_toolkit/render_data/typst/typst-show.typ`
  - `tools/src/handbook_toolkit/web_lists.py`
  - `tools/tests/test_appendices_document_control.py`
  - `tools/tests/test_numbering_parity.py`
  - `tools/tests/test_reading_site.py`
  - `sdd/changes/0060-appendices-document-control/record.md`
  - `CHANGELOG.md`

## Design

The previous attempt mixed three mechanisms that fought each other: native Quarto
`book.appendices`, a Typst `part()` override that compared content with a string, and a post-render
regular expression over Quarto's HTML. This revision uses one mechanism — the staged heading — and
lets every renderer print the same text.

1. **Literal labels in the staged heading (`build_staging._transform_chapter`).** For every appendix
   file the first level-1 heading becomes `# Appendix X — Title {.unnumbered}`: the old numeric or
   "Appendix X —" prefix is stripped and the letter comes from the reading-order position. The
   attribute is always kept (or added), other attributes such as `{#sec_…}` are preserved, and
   `.unnumbered` stops any renderer from adding a second number. This covers sources that already
   carry the label (sample, Solutions Architecture) and sources that do not.
2. **Literal section numbers (`_number_appendix_section`).** Because the level-1 heading is
   unnumbered, the renderer no longer numbers the sections under it. The staged headings therefore
   carry `A.1`, `A.1.1`, … themselves, computed per file, written only outside fenced code blocks
   and skipped for an authored `.unnumbered` section. HTML, PDF, DOCX and Markdown then agree.
3. **No native appendices in the print editions (`_render_config`).** `book.appendices` is never
   set and the appendices stay ordinary chapters in one flat list. Quarto's native part page — the
   page holding only "Appendices" — is gone at the source; no Typst suppression is involved and
   `typst-show.typ` returns to its original `part()`.
4. **Reading-site part (`reading_site.prepare_reading_site`).** The HTML configuration gets
   `{"part": "Appendices", "chapters": [...]}` holding only the appendices, with References and the
   analytic Index as top-level entries after it. This produces the sidebar, breadcrumb, previous/next
   links and search index from one structure; `_adjust_html_sidebar` and its HTML rewriting are
   removed.
5. **Appendix-aware float labels (`front-crossrefs.lua`, `web_lists.py`).** Appendix figure and table
   labels (`tbl-a-1`, `fig-f-1`) now render as `Table A.1` / `Figure F.1` in HTML and DOCX and in
   the generated list pages, matching the Typst show rules, because the labels no longer come from
   Quarto's appendix counter.
6. **Document Control (unchanged from `b4d78f8`, accepted by the review).** A book-owned
   `| Field | Value |` table is kept and its `Version` row is validated against the edition version
   (exact version, or `major.minor` for a final `x.y.0`); books without a table get the generated one.

## Verification

### 1. Focused unit tests

```
$ PYTHONPATH=tools/src:tools/tests .venv/bin/python -m unittest tools.tests.test_appendices_document_control -v
test_end_to_end_synthetic_book_with_appendices_and_document_control (tools.tests.test_appendices_document_control.AppendicesDocumentControlIntegrationTests.test_end_to_end_synthetic_book_with_appendices_and_document_control) ... ok
test_extract_document_control_version (tools.tests.test_appendices_document_control.AppendicesDocumentControlUnitTests.test_extract_document_control_version) ... ok
test_has_document_control_table (tools.tests.test_appendices_document_control.AppendicesDocumentControlUnitTests.test_has_document_control_table) ... ok
test_inject_document_control_preserves_existing_table_and_validates (tools.tests.test_appendices_document_control.AppendicesDocumentControlUnitTests.test_inject_document_control_preserves_existing_table_and_validates) ... ok
test_transform_chapter_appendix_l1_and_l2_formatting (tools.tests.test_appendices_document_control.AppendicesDocumentControlUnitTests.test_transform_chapter_appendix_l1_and_l2_formatting) ... ok
test_validate_document_control_version (tools.tests.test_appendices_document_control.AppendicesDocumentControlUnitTests.test_validate_document_control_version) ... ok

----------------------------------------------------------------------
Ran 6 tests in 23.784s

OK
```

The synthetic book asserts, from the built artifacts: literal `Appendix A — …` and `A.1 …` in the
HTML page and DOCX headings, an Appendices sidebar part that holds only the appendices, a References
breadcrumb without "Appendices", no page whose body text is only "Appendices", and no double space.
The unit test covers a source with and without `.unnumbered`, a colon instead of an em dash, an
authored section id, an unnumbered section, and `#` lines inside a fenced code block.

### 2. Hub checks

```
$ make full PYTHON=./.venv/bin/python
...
Ran 535 tests in 538.449s

OK (skipped=3)
site-check: 1 page(s), 3 asset(s), all 200
PYTHONPATH=tools/src ./.venv/bin/python -m handbook_toolkit --root . verify
repository files: OK
packaged schemas: OK
.../catalog/catalog.json: OK
.../profiles/standard/profile.yaml: OK
.../template/book/book.yaml: OK
VERIFY: 5 check(s), 0 problem(s)
PYTHONPATH=tools/src ./.venv/bin/python -m handbook_toolkit --root . verify --full
repository files: OK
packaged schemas: OK
documentation links: OK
documentation currency: OK
VERIFY (full): 7 check(s), 0 problem(s)
```

`make check` (the first half of the same target) ran the same 535 tests and the five-check
`verify`; the run above is the complete `make full`.

### 3. Sample book build

`handbook-sample-01` at `8ed1b7035430ab3dc25fb65d712577bc197394ef` (stable `0.5.2`, built as a
preview so the toolkit pin may differ):

```
$ PYTHONPATH=<worktree>/tools/src .venv/bin/python -m handbook_toolkit build-book \
    --repo /home/ubuntu/github/handbook-sample-01 --commit 8ed1b70... \
    --output /tmp/opencode/0060/sample --preview --version 0.6.0-preview --require-page-numbers
/tmp/opencode/0060/sample: OK
```

- PDF: 61 pages (`pdfinfo`), pages whose body text is only "Appendices": **none**.
- PDF Contents:
  `Appendix A — Brief and Outline Templates … 52`, `Appendix B — Gate and Review Checklists … 55`,
  `Appendix C — Glossary … 58`; section lines `A.1 Brief and Outline Template Library`,
  `A.2 …`, `A.3 …`.
- PDF bookmarks: `Appendix A — Brief and Outline Templates`, `Appendix B — …`, `Appendix C — …`.
- No double space after the dash in the PDF, the DOCX or the HTML.
- Reading site (`references.html`): the sidebar sections are `Front matter`, `Chapters` and
  `Appendices`; the Appendices section holds exactly the three appendix pages, References is a
  top-level item after it, and the References breadcrumb is `References`.
- The sidebar shape is identical to the published `v0.5.2` release (downloaded from the GitHub
  release and compared section by section).
- DOCX: headings and cached contents read `Appendix A — Brief and Outline Templates` and
  `A.1 Brief and Outline Template Library`.

### 4. Solutions Architecture Handbook build

`handbook-solutions-architecture` at `ba9e1df1c985a48d1b5dedb98e2b982101d03fbb`, version
`3.1.0-rc.1`, built with `--preview --require-page-numbers`:

- PDF: **512 pages** (513 before this change; the standalone Appendices page is gone).
  Pages whose body text is only "Appendices": **none** (previously page 417).
- PDF Contents: the ten literal entries `Appendix A — Worked Architecture Cases … 417` through
  `Appendix J — Pattern Catalog … 484`; the first appendix now starts on the page the part page
  used to occupy.
- PDF bookmarks: the ten `Appendix X — …` entries.
- Navigation parity, measured with the change `0053` audit script (adapted to this branch, with the
  annotation prefix corrected to `u:Section` so rows wrapped across lines are classified like the
  rest):

```
index: section_links 3497, glossary_links 466, glossary_pointers 493, word_rows_protected 529
html: generated 6182, internal fragments 7570, broken []
docx: internal hyperlinks 7183, navigation 6182, broken [], missing registered bookmarks []
pdf: internal link annotations 6886, named destinations 621, broken []
     index first page 492, index section annotations 3499, index glossary annotations 466
NAVIGATION_OK
```

The Index text is identical to the build of `39c524c` (only the footer page numbers move by one,
because the part page is gone). The one fewer PDF link annotation is the removed Contents line for
the "Appendices" part itself.

### 5. CI edition-preview artifacts

Run `44134889854` on head `ac880f9`: every job passed, including the three edition previews. The
sample (`8ed1b70`) and Solutions Architecture (`d9eca79`) artifacts were downloaded and re-checked:

```
$ gh run download 44134889854 -n edition-preview-sample -D ci-sample
$ gh run download 44134889854 -n edition-preview-solutions-architecture -D ci-sa
== sample: 61 pages; standalone Appendices pages: []
   sections: [('Front matter', 4), ('Chapters', 8), ('Appendices', 3)]
   appendices items: ['Appendix A — Brief and Outline Templates',
                      'Appendix B — Gate and Review Checklists',
                      'Appendix C — Glossary']
   references in appendices part: False
   references breadcrumb: ['References']
   double space: False
== sa: 512 pages; standalone Appendices pages: []
   sections: [('Front matter', 5), ('Chapters', 18), ('Appendices', 10)]
   references in appendices part: False
   references breadcrumb: ['References']
   top level after appendices: ['Appendix J — Pattern Catalog', 'References', 'Index']
   double space: False
```

- Sample PDF Contents: `Appendix A — … 52`, `Appendix B — … 55`, `Appendix C — … 58`; the outline
  lists the three literal appendix titles (84 outline entries); no double space.
- The sample sidebar sections are identical to the published `v0.5.2` HTML (section titles and
  entries compared item by item).
- The `0053` audit on the CI Solutions Architecture artifact returns the same numbers as the local
  build: Index 529 rows and 3 497 location links, 466 glossary links, 493 glossary pointers, DOCX
  0 missing bookmarks, and no broken HTML fragment, DOCX anchor or PDF annotation.
