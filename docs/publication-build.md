# Local publication build

`handbook-toolkit build-book` builds a verified seven-file release directory from an exact clean
book commit. It does **not** publish, upload, deploy, tag or release anything.

## Requirements

- Git and a clean book repository at the exact full commit.
- Quarto `1.11.9`.
- Poppler `pdfinfo` for PDF inspection.
- qpdf 11 or later for lossless PDF compaction. It is on by default; a release build fails
  without it, an explicit `--preview` build records `skipped` in the manifest, and
  `--no-optimize` turns it off together with the PNG and ZIP optimization.
- No profile argument by default: the toolkit resolves the exact `book.yaml` profile pin from its
  installed `profile_data/`. `--profile PATH` remains an explicit reviewed override; there is no
  parent-checkout fallback.
- A book-side `publishing/_quarto.yml` and `manuscript/book.yml` reading order.
- A `book.yaml` toolkit pin exactly equal to the installed builder version. `--preview` is an
  explicit, non-release exception and is recorded in the manifest command.
- Section-pilot and preview builds require a prerelease book version such as `0.1.0-preview`;
  stable versions are refused for those modes.

Quarto supplies its bundled Pandoc and Typst. The current validators do not require Quarto; only this
publication build does.

## Command

```bash
handbook-toolkit build-book --repo /path/to/book --commit 0123456789abcdef0123456789abcdef01234567 --output /external/path/release-1.0.0
```

Optional arguments:

- `--version 1.0.0` overrides `publishing/metadata.yaml` for the book version.
- `--epoch 1761868800` overrides the default commit timestamp / `SOURCE_DATE_EPOCH`.
- `--quarto /path/to/quarto` selects the executable; it must report `1.11.9`.
- `--profile PATH` overrides the packaged profile; omit it to resolve the exact book pin from the
  installed package.
- `--mode chapter` (default) validates every chapter and appendix in the reading order.
  Front matter, back matter and references remain documented special groups.
- `--mode section-pilot` validates exactly one chapter and no appendices; it requires a prerelease
  version such as `0.1.0-preview`.
- `--preview` allows a `book.yaml` toolkit pin that differs from the builder, only for an explicit
  non-release preview, and also requires a prerelease version. The manifest command records
  `--mode` and `--preview`.

The output directory must not exist and must be outside the source repository.

## What the build does

1. Rejects a dirty repository or a commit that is not `HEAD`.
2. Creates a private staging directory beside the final output.
3. Extracts only tracked files from the exact commit with `git archive`.
4. Inspects the source ZIP before extracting or rendering: reading order coverage, canonical
   manuscript, descriptor and notices must be valid at the commit.
5. Reads and validates `book.yaml`, `publishing/metadata.yaml` and the reading order from the staged
   source, not from the mutable working tree.
6. Checks the book's toolkit pin against the builder version (unless explicit `--preview`).
7. Resolves the reviewed profile and runs the structural manuscript gate for every chapter and
   appendix, plus the reference/label/local-image gate across the full reading order. Front matter,
   back matter and references are special manuscript groups but are included in reference checks.
8. Stages the packaged render resources: `table-layout.lua` and `task-checkbox.lua` at `pre-ast`,
   and `callout-breakable.typ` via Typst `include-before-body`.
9. Generates a deterministic Quarto project config, using the book-side `publishing/_quarto.yml`
   and reading order; the first reading-order file becomes the home page so there is no separate
   empty title chapter. It renders only HTML, Typst and DOCX with `--no-execute` and
   `SOURCE_DATE_EPOCH`.
10. Stages a render-only heading wrapper for each chapter/appendices file, strips manual heading
   numbers so Quarto numbers the rendered sections, and converts source table captions into
   explicit `**Table N.T — Title**` paragraphs below the table. Canonical files are not changed.
11. Renders a single-file Markdown edition with Quarto `gfm` from the canonical sources in reading
   order: per-file front matter is dropped, include shortcodes are resolved against the combined
   document, and cross-references become plain text. The edition opens with the same
   document-control fields as the other editions plus the source commit. Figures become their
   captions because one file cannot carry the images.
12. Packages the HTML site as a ZIP, the PDF, the DOCX and the Markdown edition as files, and the
   tracked source as a ZIP whose comment is the full source commit.
13. Inspects every payload with the shared format inspector.
14. Writes `publication-manifest.json` (schema `1.1`) and `SHA256SUMS.txt`, then runs
    `verify_publication`.
15. Atomically renames the complete verified directory to `--output`.

No writer staging directory is visible at the final output path. A failed build leaves no final
output and removes its private staging directory.

## Output

Exactly seven assets:

- `book-html.zip`
- `book.pdf`
- `book.docx`
- `book.md`
- `book-source.zip`
- `publication-manifest.json`
- `SHA256SUMS.txt`

`book.md` is one GitHub-flavoured Markdown file in reading order: front matter, chapters, appendices
and references. It is meant for search, diffing and AI tools; the HTML, PDF and DOCX payloads remain
the reading and print editions. Its limits:

