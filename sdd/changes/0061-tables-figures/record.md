# Change 0061 — Table fit and raster figure layout

Implementer Codex; reviewer/merger Claude. Branch `fix/0061-tables-figures` in the assigned new
worktree, started at `39c524c` (0062 qpdf compaction), rebased onto merged 0060/PR 96 (`6d464ef`). No version bump, tag or self-merge.
0060 owns appendix transforms/numbering and Document Control; this change stays out of those regions.

## Design

Raster widths are staged once for every writer, using PNG pHYs density, the shared print page
geometry and the frozen v3.0.0 natural/tall caps. Stated smaller widths win. SVG and rasters without
physical density retain their widths. Code examples are protected; image bytes are never rewritten
by this feature. The light-screen raster CSS rule uses multiply; dark mode and print remain native.

Typst measures the entire table float, including its caption, against the complete page body.
Only oversized table/lead-in groups may break; page-sized groups move whole. Caption space is reserved below table fragments and reclaimed with strong negative spacing,
keeping the final row and bottom caption together without making a long table sticky. Transparent context avoids accidentally boxing/clipping
long tables. The native figure remains internally breakable; its measured outer block owns fit.
The metadata tags are invisible and support mechanical start/end page checks in the proof harness.

Word probes actual data tables, excluding one-row layout wrappers, in isolated fresh sections
using their own page geometry, styles and bundled fonts. First-row and last-character markers
measure every final-row cell and caption. Only page-sized tables receive keepNext row chains and
cantSplit; taller tables retain their existing properties. Probe markers are never published.
This runs before the existing verified native page-number cache, so the cache uses final layout.

Source algorithm: same-author MIT `cesarcastrocuba/solutions-architecture-handbook`, frozen tag
`v3.0.0` / `13d295b`, `scripts/build_book.py:_figure_width` and `figure_layout`. The read-only
`/tmp/agy-sa/src` is used; the original reference repository is never touched. Committed fixtures
are synthetic. Full source hashes and proof commands will be appended from actual tools.

## Initial evidence

Own venv from `requirements-dev.txt`. Four raster/geometry unit tests pass (0.018s), two native
layout/Word-property tests pass (0.953s), and one complete synthetic all-edition publication test
passes (24.620s). It contains a short table near a page boundary, a tall repeated-header table,
a natural raster, a tall raster and an SVG, plus Word keep-chain assertions on real data rows.

`figure-widths.csv` contains all 121 SA figures and the actual frozen function comparison:

```text
figures 121 below100 83 min 43 median 94 all_match True
{'id': 'fig-1-2', 'px_width': 904, 'px_height': 893, 'dpi': 199.9996, 'toolkit_percent': 69, 'reference_percent': 69}
{'id': 'fig-1-4', 'px_width': 1059, 'px_height': 1046, 'dpi': 199.9996, 'toolkit_percent': 81, 'reference_percent': 81}
```

Baseline SA PDF semantic tags: 378 tables, 263 captioned; 63 table bodies span pages; five captions
are orphaned (6.6, 16.9, F.11, H.12, H.17). The proof walks the tagged PDF structure and associates
captions with their actual table, including native Div wrappers, instead of guessing by text.
Baseline and final split lists will be recorded with the complete build inputs and outputs.

## Pending final gates

Whole-book after builds, screenshots, `make full`, CI previews and rechecking the CI artifacts
are not yet complete. These are required before ready. Owner desktop Word acceptance, tags,
publication and deployment are not performed. Rollback removes the figure hook/module/shared
geometry wiring, table measurement/wrapping/probe hook, CSS rule and their tests together.

## Reviewer R1 — preceding heading and short introduction

[Early review](https://github.com/cesarcastrocuba/handbooks-hub/pull/100#issuecomment-6956425024)
identified a heading-only SA page 470. A semantic PDF structure audit independently reproduced it.
The sticky wrapper on a long table caused the heading to strand. Removing stickiness alone then
exposed caption-only boundary cases, so the fix reserves caption space explicitly and keeps the
leading heading and one short introduction with the first table/figure fragment. A short introduction
is at most 80 words and 600 Unicode characters; other paragraphs remain ordinary flowing text.
When the complete heading/introduction/float group exceeds the page body, the table may break;
its first fragment stays with the lead and its caption stays with its last row. This also covers a
table that fits alone but cannot fit together with its heading and caption.

The Typst leading measurement includes collapsed block spacing using a 1 pt probe only inside
`measure`; the probe is never rendered. Caption padding sits outside the clipped table surface,
so the row corners retain their radius. Strong negative spacing is necessary: a negative weak
`below` spacing collapses against the native caption gap and can still orphan a caption.
Word explicitly keeps preceding headings and one bounded lead-in with table/image wrappers,
including across bookmark nodes, before the verified pagination cache is rebuilt.

Actual focused outputs after the fix:

```text
$ .venv/bin/python -m unittest discover -s tools/tests -p test_table_fit.py
Ran 5 tests in 3.891s
OK
$ .venv/bin/python -m unittest discover -s tools/tests -p test_tables_figures_build.py
Ran 1 test in 26.948s
OK
```

The native boundary test checks all row counts 10 through 45, including the caption-fit boundary;
headings share the first row's page and captions share the final row's page. The complete synthetic
book also checks headings and short introductions before both tables and an image, repeated
headers on every tall-table page, all three formats and Word's explicit keepNext properties.
Both runtime test modules now run in the publication-build CI job with Quarto and LibreOffice.
The final whole-book heading/caption-only page audit, rebuilt artifacts and refreshed CI evidence
will follow before this draft is marked ready.
