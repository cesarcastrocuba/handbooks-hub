# Change 0073 — Toolkit 0.14.1

Prepare toolkit `0.14.1`, a patch release with the fixes merged after `toolkit-v0.14.0`
(`9dedd3c`). They come from the Owner's review of the deployed Solutions Architecture `v3.1.0`
(2026-11-18) and from preparing that release:

- change `0068` (PR 109): preview builds validate a book-owned Document Control `Version` row
  against the release version they preview;
- change `0071` (PR 115): web raster figures blend with the light canvas inside revealed sections,
  invert to light lines on the dark canvas, and the light and dark themes share one navbar size.

Changes `0069` (PR 110, catalog verification accepts the optional `book-extras.zip` pair) and
`0070` (PR 112, qpdf in every hub workflow, git identity in the numbering-parity fixtures,
bounded download retries) are also listed under `[0.14.1]`. They act in the hub, which runs them from
`main`.

Change `0072` (authors in the catalog and portal) is not part of this release. Its entries
stay under `[Unreleased]` when it merges.

## Write set

`tools/pyproject.toml`, `tools/src/handbook_toolkit/__init__.py`, `tools/tests/test_cli.py`,
`tools/tests/test_build.py` (the fixture book's toolkit pin must match the builder),
`CHANGELOG.md` and this record.

The template still pins toolkit `0.14.0`. Template `1.9.1` pins this release in a separate change.

## Owner gates before the tag `toolkit-v0.14.1`

1. The PDF and DOCX builders are unchanged. The Owner decides whether a desktop Word check is
   needed for this tag.
2. Approval of the tag in the chat.

## Verification evidence

The pull request records the evidence, from commands run on its exact HEAD.

Rollback boundary: revert this commit. No tag, template, mirror, catalog entry or book release
changes here.
