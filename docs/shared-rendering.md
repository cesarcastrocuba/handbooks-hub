# Shared rendering resources

The toolkit distributes Quarto filters and a Typst callout override as installed package data.
Books keep canonical prose and publishing settings; they do not copy these resources.

`stage_render_resources(destination)` creates a new resource directory in a private build
workspace and returns paths keyed by resource name. It supports wheel and zip imports, refuses
existing destinations and removes its own directory on copy failure. Reverting this module,
`render_data/`, its tests and the package-data entries removes this unit without changing prose.

| Resource | Behavior |
| --- | --- |
| `filters/table-layout.lua` | Adds IDs to captioned tables without labels; derives soft width weights from visible Unicode character counts. Preserves explicit labels and `tbl-colwidths`. |
| `filters/task-checkbox.lua` | Replaces the standalone unchecked square glyph `☐` with `□` for readable output; list structure remains intact. |
| `typst/callout-breakable.typ` | Replaces Quarto's callout function with a breakable block. |

Register the Lua filters at `pre-ast`; include the Typst file using `include-before-body`.
The renderer must stage these files and wire them into its generated configuration. Merely
installing the package does not enable the filters.

Auto IDs include a deterministic hash of the project-relative input path and visible document
content, plus table ordinal. Thus identical chapters with different filenames have different
IDs, and relocating a project preserves IDs. Explicit author labels remain the stable public
cross-reference interface: auto IDs can change when content changes and use a noncryptographic
32-bit hash. Duplicate explicit labels require manuscript validation.

Width shares are content weights, not hard minimum/maximum bounds or a substitute for visual
review. Tables over 100 columns retain renderer defaults. Merged cells and long unbreakable
strings require manual inspection. Breakable callouts may split embedded tables across pages.
Chapter numbering, caption placement and table row layout remain renderer responsibilities.

Validation: `PYTHONPATH=tools/src python3 -m unittest discover -s tools/tests -p test_render_resources.py -v`.
The suite covers zip-package staging and cleanup; its real Pandoc boundary (through Quarto)
checks Unicode widths, explicit attributes, identical chapters and project relocation.
The runtime test skips if Quarto is absent; publication CI must install the pinned Quarto.
The three-format pilot prototype is supporting evidence, not a published book or a complete
layout acceptance. Quarto API references: [document/project paths](https://quarto.org/docs/extensions/lua-api.html).
