# Change 0064 — Toolkit 0.14.0

Prepare toolkit `0.14.0`, the fixes from the Owner's review of the toolkit 0.13.0 previews of the
Solutions Architecture Handbook and the sample (round 3 of Phase 6). It releases the toolkit work
merged since `0.13.0` (PR 94, `4b9e311`):

- change `0060` (PR 96): literal "Appendix X — Title" labels in every edition, no standalone
  "Appendices" page, References and Index outside the Appendices part in HTML, and a book-owned
  Document Control table validated instead of duplicated;
- change `0061` (PR 100): page-sized tables kept together with their caption and the heading or
  lead-in before them (PDF and Word), natural-size raster figures with the tall-page cap in every
  edition, light-theme background blending of raster figures in HTML;
- change `0062` (PR 97): lossless PDF compaction with qpdf, on by default;
- change `0063` (PR 102): PDF bookmarks keep their section numbers.

Owner decision (2026-11-17): `0.12.0` and `0.13.0` are superseded and never tagged; only
`toolkit-v0.14.0` (and template `1.9.0`) are tagged. The CHANGELOG records both as "Superseded,
never tagged"; their entries ship in this release.

## Write set

`tools/pyproject.toml`, `tools/src/handbook_toolkit/__init__.py`, `tools/tests/test_cli.py`,
`tools/tests/test_build.py` (the fixture book's toolkit pin must match the builder) and `CHANGELOG.md`.
Review follow-up of PR 97: the attribution in `sdd/changes/0062-pdf-qpdf/record.md` now names the
durable source (tag `v3.0.0`, `13d295b`, of `cesarcastrocuba/solutions-architecture-handbook`)
instead of a temporary local path.

The template still pins toolkit `0.13.0`; template `1.9.0` pins this release in a separate change.

## Owner gates before the tag `toolkit-v0.14.0`

1. Desktop Word check of the DOCX of the Solutions Architecture Handbook, the sample and the
   template built with this commit (appendix headings, keep-with-next tables, figure sizes, links,
   Index).
2. Approval of the tag in the chat.

## Verification evidence

In the pull request, from commands run on its exact HEAD.

Rollback boundary: revert this commit. No tag, template, mirror, catalog entry or book release changes here.
