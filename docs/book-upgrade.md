# Book upgrade procedure

Books pin exact toolkit and profile versions. Upgrades are deliberate changes reviewed like any
other contribution; nothing upgrades automatically.

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

## Example: toolkit 0.9.0 to 0.9.1

`0.9.1` fixes the rendered details of the 0.9 design. The hub and book share a 1300 px desktop
column, the List of Tables sits in the book sidebar below Document Control, callout tables drop the
alternating stripe, `Review Checklist` uses a neutral callout role, web code and licence blocks use
the `code` token, and Word callouts become single-cell boxes with clickable table links and
full-width licences. It changes no command, descriptor field, profile rule or manuscript contract.

Migration (`HUB-DEC-014`):

1. Update `toolkit` in `book.yaml` to `"0.9.1"` and the commit in `requirements.txt`.
2. Remove any `Tables` entry from the book `navbar` in `publishing/_quarto.yml`. The build injects the
   List of Tables link into the book sidebar below Document Control, so the navbar entry would
   duplicate it.
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
