# Change 0059 — Template 1.8.0

Prepare template `1.8.0` pinned to toolkit `0.13.0` at `4b9e3114d0a6c638eb7715784e7f0bb622f88322`
(merge of PR 94, change `0058`), keeping standard profile `1.1.0`. It ships the release-workflow
change `0057` (PR 92): a book's own `release-assets` target is published as `book-extras.zip` with
`EXTRAS-SHA256SUMS.txt`. The coordinator publishes the mirror and the tag `template-v1.8.0` after
review, merge and the Owner's approval, after `template-v1.7.0`.

## Scope

Template `book.yaml`, `requirements.txt` and README; `tools/tests/test_template.py`; hub README,
CHANGELOG `[1.8.0]`, the upgrade example `0.12.0` → `0.13.0` and STATUS.

## Owner gates (not part of the merge)

This PR's edition preview builds the Solutions Architecture Handbook from book main, which opts in to
links, glossary pointers and the Index (book PR 12). The Owner checks that `book.docx` in desktop Word
and decides: optimization on by default, `qpdf` for the PDF, the two link-range points from PR 88's
review, then approves `toolkit-v0.13.0`, `template-v1.8.0` and the book's `v3.1.0`.

## Verification evidence

In the pull request, from commands run on its exact HEAD.

Rollback boundary: revert this change. No mirror, tag, catalog entry or book release changes here.
