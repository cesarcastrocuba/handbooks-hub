# Record — Template `1.4.2` and toolkit `0.9.2`

**Change:** `0034-release-0.9.2`. **Released:** 2026-11-14. **Implementer pull request:** this release
branch. **Reviewer:** a different agent; the Owner merges.

## What the release contains

Toolkit `0.9.2` ships work package WP1 of change `0027`:

- Word callout styles use the reference document's real style names, with one definition per style.
- Contents and caption lists are native Word fields with linked cached entries; before a viewer
  updates the fields they hold linked titles only, without tabs, page numbers or empty dot leaders.
- Table banding comes from the reference styles, callout tables stay unbanded, font aliases are
  declared and callout boxes fit the text column.
- The DOCX gate rejects duplicate or undefined styles, invalid authored property containers,
  malformed fields and broken bookmark references.
- The List of Tables page has one title rule, without the extra empty band.

Template `1.4.2` carries only the pin and the version statements. The `0.9.1` to `0.9.2` note in
`docs/book-upgrade.md` requires no manuscript or configuration edit, so no other template file
changes.

## Pins

| File | Value |
| --- | --- |
| `template/book/book.yaml` | `toolkit: "0.9.2"` |
| `template/book/requirements.txt` | `handbook-toolkit @ git+https://github.com/cesarcastrocuba/handbooks-hub.git@2e294388ea4e4039744b14e4164301f6c085f587#subdirectory=tools` |
| `template/book/README.md` | heading `# Book template 1.4.2`, pins toolkit `0.9.2` |
| `.github/workflows/ci.yml` | no edit: `template-install` derives the expected version from `template/book/book.yaml` and compares it with `handbook-toolkit version` |

`2e294388ea4e4039744b14e4164301f6c085f587` is the commit of tag `toolkit-v0.9.2`, read with
`git rev-list -n1 toolkit-v0.9.2`.

## Steps still to run after merge

1. Export `template/book/` with `python3 tools/scripts/export_template.py`, push it to
   `cesarcastrocuba/handbooks-template` and tag `template-v1.4.2`.
2. Upgrade the sample book to toolkit `0.9.2`: re-pin `book.yaml` and `requirements.txt`, run its
   checks, review the rebuilt Word edition and publish the next release.
3. Update the catalog to that release with the `catalog-update` workflow, review the pull request and
   merge it so `portal-pages` redeploys.
