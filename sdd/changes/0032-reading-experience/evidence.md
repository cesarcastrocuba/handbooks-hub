# WP4 implementation evidence

Base: WP3 PR 55, integrated updates through 78c2db9 and main merge 4881680. The implementation
uses toolkit 0.10.0. Sample checkout is read-only at 70383d125841006b8a73c5906cfa6dda4741300b;
its metadata is 0.4.1, so the explicit preview is 0.4.1-preview, not a published release claim.
Quarto 1.11.9 / Pandoc 3.10 / Typst 0.15.1 / Python 3.12 / LibreOffice 24.2.

## Commands and results

- Created and activated .venv; installed requirements-dev.txt and the edition-preview requirements;
  installed Chromium. tinycss2 is a dev dependency for structural CSS tests. Pillow was installed
  only to assemble local screenshot contact sheets.
- make full: 374 tests passed in 166.141 s; fast verify 5 checks/0 problems; full verify
  7 checks/0 problems. This includes the current main catalog-verification tests.
- Focused test_build.py: 24 tests passed in 130.318 s; test_template.py: 18 passed in 32.365 s;
  test_docx_native.py: 26 passed. The root-index real build proves source preservation and direct
  link rebasing; the SVG build checks native figure fields, alt text, links and unshaded wrappers.
- edition_preview.py --repo /home/ubuntu/github/handbook-sample-01 --output /tmp/wp4-sample-final:
  succeeded, seven edition files, LibreOffice PDF and 12 screenshots.
- edition_preview.py --template --output /tmp/wp4-template-final:
  succeeded, seven edition files, LibreOffice PDF and 16 screenshots. The tracked source asset is
  the generated original SVG, not an external image. The preview export is a temporary repository.
- verify_publication and validate_docx on both preview edition directories: passed; manifest and
  checksums match all five payloads. OpenXmlValidator SDK 3.3.0 / Office2019: 0 errors for both DOCX.
- pdfinfo / pdffonts on both PDFs: sample 59 A4 pages, template 4 A4 pages; Handbook Sans, Handbook
  Serif and JetBrains Mono embedded and subsetted. No PDF JavaScript. Poppler emits its preexisting
  Suspects-object diagnostic on both baseline and new Typst PDFs; rendering succeeds.
- LibreOffice smoke: sample 68 pages, template 5. Inspected template PDF List of Figures/page 3 and
  figure/page 4; Word-as-PDF pages 3/4 show a linked cached title without dangling leaders and a
  plain centered figure with an italic caption below, followed by intact colored callout boxes.
  Inspected sample PDF pages 6/16 and Word pages 8/10/16 for retained text, table and callout behavior.

## Browser and visual evidence

edition_preview.py generated all referenced screenshots. Inspected light/dark at 1440 and 390:

- Sample cover, chapter 2 callouts/tables and native Tables page (12 captures).
- Template cover, separate Document Control, Figures page and example chapter (16 captures).

Cover and footer identify the edition; Start reading is visible, correctly labeled and routes to
chapter 1. Sidebar parts retain chapter numbering (chapter 2/table 2.1 in the sample; figure 1.1 in
the template). Figure/caption/alt text and front-matter list links are present. Previews omit unknown
download links. Native navigation, footer and one title rule are visible on the list pages.

A local HTTP Chromium check covered 12 sample viewport/scheme/page combinations: document width
matches viewport at 1440/390; reduced-motion reports no animations; keyboard Tab reaches the skip
link, Enter reaches main, and Start reading reaches chapter 1. Every sample HTML page (17) has the
edition footer and native canonical link. The sampled script inventory is identical to baseline:
13 same-origin Quarto scripts plus four native inline/JSON script blocks, no toolkit script.

Computed contrast (light/dark): warning title 4.57/8.14, footer 5.34/7.87, table-header link
7.65/5.28, body-table link 6.80/9.57. Link fixtures were placed in real rendered table cells to
exercise the compiled selectors. Token tests also cover striped-row links and every callout role.
Motion is parsed structurally and rejects declarations outside the reduced-motion guard.

Authored important declarations remain zero. No fallback or requested feature is deferred. Desktop
Word is not run; field updates and its own pagination remain a publication check. Local /tmp paths
are reproducible inspection evidence; generated publication files are not committed to source.
