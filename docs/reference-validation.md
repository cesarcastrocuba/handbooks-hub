# Reference validation

`handbook-toolkit validate-references` validates explicit cross-references, duplicate labels and
local image paths across the canonical reading order declared by `book.yaml` and
`manuscript/book.yml`.

```sh
handbook-toolkit --root . validate-references book.yaml
```

The command first runs the full book/reading-order validation, so every canonical `.qmd` must be
listed exactly once. It then checks every listed file, including front matter, appendices and back
matter, without imposing chapter/section profile shape on those special files.

## What is checked

- Explicit `{#label}` identifiers, including labels on headings, figures and tables.
- Duplicate explicit label IDs across every file in the reading order.
- `@sec-*`, `@fig-*`, `@tbl-*`, `@eq-*` and `@lst-*` references must resolve to an explicit label.
- Local Markdown anchors `](#fig-*)`, `](#tbl-*)`, `](#sec-*)`, `](#eq-*)` and `](#lst-*)` must
  resolve to an explicit label in the same file.
- Local links `chapter.qmd#fig-*` (and the other explicit prefixes) must target a canonical
  reading-order file and resolve an explicit label in that file.
- Local image targets must be relative, stay inside the book repository, exist and not use a symlink component.
- Local image safety is checked against the repository root, so chapter-relative paths such as
  `../../assets/figure.png` remain valid. Any symlink component in the resolved path is rejected.

## Preserved / not checked

- External links and external images are not fetched, rejected or rewritten.
- Automatic heading anchors are not treated as explicit labels. Link checking is limited to
  explicit `sec-`, `fig-`, `tbl-`, `eq-` and `lst-` anchors; `[text](#Some-Heading)` is left to
  manual review.
- Labels and references inside fenced code, inline code spans and HTML comments are ignored.
- Markdown links with non-explicit fragments are not resolved.
- Visual accuracy, factual correctness, citation validity and semantic quality remain review
  concerns.

The validator is offline and deterministic. It does not render Quarto or verify generated HTML
anchors.