- Figures are represented by their caption or alternative text, not by images.
- Raw HTML from the render is reduced to plain Markdown: cross-references keep their text and tables
  keep their Markdown form, without Quarto `<div>` wrappers or `<a>` anchors.
- Table and figure counters run sequentially across the whole file, so they may differ from the
  chapter-scoped numbers of the print and HTML editions.
- Include shortcodes that resolve through the manuscript path work, but any reader that assumes the
  original per-file directory layout is not reproduced.
- The build fails when the rendered file contains one of its own absolute paths (staging workspace,
  output directory, source repository or home directory). Book content may still mention paths such
  as `/tmp/` or `file://`; those are not rejected. Paths with fewer than three components are never
  used as needles.

The manifest records the exact commit, book version, toolkit/profile versions, build command, source
epoch, and Quarto/Pandoc/Typst/Python/zlib runtime versions. `build.optimization.pdf` records the
compaction tool and version, whether the PDF was `optimized`, `kept: no gain` or `skipped` (with the
reason), and the size before and after in bytes.

## Limits

The build verifies presence, structure, links within the HTML archive, checksums and identity. It does
**not** prove editorial quality, factual accuracy, visual layout, accessibility, PDF pagination or
reproducible bit-for-bit output across all environments. Human review remains required before any
publication gate.

Rendered chapter and table numbers come from the reading-order position, not from the manual `N.M`
text in the canonical headings. A partial pilot is therefore rendered as Chapter 1 with Table 1.1;
manual cross-reference numbers inside that pilot are not renumbered. The staged Typst project sets a
white brand primary and explicit black link color, which suppresses the overflowing orange-book
chapter-title block without hiding links. Table column widths and callout pagination remain shared
renderer responsibilities and require visual review.


## Word field and rendering gate (toolkit 0.10.2)

The build prepares the Word package in docx_post, using parsed XML, registered namespace prefixes,
schema-ordered properties and deterministic ZIP metadata. It normalizes caption/heading bookmarks,
adds a TC field at the start of each caption (not formatted as hidden text), and caches Contents and caption-list entries as internal hyperlinks.
The build uses a private LibreOffice profile and fontconfig configuration pointing only at the
staged toolkit fonts. It exports named destinations, maps them from authored bookmark names and
writes numeric PAGEREF caches. A final conversion must agree with every cached page or the build
fails. Decimal section restarts are respected; unsupported numbering formats block a required probe.
No dirty attribute or updateFields setting is published. Cached numbers are LibreOffice
pagination; F9 in Word regenerates Word's pagination. Optional builds without a working probe
warn and record title-only caches in build.tool_versions.docx_page_numbers, never blank PAGEREF
results. build.tool_versions also records the LibreOffice version. Release workflows must install
libreoffice-writer and pass --require-page-numbers; missing or failed probes then block publication.
Caption lists are omitted when there are no entries. The Typst front matter also
emits conditional table/figure/listing outlines from the shared registry.

The first canonical page is rendered as index.qmd. A native Pandoc image filter rebases its local
image references against that page's original directory before the HTML, PDF and DOCX writers run.
The canonical sources and their image paths are unchanged.

Publication-build CI installs LibreOffice Writer as well as Poppler. Its real build uses an
original generated image, checks the three populated lists in a LibreOffice PDF conversion, and
passes the DOCX through the structural artifact gate. Desktop Word must still be opened during
Owner acceptance; it was not opened by an agent. See [artifact inspection](artifact-inspection.md)
for the validator boundary.

## Figure and callout placement (change 0081)

Owner decisions of 2026-11-22 and 2026-11-23 apply to the PDF and to Word:
- a figure stays right after the text that introduces it, because a figure away from its
  description is a defect and a part-empty page is not;
- a callout box is never split across pages;
- figures print a little smaller than their stated size.

- **Print scale and gap fit, shared by both editions.**
  - Every raster figure prints at 85% of its stated size (`PRINT_SCALE`, `handbook-print-scale`).
  - A figure group is the figure, its caption and the heading or short lead-in kept with it. A
    group that would still start the next page below a gap of at least 15% of the text block is
    scaled further, just enough to fit the gap.
  - Neither step goes below 75% of the image's natural raster size, read from the PNG's pixel
    density. That floor keeps diagram text at 8 pt or more. A figure near the floor shrinks less
    or not at all.
  - A gap fit that would cross the floor is not applied: the group moves to the next page.
  - Tables are never scaled.
  - The constants live in `docx_figure_place.py` and `table-fit.typ` and change together.
- **PDF.**
  - Figures do not float. The float-leadins filter wraps every figure in `handbook-figure-group`
    (`table-fit.typ`) with its heading and short lead-in.
  - The group measures the room left after the text before it from a zero-height marker block.
    The marker records its position in a state; a `query` for it kept the table measurement from
    converging.
  - `handbook-scale-images` applies the rule and records each decision as `<handbook-figure-fit>`
    metadata.
  - The filter passes `open: p => image(p, alt: "handbook-natural")` from the document, so that an
    image path resolves from the document when the natural size is measured.
  - Tables keep `handbook-float-group`.
