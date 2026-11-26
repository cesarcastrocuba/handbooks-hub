# Change 0084 — Toolkit 0.16.0

Prepare toolkit `0.16.0`, a minor release with change `0083` (PR 140): Inter replaces Source Sans 3
and Source Serif 4 in every edition and the portal, the Word edition embeds Inter and JetBrains
Mono, and the PDF body text is 9.5 pt (`HUB-DEC-045`). It is a minor release because the typeface
and the pagination change for every book.

## Write set

`tools/pyproject.toml`, `tools/src/handbook_toolkit/__init__.py`, `tools/tests/test_cli.py`,
`tools/tests/test_build.py` (the fixture book's toolkit pin must match the builder),
`CHANGELOG.md` (the `0.16.0` section, and the `0.15.0` heading dated with its tag, 2026-11-26) and
this record. Two one-line fixes from the PR 140 re-review (comment 7205182366): the 0083 record
names both web subset families, and the `THREE_LEVEL_LIMIT` comment in `print_layout.py` names the
9.5 pt body size.

The template still pins toolkit `0.14.2`. A template release pins this one in a separate change.

## Owner gates before the tag `toolkit-v0.16.0`

1. Desktop Word check of the CI-built DOCX: done on the `edition-preview (solutions-architecture)`
   DOCX of PR 140 at `14c095e` (run 45902504237, artifact 15157410504, book `100c2fa`, sha256
   `c9013dab9bf1c31416d11d7700a0c9592a9c9cc9a7b1a8c0ac003a78ce843248`). On 2026-11-26 the Owner
   wrote "Me gusta el resultado" ("I like the result") and, asked whether that included the desktop
   Word check and the tags, "Todo sí" ("Yes to everything").
2. Approval of the tag in the chat: given on 2026-11-26 in the same answer, together with the
   approval of the book tag `v6.0.0`.

## Merge authority

On 2026-11-26 the Owner authorised, for that night only, the implementer to merge each pull request
of the 6.0.0 publication (PR 140, this release, the book pin and the catalog) with a merge commit,
after a different agent approves it and CI is green; Minor and Optional findings go to follow-up
issues. PR 140 was merged under that authority (`34d868c`) after the approvals in comments
7203474309 and 7205182366.

## Verification evidence

The pull request records the evidence, from commands run on its exact HEAD.

Rollback boundary: revert this commit. No tag, template, mirror, catalog entry or book release
changes here.
