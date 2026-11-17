# Change 0061 — Table fit and raster figure layout

Implementer OpenCode 2 (takeover of the draft from Codex, whose credit ran out); reviewer and merger
Claude. Branch `fix/0061-tables-figures`, rebased onto `eee5411` (main with 0063 merged). No version
bump, tag or self-merge. This change stays out of the 0060 appendix/Document Control and 0063 Typst
numbering regions.

## Design

Raster widths are staged once for every writer, using PNG pHYs density, the shared print page
geometry and the frozen v3.0.0 natural/tall caps. Stated smaller widths win; SVG and rasters without
physical density keep their widths; code examples are protected and image bytes are never rewritten.
The light-screen CSS rule uses `mix-blend-mode: multiply`; dark mode and print stay native.

Typst measures the complete table float, caption included, against the page body. A float that fits
moves whole; an oversized float breaks with a repeated header and keeps its caption with the final
row. A heading and one short introduction (at most 80 words and 600 characters) are measured with the
float and placed in an unbreakable block only when the group fits the page body; otherwise the lead
stays and the float may break. The filter emits the group as flat Typst blocks: a Pandoc Div would
render as a breakable `#block[`, and Typst scales an image down to the remaining space inside it.
A breakable helper wrapper was tried first and rejected for the same reason; it shrank three SA
figures by up to 27 %.

Word measures every data table in isolated fresh sections with the workbook's page geometry, styles
and bundled fonts, using bookmarks on the first paragraph and on the final row and caption. Quarto
writes a table float's caption into the same one-cell layout table that wraps the table and styles it
`ImageCaption`, not `TableCaption`; the caption is therefore found in that cell, the whole wrapper is
measured including its cell spacing, and only floats that fit one page are kept. Keeping sets the
paragraph keep chain, `cantSplit` on every data row, and `cantSplit` on the wrapper row, which is what
LibreOffice honours across the nested-table boundary. Taller tables keep their existing properties.
Probe markers are never published, and this step runs before the verified native page-number cache so
the cache sees the final layout.

Source algorithm: same-author MIT `cesarcastrocuba/solutions-architecture-handbook`, frozen tag
`v3.0.0` / `13d295b`, `scripts/build_book.py:_figure_width` and `figure_layout`; the read-only
reference at `/tmp/agy-sa/src` was used and the original repository was never touched.

## Reviewer R1 — heading and caption-only pages

