# Change 0076 — Word floats without Quarto's layout table; section introductions keep with the next heading

Implementer Claude; reviewer and merger OpenCode 2. Branch `fix/0076-docx-float-unwrap` from main
`f9e5eb1` (after change `0075`). No version bump; it ships with the next toolkit release.

## Finding

The Owner checked the CI-built Solutions Architecture Handbook 4.0.0 DOCX (hub PR 120, run
44694058714) in desktop Word on 2026-11-20:

- B.10 and B.12: heading and short description at the foot of a page, table on the next page;
- H.10, I.9, J.4 and J.6: only the heading at the foot of a page;
- 9.2.1 and others: Table 9.3 (and Table 9.8) moved to the next page although it would fit below
  *What it includes*;
- 9.3: the section heading and its two-sentence introduction at the foot of page 306, with 9.3.1 on
  the next page.

The LibreOffice rendering of the same DOCX keeps every one of these together (pages 571, 572, 629,
640, 649, 650 and 288), so the toolkit's LibreOffice probes could not see the defect.

## Cause

Quarto writes every captioned table and figure into a one-row, one-cell layout table that holds the
data table or the image paragraph and the caption (`ImageCaption`). In the SA DOCX there were 412 such
wrappers (280 tables, 132 figures), all at body level. Change `0061` kept headings and lead-ins with
the float (`keepNext`) and guarded the wrapper row with `cantSplit`, which LibreOffice honours across
the table boundary. Desktop Word did not carry the keep-with-next into the wrapper.

v3.0.0, which the Owner had accepted in Word, wrote plain body-level tables with the caption moved
below them (`scripts/docx_postprocess.py:move_table_captions`, read-only reference at `13d295b`).

## Owner experiment

Before changing the toolkit, the CI-built DOCX was post-processed with the same unwrap step only
(`unwrap_floats.py` in the coordinator's scratchpad; 280 table and 132 figure wrappers replaced by
their content, nothing else changed) and given to the Owner. The Owner checked it in desktop Word on
2026-11-20: "Si salen bien" for B.10, B.12, H.10, I.9, J.4, J.6 and Tables 9.3 and 9.8, and reported
9.3 as the remaining case.

## Fix

`docx_tables.keep_fitting_tables` now runs, before the existing keep logic:

1. `unwrap_float_layouts`: a body-level one-cell table whose cell holds exactly one caption
   (`ImageCaption`/`TableCaption`) and exactly one data table or image paragraph is replaced by its
   content in place, bookmarks included. A figure's image paragraph keeps with the caption after it.
   Callouts (no caption in the cell) are left alone. The existing keep chain then works on plain
   tables: `cantSplit` and `keepNext` on rows of fitting tables, the final row with its caption, and
   headings and one short introduction with the float.
2. `keep_section_intros`: a paragraph between two headings that is at most 80 words and 600
   characters (the limits of a float lead-in) keeps with the next heading, so a section heading and
   its introduction move to the next page only when they would otherwise be left alone. Headings
   already keep with the next paragraph through their styles.

The manifest's `tool_versions` reports both counts (`docx_float_layouts`, `docx_section_intros`).
PDF and HTML are unchanged.

## Evidence

Book `handbook-solutions-architecture` `main` `f1cf3c0` (4.0.0 content with book PR 21), built locally
with this branch (venv with `./tools`, Quarto 1.11.9) by `make build`: exit 0.

| Measure | Before (CI run 44694058714) | This branch |
| --- | --- | --- |
| Float layout tables in the DOCX | 412 | 0 (280 table and 132 figure wrappers unwrapped) |
| Captions at body level | 0 | 412 |
| Page-sized tables kept together (LibreOffice probe) | 399/405 | 400/405 |
| Heading/lead-in paragraphs kept with floats | 672 | 672 |
| Section introductions kept with the next heading | — | 67 |
| PDF pages | 552 | 552 |
| LibreOffice rendering: pages ending in a heading and at most one line | 3 (58, 64, 364) | 0 |
| LibreOffice rendering: B.10, H.10, I.9, J.4, J.6, 9.3 with their table or subsection | same page | same page |

The four links of change `0075` are present in the HTML and no explicit cue other than table column
headers remains unlinked.

LibreOffice is not a Word oracle. The Owner's desktop Word check of the CI-built DOCX of this pull
request decides acceptance.

## Tests

`test_table_fit.FloatLayoutTests`: a table wrapper and a figure wrapper are unwrapped in place with
their bookmarks, the caption follows the data table and is found by `candidates`, the image keeps
with its caption, the heading reaches the table and the table's caption does not chain onward; a
callout stays wrapped; a short section introduction keeps with the next heading and a long one does
not.
`test_template.test_copied_template_builds_seven_verified_payloads` asserted the old structure (the
template's one figure inside a layout table). It now asserts that no table holds a drawing, that the
image paragraph is a body block that keeps with the `ImageCaption` paragraph after it, and that the
caption is not bold.

| Command | Result |
| --- | --- |
| `make full` (venv from `requirements-dev.txt`), first run | 1 failure: the template test above, which pinned the wrapper |
| `make full` after updating that test | 593 tests OK (5 skipped); `VERIFY (full): 7 check(s), 0 problem(s)` |
| `make build` of the SA book `f1cf3c0` with this branch | exit 0; counts in the table above |
