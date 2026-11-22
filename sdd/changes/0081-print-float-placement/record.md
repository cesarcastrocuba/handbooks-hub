# Change 0081 — Floats fill the page: floating PDF figures and measured Word deferral

Implementer Claude; reviewer and merger a different agent (OpenCode 2). Branch
`feat/print-float-placement` from main `54475fc`. No version bump or tag: it ships with toolkit
`0.15.0`, whose tag needs the Owner's approval.

## Finding

The Owner checked the CI-built Solutions Architecture Handbook 6.0.0 preview DOCX (hub run
44948135399, book `main` `3c89a01`) in desktop Word on 2026-11-21:

- 1.1, 1.2, 1.3 and 2.16: a section heading and one short paragraph alone at the foot of a page, the
  rest of the section on the next page;
- callouts that "could have fitted" on the previous page, leaving a half-empty page;
- Figures 2.10, 2.13, 2.14, 2.15 and 2.16 moved to the next page although a slightly smaller figure
  would have fitted; the edition had grown to 712 pages in Word.

## Measurement

LibreOffice conversions with the toolkit fonts (the build's own font configuration; system fonts give
different page counts), measured by a script in the coordinator's scratchpad: a "gap page" is a page,
not the last of its chapter, whose content ends at least 25% of the text block above the bottom
margin; a "lonely heading" is a numbered heading among the last lines of such a page.

| Edition | Pages | Gap pages | Gap total (pages) | Lonely headings |
| --- | --- | --- | --- | --- |
| 5.0.0 release DOCX | 681 | 135 | 58.0 | 34 |
| 6.0.0 preview DOCX | 687 | 138 | 59.5 | 34 |
| 6.0.0 preview PDF (Typst) | 549 | 108 | 46.2 | 30 |

The defect predates the 6.0.0 reorder and affects both print editions.

## Cause

Every figure and every table that fits a page is kept unbreakable together with the heading and the
one short lead-in before it (changes `0061` and `0076`: the Typst `handbook-float-group`, the Word
`keepNext` chain). When the group does not fit the rest of the page, the whole group moves on and the
page stays part empty. The heading and the first paragraph of a section are not part of the chain, so
they stay alone at the foot. 73 of the 131 figures are taller than half the text block; the tallest
reach 83%.

## Alternatives measured (Word, LibreOffice pages)

| Variant | Pages | Gap total | Lonely headings |
| --- | --- | --- | --- |
| Height cap at 50% of the text block | 668 | 50.7 | 35 |
| Height cap at 45% | 660 | 46.9 | 35 |
| Heading and short intro chained with the float | 699 | 72.1 | 10 |
| Scale only the figures that nearly fit (at least 8 pt diagram text) | 680 | 55.3 | 32 |

A height cap is rejected: at 45%, 18 diagrams would print their 11 pt text below 7 pt. The heading
chain removes lonely headings but adds 12 pages of gaps. The Owner chose floating PDF figures, measured
deferral and bounded scaling in Word, and a redraw of the tallest diagrams in the book (book PR,
separate), with figures allowed to float past the next heading in the PDF.

## Fix

| File | Change |
| --- | --- |
| `render_data/typst/handbook-typst.typ` | Quarto figure floats and plain image figures float (`placement: auto`): top or bottom of the page, or of the next page, and the text after them fills the page. |
| `render_data/filters/float-leadins.lua` | Groups a heading and short lead-in only with tables; an image float is not grouped. A Figure or Div that holds a table is still a table. |
| `docx_figure_place.py` (new) | Word pass between the table measurement and the page-number probe (`build.py`). LibreOffice export with probe bookmarks; named-destination coordinates (`pdfinfo -dests`) and word boxes (`pdftotext -bbox`). For each figure or kept-whole data table whose group starts a page below a gap of at least 15%: move the following blocks of its section that fit (a plain paragraph of 30+ words that crosses the foot also moves); else scale a figure to fit, never below 75% of its natural raster size. Stops at headings, breaks and any other float; never separates a kept block. Actions of one pass are at least three pages apart; up to four passes. |
| `tests/test_figure_place.py` (new) | Units, decisions, application, destination parsing, missing tools, and a LibreOffice integration test. |
| `tests/test_table_fit.py` | The group test uses a table; figures are not grouped; the template floats a figure so the text after it stays on page 1. |
| `docs/publication-build.md`, `CHANGELOG.md` | Figure placement section; Unreleased entry. |

`build.tool_versions.docx_figure_placement` records the counts. A release build
(`--require-page-numbers`) fails if the measurement fails, as the page-number probe does.

## Evidence

The Word pass applied to the CI-built 6.0.0 preview DOCX (`3c89a01`), measured as above:

| Variant | Pages | Gap pages | Gap total | Lonely headings |
| --- | --- | --- | --- | --- |
| 6.0.0 preview (before) | 687 | 138 | 59.5 | 34 |
| Final pass: 18 figures scaled, 105 floats deferred (50 tables), 4 passes | 662 | 89 | 36.4 | 20 |

Typst with floating figures, full book build of `3c89a01` (experimental build in the scratchpad):
549 → 524 pages, gap total 46.2 → 24.7, lonely headings 30 → 14.

What remains: figures too tall for any gap (the book redraws the 16 that exceed 70% of the text
block), data tables that do not fit the gap and sections that end right after a float.

Checks: see the pull request for `make check`, `make full` and the edition-preview run on book `main`.

## Limits

- LibreOffice is the measuring engine; desktop Word paginates slightly differently (712 pages against
  687 for the 6.0.0 preview). The Owner's desktop Word check is the acceptance test.
- Four more LibreOffice exports of the whole book per Word build.
- A PDF figure may appear after the next heading or on the following page, as in typeset books.

## Review follow-up (after merge of PR 133)

The reviewer (OpenCode 2) approved PR 133 at `3f54598` with two Minor and two Optional findings, fixed
on `fix/float-placement-followups`:

- Minor: the Figure placement section in `docs/publication-build.md` split the preceding section; it
  now follows it.
- Minor: `_barrier` stopped at `Heading*` styles and explicit breaks but not at a paragraph that
  starts a page through `pageBreakBefore` (direct or inherited from its style through `basedOn`).
  `page_break_styles` reads `word/styles.xml`, and such a paragraph is now a barrier; two unit tests.
- Optional: the missing-tools test asserts `BuildError`; a new test makes the measurement fail and
  proves the document is byte-identical (`required=False`) and that a required build raises.
- Optional: the docs state that only blocks starting on the float's page are moved, as the code does.