The [early review](https://github.com/cesarcastrocuba/handbooks-hub/pull/100#issuecomment-6956425024)
found SA page 470 holding only "I.2 Chapter 2: Architecture Principles" while Table I.2 moved to page
471: keeping a table whole had traded an orphan caption for an orphan heading. The lead group now
keeps a heading and one short introduction with the float, in Typst and in Word, and the semantic PDF
audit reports no page whose body is only a heading or only a caption.

## Takeover round (OpenCode 2)

Three defects were reproduced and fixed on top of R1.

1. **The lead group scaled figures.** A breakable group block made Typst shrink an image to the
   remaining space instead of moving it to the next page. On the 8ae8b17 CI artifact, Figures 5.3,
   8.8 and 8.9 rendered at 83.0 %, 83.9 % and 43.9 % of the body instead of 85 %, 86 % and 60 %.
   The group is now measured and made unbreakable only when it fits; a figure that cannot share a
   page with its lead keeps its stated width, and a regression test pins the rendered resolution
   through `pdfimages`.
2. **Word captions were never found.** `candidates` required the `TableCaption` style; Quarto emits
   `ImageCaption` inside the float's layout cell. The caption therefore fell outside the keep chain
   and the measured end bookmark. On the main baseline the LibreOffice rendering of the SA DOCX has
   15 pages that begin with a caption whose table ended on the previous page; the R1 build, which
   kept tables without their captions, has 17. Captions are now discovered in the cell, the whole
   wrapper is measured, and the wrapper row is guarded with `cantSplit`. The first attempt guarded
   the row without measuring the wrapper; it left one float that the probe called page-sized but
   LibreOffice could not place, with its caption on the next page. Both are fixed together.
3. **Pandoc wrapped the lead group in a breakable Div.** Even with the group helper fixed, the AST
   filter returned a `pandoc.Div`, which the Typst writer renders as `#block[`. A breakable block
   still shrank an image to the remaining page space, which is why the CI artifact at d476566 kept
   the three distortions. The filter now emits flat raw blocks, so the helper owns the only block.
   A filter test parses the generated Typst and rejects the `#block[` wrapper.

## Commands and evidence

All numbers below come from runs in this round: hub `f6db9af` (rebased onto `eee5411`); SA book
`176c6aa43485a652eb05e87f651fd46a3d6acd60`; sample `8ed1b7035430ab3dc25fb65d712577bc197394ef`;
before = toolkit at `6d464ef`, after = this branch. Builds use
`tools/scripts/edition_preview.py --require-tools` (the CI path) with local Quarto 1.11.9,
LibreOffice 24.2.7.2, qpdf 11.9.0 and poppler 24.02.

### 1. Natural raster width, all 121 SA figures

```text
$ .venv/bin/python /tmp/opencode/oc2-0061/widths.py
figures 121 below100 83 min 43 median 94 all_match True
{'id': 'fig-1-2', 'px_width': 904, 'px_height': 893, 'dpi': 199.9996, 'toolkit_percent': 69, 'reference_percent': 69}
{'id': 'fig-1-4', 'px_width': 1059, 'px_height': 1046, 'dpi': 199.9996, 'toolkit_percent': 81, 'reference_percent': 81}
committed_csv_equal True
```

The script re-stages book `176c6aa`, imports v3.0.0 `_figure_width` from the read-only reference and
regenerates `figure-widths.csv` byte-for-byte.

The three figures distorted by the R1 group (CI run 44151226793) and the same check on the final
build:

```text
$ .venv/bin/python /tmp/opencode/oc2-0061/pdf_width_probe.py <edition>   # 8ae8b17 CI artifact
raster figures seen: 121, mismatched: 3
('fig-5-3', 85, 83.0, 127)
('fig-8-8', 86, 83.9, 214)
('fig-8-9', 60, 43.9, 217)
$ .venv/bin/python /tmp/opencode/oc2-0061/pdf_width_probe.py <final SA edition>
raster figures seen: 121, mismatched: 0
$ .venv/bin/python /tmp/opencode/oc2-0061/figures.py <final SA edition> ci-sa-final
HTML widths + raster class: 121/121; PDF widths + image/caption body bounds: 121/121; DOCX widths + unchanged HTML/Word PNG pixels: 121/121
maximum PDF image + caption height: 603.459 pt; body: 705.827 pt
```

Every raster figure keeps its staged percentage in HTML, PDF and DOCX, the decoded PNG pixels are
unchanged in HTML and Word, and no figure plus caption is taller than the body.

`tools/scripts/edition_preview.py` reports zero skipped steps for SA and sample, and the sample (SVG
figures) is unchanged: 61 PDF pages before and after.

### 2. Table bodies, captions and heading/caption-only pages

`tools/scripts/pdf_float_audit.py` walks the tagged PDF structure tree, associates every caption with
its table, and classifies pages whose only tagged body content is a heading or a caption.

```text
$ .venv/bin/python tools/scripts/pdf_float_audit.py <before SA edition> before.json
{
  "all_tables": 376,
  "captioned_tables": 263,
  "pdf_pages": 511,
  "heading_or_caption_only": {
    "441": [
      "caption"
    ]
  }
}
split tables: 63 orphan captions: 5
$ .venv/bin/python tools/scripts/pdf_float_audit.py <after SA edition> after.json
{
  "all_tables": 376,
  "captioned_tables": 263,
  "pdf_pages": 514,
  "heading_or_caption_only": {}
}
split tables: 5 orphan captions: 0
$ .venv/bin/python tools/scripts/pdf_float_audit.py <after sample edition> sample.json
{
  "all_tables": 33,
  "captioned_tables": 2,
  "pdf_pages": 61,
  "heading_or_caption_only": {}
}
split tables: 0 orphan captions: 0
```

The sample is unchanged: 33 table bodies, none split, no orphan caption and no heading/caption-only
page before or after.

The five baseline orphan captions are gone: 6.6, 16.9, F.11, H.12 and H.17. Baseline page 441 held
only the F.11 caption.

**Split table bodies before (63) and after (5).** Only tables taller than the page body may split.

```text
before (6d464ef): 0.3 21-23; 0.5 24-25; 0.6 25-26; 1.3 34-35; 1.4 40-41; 2.1 50-51; 3.3 86-87;
4.4 104-105; 4.5 106-107; 5.3 122-123; 6.3 147-148; 6.7 158-159; 7.5 174-175; 7.6 175-176;
7.11 181-182; 7.12 184-185; 8.4 198-199; 8.12 210-211; 8.13 212-213; 8.14 214-215; 8.15 218-219;
9.1 225-226; 9.2 228-229; 9.9 249-250; 9.10 251-252; 10.5 267-268; 11.1 274-275; 11.7 283-284;
11.10 287-288; 12.2 295-296; 12.5 303-304; 12.6 304-305; 12.7 306-307; 13.1 310-311; 14.3 327-328;
14.6 332-333; 15.1 337-338; 16.3 353-354; 16.6 357-358; 16.10 361-362; 16.12 362-363;
16.15 366-367; 17.1 371-372; 18.2 390-391; BM.1 414-415; A.1 418-419; B.6 423-424; B.8 424-425;
B.14 427-428; E.2 431-432; E.5 432-433; E.7 433-434; F.3 436-437; F.7 438-439; F.10 439-440;
G.1 442-467; I.2 474-475; I.8 477-478; I.14 480-481; I.17 481-482; J.2 483-484; version history
(uncaptioned) 16-18 (3 pages); index (uncaptioned) 491-511 (21 pages)
after (f6db9af): version history (uncaptioned) 16-18 (3 pages); 0.3 21-23; G.1 443-468 (26 pages);
I.2 475-476; index (uncaptioned) 494-514 (21 pages)
```

The five remainders are the version history and the index, which are uncaptioned front/back matter,
plus Tables 0.3, G.1 and I.2. The Typst fit metadata marks exactly those three captioned floats as
taller than the body; the two uncaptioned tables run over several pages in every engine:

```text
$ quarto typst query index.typ '<handbook-table-fit>' --field value --root .   # final staged book
figure-wrapped table bodies 263 taller than the body: 3
  tbl-0-3: 1027.2 > 656.6 pt, starts p.22
  tbl-g-1: 16349.5 > 688.7 pt, starts p.438
  tbl-i-2: 720.4 > 683.3 pt, starts p.470
```

The Word probe measures its own page and reports 370/376 fitting. Its six oversized floats are the
five PDF splits plus Table F.7, which fits the Typst page (498.8 pt against a 683.3 pt body) but not
the Word page. Each engine splits only its own oversized floats; no table that fits its engine's page
is split. The ordinal sequence is identical in both documents, so the comparison is positional:

```text
$ .venv/bin/python /tmp/opencode/oc2-0061/cross_check.py after.json <after SA DOCX>
tables 376 word tables 376 labels aligned True
pdf split 5 word oversized 6 identical False
  uncaptioned-2: pages 16-18 (3), 23 rows
  Table 0.3: pages 21-23 (3), 49 rows
  Table G.1: pages 443-468 (26), 493 rows
  Table I.2: pages 475-476 (2), 17 rows
  uncaptioned-376: pages 494-514 (21), 529 rows
```

The sixth Word float is Table F.7; the PDF keeps it whole on one page.

### 3. Word

The build records its own measurement in `publication-manifest.json`:

```text
SA:     "docx_table_fit": "370/376 page-sized tables kept together (isolated LibreOffice measurement)"
sample: "docx_table_fit": "33/33 page-sized tables kept together (isolated LibreOffice measurement)"
```

Fitting tables carry the keep chain (`cantSplit` on every row, `keepNext` on every row except the
last, and on the caption after it) and the wrapper row; oversized tables keep their properties. The
end-to-end synthetic test asserts this on a real Quarto build, and unit tests pin caption discovery
in the `ImageCaption` layout cell.

The LibreOffice rendering of the DOCX is checked page by page: a caption printed below its table must
not be the first body content of a page, and no page may hold only a heading.

```text
$ .venv/bin/python /tmp/opencode/oc2-0061/lo_page_audit.py <baseline SA DOCX-as-LibreOffice.pdf>
pages: 601
caption-first pages: 15
heading-only pages: 0
$ .venv/bin/python /tmp/opencode/oc2-0061/lo_page_audit.py <R1 8ae8b17 SA DOCX-as-LibreOffice.pdf>
pages: 606
caption-first pages: 17
heading-only pages: 0
$ .venv/bin/python /tmp/opencode/oc2-0061/lo_page_audit.py <final SA DOCX-as-LibreOffice.pdf>
pages: 639
caption-first pages: 0
heading-only pages: 0
$ .venv/bin/python /tmp/opencode/oc2-0061/lo_page_audit.py <final sample DOCX-as-LibreOffice.pdf>
pages: 71
caption-first pages: 0
heading-only pages: 0
```

### 4. Figure background, light and dark

The SA reader site from the final build shows `mix-blend-mode: multiply` on Figure 1.2 in the light
theme only:

```text
$ .venv/bin/python /tmp/opencode/oc2-0061/screenshots.py <final SA edition> sa
{
  "light": { "blend": "multiply", "canvas": "rgb(246, 241, 231)", "width": 520.9375, "height": 514.59375 },
  "dark":  { "blend": "normal",   "canvas": "rgb(20, 26, 27)",     "width": 520.9375, "height": 514.59375 }
}
```

Screenshots: `sa-figure-1-2-light.png` and `sa-figure-1-2-dark.png` in `/tmp/opencode/oc2-0061/`;
the CI edition-preview artifact carries the same figure and tables pages under `screenshots/`.

### 5. Repository checks and CI

```text
$ make full PYTHON=.venv/bin/python
Ran 549 tests in 610.572s

OK
...
VERIFY (full): 7 check(s), 0 problem(s)
```

```text
$ gh run view 44169052627
checks            success    quickstart         success
template-install  success    wheel-install      success
publication-build success    edition-preview (template) success
edition-preview (sample, cesarcastrocuba/handbook-sample-01) success
edition-preview (solutions-architecture, cesarcastrocuba/handbook-solutions-architecture) success
```

The checks above are re-run on the downloaded artifacts of that run, not on a local build:

```text
$ .venv/bin/python tools/scripts/pdf_float_audit.py ci/edition ci.json | tail -1
split tables: 5 orphan captions: 0
$ .venv/bin/python /tmp/opencode/oc2-0061/lo_page_audit.py ci/libreoffice/book-docx-as-libreoffice.pdf
pages: 639
caption-first pages: 0
heading-only pages: 0
$ .venv/bin/python /tmp/opencode/oc2-0061/pdf_width_probe.py ci/edition
raster figures seen: 121, mismatched: 0
```

The local build of the same commit reproduces every number: 370/376 Word floats kept, 514 PDF pages,
5 split bodies and 0 orphan captions, 639 LibreOffice pages with 0 caption-first and 0 heading-only
pages, and 121/121 raster widths. The sample artifact is identical locally and in CI: 33/33 Word
floats kept, 61 pages, 0 splits, 0 orphans, 0 heading/caption-only pages, 71 LibreOffice pages, no
caption-first or heading-only page. The sample figures are SVG, so the raster-width checks do not
apply there; its HTML, PDF and DOCX are otherwise unchanged.

## Known gaps and not done

- LibreOffice pagination differs from the Typst PDF in page count; the DOCX keep logic is verified on
  the LibreOffice rendering, not on desktop Word. Owner acceptance in desktop Word, release tagging,
  publication and deployment are not part of this change.
- The `build.optimization.pdf` block and other 0062 behaviour are untouched.
- Rollback removes the figure hook/module/shared geometry wiring, the table measurement, lead group
  and probe hooks, the CSS rule and their tests together.
