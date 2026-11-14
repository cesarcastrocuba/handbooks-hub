# Changelog

All notable changes to the hub are recorded here. The format follows Keep a Changelog; versions use
semantic versioning once the toolkit is published.

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
