# Change 0091 — Toolkit 0.16.2

Prepare toolkit `0.16.2`, a patch release with change `0090` (PR 152, merge `0084ef1`: Word no
longer splits a word inside a table cell) and change `0089` (PR 151, merge `0332f6b`: the optional
catalog link to a release's extras, issue 142).

## Write set

`tools/pyproject.toml`, `tools/src/handbook_toolkit/__init__.py`, `tools/tests/test_cli.py`,
`tools/tests/test_build.py` (fixture pin), `CHANGELOG.md` (the `0.16.2` section), `STATUS.md` (the
Toolkit and Template rows and the follow-ups) and this record.

## Print editions change

Table column widths change in the reading site, PDF and Word editions; the Markdown and source
payloads carry no widths. Measured by the reviewer with `word_wrap_audit.py` (Inter metrics, 10.5 pt, 3 + 3 pt cell margins, breaks
allowed after `-`, `–` and `/`):

Sources: the 0.16.1 sample preview (sample PR 33, run 45975745994) and the SA 6.0.0 preview of
PR 147 (its DOCX is content-identical to 0.16.1's) for the left column; the PR 152 previews (run
46006866263) for the 0.16.2 column.

| Book | Words split inside a table cell, 0.16.1 | 0.16.2 | PDF pages |
| --- | --- | --- | --- |
| Sample | 10 | 0 | 62 → 62 |
| Solutions Architecture | 42 | 0 | 569 → 566 |

## Owner gates

1. Desktop Word check of the PR 152 previews (sample `book.docx` sha256 `43f6a6fd…449a16`,
   Solutions Architecture `book.docx` sha256 `0f3241d1…184af`): pending.
2. Approval of the tag `toolkit-v0.16.2` in the chat: pending.

## Merge authority

On 2026-11-27 the Owner confirmed that the implementer merges each pull request of this round with a
merge commit after a different agent approves it and CI is green. Merging this record does not tag.

Rollback boundary: revert this commit. No tag, template, mirror, catalog entry or book release
changes here.
