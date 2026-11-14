# Record — Template `1.5.1` and toolkit `0.10.2`

**Change:** `0039-release-0.10.2`. **Released:** 2026-11-14. **Toolkit:** `0.10.2`.
**Implementer pull request:** this release branch. **Reviewer:** a different agent; the Owner merges.

## What the release contains

Toolkit `0.10.2` carries change `0038`:

- Word Contents, List of Tables and List of Figures open with cached page numbers obtained from a
  private LibreOffice bookmark probe and verified by a second conversion.
- No field is marked dirty and no `updateFields` request is written, so Word shows the caches without
  a prompt; the reader can still update a field with F9 for Word's own pagination.
- Table stripes use direct cell shading, because Word did not display the conditional banding.

Also on `main` since `0.10.1` and shipped in `0.10.2`:

- The generated Quarto portal engine (change `0033`, PR 63), including the five guide pages, the
  living Design page and the native navigation/search, now deployed (`HUB-DEC-041`, PR 64).
- The `design-preview` command that renders the living style guide from the packaged tokens.
- Markdown figure and table numbering aligned with the other editions (change `0041`, PR 67).

The development tooling merged in the same window does not change the toolkit API: CI actions are
pinned by commit and `requirements-dev.txt` by version (change `0040`, PR 66).

Template `1.5.1` carries the pin and the version statements. The `0.10.1` to `0.10.2` note in
`docs/book-upgrade.md` asks a book to install `libreoffice-writer` and pass
`--require-page-numbers`; the template release workflow already does both (change `0038`), so no
other template file changes.

## Pins

| File | Value |
| --- | --- |
| `template/book/book.yaml` | `toolkit: "0.10.2"` |
| `template/book/requirements.txt` | `handbook-toolkit @ git+https://github.com/cesarcastrocuba/handbooks-hub.git@5e3c6b9c9e38bc17324fba1642fc8646f6f7f444#subdirectory=tools` |
| `template/book/README.md` | heading `# Book template 1.5.1`, pins toolkit `0.10.2` |
| `.github/workflows/ci.yml` | no edit: `template-install` derives the expected version from `template/book/book.yaml` |

`5e3c6b9c9e38bc17324fba1642fc8646f6f7f444` is the commit tag `toolkit-v0.10.2` points to. The tag
is created only after the Owner opens the CI-built edition preview `book.docx` in desktop Word and
confirms the indexes, F9 on each and the banding; the approved preview is the acceptance record.

## Steps still to run after merge

1. Export `template/book/` with `python3 tools/scripts/export_template.py`, push it to
   `cesarcastrocuba/handbooks-template` and tag `template-v1.5.1`.
2. Upgrade the sample book to toolkit `0.10.2`, run its checks, review the rebuilt editions and
   publish `v0.5.1`, which carries the Word index fix. `v0.4.2` and `v0.5.0` keep the defect.
3. Update the catalog to `v0.5.1` with the `catalog-update` workflow, review the pull request and
   merge it so `portal-pages` redeploys.
