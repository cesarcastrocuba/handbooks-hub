# Change 0086 — Close the 0081 follow-ups (hub issue 138)

Implementer: an AI agent, role Implementer (`AGENTS.md`). Branch `test/0081-followups` from
`main` `9649ba7`. Reviewer and merger: a different agent. No version bump or tag: the change is
test and documentation hardening plus two small behaviour edges; it ships in the next toolkit
release, whose tag needs the Owner's approval.

Issue 138 collects the test and documentation gaps left by the PR 136 and PR 139 reviews of change
`0081`. This record lists every item and its outcome. Nothing here changes the approved 6.0.0
artifacts: the Solutions Architecture Handbook figures are all PNG, and the two Word report counts
change but no page position does.

## Outcome summary

| # | Item | Outcome |
| --- | --- | --- |
| 1 | 15% gap threshold has no failing test in either edition (`MIN_GAP`, `handbook-min-gap`) | Fixed and tested: Word `decide` boundary case and a Typst `handbook-gap-admits` assertion; a parity test keeps both constants equal. |
| 2 | PDF 10 pt safety margin has no failing test (`handbook-gap-safety`) | Fixed and tested: `handbook-gap-fit` returns 0.8 for a 105 pt group, 95 pt room and a 100 pt figure; setting the margin to 0 makes the assertion fail. |
| 3 | "A group taller than a page is not wrapped" has no failing test | Tested: a tall figure plus lead-in compiles, the lead-in stays on the earlier page, and no overflow is reported. Mutating the guard to `if true` moves the lead-in and fails the test. |
| 4 | Nothing pins that the Word print scale runs before the gap pass | Tested: one LibreOffice case that fits at 85% but would be gap-scaled at 100% reports `figures at print scale: 1; figures scaled to fit page gaps: 0`. Moving `print_scale` after the pass fails the extent assertion. |
| 5 | The normal (measured) path of `keep_fitting_tables` has no callout keep-release test | Tested: a LibreOffice measured run on a package with a callout and a page-sized data table. The report says one box released, and every box paragraph, including a nested data table's header row, is `w:val="0"`. |
| 6 | Word and Typst constants are not compared by a test | Tested: `ConstantParityTests` reads `table-fit.typ` and compares `PRINT_SCALE`, `MIN_GAP`, `MIN_NATURAL` and `SAFETY`. |
| 7 | The HTML canvas rule's `.callout` exclusion is not exercised | Tested: the Playwright pixel fixture now has a figure inside `.callout-warning`; the light-theme pixel is the callout tint. Removing the two `:not(.callout …)` guards makes it the canvas and fails the test. |
| 8 | The checklist-colour test only asserts source order and is needlessly skipped | Fixed: the skip is removed (the test only reads the template), and a new compile test renders the real template with "Architecture Review Checklist — Decisions" and finds the checklist tint, not the important tint. |
| 9 | `print_scale` can count a factor that rounds to 1.0 as scaled | Fixed and tested in Word: the factor is rounded first and a 1.0 no-op is not counted. The PDF applies the same rounded factor (`handbook-print-factor`), with an assertion for the 0.99999 band. |
| 10 | The `docx_float_leadins` count includes keeps that `release_callout_keeps` later clears inside a box | Fixed and tested: `keep_leadins` skips any container inside a callout box, so the count no longer includes a keep that is later released. |
| 11 | `docs/publication-build.md` does not mention that nothing before a callout box keeps with next | Fixed: the Callouts bullets now say `keep_leadins` treats a box as text, not a float. |
| 12 | No body-order test for `_wrap_callout_box` | Tested: the box lands at the callout's position (`BEFORE, spacer, box, spacer, AFTER`) and its content order is preserved. |
| 13 | The Typst callout test only greps `breakable: false` and is needlessly skipped | Fixed: the source assertion no longer skips, and `test_a_long_callout_stays_whole` compiles the real template with a long callout and asserts its first and last lines share a page. Setting `breakable: true` fails it. `test_a_checklist_on_decisions_prints_the_checklist_tint` adds the second real compile. |
| 14 | The release fixture is not schema-ordered and does not exercise a keep inherited from a style | Fixed: the measured-path fixture ships a `word/styles.xml` whose `CalloutWarningTitle` style carries `keepNext`, and its `w:pPr` children are in schema order. The title has no direct keep before the run. |
| 15 | PDF and Word differ for non-PNG figures | Deliberately deferred as a known gap; see below. |
| 16 | The tall-group guard measures the print-scale height, not the final height | Fixed: the guard is evaluated on the measured final group height when a gap fit applies. The formula is unchanged at the print scale, and the tall-group test passes. |
| 17 | `release_callout_keeps` also clears keeps in a callout's nested data tables | Kept as is, with reason: the issue called it harmless "while every box is one `cantSplit` row", and that condition holds. A nested table's paragraph is still a paragraph of the outer box row, so Word would chain the box through it. Tested inverted: a nested header-row keep **is** released (`w:val="0"`). |

