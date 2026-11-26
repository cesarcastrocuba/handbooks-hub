# Changelog

All notable changes to the hub are recorded here. The format follows Keep a Changelog; versions use
semantic versioning once the toolkit is published.

## [Unreleased]

## [0.15.0] - Unreleased

Toolkit minor release prepared by change `0082`. It carries the changes merged after
`toolkit-v0.14.2`: change `0081` (print figure and callout placement, PRs 133–136) changes how
the Word and PDF editions lay out figures and callouts; changes `0079` and `0080` fix the clean-
clone gate and make `book-html.zip` reproducible. The Owner checked the CI-built 6.0.0 DOCX of PR
136 in desktop Word. The tag needs the Owner's approval.

### Changed

- Figures stay right after the text that introduces them in the PDF and Word editions, and print
  at 85% of their stated size (change `0081`, from the Owner's checks of the Solutions
  Architecture Handbook 6.0.0 preview). PDF figures no longer float. In both editions a figure
  that nearly fits the gap in front of it is scaled further. Neither step goes below 75% of the
  natural size. `build.tool_versions.docx_figure_placement` records the Word counts and
  `<handbook-figure-fit>` records the PDF decisions. Callout boxes stay whole; a pitfall and its
  decision are separate boxes; in Word no paragraph inside a box, and no spacer or paragraph before
  it, keeps with next, so a pitfall that fits stays on the page before its decision and a box that
  starts a page has no empty line above it. A PDF review checklist whose title names decisions
  keeps the checklist colour. In the HTML light theme a raster figure no longer shows white
  while the scroll reveal fades it in.

### Fixed

- The Markdown leak check also catches the given spelling of a build's repository and output paths
  when they are reached through a symlink, as macOS does with `/var`; `stage_figures` accepts a
  workspace reached through a symlink. The `clean-clone` workflow installs Playwright and Chromium so
  that its no-skip gate passes with the browser tests running (change `0079`, issue 113).
- `book-html.zip` is byte-reproducible for the same commit: the build removes the render-time
  `lastmod` that Quarto writes into `sitemap.xml`, as the portal already did; both now share
  `artifacts.omit_sitemap_times` (change `0080`, issue 98).

## [1.9.2] - 2026-11-20

Template release prepared by change `0078`. Template `1.9.2` pins toolkit `0.14.2` at
`47c37e23819abb801b1c8635401d6b64e7e14fad` (tag `toolkit-v0.14.2`) and
keeps standard profile `1.1.0` and the workflows of `1.9.0`. The coordinator publishes the template
mirror and tag after the merge and the Owner's approval.

### Changed

- `book.yaml` and `requirements.txt` pin toolkit `0.14.2`; the Word edition gains the float and
  section-introduction fixes of change `0076`, and every edition the links of change `0075`.

## [0.14.2] - 2026-11-20

Toolkit patch release prepared by change `0077`. It carries the changes merged after
`toolkit-v0.14.1`: changes `0075` (cross-reference links) and `0076` (Word floats and section
introductions) change the toolkit that books install, from the Owner's review of the Solutions
Architecture Handbook 4.0.0 preview; change `0072` changes the catalog verification and the portal,
which run from the hub. The PDF and HTML builders are unchanged apart from the added links. The Owner
checked the CI-built 4.0.0 DOCX of change `0076` in desktop Word. The tag needs the Owner's approval.

### Added

- Catalog schema `1.2` records each book's `authors` (change `0072`): the catalog lists the author of
  both books, `catalog_verification` compares the field with `publishing/metadata.yaml` in the
  release's `book-source.zip`, and the catalog automation keeps the field and the schema version when
  it moves a book to a newer release. Schema `1.1` catalogs without `authors` stay valid, and the
  listing request asks for the author names.

### Changed

- The portal shows the authors on each card (`By …`) and on the generated cover, adds an Author
  select beside the topic chips, the search and the sort, matches author names in the search, and
  names the publisher in the footer (change `0072`).

### Fixed

- Cross-reference links: a handbook location ("Section 8.4", "Table 8.8") no longer starts a version
  list, so a later location in the same sentence is linked ("…, Section 2.12 sets …"). Software and
  standard version lists ("TLS 1.2 minimum, 1.3 preferred") stay plain (change `0075`).
- Word: captioned tables and figures are no longer wrapped in Quarto's one-cell layout table. Desktop
  Word did not carry a heading's keep-with-next into that wrapper, so a heading or a short
  introduction stayed at the foot of a page while its table or figure moved to the next one. A short
  introduction between two headings now also keeps with the next heading (change `0076`).

