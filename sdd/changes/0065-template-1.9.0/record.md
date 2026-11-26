# Change 0065 — Template 1.9.0

Prepare template `1.9.0` pinned to toolkit `0.14.0` at `80b833875bce2018b6c15a2ee0acc4726b659175`
(merge of PR 104, change `0064`), keeping standard profile `1.1.0`. Its workflows already install
qpdf (change `0062`); its release workflow publishes a book's `release-assets` (change `0057`).

Owner decision (2026-11-17): templates `1.7.0` and `1.8.0` are superseded and never tagged; only
`template-v1.9.0` is tagged after `template-v1.6.0`. The coordinator publishes the mirror and the
tag after review, merge and the Owner's approval.

## Scope

Template `book.yaml`, `requirements.txt` and README; `tools/tests/test_template.py`; hub README,
CHANGELOG `[1.9.0]` (and `1.7.0`/`1.8.0` marked superseded), the upgrade example `0.13.0` → `0.14.0`
(the `0.12.0` and `0.13.0` examples marked never tagged) and STATUS.

## Owner gates (not part of the merge)

This PR's edition previews build the template, the sample and the Solutions Architecture Handbook
(book main, `3.1.0-rc.1`) with toolkit `0.14.0`. The Owner checks the three `book.docx` files in
desktop Word, reads the PDF and HTML editions, then approves `toolkit-v0.14.0` and
`template-v1.9.0`. The book's `v3.1.0-rc.1` follows after the book pins toolkit `0.14.0`.

## Verification evidence

In the pull request, from commands run on its exact HEAD.

Rollback boundary: revert this change. No mirror, tag, catalog entry or book release changes here.
