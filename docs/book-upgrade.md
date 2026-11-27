# Book upgrade procedure

Books pin exact toolkit and profile versions. Upgrades are deliberate changes reviewed like any
other contribution; nothing upgrades automatically.

## Example: toolkit 0.14.2 to 0.16.1

1. Set `toolkit: "0.16.1"` in `book.yaml` and pin `0c89c38c9375d39cc9f2747469f545ee5dd7b561`
   (`toolkit-v0.16.1`) in `requirements.txt`. The profile stays `1.1.0`.
2. Copy the release workflow of template 1.10.0: its "Read the repository star count" step passes
   the count to the build in `HANDBOOK_STAR_COUNTS`, so the reading-site navbar shows "★ Star · N".
   Without the step the link is shown alone.
3. Every edition uses Inter and JetBrains Mono (toolkit 0.16.0); the Word edition embeds them, and
   the PDF body is 9.5 pt. Figures stay where they are cited and callouts may split across pages in
   PDF and Word (toolkit 0.15.0). Page numbers move; the Contents and the indexes are rebuilt.
4. Rebuild once and open the DOCX in desktop Word before the next tag.

## Example: toolkit 0.14.1 to 0.14.2

1. Set `toolkit: "0.14.2"` in `book.yaml` and pin `47c37e23819abb801b1c8635401d6b64e7e14fad`
   (`toolkit-v0.14.2`) in `requirements.txt`. The profile stays `1.1.0`, and the release workflow of
   template 1.9.0 needs no change.
2. The Word edition changes: captioned tables and figures are no longer inside Quarto's one-cell
   layout table, so desktop Word keeps a heading and a short introduction with the table or figure
   after them, and a short introduction between two headings keeps with the next heading. Page
   numbers in the DOCX can move; the Contents and the indexes are rebuilt by the build.
