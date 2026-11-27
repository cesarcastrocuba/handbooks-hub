# Change 0087 — Toolkit 0.16.1

Prepare toolkit `0.16.1`, a patch release with change `0085` (PR 146, merge `12ce796`: portal guide
pages, mobile button rows, cover links, GitHub stars with a build-time count, `HUB-DEC-046`, and
the PDF body size from its token, issue 142) and change `0086` (PR 147, merge `2ebaf4b`: the 0081
follow-ups, issue 138). It is a patch release: no edition changes its layout.

## Write set

`tools/pyproject.toml`, `tools/src/handbook_toolkit/__init__.py`, `tools/tests/test_cli.py`,
`tools/tests/test_build.py` (fixture pin), `CHANGELOG.md` (the `0.16.1` section), the Toolkit row of `STATUS.md` and this record.

## Print editions unchanged

- DOCX: the `edition-preview (solutions-architecture)` `word/document.xml` of PR 147's fixed HEAD is
  byte-identical to PR 146's preview (md5 `2e600f1fe4902ad945c1b7a8fb0f4b84`), and PR 146 changes
  no Word code. The Owner's desktop Word check of the 0.16.0 DOCX therefore still applies.
- PDF: 569 pages; `pdftotext -layout` and `pdfimages -list` identical to PR 146's preview; PR 146's
  preview PDF was byte-identical to the 0.16.0 build (review of PR 146 by oc8).

## Owner gates

1. Desktop Word check: not needed (no DOCX change, above).
2. Approval of the tag `toolkit-v0.16.1` in the chat: given on 2026-11-27 ("si a 1,2,3 por favor
   dale caña", answering the request to approve the tags of toolkit 0.16.1, the template and the
   sample, with the template and sample on 0.16.1 instead of 0.16.0).

## Merge authority

On 2026-11-27 the Owner confirmed that the implementer merges each pull request of this round with a
merge commit after a different agent approves it and CI is green (same answer). PR 146 was approved
by oc8 and PR 147 by Claude (oc7 implemented it).

Rollback boundary: revert this commit. No tag, template, mirror, catalog entry or book release
changes here.
