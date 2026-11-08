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