## Code changes

| File | Change |
| --- | --- |
| `tools/src/handbook_toolkit/docx_figure_place.py` | `print_scale` rounds the factor before applying it and skips a 1.0 no-op. |
| `tools/src/handbook_toolkit/docx_tables.py` | `keep_leadins` skips every container inside a callout box, so its count never includes a keep that `release_callout_keeps` clears. `release_callout_keeps` still clears every paragraph of the box, nested tables included. |
| `tools/src/handbook_toolkit/render_data/typst/table-fit.typ` | `handbook-gap-admits` and `handbook-gap-fit` are pure helpers used by `handbook-figure-group`; `handbook-print-factor` rounds the print/gap factor; the tall-group guard measures the final height. |
| `docs/publication-build.md` | Non-PNG note in the print-scale bullet; nested-table wording; "nothing before a box keeps with next". |
| `CHANGELOG.md` | Unreleased Fixed/Changed entries. |

The PDF helper refactor is algebraic: the factor is the same expression as before, rounded before
the `>= 1` test instead of after. The Word and PDF layouts are unchanged. The only observable
difference is the Word report: a factor that rounds to 1.0 no longer increments
`figures at print scale`. The callout keep release is unchanged: every box paragraph, including a
nested table's, still gets the explicit `w:val="0"`.

## Tests

| File | Test |
| --- | --- |
| `tools/tests/test_figure_place.py` | `test_the_gap_threshold_rejects_a_gap_the_floor_would_allow`; `test_a_factor_that_rounds_to_one_is_not_counted`; `ConstantParityTests`; `test_the_print_scale_runs_before_the_gap_pass` (LibreOffice). |
| `tools/tests/test_table_fit.py` | `test_the_gap_gate_and_safety_margin_are_pinned`; `test_the_print_scale_rounds_to_one_before_scaling`; `test_a_group_taller_than_a_page_is_not_wrapped`; `test_a_long_callout_stays_whole`; the checklist and callout source tests no longer skip. |
| `tools/tests/test_docx_callouts.py` | `test_the_box_lands_where_the_callout_was`; `test_a_data_table_inside_a_box_does_not_chain_the_box`; `test_the_measured_path_releases_the_box_including_a_nested_table` (LibreOffice and Poppler). |
| `tools/tests/test_reading_site.py` | The callout figure in the pixel fixture; `.first` locators for the two figures. |

Mutation evidence, each run on a copy of the source and reverted:

- Old `print_scale` rounding → `test_a_factor_that_rounds_to_one_is_not_counted` fails (`1` vs `0`).
- `print_scale` moved after the pass loop → `test_the_print_scale_runs_before_the_gap_pass` fails
  (`2699867` vs `3060000`).
- `keep_leadins` skip removed → `test_a_data_table_inside_a_box_does_not_chain_the_box` fails
  (`1 != 0`).
