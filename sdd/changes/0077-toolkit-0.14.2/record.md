# Change 0077 — Toolkit 0.14.2

Prepare toolkit `0.14.2`, a patch release with the changes merged after `toolkit-v0.14.1`
(`9c4355e`). They come from the Owner's review of the Solutions Architecture Handbook 4.0.0
preview (2026-11-20):

- change `0075` (PR 121, `f9e5eb1`): a handbook location no longer starts a version list, so
  "…, Section 2.12 sets …" is linked;
- change `0076` (PR 122, `267d02c`): Word captioned tables and figures are no longer wrapped in
  Quarto's one-cell layout table, and a short introduction between two headings keeps with the next
  heading.

Change `0072` (PR 116, catalog schema `1.2` with authors, authors on the portal) is listed under
`[0.14.2]` for completeness; it acts in the hub, which runs it from `main`.

## Write set

`tools/pyproject.toml`, `tools/src/handbook_toolkit/__init__.py`, `tools/tests/test_cli.py`,
`tools/tests/test_build.py` (the fixture book's toolkit pin must match the builder),
`CHANGELOG.md` and this record.

The template still pins toolkit `0.14.1`. Template `1.9.2` pins this release in a separate change.

## Owner gates before the tag `toolkit-v0.14.2`

1. Desktop Word check of the CI-built DOCX: done on the `edition-preview (solutions-architecture)`
   DOCX of PR 122 (run 44735543751, book `f1cf3c0`, sha256
   `54cf8de5bd8d7044e34d059631d7eea3458fff5356ad122a14a365305d4611ac`): "All good" (2026-11-20).
   This pull request only changes version numbers.
2. Approval of the tag in the chat.

## Verification evidence

The pull request records the evidence, from commands run on its exact HEAD.

Rollback boundary: revert this commit. No tag, template, mirror, catalog entry or book release
changes here.
