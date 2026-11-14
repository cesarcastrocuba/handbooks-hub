# Record — Figure paths in the PDF and DOCX editions

**Change:** `0037-print-figure-paths`. **Recorded:** 2026-11-14. **Toolkit:** `0.10.1`.
Follow-up of work package WP4 of change `0027` (finding H6).

## Problem

The prepared sample `v0.5.0` adds the first figure of a published book, in Chapter 1. With toolkit
`0.10.0` its build stopped in the PDF step:

```text
error: file not found (searched at …/work/manuscript/chapters/manuscript/images/lifecycle.svg)
#box(image("manuscript/chapters/manuscript/front-matter/../images/lifecycle.svg", …))
```

The toolkit stages the first reading-order page at the project root as `index.qmd`, so its
relative images no longer resolve. A Pandoc filter, `index-resources.lua`, rebased them when the
input file was `index.qmd`. In the single-file formats (Typst and DOCX) Quarto renders the whole
book as one document whose input file is `index.qmd`, so the filter rebased the images of **every**
chapter with the first page's directory, and Quarto then added the chapter's own directory. The
defect is older than `0.10.0`; no test or published book had a figure outside the first page, which
is audit finding H6. The template passes because its only chapter is the first page.

## What changed

- `build_staging._rebase_images` rewrites the relative image targets of the staged `index.qmd`
  when it is written, outside fenced and inline code, and leaves remote, absolute and anchor
  targets alone. Every reading-order file, the first included, is now transformed in place, so
  the reading site renders the first page from its own directory with its paths untouched.
- `index-resources.lua` no longer touches images; it keeps only the link rewrite for a book whose
  own first page is the root `index.qmd`. The `handbook-index-source-dir` metadata and its marker
  file are removed.
- `reading_site.restore_first_source` only renames a root `index.qmd`; it no longer copies the
  staged index over the first page.
- Tests: unit tests for the rewrite and for staging, and a real-build test with a figure on a first
  page under `front-matter/` and another in `chapters/`, checked in the PDF, the DOCX and the
  reading site.

## Why at staging time and not in the filter

A filter cannot tell which images belong to the first page in a single-file render: the input file
is the same for all of them, and the markers Quarto uses to attribute content to chapters are
internal. The toolkit knows exactly which file it moved, so it fixes the paths where it moves it.

## Consequences

- Tag `toolkit-v0.10.0` stays, because tags are not rewritten, but no template or book pins it.
  Template `1.5.0` and sample `v0.5.0` pin `0.10.1`.
- The rewrite reads Markdown source with the same image pattern as `validate-references`. An image
  written as raw HTML in the first page is not rebased; `validate-references` does not accept such
  images as local images either.

## Evidence

- Before: `python3 tools/scripts/edition_preview.py --repo <sample at release/v0.5.0>` with toolkit
  `0.10.0` failed with the error above.
- After, same command with this change: seven edition files; `book.pdf` lists "Figure 1.1 The seven
  lifecycle states…" with its page under "List of Figures"; the LibreOffice conversion of
  `book.docx` shows the List of Figures entry and the figure; the reading site shows the figure in
  Chapter 1 and has `figures.html`.
- `python3 -m unittest test_build.FirstPageStagingTests
  test_build.BuildTests.test_figures_outside_the_first_page_directory_build_in_every_edition`:
  6 tests OK.
- Not verified: desktop Word.
