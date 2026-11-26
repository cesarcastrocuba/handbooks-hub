# Change 0082 — Toolkit 0.15.0

Prepare toolkit `0.15.0`, a minor release with the changes merged after `toolkit-v0.14.2`. Change
`0081` comes from the Owner's review of the Solutions Architecture Handbook 6.0.0 preview
(2026-11-22 to 2026-11-26). Changes `0079` (issue 113) and `0080` (issue 98) come from hub issues
and were merged on 2026-11-21.

- Change `0081` (PRs 133, 134, 135 and 136; merge `76682fc`) changes the Word and PDF layout:
  - figures stay in place and print at 85%, with the bounded gap fit;
  - callout boxes stay whole;
  - Word keeps are released inside and before boxes;
  - the PDF checklist colour is fixed;
  - the HTML light-theme reveal no longer flashes white.

  It is a minor release because placement behaviour changes for every book.
- Change `0079` (PR 130) fixes the clean-clone gate on macOS paths and with the browser tests.
- Change `0080` (PR 131) removes the render-time `lastmod` so that `book-html.zip` is
  reproducible.

## Write set

`tools/pyproject.toml`, `tools/src/handbook_toolkit/__init__.py`, `tools/tests/test_cli.py`,
`tools/tests/test_build.py` (the fixture book's toolkit pin must match the builder),
`CHANGELOG.md` and this record.

The template still pins toolkit `0.14.2`. A template release pins this one in a separate change.

## Owner gates before the tag `toolkit-v0.15.0`

1. Desktop Word check of the CI-built DOCX: done on the `edition-preview (solutions-architecture)`
   DOCX of PR 136 at `2a1a9ee` (run 45708879984, artifact 15067806667, book `1dee3a4`, sha256
   `7b36ae194d6a27ad393a4d88a8d2c493fabb13ca5b1bf1b5e53c4d56922db9a0`). On 2026-11-26 the Owner
   wrote, in Spanish, "Buen trabajo, al final creo que tenemos una versión estable" ("Good work,
   I think we finally have a stable version"). This pull request only changes version numbers.
2. Approval of the tag in the chat: given on 2026-11-26 ("Aprobado 1, y 2", "Approved 1 and
   2": the merge of PR 136 and the tag).

## Follow-ups

Issue 138 records every remaining Minor and Optional finding of the PR 136 reviews (comments
7109788023, 7168168232 and 7176284448), and of this pull request's review (comment 7189929591).
None of them changes the approved 6.0.0 artifacts.

- Most are test and documentation gaps.
- Three are behaviour edges, also in issue 138:
  - the PDF scales SVG figures and Word does not;
  - the tall-group guard measures the group at the print scale;
  - the release clears keeps inside a callout's nested tables.

## Verification evidence

The pull request records the evidence, from commands run on its exact HEAD.

Rollback boundary: revert this commit. No tag, template, mirror, catalog entry or book release
changes here.
