# Change 0090 — Word table columns floor on Inter word widths

Implementer: oc7 (OpenCode). Reviewer and merger: a different agent. Branch
`fix/table-word-floors` from `main` `d432bfa`. No version bump or tag.

## Defect

The Owner's desktop Word check of the sample `0.6.0` preview found words split inside table cells:
"November 2026" printed "Novembe" / "r 2026", "Handbook" as "Handboo" / "k". The sample DOCX had
10 split words; the Solutions Architecture `v6.0.0` DOCX had 48, including 'November' ×21,
'scanning', 'configuration', 'Penetration', 'Technique' and 'PAYMENT_PENDING'.

## Cause

`render_data/filters/table-layout.lua` measured the longest token in characters and floored a
column at `ceil(longest_chars * 1.5)` percent. That constant was tuned for the narrower Source
Sans. In Inter 10.5 pt, 'November' is 51.9 pt wide, but its 12 % column on the 470.6 pt A4 text
width leaves 50.5 pt after the 6 pt cell margins. The deficit was also taken from one donor only:
when no single column had enough room, no column moved. SA Appendix F's five-column table left
column 1 at about 8 % for 'configuration'.

## Fix

- `tools/scripts/table_font_widths.py` reads `Inter-Bold.ttf` with fontTools and produces ASCII
  32-126 advance widths in 1/1000 em. `--write` updates the table embedded in `table-layout.lua`;
  `--check` fails on drift.
- `table-layout.lua` measures the longest unbreakable piece of each column in em. Whitespace
  breaks, and Word also breaks after `-`, `/` and an en dash, keeping the break character on the
  left piece. Non-ASCII characters count 0.62 em; code points at or above U+2E80 count 1.0 em.
- The floor percent is
  `ceil((em * 10.5 + 6 + 2) / 440 * 100)`: 10.5 pt is the Word table size (reference.docx Normal
  `w:sz=21`), 6 pt is the cell margins, 2 pt is safety, and 440 pt is a conservative usable width
  that also covers a table inside a callout box. The named constants sit at the top of the file.
- The existing caps (35/28/20 %) and the scaling when floors sum above 100 stay. A deficit is
  taken from every column with room above its own floor, largest room first and repeatedly, so one
  narrow donor cannot block the move. The total stays 100 and explicit `tbl-colwidths` stay
  untouched.

The existing `[50,50]` expectation is unchanged: both columns contain a single 20-character
unbreakable piece, their floors are below 50 and the initial equal shares already satisfy them.

## Tests

- `tools/tests/test_render_resources.py`:
  - `test_table_floors_fit_inter_bold_words` through Quarto Pandoc: a three-column
    `Version | Date | Summary` table with `November 2026` rows keeps column 2 at or above the 15 %
    floor; a five-column Appendix F shape keeps column 1 at or above the 18 % floor for
    'configuration'. The five-column case also exercises the multi-donor path.
  - `test_embedded_inter_widths_match_the_font` runs the generator with `--check`.
- `tools/tests/test_reference_docx.py`: `test_normal_table_text_is_10_5_points` pins Normal to
  `w:sz=21`.
- `tools/tests/test_tables_figures_build.py`: the real book build still passes.
- `make verify-full`: 7 checks, 0 problems.

## Sample measurement

Built from `/home/ubuntu/github/handbook-sample-01.worktrees/0090-verify` at
`origin/main` `7c847f8` (sample `0.6.0`) with this branch installed in a separate venv:

| | Before (sample PR 33 preview, toolkit 0.16.1) | After (this branch) |
| --- | ---: | ---: |
| Split words (audit) | 10 (9 × 'November', 'Handbook') | 1 |
| PDF pages | 62 | 62 |
| DOCX bytes | 1,296,054 | 1,296,032 |

The remaining audit hit is `'Apache-2.0'` at 55.2 pt in a 58.8 pt column. It is a false positive:
Word breaks after `-`, and the filter measures `'Apache-'` (42.7 pt in Inter Regular), which fits.
No actual word is split.

## Solutions Architecture measurement

Audited the `edition-preview-solutions-architecture` artifact of run `46003235071` (commit
`22b2b9b`). Before: 48 split words in the released `v6.0.0` DOCX. After: 49 audit hits, in two
classes:

- 44 are hyphen or en-dash compounds such as `Cross-platform`, `Self-managed`,
  `Expand-migrate-contract` and `Low–medium`. The audit splits on whitespace only, but Word breaks
  after `-` and `–`; the filter measures the pieces and these do not split.
- 5 are `PAYMENT_PENDING` in a column at the 20 % cap. The token is 103.4 pt, the capped column
  leaves 88.1 pt after the cell margins, and the cap is kept by design.

So the class the Owner reported is gone: no ordinary word is split. The five `PAYMENT_PENDING`
hits remain because the column is at its cap. PDF pages: 569 (released `v6.0.0`) → 566 (preview).

## Known gaps

- The audit script splits on whitespace only, so a hyphenated token such as `'Apache-2.0'` is
  reported even though Word can break it; the remaining hit above is that case.
- The floor is a conservative content rule, not a hard Word constraint; a column at its 20 % cap
  can still be too narrow for an exceptionally long unbreakable word, which the audit would show.
- The 440 pt usable width is deliberately smaller than the A4 text width to cover callout tables;
  the floors are slightly conservative for full-width tables.
