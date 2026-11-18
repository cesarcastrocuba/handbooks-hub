# Change 0067 — Toolkit 0.14.0 includes change 0066; template 1.9.0 repins

The Owner checked the CI-built DOCX and PDF of the template 1.9.0 previews (run 44190542041) in
desktop Word and found one remaining issue: raster figures showed a white box on the cream page in
Word and PDF. Change `0066` (PR 106, merged at `9dedd3c70bb7ad345eb2e3dbcb54773de9bc4ea2`) fixes it
with print-only transparent copies.

Neither `toolkit-v0.14.0` nor `template-v1.9.0` is tagged, so the version numbers stay: toolkit
`0.14.0` now means hub commit `9dedd3c`, and template `1.9.0` pins it.

## Write set

`template/book/requirements.txt` (pin `9dedd3c`), `docs/book-upgrade.md` (0.14.0 pin),
`CHANGELOG.md` (`[0.14.0]` and `[1.9.0]` notes), `STATUS.md` (toolkit and template rows) and this
record. No toolkit code changes.

## Owner gates before the tags

1. Desktop Word check of the figures in the DOCX built by this PR's edition previews (and a look at
   the PDF), on top of the round-3 check that found everything else correct.
2. Approval in chat of `toolkit-v0.14.0` (at the merge of this change or `9dedd3c`) and
   `template-v1.9.0` (mirror export from this change's merge).

## Verification evidence

In the pull request, from commands run on its exact HEAD.

Rollback boundary: revert this change. No tag, mirror, catalog entry or book release changes here.