3. Cross-reference links: a location after another location in the same sentence ("…, Section 2.12
   sets …") becomes a link in every edition. Version lists stay plain.
4. Rebuild once and open the DOCX in desktop Word before the next tag.

## Example: toolkit 0.14.0 to 0.14.1

1. Set `toolkit: "0.14.1"` in `book.yaml` and pin `9c4355e5174c41dbbaaae7fe6304c247768b69d2`
   (`toolkit-v0.14.1`) in `requirements.txt`. The profile stays `1.1.0`, and the release workflow of
   template 1.9.0 needs no change.
2. The reading site changes only: raster figures blend with the cream page in the light theme and
   read as light lines on the dark page in the dark theme, and switching themes no longer moves the
   page. The PDF and DOCX builders are unchanged.
3. A preview build of a final `X.Y.0` book whose Document Control states `X.Y` now passes.
4. A patch edition `X.Y.Z` with `Z` > 0 must state its exact version in a book-owned Document Control
   `Version` row. Rebuild once and open the DOCX in desktop Word before the next tag.

## Example: toolkit 0.13.0 to 0.14.0

Toolkit `0.12.0` and `0.13.0` were never tagged (superseded by `0.14.0`, Owner decision 2026-11-17).
A book on `0.11.0` or `0.12.0` pins `0.14.0` directly and also applies the steps of the examples below
that it has not applied yet.

1. Set `toolkit: "0.14.0"` in `book.yaml` and pin `9dedd3c70bb7ad345eb2e3dbcb54773de9bc4ea2`
   (`toolkit-v0.14.0`) in `requirements.txt`. The profile stays `1.1.0`.
2. Lossless PDF compaction with qpdf is on by default. Install qpdf 11 or later in the book's release
   workflow next to `poppler-utils` and LibreOffice Writer, as template 1.9.0 does: a release build
   fails without it, a `--preview` build records `skipped` in `build.optimization.pdf`, and
   `--no-optimize` turns the compaction off.
3. Appendix headings read "Appendix A — Title" in every edition, with no standalone "Appendices" page
   in the PDF; in the reading site References and the Index sit after the Appendices part. No source
   change is needed.
4. A book whose `# Document Control` section has its own `| Field | Value |` table keeps only that
   table; its `Version` row must contain the edition version (or `major.minor` for a final `x.y.0`),
   otherwise the build fails. Books without such a table keep the generated one.
5. Tables that fit a page stay together with their caption and the heading before them, and raster
   figures with a pHYs density print at their natural size (capped by the text width and the
   tall-page rule) in every edition. Page counts change; rebuild and review the PDF.
6. Rebuild once and open the DOCX in desktop Word before the next tag.

## Example: toolkit 0.12.0 to 0.13.0 (never tagged)

1. Set `toolkit: "0.13.0"` in `book.yaml` and pin `4b9e3114d0a6c638eb7715784e7f0bb622f88322`
   (the 0.13.0 merge commit) in `requirements.txt`. The profile stays `1.1.0`.
2. Lossless size optimization is on by default: staged PNG figures are recompressed with a pixel
   check, and the DOCX and HTML zip use zlib level 9. Only those two files change; build with
   `--no-optimize` to reproduce 0.12.0's bytes.
3. Optional features, off unless the book opts in: `publication.cross_reference_links: true` links
   prose references such as "Section 6.2" or "Table 4.1"; `manuscript.glossary` (a reading-order file)
   adds stable glossary anchors and definition pointers; with it, `publication.index_vocabulary` (a
   YAML file validated against the packaged schema) adds the analytic Index as the last page. See
   `docs/publication-build.md`.
4. Update the book's release workflow from template 1.8.0. A book may add a `release-assets`
   Makefile target that writes its own deliverables to `$(RELEASE_ASSETS_DIR)`; the release then
   adds `book-extras.zip` and `EXTRAS-SHA256SUMS.txt`. Books without the target are unchanged.
   Catalog verification accepts that optional pair alongside the seven files and checks its checksum
   and ZIP contents.
5. Rebuild once and open the DOCX in desktop Word before the next tag.

## Example: toolkit 0.11.0 to 0.12.0 (never tagged) and profile 1.0.0 to 1.1.0

1. Set `toolkit: "0.12.0"` and the profile `version: "1.1.0"` in `book.yaml`, and pin
   `0824ddfaebd28f170f157fcb38641c7dc65d6c20` (the 0.12.0 merge commit) in `requirements.txt`. Profile `1.0.0`
   stays resolvable; `1.1.0` only relaxes rules (qualified callout titles, the appendix rule and the
   unit relaxations of `HUB-DEC-044`), so no manuscript text has to change.
2. Update the book's release workflow from template 1.7.0: the version input accepts `X.Y.Z` or
   `X.Y.Z-rc.N`, and a pre-release is published with `--prerelease --latest=false` while the Pages
   deployment and the deployed-site check still run.
3. Figure and table numbering now follows the displayed chapters (change `0051`). Tables and
   figures in unnumbered front matter become `0.1`, `0.2`, … (the sample's `Table 1` becomes
   `Table 0.1`), appendices use their letter (`Table A.1`) in every edition, and unnumbered back
   matter uses `BM.1`. A caption that starts with its own label (`Figure 1.1 — …`) keeps the text
   after the label; a label that disagrees with the figure's position fails the build. Rebuild
   once and check the List of Tables and List of Figures in the PDF and DOCX.
4. Reinstall dependencies, run the book's checks and build its editions once; open the DOCX in
   desktop Word before the next tag.
5. Book-owned extra release assets (change `0057`, gap G6): if the book generates additional
   deliverables (e.g. checklist exports, spreadsheets, data templates), define a `release-assets`
   target in `Makefile`. The release workflow validates deliverables, requires a clean working tree,
   packages them deterministically into `book-extras.zip`, and writes `EXTRAS-SHA256SUMS.txt`. Books
   without this target publish only the standard seven files. Catalog verification accepts the pair
   alongside the seven files and checks the extras checksum and ZIP.

## Example: toolkit 0.10.3 to 0.11.0

1. Set `toolkit: "0.11.0"` in `book.yaml` and pin
   `d4bef53af4c70f86fecdb13d1924c79353dde32f` (`toolkit-v0.11.0`) in `requirements.txt`.
2. Update the book's release workflow from template 1.6.0: export `page_url` from the deploy job,
   then add its dependent, read-only `verify` job. It checks out without persisted credentials,
   installs the pinned toolkit, passes `needs.deploy.outputs.page_url` through `PAGE_URL`, and
   runs `python3 -m handbook_toolkit.site_check "$PAGE_URL"`. Do not import hub scripts or add
   a second deployment; the check inspects the site that was just deployed.
3. For neutral review checklists, use
   `::: {.callout-note .review appearance="simple" icon=false title="Review Checklist"}`.
   Existing suffixed titles such as “Review Checklist — Example Chapter” retain the neutral PDF
   role; HTML and DOCX require the `review` class. Other manuscript content needs no migration.
4. Reinstall dependencies, run the book's checks and build its editions once. Inspect the compact
   web controls, uniform cream table rows and rules in HTML/PDF/DOCX, grey review boxes and cached
   Word indexes. Page transitions are removed; guarded reveals, progress and hover/focus remain.

Keep the existing LibreOffice installation and `--require-page-numbers` gate. A successful Pages
upload is followed by the deployed asset check; a missing stylesheet, script or image makes the
release workflow fail. The hub template release does not publish or redeploy an existing book.

## Supported upgrade path

1. Read the hub `CHANGELOG.md` for the target toolkit version and every version in between.
2. Check the hub's release notes for breaking CLI, profile or build-contract changes.
3. Update `toolkit` in `book.yaml` to the exact target version.
4. Update `profile.version` in `book.yaml` only when the target toolkit ships that profile and the
   owner has approved the editorial change.
5. Replace the full commit SHA in `requirements.txt` with the reviewed hub commit that contains the
   target toolkit version.
6. Reinstall the toolkit in the book's own venv.
7. Run `make check`, then `make full`.
8. Review the rendered HTML, PDF and DOCX, including page breaks, chapter headings and table widths.
9. Commit the pins, `requirements.txt`, any prose changes and the recorded evidence together.

Never use a version range. Never install the toolkit from a parent checkout or copy hub source into
the book.

## Incompatible changes

A major toolkit version may rename commands, change manifest fields or require a new profile. A
profile version change may require manuscript edits. When the changelog marks a change as
incompatible, upgrade in a dedicated branch, update the affected manuscript units, and record a
rendered review before requesting approval.

## Example: toolkit 0.10.1 to 0.10.2

Update `book.yaml` and the reviewed commit pin in `requirements.txt` to toolkit 0.10.2. Install
`libreoffice-writer` alongside `poppler-utils` in the book's release workflow, and pass
`--require-page-numbers` to `handbook-toolkit build-book`. Run local `make full`; a strict local
build can use `make build BUILD_FLAGS=--require-page-numbers` with the current template Makefile.
No manuscript edit or profile change is required. The template's released toolkit pin changes
separately; copying the toolkit's implementation into a book is not an upgrade.

Contents, List of Tables and List of Figures now open with cached page numbers and no update
prompt. They are LibreOffice's pagination using the packaged fonts; updating each field with F9
in desktop Word gives Word's pagination. The Owner's actual v0.5.0 Word check found the previous
dirty-field caches empty on open; 0.10.2 removes every dirty marker and updateFields request.
Table stripes now use direct cell shading because Word did not show the conditional banding.

Without LibreOffice/pdfinfo, optional builds warn on stderr and record title-only caches in the
manifest; they have no tabs or empty PAGEREF fields. Missing or failed probes block strict builds;
nonconvergent page numbers block every build. Non-decimal/chapter-prefixed page formats are not
silently treated as physical decimal pages. Inspect all three indexes and table banding in the
PR's sample edition-preview artifact in desktop Word before a release is tagged.

## Example: toolkit 0.9.1 to 0.9.2

Toolkit 0.9.2 fixes Word style definitions and replaces the static List of Tables with native
contents/caption fields. It originally attempted to show linked title-only caches while requesting field updates.
The Owner later found these caches empty on open in desktop Word for v0.5.0. Toolkit 0.10.2
supersedes that approach with verified numeric caches and no forced update; see the upgrade above.

Update the toolkit field in book.yaml to "0.9.2" and pin the reviewed toolkit commit in
requirements.txt. Run make full, rebuild all editions, inspect callout titles and banded tables,
and check Contents, List of Tables and (when the book has figures) List of Figures.
No manuscript edit is required. Existing caption bookmarks are normalized to Word-compatible
identifiers and internal hyperlinks/REF/PAGEREF fields are updated together. HTML labels are
unchanged. Fonts are not embedded; install the brand fonts for the intended metrics.

## Example: toolkit 0.9.0 to 0.9.1

`0.9.1` fixes the rendered details of the 0.9 design. The hub and book share a 1300 px desktop
column, the List of Tables sits in the book sidebar below Document Control, callout tables drop the
alternating stripe, `Review Checklist` uses a neutral callout role, web code and licence blocks use
the `code` token, and Word callouts become single-cell boxes with clickable table links and
full-width licences. It changes no command, descriptor field, profile rule or manuscript contract.

Migration (`HUB-DEC-014`):

1. Update `toolkit` in `book.yaml` to `"0.9.1"` and the commit in `requirements.txt`.
2. Remove any `Tables` entry from the book `navbar` in `publishing/_quarto.yml`. The build injects the
   List of Tables link into the book sidebar below Document Control only when the page has no Tables
   entry; a leftover navbar entry suppresses the sidebar link instead of adding a second one.
3. Run `make check` and `make full`; rebuild HTML, PDF and DOCX and inspect the sidebar Tables link,
   the callout boxes and the List of Tables page.
4. A book that wants the neutral review box adds the `review` class to that callout, for example
   `::: {.callout-note .review title="Review Checklist"}`. HTML and DOCX select it by class. The PDF
   template selects the neutral role by the `Review Checklist` title, so a renamed review box keeps
   the note colour in print. Books without either keep the note colour.

## Example: toolkit 0.8.0 to 0.9.0

`0.9.0` is a rendering refinement. It makes the hub cards compact and full-width, adds a dedicated
web List of Tables, aligns the book navbar to 1040 px, gives callouts one shared palette with atomic
pagination, adds table stripes in web/PDF/DOCX, and gives Word a cream page, shaded callout boxes,
a static List of Tables, centered captions and no outer table border. It changes no command,
descriptor field, profile rule or manuscript contract.

Migration (`HUB-DEC-014`):

1. Update `toolkit` in `book.yaml` to `"0.9.0"` and the commit in `requirements.txt`.
2. Run `make check` and `make full`; rebuild the HTML, PDF and DOCX and inspect the callouts, tables
   and the List of Tables page. Word shows the static List of Tables without waiting for a field
   update.
3. Books that stay on `0.8.0` keep their previous rendering.

## Example: toolkit 0.7.0 to 0.8.0

`0.8.0` changes the visual edition without changing the manuscript contract. It replaces Liberation
Sans/Arial with Source Sans 3 for text and Source Serif 4 for headings, both bundled as OFL subsets;
the PDF embeds the renamed fonts and the DOCX names the upstream families. The book HTML gains
generated chrome for the navbar, sidebar, links, title block and callouts, a compact type scale, table
captions below each table and a List of Tables. The DOCX reference gains `Contents`, page breaks before
top-level sections, teal first-row table headers, callout styles and a List of Tables field. The table
width algorithm now derives a floor from the longest unbreakable token.

Migration (`HUB-DEC-014`):

1. Update `toolkit` in `book.yaml` to `"0.8.0"`; keep the profile pin unchanged.
2. Replace the hub commit in `requirements.txt` with the reviewed commit that contains `0.8.0`.
3. Run `make check` and `make full`. No manuscript change is required.
4. Inspect the HTML, PDF and DOCX. Word populates the TOC and List of Tables fields when it updates
   fields; LibreOffice displays their titles but not the generated entries.
5. If the book overrides `_quarto.yml`, keep the search/repository navigation and review its custom
   CSS: the generated book stylesheet loads before book CSS, so book rules still win where they set a
   value.

Books that stay on `0.7.0` keep their previous rendering and remain publishable.

## Example: toolkit 0.6.0 to 0.7.0

`0.7.0` changes the rendered output on every surface. It adds a packaged design-token contract and
one brand typeface: Liberation Sans, self-hosted as WOFF2 for the HTML edition and embedded in the
PDF, with Arial named in the DOCX as its metric-compatible equivalent. JetBrains Mono remains the code
font. A generated `design-tokens.css` carries the HTML variables and a light/dark scheme, and the table
filter keeps narrow columns above a floor so labels do not break mid-word. It changes no CLI command,
descriptor field, profile rule or payload set.

Migration (`HUB-DEC-014`):

1. Update `toolkit` in `book.yaml` to `"0.7.0"`; keep the profile pin unchanged.
2. Replace the hub commit in `requirements.txt` with the reviewed commit that contains `0.7.0`.
3. Run `make check` and `make full`. No manuscript change is required; only the toolkit pin in
   `book.yaml` and the commit in `requirements.txt` change.
4. Inspect the HTML, PDF and DOCX before release. The PDF body type and table header colour change;
   the DOCX body style changes from Selawik to Arial. If the book has its own CSS that sets colours,
   fonts or table rules, confirm it still matches the book's identity; the generated stylesheet loads
   first, so book CSS wins where it sets a value.
5. Keep the release workflow uploading the generated HTML archive as-is. It now contains the
   `design-tokens.css`, seven WOFF2 files and both `OFL.txt` notices.

Books that stay on `0.6.0` keep their previous rendering and remain publishable.

## Example: toolkit 0.5.0 to 0.6.0

`0.6.0` adds a fifth payload, `book.md`: one GitHub-flavoured Markdown file in reading order, meant
for search, diffing and AI tools. It also writes publication manifest schema `1.1`, which lists five
artifacts; schema `1.0` remains valid so already published releases keep verifying. Migration
(`HUB-DEC-014`):

1. Update `toolkit` in `book.yaml` to `"0.6.0"`; keep the profile pin unchanged.
2. Replace the hub commit in `requirements.txt` with the reviewed commit that contains `0.6.0`.
3. **Do not** change `publication.formats` in `book.yaml`. It keeps listing `html`, `pdf` and `docx`;
   the Markdown edition is implicit, like the source bundle.
4. Update the release workflow if it uploads a fixed list of files: it must upload seven assets,
   including `book.md`.
5. Run `make check` and `make full`, and inspect `book.md` in the build output. Figures appear as
   their captions and table and figure counters are sequential in that file.

The release gate accepts both manifest versions: a catalog entry that still points at a `1.0`
release (six assets) keeps verifying until that book publishes a `1.1` release.

## Example: toolkit 0.4.0 to 0.5.0

`0.5.0` changes the rendered output: it adds the print-layout stage, bundled Selawik, JetBrains Mono and
Liberation Sans fonts, the HTML stylesheet and a regenerated DOCX reference document. It also lets the manuscript validator accept letter-prefixed appendix numbers such as `A.2`. It changes no command, descriptor field or profile rule. Update the
`toolkit` value in `book.yaml` and the commit in `requirements.txt`, run the checks, and inspect a full
build before release, because the published pages will differ. Builds made from hub commits between
`988773c` and `5f96202` reported `0.4.0` although their rendering had already changed.

## Example: toolkit 0.3.0 to 0.4.0 and profile 0.2.0 to 1.0.0

`0.4.0` adds the public `build-book` assembly path, `validate-references` and the packaged render
resources. `1.0.0` keeps every approved `0.2.0` rule unchanged and adds a required explicit
`automated`/`assisted`/`manual` classification for each rule. Books that remain on `0.2.0` still
resolve that packaged snapshot.

```bash
# In the book clone
git switch -c chore/upgrade-toolkit-0.4.0
sed -i 's/^toolkit: .*/toolkit: "0.4.0"/' book.yaml
sed -i 's/^  version: .*/  version: "1.0.0"/' book.yaml
# Replace the hub commit in requirements.txt with the reviewed commit
source .venv/bin/activate
python3 -m pip install --upgrade -r requirements.txt
handbook-toolkit version
make check
make full
```

The template `1.0.0` already carries these pins, `publishing/_quarto.yml`, the licenses and the
`check`/`build`/`full` Makefile targets. A book copied from an older template can adopt those files
from the new template, but it must keep its own content, attribution and catalog metadata.

## Toolkit 0.9.2 to 0.10.0

The reading site uses the same Cosmo base for both schemes, with generated token Sass layers and
a packaged layout stylesheet. In publishing/_quarto.yml, replace dark: darkly with dark: cosmo.
The toolkit stages the final light/dark theme layers; books should remove any legacy navbar Tables
entry. Nonempty table, figure and listing indexes are native Quarto chapters immediately after the
first page, participating in search, breadcrumbs and sidebar navigation. The old post-render Tables
page and sidebar injection are gone. Manuscript edits are not required. Print and Markdown retain
their existing independent indexes. Template release pins are updated separately.

### Reading experience in 0.10.0

The toolkit generates a web cover and keeps Document Control on a separate page. It groups the
sidebar by the existing reading-order groups and places caption lists in front matter. No manual
cover, list chapter, sidebar entry or footer needs to be added to publishing/_quarto.yml. Remove a
legacy navbar Tables entry if present. PDF, DOCX and Markdown retain their existing reading order.

The summary comes from book.yaml catalog.summary; publishing/metadata.yaml may provide subtitle,
author and status. The footer carries the edition, source-derived date and licence on every page.
For a custom publication domain set site_url in metadata (or book.site-url in the Quarto config).
GitHub repository URLs use the publication pipeline's standard owner.github.io/repository/ URL.
Placeholder or non-GitHub repositories need an explicit site URL for canonical links.

Only known URLs should be supplied as release_url and edition_urls in metadata; edition_urls may
map pdf, html, docx, markdown and source to immutable asset URLs. Unknown links and all release
links in preview builds are omitted. The toolkit never invents a release URL from a future version.
Favicon, description, Open Graph, Twitter metadata and canonical links use native Quarto options.

Motion uses native CSS progressively and is disabled by the reduced-motion preference. No script
or external resource is added. The warning title accent is slightly darker to meet normal-text AA
on its tint (4.57:1); the DOCX reference is regenerated from that same token.

## Toolkit 0.10.0 to 0.10.1

Toolkit `0.10.0` cannot build the PDF or the DOCX of a book that has a figure in any page other
than the first while its first page lives in a different directory (for example an introduction
under `front-matter/` and a figure in `chapters/`). Quarto stops with "file not found" for a path
such as `manuscript/chapters/manuscript/front-matter/../images/figure.svg`. Do not pin `0.10.0`;
pin `0.10.1`. No manuscript or configuration edit is required: image paths stay relative to the
file that uses them.

## Toolkit 0.10.2 to 0.10.3

Until `0.10.2` the reading site loaded its stylesheets, fonts and favicon from `.handbook-render/`,
a hidden directory. A static host that does not publish hidden paths serves the pages without
styles; `actions/upload-pages-artifact` v4 and later drop hidden files, and the book template's
release workflow uses v5. A book that still deploys with v3 was not affected. From `0.10.3` the
directory is `handbook-render/` and `build-book` fails if the site archive holds any hidden path.
No manuscript or configuration edit is required. Do not pin `0.10.2` or older in a book that
deploys with a current Pages action.

## Template onboarding enhancements (G1, G10, G11)

1. **Pre-release editions (`release.yml`):** The release workflow accepts pre-release versions
   matching `X.Y.Z-rc.N` (for example `3.1.0-rc.1`) alongside stable `X.Y.Z`. Releases with `-rc.N`
   are published with `--prerelease --latest=false` in GitHub Releases while still deploying to Pages
   and executing the `site_check` verification step.
2. **Branch protection status check (`Fast checks`):** Required branch protection rules on `main`
   should specify the exact status check `Fast checks` (reported by `ci.yml`).
3. **Book-owned bootstrap (`initialize_book.py`):** The `initialize-book` workflow replaces the
   generic template README with a clean book README containing the book title, catalog summary,
   pointers to `AGENTS.md`, `NOTICE.md`, optional `PROJECT_STATUS.md` and `DECISIONS.md`, and
   local development commands.