## [1.9.1] - 2026-11-19

Template release prepared by change `0074`. Template `1.9.1` pins toolkit `0.14.1` at
`9c4355e5174c41dbbaaae7fe6304c247768b69d2` (tag `toolkit-v0.14.1`) and keeps standard
profile `1.1.0` and the workflows of `1.9.0`. The coordinator publishes the template mirror and tag
after the merge and the Owner's approval.

### Changed

- `book.yaml` and `requirements.txt` pin toolkit `0.14.1`; the reading site gains the figure and
  theme fixes of change `0071`.

## [0.14.1] - 2026-11-19

Toolkit patch release prepared by change `0073`. It carries the fixes merged after `toolkit-v0.14.0`:
changes `0068` and `0071` change the toolkit that books install; changes `0069` and `0070` change the
hub's catalog verification and workflows, which run from the hub and are listed here for
completeness. The PDF and DOCX builders are unchanged. The tag needs the Owner's approval.

### Fixed

- Web reading site: raster figures blend with the light canvas even inside revealed sections, and
  invert to light lines on the dark canvas (change `0071`); the theme toggle no longer changes the
  navbar height because both schemes share one navbar padding, and a scheme-parity test keeps every
  non-colour SCSS variable identical.
- qpdf 11 or later is installed and version-checked in every hub workflow that runs the toolkit tests
  or builds a book (change `0070`). `portal-pages.yml` and `catalog-update.yml` now install
  `poppler-utils qpdf libreoffice-writer`, `ci.yml` installs qpdf for its check jobs and verifies the
  version in `publication-build`, and `clean-clone.yml` installs qpdf and LibreOffice on Linux and
  macOS. A test fails if a workflow that runs `make check`/`make full`, `build-book` or the build
  tests does not install and verify qpdf. The release verifier also retries transient HTTP
  429/5xx responses up to three times (2/4/8 s, or a numeric `Retry-After` up to 30 s) without
  writing partial files.
- Catalog release verification accepts the optional `book-extras.zip` and `EXTRAS-SHA256SUMS.txt`
  pair alongside the seven declared assets (change `0069`). One of the pair alone, or any other
  name, still fails; the verifier checks the sums line, the ZIP checksum and archive integrity, and
  rejects unsafe member paths. Extras are not catalog asset roles.
- Preview builds validate a book-owned Document Control `Version` row against the release version
  they preview (change `0068`): the `-preview` suffix is removed only for that check, so a final
  `3.1.0` book that states `3.1` previews, while release builds stay strict and exact. The suffix is
  defined once in the toolkit and reused by `tools/scripts/edition_preview.py`.

## [1.9.0] - 2026-11-18

Template release prepared by change `0065` and repinned by change `0067`. Template `1.9.0` pins toolkit `0.14.0` at
`9dedd3c70bb7ad345eb2e3dbcb54773de9bc4ea2` (tag `toolkit-v0.14.0`) and keeps standard
profile `1.1.0`. It also carries everything prepared for templates `1.7.0` and `1.8.0`, which are
superseded and never tagged (Owner decision, 2026-11-17): `template-v1.9.0` is the first template tag
after `template-v1.6.0`. The template mirror and tag are published by the coordinator after the merge
and the Owner's approval.

### Changed

- Template `release.yml` and `ci.yml` install qpdf 11 or later, and a release whose manifest shows no
  compacted PDF fails (change `0062`).

## [0.14.0] - 2026-11-18

Toolkit release prepared by change `0064`: changes `0060`, `0061`, `0062` and `0063`, the fixes from
the Owner's review of the toolkit 0.13.0 previews, and change `0066` (repinned by change `0067`),
the fix from the Owner's Word and PDF check of the 0.14.0 previews. It also carries everything prepared for `0.12.0`
and `0.13.0`, which are superseded and never tagged (Owner decision, 2026-11-17): `toolkit-v0.14.0`
is the first toolkit tag after `toolkit-v0.11.0`. The tag needs the Owner's approval and desktop Word
check, because the DOCX gains appendix labels, keep-with-next tables and natural-size figures.

### Added

