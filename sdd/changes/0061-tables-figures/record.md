# Change 0061 — Table fit and raster figure layout

Implementer Codex; reviewer/merger Claude. Branch `fix/0061-tables-figures` in the assigned new
worktree, based on `39c524c` (0062 qpdf compaction). No version bump, tag or self-merge.
Parallel 0060/PR 96 owns appendix transforms/numbering and Document Control; this change stays
out of those regions. Rebase and final evidence follow before handoff.

## Design

Raster widths are staged once for every writer, using PNG pHYs density, the shared print page
geometry and the frozen v3.0.0 natural/tall caps. Stated smaller widths win. SVG and rasters without
physical density retain their widths. Code examples are protected; image bytes are never rewritten
by this feature. The light-screen raster CSS rule uses multiply; dark mode and print remain native.

Typst measures the entire table float, including its caption, against the complete page body.
Only oversized tables may break; page-sized floats move whole. The table's sticky block keeps a
bottom caption with its final fragment. Transparent context avoids accidentally boxing/clipping
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
