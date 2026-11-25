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

The reviewer measured the guard on the 6.0.0 preview DOCX: `page_break_styles` returns `Heading1`
and `TOCHeading`, `figure_units` finds 407 units with and without it, and no unit changes its blocks
or stop. It protects other books and templates; it does not change the current edition.

## Second follow-up (after merge of PR 134)

- The Owner's Figure 2.15 case: a Common Pitfall callout follows the figure and is the last block on
  its page. The deferral measured a block only up to the next block on the same page, so a callout
  that ends the page was never a candidate. A block that cannot break across pages (a one-row callout
  with `cantSplit`, a kept-whole table, a `keepLines` paragraph) is now measured to the end of the
  page's text. Applied to the CI-built DOCX of PR 134 (book `a32a840`): 655 → 654 pages, gap total
  33.5 → 32.4.
- Review follow-up of PR 134: the docs bullet is re-worded and re-flowed; the `basedOn` walk is
  iterative (no recursion limit, cycles stop); tests for cycles, a 3,000-link chain, missing
  `styles.xml` and a direct `pageBreakBefore w:val="0"` that overrides a page-starting style.

Remaining cases need an Owner decision, not a rule: Figures 1.2, 1.3 and 2.15 print at their natural
size (0.45, 0.53 and 0.58 of the text block) and fit the gap in front of them only below 75% of it
(Figure 2.15: 0.69, text 7.6 pt); the alternative, leaving the heading and its lead-in at the foot of
the previous page, is what the Owner rejected.

## Third follow-up (Owner's Word check of the PR 135 preview)

The Owner found a figure between a Common Pitfall and its Decision & Trade-off (chapter 2, pages
79, 81, 84, 87, 89 and 93; chapter 3 too), and Common Pitfall callouts that start a page although
the previous page has room (pages 53, 64 and 67).