- Page-sized tables stay with their captions and with the heading or lead-in that precedes them in PDF and Word; raster figures keep their natural physical size and the tall-page cap in every edition, with light-only raster background blending in HTML (change `0061`).
- Lossless PDF compaction with qpdf (change `0062`), on by default: `build-book` runs qpdf 11 or
  later with `--deterministic-id --object-streams=generate --compress-streams=y
  --stream-data=compress --recompress-flate --compression-level=9`, verifies the result with
  `qpdf --check` and an unchanged page count, and keeps it only when it is strictly smaller. A
  release build fails without qpdf; an explicit `--preview` build records `skipped` in the manifest;
  `--no-optimize` turns the compaction off with the PNG and ZIP optimization. The manifest adds
  `build.optimization.pdf` (tool, version, status, and bytes before and after) and hub CI, the
  template CI and the template release workflow install qpdf.

### Fixed

- Print editions no longer show a white box around raster figures (change `0066`). Typst and Word
  embed a staged colour-to-alpha copy of a white-backed PNG, while HTML keeps the original image and
  its light-only CSS blending. Figure ids, widths, captions, anchors and the Markdown edition are
  unchanged; the source PNGs in the book repository are never modified.
- PDF bookmarks keep their section numbers (change `0063`, issue #99). The heading numbering
  function is no longer `context`: Typst cannot resolve a contextual function while it assembles the
  PDF outline, so numbered headings lost their number and kept only the separating space in the
  bookmark. Chapter and section bookmarks now read exactly like the Contents page (`1. Why Handbooks
  Fail`, `3.3 Diagrams, Tables and Explicit Cross-References`); unnumbered front matter, References,
  the Index and the literal appendix entries are unchanged.
- Appendices and Document Control normalization (change `0060`):
  - Appendix headings read the literal "Appendix X — Title" in the body, the PDF Contents and bookmarks, the DOCX heading and cached contents, and the HTML page title and sidebar, for sources that carry the label and for `{.unnumbered}` and numbered ones alike, with no double space after the dash.
  - Appendix sections are staged as literal "A.N Title" headings, so their numbering is the same in HTML, PDF, DOCX and Markdown.
  - The print editions keep one flat chapter list: Quarto's native `book.appendices` no longer opens a standalone page holding only "Appendices".
  - The reading site builds an "Appendices" part that holds only the appendices; References and the analytic Index stay top level after it and the References breadcrumb reads "References". The post-render HTML rewriting is removed.
  - Appendix figure and table labels (`tbl-a-1`, `fig-f-1`) read "Table A.1" and "Figure F.1" in HTML, DOCX and the list pages; section anchors, glossary pointers, cross-reference links and Index locations keep their parity.
  - A book-owned Document Control `| Field | Value |` table is validated against the edition version instead of receiving a duplicate table.


## [1.8.0] - Superseded, never tagged

Superseded by `1.9.0` (Owner decision, 2026-11-17); its changes ship in `template-v1.9.0`.

Template release prepared by change `0059`. Template `1.8.0` pins toolkit `0.13.0` at
`4b9e3114d0a6c638eb7715784e7f0bb622f88322` (`toolkit-v0.13.0` once the Owner approves the tag) and keeps standard
profile `1.1.0`. Its release workflow publishes a book's own `release-assets` as `book-extras.zip`.
The template mirror and tag are published by the coordinator after the merge and the Owner's approval.

### Added

- Book-owned extra release assets (change `0057`, gap G6): template `release.yml` optionally runs `make release-assets RELEASE_ASSETS_DIR="$RUNNER_TEMP/extra-assets"` when defined in the book's `Makefile`, verifies that the working tree remains clean, validates regular file constraints (names matching `^[A-Za-z0-9][A-Za-z0-9._-]*$`, caps of max 100 files, 10 MB per file, 50 MB total, and no collisions with publication payloads), packages them deterministically into `book-extras.zip`, and writes `EXTRAS-SHA256SUMS.txt`. Books without the target publish only the standard seven files.

## [0.13.0] - Superseded, never tagged

Superseded by `0.14.0` (Owner decision, 2026-11-17); its changes ship in `toolkit-v0.14.0`.

Toolkit release prepared by change `0058`: changes `0052`, `0053` and `0055`. The tag
`toolkit-v0.13.0` needs the Owner's approval and desktop Word check, because the DOCX gains links,
the Index and recompressed images.

### Added

- Opt-in `publication.cross_reference_links`: staged, whitelist-only prose navigation with stable section anchors and cross-page HTML links (change `0052`, G8); existing books remain opted out.
- Opt-in glossary definition pointers and a final analytic Index (change `0053`, G9/G4), with declared glossary/vocabulary inputs, cross-edition internal links and protected print rows; prose term auto-linking remains off.
- Lossless artifact size optimization (change `0055`), on by default: staged PNG diagrams are losslessly recompressed (filter 0, zlib level 9) with exact pixel-identity verification before Quarto rendering, and ZIP distributions (Word `.docx` package and HTML site archive `book-html.zip`) are compressed at zlib level 9. The `--no-optimize` build flag opts out of both PNG recompression and ZIP level 9 compression.

## [1.7.0] - Superseded, never tagged

Superseded by `1.9.0` (Owner decision, 2026-11-17); its changes ship in `template-v1.9.0`.

Template release prepared by change `0056`. Template `1.7.0` pins toolkit `0.12.0` at
`0824ddfaebd28f170f157fcb38641c7dc65d6c20` (`toolkit-v0.12.0` once the Owner approves the tag) and
standard profile `1.1.0`. The template mirror and tag are published by the coordinator after the
merge and the Owner's approval. Hub CI's edition preview also builds the Solutions Architecture
Handbook.

### Changed

- Template `release.yml` accepts pre-release versions `X.Y.Z-rc.N` alongside stable `X.Y.Z`, publishing pre-releases with `--prerelease --latest=false` while keeping Pages deployment and site verification active (Gap G1).
- Template `initialize_book.py` writes a clean, tailored book README with book title, summary, contributor pointers, and verification commands (Gap G11).
- Align author guide and template quickstart documentation to specify the exact required branch protection status check `Fast checks` (Gap G10).

## [0.12.0] - Superseded, never tagged

Superseded by `0.14.0` (Owner decision, 2026-11-17); its changes ship in `toolkit-v0.14.0`.

Toolkit release prepared by change `0054`: changes `0050` and `0051`. The tag `toolkit-v0.12.0`
needs the Owner's approval and the Owner's desktop Word check of a DOCX built with it, because the
DOCX table and figure labels change.

### Added

- Standard profile version 1.1.0 (`HUB-DEC-044`, change `0050`):
  - Qualified callout titles (G3): callout titles may include domain qualifiers preceding the title on word boundaries (e.g. `Architecture Review Checklist — Requirements` satisfies `Review Checklist`).
  - Appendix rule (G2): appendices in chapter mode and appendix mode are validated by a dedicated appendix rule (single H1, non-empty body) instead of textbook chapter anatomy.
  - Unit relaxations: permits multiple closing elements of the same kind, block list bodies following a label paragraph, and ignores table cells in the unit scanner.
  - A bold paragraph label inside a heading section of the same name (`**Worked example.**` inside
    `## 17.5 Worked Example`) is section body prose, not a wrong-form heading. This fourth
    relaxation goes beyond the three named in `HUB-DEC-044 (2)` and needs the Owner's
    confirmation before the tag.
- Packaged snapshot `tools/src/handbook_toolkit/profile_data/standard-1.1.0.yaml`; profile 1.0.0 and 0.2.0 remain resolvable.

### Fixed

- Figure and table numbering follows the displayed chapters in every edition (Gap G12, change
  `0051`): numbered chapters use `N.M`, appendices use their letter (`A.1`) in HTML, DOCX, PDF and
  Markdown, tables and figures in unnumbered front matter are numbered `0.N` continuously, and those
  in unnumbered back matter `BM.N`. An author-written caption prefix (`Figure 1.1 — …`) is stripped
  when it matches its position, and a mismatch fails the build. The List of Tables and List of
  Figures carry the same labels. Visible change: the sample's front-matter `Table 1` becomes
  `Table 0.1`.

## [1.6.0] - 2026-11-15

Template release. Template `1.6.0` pins toolkit `0.11.0` at
`d4bef53af4c70f86fecdb13d1924c79353dde32f` (`toolkit-v0.11.0`). It carries the preview-aligned
scale and controls, uniform cream table bodies without stripes in every edition, no page
transition, and the example chapter's neutral Review Checklist role. The release workflow checks
the deployed reading site's assets with `site_check` in a read-only job after Pages deployment.
The template mirror and tag are published by the coordinator after this change is merged.

## [0.11.0] - 2026-11-15

### Changed

- Align the portal and reading site with the Owner's design preview: token-driven Bootstrap scale,
  rounded compact controls, smaller book cards and whole-card home guide links.
- Use uniform surface-filled table bodies and border rules across HTML, PDF and DOCX. Web tables
  and PDF tables have rounded corners; PDF keeps page splitting and Word keeps native square corners.
- Remove cross-document page transitions and render-blocking capture metadata; retain reduced-motion
  guards, reading progress, once-only reveals, card stagger and hover/focus/theme interactions.

### Fixed

- Remove decorative hover arrows from buttons while retaining lift and keyboard focus.
- The template's example Review Checklist now opts into the documented neutral review role in
  HTML and DOCX, matching PDF. This content correction is queued for the later template 1.6.0
  release; the current template version and toolkit pin are unchanged here.

## [1.5.1] - 2026-11-15

Template release. Template `1.5.1` pins toolkit `0.10.3` (`58384af`). The release workflow already
installs LibreOffice and passes `--require-page-numbers` (change `0038`), so the book's indexes open
with cached page numbers; no other template file changes. Toolkit 0.10.2 was tagged but is not
pinned by any template or book, because the reading site it builds loads its stylesheets from a
hidden directory that static hosts do not publish (change `0042`).

## [0.10.4] - 2026-11-15

### Added

- `python3 -m handbook_toolkit.site_check URL`: checks a deployed site from the outside by
  requesting every local stylesheet, script and image its pages load. `portal-pages` runs it after
  each deployment.

### Changed

- The reading site and Quarto portal share token-driven layered page transitions, once-only
  reveals, reading progress and native hover/focus, details and theme micro-interactions, guarded
  by the reduced-motion preference and feature support.

### Fixed

- The online release gate (`catalog_verification`) applied the build invariants of the current
  toolkit to releases built by older versions, so a new Word or site rule rejected an edition that
  was valid when it was published and blocked the portal deployment. `inspect_payload` now takes
  `build_invariants`; the release gate checks integrity, format and local targets only. This
  change is hub-side: books do not need `0.10.4`.

## [0.10.3] - 2026-11-15

### Fixed

- The reading site and the Quarto portal loaded their stylesheets, fonts and favicon from a hidden
  directory, `.handbook-render/`. Static hosts do not publish hidden paths: the deployed Quarto
  portal rendered without styles, and so would any book deployed with `actions/upload-pages-artifact`
  v4 or later, which the book template uses. The directory is now `handbook-render/`, and the HTML
  payload inspection and the portal builder reject any hidden path.

## [0.10.2] - 2026-11-14

The Markdown edition now uses native chapter-aware figure, table and listing labels and cross-
references matching the other editions, including unnumbered front matter and appendices.

Native Word indexes now open with linked, cached page numbers obtained from a private LibreOffice
bookmark probe and verified by a second conversion. No fields are marked dirty and the document
requests no update on open. F9 remains available to repaginate each index in desktop Word, and
"Update entire table" rebuilds each list: the caption markers are not formatted as hidden text,
which made desktop Word skip them.
Captioned data tables use direct cell banding; callout tables stay plain. Releases require the
probe with `build-book --require-page-numbers`; local builds without it warn and record title-only
caches. Decimal page-number restarts are respected; unsupported formats fail a required probe.

Also included since 0.10.1: an opt-in generated Quarto portal (`build-portal --engine quarto`) and
`design-preview`, with shared token-driven code colours. Portal deployment and its page-weight
exception are governed separately by change 0033.

## [1.5.0] - 2026-11-14

Template release. Template `1.5.0` pins toolkit `0.10.1` (`d4480f9`) and adapts the shipped Quarto
configuration to the new reading site: `publishing/_quarto.yml` already selects `dark: cosmo` and has
no legacy navbar Tables entry, so the `0.9.2` to `0.10.0` upgrade note requires no further template
change. Toolkit `0.10.0` was tagged but is not pinned by any template or book, because `0.10.1` fixes
its figure-path defect in the PDF and DOCX editions (change `0037`).

## [0.10.1] - 2026-11-14

### Fixed

- PDF and DOCX builds failed for a figure in any page other than the first when the first page
  lives in a different directory: the image path was rebased for every chapter. The first page's
  images are now rebased when it is staged, and the image part of the Pandoc filter is removed.

## [0.10.0] - 2026-11-14

### Changed

- Generate reading-site theme layers from tokens with one base in light and dark; package layout CSS.
- Render nonempty table, figure and listing indexes as native Quarto pages without HTML repair.
- Separate publication orchestration, staging, identity and edition packaging into focused modules.
- Add a generated web cover, native part navigation, edition footer, favicon and social metadata.
- Add an original SVG example figure and native CSS motion that respects reduced-motion preferences.
- Validate component contrast; darken the light/print warning accent for accessible small titles.

## [1.4.2] - 2026-11-14

Template release. Template `1.4.2` pins toolkit `0.9.2` (`2e29438`) and changes nothing else: the
`0.9.1` to `0.9.2` upgrade note requires no manuscript or configuration edit. The hub
`template-install` job derives the expected version from `template/book/book.yaml`, so the pin is the
only update it needs.

## [0.9.2] - 2026-11-13

### Fixed

- Word callouts use the reference document's real style names, with one definition per style.
- Contents and caption lists are native Word fields with linked cached entries. Until a viewer updates the fields, cached entries contain linked titles only,
  without tabs, empty page references or dangling dot leaders; no page numbers are invented.
- Lists of Tables, Figures and Listings share one registry and appear only for existing entries.
  The PDF now includes a conditional List of Figures.
- Word table banding comes from reference styles, callout tables stay unbanded, font aliases are
  declared, and callout boxes fit the text column.
- The DOCX gate rejects duplicate/undefined styles, invalid authored property containers,
  malformed fields and broken bookmark references. A real figure and LibreOffice conversion
  exercise the build in CI.
- First-page image paths are rebased in a native Pandoc filter when staged as index.qmd.
- The HTML Tables page has one title rule without the extra empty band.

## [0.9.1] - 2026-11-13

### Changed

- Hub and book web now share a 1300 px desktop column, so the library chrome and the three-column book align.
- The List of Tables moved from the top navigation to the book sidebar, directly below Document Control; the generated page reuses the book chrome.
- Callout-contained tables drop the alternating stripe in HTML, PDF and DOCX and inherit the callout tint.
- `Review Checklist` uses a new neutral callout role in HTML, PDF and DOCX; section 2.2 now uses the warning and important roles for its two closing callouts.
- Web code and licence blocks use the `code` token, matching the PDF block colour and spanning the full column.
- DOCX callouts are single-cell tables with an aligned left rule and keep-together rows; titles carry their palette colour directly; tables keep body text left and captions centred.
- The Word List of Tables is a static, clickable index that links to each table bookmark; licence blocks reflow to the full text width.

## [0.9.0] - 2026-11-13

### Changed

- Hub cards and header: full-width intro, single-line edition links and the preview tag style.
- Book web: 1040 px navbar, bold display brand, Pages link for Handbook Hub, dedicated List of Tables page, no colored title band and full-width prose.
- Callouts share one accent/tint palette in web, PDF and DOCX; PDF callouts are atomic and do not split across pages; Word callouts are real shaded boxes with keep-together rules.
- Table rows alternate with a `table_stripe` token in web, PDF and DOCX; outer table borders are removed and captions stay centered below.
- Word pages use the cream canvas, a static List of Tables, `updateFields`, teal first-row headers and a 10.5 pt body.

## [0.8.0] - 2026-11-13

### Changed

- Replaced Liberation Sans/Arial with a real editorial type system: Source Sans 3 for text and
  Source Serif 4 for headings, both self-hosted as renamed OFL subsets for the web and embedded in
  the PDF. The DOCX names the upstream families; the metric-compatible Arial fallback is gone.
- Compacted the portal to the reviewed card and control scale, and rebuilt the book chrome from
  tokens: canvas navbar and sidebar, teal links, near-black headings, title-block band and a soft
  divider.
- Unified table captions and numbering. The build no longer injects bold `Table N.M` paragraphs;
  every table is a Quarto float with a deterministic id, captions sit below the table in italic,
  and the PDF, HTML and DOCX share chapter-based numbers. The PDF gains a List of Tables.
- Replaced the table width floor with a longest-token calculation, so long labels such as
  `Detailed content specification` and `Continuous unversioned edits` no longer overflow or break
  mid-word.
- Rebuilt the DOCX reference: Contents title, page breaks before each top-level section, teal
  first-row table headers with white bold text, body/table/callout text at 10.5 pt, callout title
  and body styles for Note/Tip/Warning/Important, and a List of Tables.

### Fixed

- The book site no longer inherits the grey Bootstrap navbar or the blue default links; it uses the
  same canvas, accent and display face as the library portal.
- The portal uses the tighter preview scale (15 px body, 8 rem cover, compact format buttons) rather
  than the oversized card layout.

## [0.7.0] - 2026-11-12

### Added

- A packaged semantic design-token contract: `design/tokens.json`, its schema, a loader and tests
  that require every colour role to cover light, dark and print, and that recompute each declared
  WCAG contrast pair.
- One brand typeface: Liberation Sans, subsetted and self-hosted as WOFF2 under the CSS name
  `Handbook Sans`, with JetBrains Mono for code. The PDF embeds the family and the DOCX names its
  metric-compatible equivalent, Arial.
- Generated surfaces: portal `:root` variables and fonts, a book `design-tokens.css` with a
  `quarto-dark` scheme, Typst design constants and a DOCX reference document generated from the
  tokens.
- Portal contribution path: a **Source and issues** link derived from the verified release URL,
  accent-insensitive card search and a correct singular result count.
- Template reader path: full-book search, `repo-url`/`repo-actions`, a library link, release
  downloads, a light/dark theme and two plain-language issue forms. Initialize rewrites the
  `OWNER/REPOSITORY` placeholder.
- Library portal: generated book covers, download buttons per edition, text search, static guide
  sections (platform, author path, publishing and withdrawal, contributing, questions and answers)
  and an `llms.txt` index for AI tools.
- Catalog schema `1.1`: optional `latest_release.assets` with a direct download link per artifact
  role. `update_catalog.py` records the links for a newly listed release and online verification
  checks each link against the release manifest. A `1.0` catalog stays valid.
- Catalog update automation: the `catalog-update` workflow validates a published release, updates an
  existing catalog entry, verifies the result and leaves a branch for review. It is manual-dispatch
  only and defaults to a dry run.
- Thin Claude Code and GitHub Copilot adapters, the adapter contract and a drift check that rejects
  missing, drifting or over-long adapters.
- Linux and macOS clean-clone matrix for the hub and the public sample book, with a post-merge run on
  `main` at `ad1f5b8`.
- Operations runbook covering toolkit/profile upgrade, rollback, release withdrawal and incident
  response.

### Fixed

- The Markdown leak guard in `build-book` compares the rendered text with its CommonMark backslash
  escapes removed as well as raw, so it detects a path such as `/tmp/build_dir` even when the gfm
  writer renders it as `/tmp/build\_dir`. This closes the real gap behind the intermittent
  `test_local_path_in_the_markdown_fails_the_build` failure. It ships in this release.

## [0.6.0] - 2026-11-10

### Added

- A fifth payload, `book.md`: one GitHub-flavoured Markdown edition of the whole book in reading
  order, rendered with Quarto `gfm` from the same source commit. It opens with the document-control
  fields (title, version, commit, licenses), keeps headings, tables, callouts and cross-reference
  text, and replaces each figure by its caption because one file cannot carry the images.
- `inspect_payload(..., version=...)` checks the Markdown edition: UTF-8, document-control header,
  version and commit identity, and no raw `<script>` or absolute local path.
- An upgrade note for `0.5.0` to `0.6.0` in `docs/book-upgrade.md`.

### Changed

- Publication manifest schema `1.1` lists five artifacts (`html`, `pdf`, `docx`, `markdown`,
  `source`). Schema `1.0` with four artifacts stays valid, so releases published before `0.6.0` keep
  verifying.
- `write_manifest` writes schema `1.1` and requires the five payloads; `verify_publication` accepts
  both versions and rejects a version whose payload set does not match.
- `catalog_verification` derives the expected release asset count from the manifest instead of a
  fixed six, so a `1.0` release keeps six assets and a `1.1` release has seven.
- The template pins toolkit `0.6.0`; `publication.formats` in `book.yaml` still lists only `html`,
  `pdf` and `docx`, because the Markdown edition is implicit like the source bundle.

### Migration

A book bumps `toolkit` and its `requirements.txt` commit, keeps `publication.formats` unchanged, and
updates any release workflow that uploads a fixed list of six files to upload seven.

## [0.5.0] - 2026-11-08

### Added

- Print-layout stage for Typst builds, the packaged HTML stylesheet and the DOCX reference document.
- Bundled Selawik, JetBrains Mono and Liberation Sans fonts with their license files. See `NOTICE.md`.
- `tools/scripts/generate_reference_docx.py`, which generates the DOCX reference document without any Pandoc template part.

### Changed

- Toolkit `0.5.0` names the rendering changes integrated after `0.4.0`. Hub commits from `988773c` to
  `5f96202` carried those changes while still reporting `0.4.0`, so manifests of sample releases
  `v0.1.1` to `v0.2.0` report `0.4.0` and only their pinned commit identifies the code used.
- The template pins toolkit `0.5.0`.
- Packaged style comments no longer name a vendor.
- The code font is JetBrains Mono instead of Cascadia Code, and styles no longer fall back to fonts from the build environment.

### Fixed

- Typst heading, table-of-contents and print layout, and packaging of the render resources in the wheel.
- The manuscript validator accepts letter-prefixed appendix numbers such as `A.2`.

## [0.4.0] and earlier

### Added

- Hub onboarding guide at `docs/setup.md` and a README quickstart covering reader/contributor/
  maintainer/book-author paths, tested Linux prerequisites, in-repo `.venv` install, no-make checks
  and missing-pip/venv troubleshooting.
- Pinned-toolkit installation instructions and `requirements.txt` for the independent book template,
  with the future Quarto/publication toolchain kept separate from current validators.
- Initial hub scaffold: governance, architecture and contract documents, phased implementation plan,
  proposed standard editorial profile, JSON schemas, book template, empty catalog and lightweight SDD
  records.
- `handbook-toolkit` 0.1.0 with deterministic catalog, profile and book validators and unit tests.
- `handbook-toolkit` 0.2.0 adds `validate-manuscript` for structural section-pilot and chapter
  validation against an explicit profile, without requiring visuals.
- `handbook-toolkit` 0.3.0 adds `build-book`: exact toolkit-pin enforcement, staged source/manuscript
  validation, one Quarto HTML/Typst/DOCX render with `--no-execute`, payload inspection,
  manifest/checksum identity and atomic finalization, without publishing. It also runs the
  reference/label/image gate and stages the packaged Quarto/Typst render resources. `--profile` is
  optional; the exact book pin resolves from the installed packaged profile.
- `handbook-toolkit` 0.4.0 publishes the assembled build, reference and render-resource APIs as the
  supported Phase 2 surface. The generated Typst project sets a white brand primary and explicit
  black link color, which removes the orange-book chapter-title block that overflowed the right page
  edge while keeping links readable.
- Standard profile `1.0.0`: every approved `0.2.0` rule is unchanged and each rule now carries an
  explicit `automated`, `assisted` or `manual` classification. The packaged `0.2.0` snapshot remains
  resolvable.
- Book template `1.0.0`: `publishing/_quarto.yml`, publication metadata, `LICENSE`, `LICENSE-CODE`,
  `NOTICE.md`, and `make check`/`build`/`full` targets against the pinned toolkit. A regression test
  copies the template outside the hub, replaces identifiers, runs the checks and performs a real
  six-file build.
- `docs/book-upgrade.md` records the supported toolkit/profile upgrade procedure, including the
  `0.3.0` to `0.4.0` and profile `0.2.0` to `1.0.0` path.
- Basic CI running the fast and full repository checks.
- CI `wheel-install` job that builds the wheel, verifies the packaged schemas, installs it in an
  isolated environment and validates a book outside the hub checkout.
- Dual licensing (`LICENSE`, `LICENSE-CODE`) and attribution notice.

### Changed

- The default standard profile is now `1.0.0`; the template pins toolkit `0.4.0` and profile `1.0.0`,
  and its requirements file points at the reviewed hub commit.
- Owner approved the Phase 1 foundation, the dual-license defaults, the broad technical/software
  audience and standard profile `0.2.0`, and authorized root integration of the reviewed
  `feat/topic-neutral-profile` branch. Pilot approval and release remain unauthorized. See
  `sdd/changes/0005-owner-approvals/`.
- Standard profile `0.2.0`: the mandatory architecture-specific checklist is now a topic-neutral
  `Review Checklist`; figures and tables are optional when they would not help the reader, and their
  absence is not an exception. The template pins the new profile version. See
  `sdd/changes/0004-topic-neutral-profile/`.

### Fixed

- The toolkit now ships its JSON Schemas as package data and resolves them from the installed package
  by default. An independent book can validate without a hub checkout or a vendored `schemas/`
  directory. `--schemas` remains an explicit override. See
  `sdd/changes/0002-toolkit-packaged-schemas/`.
- Documented CLI examples now put global `--root` and `--schemas` options before the subcommand, and a
  regression test parses every documented example. See
  `sdd/changes/0003-cli-docs-and-wheel-ci/`.

### Notes

- No GitHub repository was created, no site was deployed, no release was published and this change
  did not modify the sample-book or reference-handbook content. The sample repository was scaffolded
  concurrently by its own session.