- Nested-table skip re-added in `release_callout_keeps` →
  `test_the_measured_path_releases_the_box_including_a_nested_table` fails (the nested keep stays
  `"1"`).
- `handbook-min-gap = 0.0` and `handbook-gap-safety = 0pt` → the Typst gap assertion fails to
  compile.
- `handbook-print-factor` unrounded → `test_the_print_scale_rounds_to_one_before_scaling` fails.
- Tall guard changed to `if true` → `test_a_group_taller_than_a_page_is_not_wrapped` fails
  (`[0]` vs `[1]` for the lead-in page).
- Typst callout `breakable: true` → `test_a_long_callout_stays_whole` fails (`[0]` vs `[1]`).
- `:not(.callout …)` removed from the CSS → the Playwright test fails with the canvas pixel
  `(246, 241, 231)` instead of the warning tint `(253, 243, 240)`.

## Known gap (item 15): PDF and Word differ for non-PNG figures

The PDF scales every `image` through `handbook-scale-images`; Word scales only PNG figures with a
`pHYs` chunk, because `_natural_ratio` reads the natural size from the PNG pixel density. A vector
figure therefore prints at 85% in the PDF and at 100% in Word. The template's
`section-structure.svg` is such a figure. The Solutions Architecture Handbook's 131 figures are
all PNG, so 6.0.0 is unaffected.

Why it is deferred rather than aligned:

- Word has no natural-resolution floor for a vector image, so making Word scale the SVG would need
  a new intrinsic-size model and a new layout on the template and the sample, which needs the
  Owner's desktop Word check.
- Making the PDF skip every non-PNG image would align the SVG but also stop scaling raster JPEGs
  in the PDF, contradicting the "raster figure" rule.
- The change is not needed for any published book, and the rule is a raster rule; the difference
  is now stated in `docs/publication-build.md` and in the record so it is not mistaken for a
  regression.

## Release artifacts

The Solutions Architecture Handbook's figures are all PNG. The Word pass therefore changes only
the print-scale report count (a rounded-to-1.0 figure is no longer counted) and no figure or table
position; the callout keep release is unchanged. The Typst refactor keeps the same factors and
the same guard for every group in the book; it now applies the factor rounded to four decimals
instead of the unrounded value, a sub-0.0001 difference, and removes a sub-pixel scale when the
factor rounds to 1.0. No page position is expected to change. The next tag does not need a new
desktop Word check for this change; the Owner's check remains the acceptance test for any later
layout change.

## Commands and results

Environment: `python3 -m venv .venv`; `.venv/bin/pip install -r requirements-dev.txt`;
`.venv/bin/pip install -e tools`; `.venv/bin/pip install -r
tools/scripts/requirements-edition-preview.txt` (Playwright 1.60.0, Chromium already cached, so the
browser test runs instead of skipping).

| Command | Result |
| --- | --- |
| `PYTHONPATH=tools/src .venv/bin/python -m unittest discover -s tools/tests -p 'test_figure_place.py' -v` | 20 tests, OK |
| `PYTHONPATH=tools/src .venv/bin/python -m unittest discover -s tools/tests -p 'test_docx_callouts.py' -v` | 9 tests, OK |
| `PYTHONPATH=tools/src .venv/bin/python -m unittest discover -s tools/tests -p 'test_table_fit.py' -v` | 20 tests, OK |
| `PYTHONPATH=tools/src .venv/bin/python -m unittest discover -s tools/tests -p 'test_reading_site.py' -v` | 14 tests, OK |
| `make verify PYTHON=.venv/bin/python` | 5 checks, 0 problems |
| `make verify-full PYTHON=.venv/bin/python` | 7 checks, 0 problems |
| `make check PYTHON=.venv/bin/python` | 639 tests, OK (2242.303 s); `verify`: 5 checks, 0 problems |

No result is claimed before it was run. The full suite ran on the final tree with Playwright and
Chromium present, so the browser test ran rather than skipping.