- Cause of the split pairs: the deferral moved the figure past the pitfall and stopped in front of
  the decision. It treated the decision as kept with the next block because `_bound` read the
  `keepNext` rows of the options table nested in the callout. Counted by re-running the PR 135
  placement on the CI pre-placement DOCX of book `a32a840` with the toolkit fonts: 19 sections
  with a figure between the two callouts (chapters 2, 3, 8, 9, 10, 19); the Typst PDF had 5 (a float at the top of the page after the pitfall). The published preview DOCX
  of PR 135 shows 3 by the same body-order detector (2.1, 2.2, 2.9; reviewer's count). The two
  counts come from different DOCX files and the difference is not explained yet; both are 0 after
  this change.
- Pitfalls at the top of a page (LibreOffice rendering of the same DOCX): in most cases the box
  does not fit the space left on the previous page; the closest misses are 3 to 5 pt (pages 53 and
  90 of the new rendering). Page 76 had a 43% gap after the pair fix alone, because the figure could
  no longer pass the pitfall.
- Fix (Word): `callout_runs` marks a run of callouts (a callout followed by another, only empty
  spacers between); a float never lands inside it. When the run's first callout fits the gap and the
  rest of the run fits the next page with the float, the float moves after the whole run: the
  pitfall fills the gap and the decision starts the next page. `_bound` reads only the paragraphs of
  the last row's cells, so a nested table does not hold its callout.
- Fix (PDF): the float-leadins filter puts `#place.flush()` in front of a run of callouts, so a
  figure still pending there is placed before the run, and scopes `placement: top` to a figure
  whose section ends in a run. With the flush alone one pair stayed split (page 60: Figure 2.5
  floated to the foot of the page below the pitfall and the decision started page 61; 524 pages,
  gap total 27.8). Adding `placement: top` for the section's figure fixed page 60 and left one
  other split: page 103, where Figure 4.4 (of the next section, whose section also ends in a run)
  floats to the top of the page above the 4.3 decision that starts it (524 pages, gap total 27.8).
  Tried and reverted: choosing each figure's placement in `context` from markers of broken runs.
  It handled all three cases in a unit test, but wrapping the figures in `context` broke their
  numbering in the book (captions in chapter 4 read "Figure 19.3" and "19.0"). Typst cannot keep a
  top float from rising above earlier text on its page, so this last case stays open. Measured
  first, and rejected:
  `#block(sticky: true)` on the first callout of a run. It also removed the split pairs (5 → 0), but
  it moved a pitfall to the next page whenever its decision could not start on the same page:
  520 → 529 pages, gap total 24.8 → 36.3, 27 gap pages followed by a page that starts with a
  pitfall (the Owner's second complaint).

Word measurement (LibreOffice with the toolkit fonts, CI pre-placement DOCX of book `a32a840`):

| Run | Pages | Gap total (pages) | Lonely headings | Pitfall/decision split by a float |
| --- | ---: | ---: | ---: | ---: |
| PR 135 | 655 | 33.6 | 18 | 19 |
| Runs never split | 655 | 33.7 | 18 | 0 |
| + float after the run, no fit check | 655 | 35.4 | 19 | 0 |
| + fit check (this change) | 655 | 33.5 | 18 | 0 |

Without the fit check the float moved after the decision even when both no longer fit the next
page, which left that page part empty (page 124: 66%). With it, 3 sections move the float after the
run (2.1, 2.2, 2.9) and no page gets worse.

- Review follow-up of PR 136 (`4fb6887`): `test_numbering_parity` ends the listing slice at the
  page before the first body caption, so `make check` is green with Quarto (632 tests); a
  LibreOffice test fails when `_place` stops passing the callout runs; `decide()` folds the runs
  into `bound`; a full lookahead followed by a barrier counts as complete; `CALLOUT_STYLE` lives in
  `docx_post`; the changelog scopes the guarantee to Word. CI coverage of the Quarto tests is
  issue 137. Re-review at `f6bb5c7`: clean.

## Fourth follow-up (Owner's Word check of the PR 136 preview)

The Owner found figures and tables far from the paragraph that cites them. In chapter 3, from
Figure 3.4 on, the figure no longer follows its description. Measured on the preview DOCX against
a build without placement (LibreOffice with the toolkit fonts):

- 59 of 131 figures and 53 of 278 tables were moved after the text that followed them;
- figures not right after the paragraph that cites them went from 3 to 52.

The manuscript order was intact. The Word deferral pass alone caused the movement.

- Owner decision (2026-11-22): in Word nothing moves. A figure away from its description is a
  defect; a part-empty page is not. Tall diagrams that leave a gap are redrawn in the book.
- Change: `docx_figure_place` keeps only the bounded scaling. A figure group that starts a page
  below a gap of at least 15% of the text block is scaled to fit the gap when the result keeps at
  least 75% of its natural raster size. Tables are never scaled. Removed: the deferral, the
  callout-run rule, the lookahead blocks and table units.
- The build report reads `N figures scaled to fit page gaps; no figure or table moved (P
  LibreOffice passes)`.
- Tests:
  - two LibreOffice tests check that a figure that does not fit leaves the body order unchanged,
    and that a figure that nearly fits is scaled in place;
  - the unit tests cover the scale bound, the gap threshold and the caption measurement.
- The PDF keeps its floats (Typst places a figure at the top or bottom of the page). The Owner has
  not asked for the Word rule there.
- Gaps and lonely headings in Word return towards the pre-0081 numbers. The CI preview of this
  commit is the measurement; the Owner's Word check remains the acceptance test.

## Fifth follow-up (Owner check of the `e3c9e9e` preview, 2026-11-23)

The Owner found three problems:
- **Word.** A Common Pitfall or a Decision & Trade-off starts a new page and leaves a large gap on
  the page before (1.1.5, 1.2.13, 1.3.2, 2.1, 2.6, 2.13, 2.14, 6.2.3, 7.3.4, 8.1, 8.2.6). It
  had shown up in several editions.
- **PDF.** Figures are away from their description: Figure 1.4 is not right after 1.4, and the
  same goes for Figures 2.1, 2.2 and others.
- **HTML light theme (Chrome, Edge).** A figure shows white and then cream as it scrolls in.

Causes, measured on the preview:
- **Word.** Every callout was a one-row table marked `cantSplit`, and the table inside a
  decision got `keepNext` on every row from the table measurement. A callout that did not fit
  whole moved to the next page. On the LibreOffice render of the DOCX (audit script
  `/home/ubuntu/ch7-recovery/audit/layout_audit.py`), 9 pitfalls and 39 decisions open a page
  after a gap of at least 60 pt (25 of those gaps are at least 120 pt).
- **PDF.** `placement: auto` floats. Measured: 40 of 131 figures sit away from the text that
  cites them, either above it or more than 14 lines after it. In Word the count is 0. The PDF
  callout was unbreakable too; only the floats around it hid its gaps.
- **HTML.** The scroll reveal animates `opacity` on `main figure`. A translucent figure isolates
  its raster, so the `mix-blend-mode: multiply` met a transparent backdrop instead of the canvas.
  Reproduced in Playwright Chromium 148: the pixel is (254, 254, 253) mid-reveal against the
  canvas (246, 241, 231).

Owner decisions (2026-11-23):
- Callouts may be split, so that at least the pitfall fills the page before.
- The PDF uses the Word rule.
- Redrawing the tall diagrams moves to a later edition.

Change:
- **Word.**
  - The callout row is breakable, and its title has `keepNext`.
  - `keep_callout_tables` keeps each inner row whole and the header row with the first data row.
  - The table measurement and the lead-in chain skip callout tables.
  - `decide()` no longer returns the 0.01 pt no-op `Shrink(1.0)` (review Minor 1); new cases
    cover the `need >= figure_height` and image-page bounds (Minor 2).
  - The report reads `figures scaled to fit page gaps: N`.
- **PDF.**
  - `placement: auto` is removed, along with the `place.flush` and `placement: top` filter rules.
  - Every figure goes through `handbook-figure-group` with its heading and lead-in.
  - The group measures the room after the text before it, from a zero-height marker block that
    records its own position in a state. A bare metadata tag travels to the next page with the
    group. A `query` for a labelled marker kept the table measurement of
    `test_tables_figures_build` from converging ("a measured element did not stabilize"); the
    state does not. It then applies the Word
    rule: a gap of at least 15% of the body, and at least 75% of the natural size, read from the
    PNG's pixel density through an image opener passed from the document.
  - The callout block is breakable, its title is `sticky`, and a table inside it breaks between
    rows (`handbook-in-callout`).
- **HTML.** In the light theme, a figure holding a raster gets the canvas background, so the
  multiply blends with the cream even while the figure is translucent. A figure inside a callout
  keeps the tint.

Tests:
- `test_docx_callouts.py`: the box row breaks and the title keeps with the next line; inner rows
  break only between rows; text before a callout is not chained to it; a LibreOffice case where
  a pitfall starts in the gap in front of it.
- `test_table_fit.py`:
  - the filter groups every figure;
  - four Typst cases: a figure that nearly fits is scaled and stays; a gap too small, or a
    figure already at 0.78 of its natural size, moves unscaled; a figure that fits is untouched;
  - a table inside a callout breaks between rows.
- `test_reading_site.py`: the pixel is sampled with the reveal frozen at half.
- Mutations fail the new tests: `cantSplit` back on the box row, the callout state removed, the
  floor at 0.1, the CSS rule removed. The five tests of the removed float rules are deleted.

### Measured on the CI preview of `600fb9e` (book `1dee3a4`)

- **PDF:** 549 pages. Figures away from their citing text: 40 → 4 (8.2, 15.3, 18.3, 19.3).
  All four follow the manuscript order: 8.2, 18.3 and 19.3 come before the sentence that cites
  them, and in 15.3 a table sits between the citation and the figure. None was moved by placement. Pitfalls and decisions opening a page after a gap: 0.
- **Word (LibreOffice render):** decisions opening a page after a gap rose from 39 to 54. With a
  single breakable row, LibreOffice moved the whole decision to the next page whenever a keep
  chain followed it, for example the 1.2 heading, its lead-in and Figure 1.2 after the 1.1.5
  decision. On a slice of the real DOCX that starts at the 1.1.5 pitfall:
  - `cantSplit` keeps the decision on the pitfall's page;
  - a breakable single row moves it;
  - removing the chain after it keeps it;
  - removing the spacer `keepNext`, every `keepNext` inside the box, or the inner `cantSplit`
    and `tblHeader` does not help.

  A synthetic document did not reproduce the drag, so no LibreOffice test pins it.
- **Fix:** one row per block. Applied to the whole preview DOCX and re-rendered: 0 pitfalls and
  0 decisions open a page after a gap of 60 pt or more (was 9 and 39 in the `e3c9e9e` preview),
  no callout title is alone at a page foot, 0 figures are away from their citing text, and the
  page count falls from 699 to 690.

## Sixth follow-up (Owner Word check of the `6c5d0ec` preview, 2026-11-23)

The Owner rejected split callouts. Decision & Trade-off boxes split in 1.1.5, 1.2.13, 2.1, 2.3,
2.8, 2.10, 2.11, 2.13, 3.1, 3.2, 4.1.2, 4.9, 5.3.5, 6.2.3, 7.2.2, 7.3.4, 7.5.4, 8.1, 8.2.6, 8.3.5,
10.3.2, 11.2.2, 11.3.5, 11.6.5, 12.2.3 and 12.3.4. Pitfalls split in 5.1.3 (two boxes split),
7.6 and 11.6.6. Review checklists split in 2.16, 6.4, 7.7 and 8.5.

Owner decision: every box stays whole. A pitfall and its decision need not share a page, so the
pitfall can end the page before. Figures may also be printed a little smaller.

Change:
- Word and Typst callouts are back to one unbreakable box (`cantSplit` row,
  `breakable: false`); the code is as in `e3c9e9e`. `keep_callout_tables` and
  `handbook-in-callout` are removed.
- **New print scale of 85%.**
  - Word `print_scale` runs before the measured gap passes; PDF `handbook-scale-images` does the
    same.
  - The 75% natural floor applies, so on the book 104 of 131 figures take the full 85%, and the
    other 27 stop at the floor.
  - A gap fit that would cross the floor is not applied in either edition.
- Tests:
  - boxes are one `cantSplit` row;
  - in LibreOffice a box that does not fit moves whole, and a pitfall that fits stays when its
    decision moves;
  - `print_scale`: the full factor and the floor;
  - four Typst cases with the print scale;
  - the Typst callout is not breakable.

## Seventh follow-up (Owner Word check of the `2129405` preview, 2026-11-25)

Boxes are now whole, but in desktop Word the pitfall still moves to the next page with its
decision and leaves a large gap. The Owner's examples are 1.1.5 (pages 55–56), 1.2.13 (pages
67–68) and 1.3.2 (page 69).

Cause, found in the DOCX:
- The callout title styles (`CalloutWarningTitle`, `CalloutImportantTitle` and the others) carry
  `keepNext`.
- Desktop Word keeps a table row with what follows when a paragraph in the row keeps with next.
- The two spacer paragraphs between a pitfall and its decision also keep with next (121 of 123
  pitfalls).
- So every pitfall was chained to its decision, and moved with it whenever the decision did not
  fit.
- LibreOffice ignores paragraph keeps inside a table, so its render, which all earlier evidence
  used, never showed the chain. This explains why the defect came back in every edition.

Fix: `docx_tables.release_callout_keeps` sets an explicit `w:keepNext w:val="0"` on every
paragraph inside a `CalloutBox`. It is the last step of `keep_fitting_tables`, after `keep_rows`,
and the explicit value overrides the style. The box is one unsplittable row, so its title can
still never be left alone. The spacers before the decision keep their keep-with-next and move
with the decision.

Verification limit: no LibreOffice measurement can show this. The evidence is structural: no
paragraph inside a box keeps with next, and that is checked on the built DOCX. Desktop Word is
the acceptance test.
