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
- The 35/28/20 % caps apply only when the real floors together exceed 100; otherwise every
  column gets its real floor, because the table has room. When the capped or real floors still sum
  above 100 they are scaled down. A deficit is taken from every column with room above its own
  floor, largest room first and repeatedly, so one narrow donor cannot block the move. The total
  stays 100 and explicit `tbl-colwidths` stay untouched.

The existing `[50,50]` expectation is unchanged: both columns contain a single 20-character
unbreakable piece, their floors are below 50 and the initial equal shares already satisfy them.

## Tests

- `tools/tests/test_render_resources.py`:
  - `test_table_floors_fit_inter_bold_words` through Quarto Pandoc: a three-column
    `Version | Date | Summary` table with `November 2026` rows keeps column 2 at or above the 15 %
    floor; a five-column Appendix F shape keeps column 1 at or above the 18 % floor for
    'configuration'; a four-column table with 'PAYMENT_PENDING' in column 1 reaches its uncapped
    26 % floor, above the 20 % cap. The five-column case exercises the multi-donor path.
  - `test_embedded_inter_widths_match_the_font` runs the generator with `--check`.
- `tools/tests/test_reference_docx.py`: `test_normal_table_text_is_10_5_points` pins Normal to
  `w:sz=21`.
- `tools/tests/test_tables_figures_build.py`: the real book build still passes.
- `make verify-full`: 7 checks, 0 problems.

## Sample measurement

| | Before (sample PR 33 preview, toolkit 0.16.1) | After (CI run `46006866263`, commit `b6b5ec9`) |
| --- | ---: | ---: |
| Split words (audit) | 10 (9 × 'November', 'Handbook') | 0 |
| PDF pages | 62 | 62 |
| DOCX bytes | 1,296,054 | 1,296,045 |

## Solutions Architecture measurement

Audited the `edition-preview-solutions-architecture` artifact of run `46006866263` (commit
`b6b5ec9`) with the audit script that breaks after `-`, `–` and `/`. Before: 42 split words in the
released `v6.0.0` DOCX (48 when hyphenated compounds are counted as single words). After: 0 split
words. PDF pages: 569 (released `v6.0.0`) → 566 (preview).

## Known gaps

- The floor is a conservative content rule, not a hard Word constraint. When the real floors
  together exceed 100 they are capped and scaled; in that case a very long unbreakable token could
  still be narrower than its column, which the audit would show. Neither book has such a case.
- The 440 pt usable width is deliberately smaller than the A4 text width to cover callout tables;
  the floors are slightly conservative for full-width tables.