- **Word.** Nothing moves. `docx_figure_place.place_figures` runs after the table measurement and
  before the page-number probe.
  - It applies the print scale (`print_scale`).
  - It paginates the document in LibreOffice with the staged fonts and applies the gap fit.
  - A scaled figure shifts the later page breaks, so the scaled figures of one pass are at least
    three pages apart and the document is measured again, up to four passes.
  - `build.tool_versions.docx_figure_placement` records both counts.
- **Callouts.**
  - Each callout is one unbreakable box: a single `cantSplit` row in Word, and
    `breakable: false` in Typst.
  - A box that does not fit the rest of a page starts the next one.
  - A pitfall and its decision are separate boxes, so a pitfall that fits stays on the page
    before its decision.
  - A breakable box was tried and rejected by the Owner: split pitfalls, decisions and review
    checklists read badly.
- **Remaining gaps.** Tall diagrams that leave a gap are redrawn in the book (a later edition).
  Desktop Word paginates slightly differently from LibreOffice; the Owner's Word check remains the
  acceptance test.

## Native HTML staging

The build orchestration delegates source/configuration staging, identity checks, HTML packaging
and the Markdown edition to separate modules. HTML lists are native nonempty registry chapters,
generated from staged source labels. Print renders use the canonical reading order; the later HTML
render adds the lists, using Quarto --no-clean to retain print outputs. Generated list pages never
enter the source archive or Markdown source. Caption numbering and links are resolved by Quarto.

## Opt-in prose cross-reference links (unreleased, change 0052)

Set `publication.cross_reference_links: true` in `book.yaml` to link resolved prose references
in the private render workspace. The default is off; the canonical sources and source archive
are never rewritten. No version bump or release is part of this change.

The shared section anchor scheme uses Word-safe ASCII names: `sec_ch_1` for Chapter 1,
`sec_app_a` for Appendix A, `sec_1_2` for Section 1.2 and `sec_a_1` for Section A.1.
Numbered headings through level six are supported. These generated IDs are the same HTML IDs,
PDF named destinations and DOCX bookmarks. Unnumbered subheadings use deterministic file-scoped
IDs, shortened with the toolkit's bookmark hash when necessary. An explicit author ID takes
precedence; Word's existing bookmark encoder still applies to author IDs containing hyphens or
other unsupported characters. Figure/table targets follow change 0051's native displayed labels:
`0.N` before numbered chapters, chapter numbers, appendix letters and `BM.N` in back matter.
They keep Quarto IDs
and their existing Word bookmark encoding; explicit author IDs remain authoritative.

Chapter, appendix, section, figure and table references link only when a target exists.
Ranges and lists retain their wording. Bare section numbers need a navigational cue, a
reference group, or a declared reference table column. Code, headings, image/caption lines,
existing links, bibliography lines under References/Further Reading, versions, dates and
measurements stay plain. A bibliography heading ends at the next heading of the same or higher
level. Automatic glossary-term linking stays off (`HUB-DEC-005`).

PDF and DOCX links are internal. After the print render, generated HTML links are rebased to
the owning source page, including a book whose first page becomes `handbook-source-index.html`.
Only generated links carry the `handbook-xref` class and receive this rewrite. Ambiguous section
numbers or duplicate navigation IDs fail the opted-in build rather than selecting a target.
This feature does not repair displayed numbering; change 0051 owns that separate contract.

## Opt-in glossary pointers and analytic Index (unreleased, change 0053)

Set `manuscript.glossary` to a glossary QMD path relative to `manuscript.root`. It must be in
the canonical reading order and contain a `Term | Meaning | Defined in` pipe table. This enables
stable `gl-<slug>` entry anchors, alphabetic grouping, definition pointers and a final unnumbered
Index in HTML, PDF and Word. Source files and the source bundle remain unchanged.

Optionally set `publication.index_vocabulary` to a repository-relative YAML file conforming to
the packaged `index-vocabulary.schema.json`: `terms` is a list of objects with `term`, optional
`aliases`, `defined`, `see` and `rationale`. Matching glossary terms merge aliases; additional
terms create Index-only entries. `see` names an existing canonical entry and creates an alphabetic
lookup row. A vocabulary requires a declared glossary. Missing files, invalid schemas, missing
`see` targets, duplicate slugs, generated-page collisions and unresolved deliberate glossary links
fail the opted-in build.

Definition sections appear in bold in the Index. Other occurrences are grouped by declared
chapter/appendix reading order. Longest non-overlapping aliases match prose case-insensitively;
short uppercase acronyms retain case. Code, headings, captions, bibliography, proper-name spans,
front/back matter and the glossary itself do not supply discussion locations. Chapter/appendix
introductions do supply locations, matching the frozen reference builder.

Deliberate `[Term](#gl-slug)` author links resolve across HTML pages and stay internal in print.
Long glossary identifiers are encoded before Pandoc writes Word bookmarks; HTML/PDF retain their
full `gl-<slug>` IDs. Index rows are unbreakable Typst cells and carry Word `cantSplit` markers.
No prose glossary term is linked automatically (`HUB-DEC-005`). The separate
`publication.cross_reference_links` option controls prose cross-reference linking; glossary and
Index navigation work with it disabled. Omitting the new keys preserves the default build path.
