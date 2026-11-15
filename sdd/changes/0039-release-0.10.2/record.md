# Record — Template `1.5.1` and toolkit `0.10.3`

**Change:** `0039-release-0.10.2`. **Released:** 2026-11-15. **Toolkit:** `0.10.3`.
**Implementer pull request:** this release branch. **Reviewer:** a different agent; the Owner merges.

## What the release contains

Toolkit `0.10.3` carries change `0038`:

- Word Contents, List of Tables and List of Figures open with cached page numbers obtained from a
  private LibreOffice bookmark probe and verified by a second conversion.
- No field is marked dirty and no `updateFields` request is written, so Word shows the caches without
  a prompt; the reader can still update a field with F9 for Word's own pagination.
- Table stripes use direct cell shading, because Word did not display the conditional banding.

Also on `main` since `0.10.1` and shipped in `0.10.3`:

- Change `0042`: the reading site and the Quarto portal serve their stylesheets, fonts and favicon
  from `handbook-render/` instead of the hidden `.handbook-render/`, which static hosts do not
  publish. The HTML payload inspection and the portal builder reject any hidden path.
- The generated Quarto portal engine (change `0033`, PR 63), including the five guide pages, the
  living Design page and the native navigation/search, now deployed (`HUB-DEC-041`, PR 64).
- The `design-preview` command that renders the living style guide from the packaged tokens.
- Markdown figure and table numbering aligned with the other editions (change `0041`, PR 67).

Change `0040` (PR 66, pinned CI actions and development dependencies) and change `0041` (PR 67,
Markdown figure and table numbering) are part of `0.10.3`.

Toolkit `0.10.2` was tagged and is not pinned by any template or book, because the reading site it
builds loads its stylesheets from a hidden directory that static hosts do not publish (change
`0042`). Template `1.5.1` pins `0.10.3` instead.

Template `1.5.1` carries the pin and the version statements. The `0.10.1` to `0.10.2` note in
`docs/book-upgrade.md` asks a book to install `libreoffice-writer` and pass
`--require-page-numbers`; the template release workflow already does both (change `0038`), so no
other template file changes.

## Pins

| File | Value |
| --- | --- |
| `template/book/book.yaml` | `toolkit: "0.10.3"` |
| `template/book/requirements.txt` | `handbook-toolkit @ git+https://github.com/cesarcastrocuba/handbooks-hub.git@58384afadce80015e5ee84955dd14eb2f90d5020#subdirectory=tools` |
| `template/book/README.md` | heading `# Book template 1.5.1`, pins toolkit `0.10.3` |
| `.github/workflows/ci.yml` | no edit: `template-install` derives the expected version from `template/book/book.yaml` |

`58384afadce80015e5ee84955dd14eb2f90d5020` is the commit tag `toolkit-v0.10.3` points to.

The Owner tested the CI-built `book.docx` in desktop Word twice on 2026-11-14: the first build kept
the indexes but Word emptied the caption lists on "Update entire table", and after the caption-marker
fix of PR 70 the Owner accepted the new build. The two tests and their results are recorded in
[change `0038`'s owner test](../0038-word-indexes/owner-test.md); that acceptance is why the tag
exists.

## Steps still to run after merge

1. Export `template/book/` with `python3 tools/scripts/export_template.py`, push it to
   `cesarcastrocuba/handbooks-template` and tag `template-v1.5.1`.
2. Upgrade the sample book to toolkit `0.10.3`, run its checks, review the rebuilt editions and
   publish `v0.5.1`, which carries the Word index fix. `v0.4.2` and `v0.5.0` keep the defect.
3. Update the catalog to `v0.5.1` with the `catalog-update` workflow, review the pull request and
   merge it so `portal-pages` redeploys.
