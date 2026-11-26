# Change 0082 — Toolkit 0.15.0

Prepare toolkit `0.15.0`, a minor release with the changes merged after `toolkit-v0.14.2`. They
come from the Owner's review of the Solutions Architecture Handbook 6.0.0 preview (2026-11-22 to
2026-11-26).

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
   DOCX of PR 136 at `2a1a9ee` (run 45708879984, book `1dee3a4`). The Owner wrote "Buen trabajo,
   al final creo que tenemos una versión estable" (2026-11-26). This pull request only changes
   version numbers.
2. Approval of the tag in the chat: given on 2026-11-26 ("Aprobado 1, y 2").

## Follow-ups

The remaining Minor and Optional findings of the PR 136 reviews (comments 7109788023,
7168168232 and 7176284448) are test and documentation gaps. They are recorded in a follow-up
issue, because they do not change the approved artifacts.

## Verification evidence

The pull request records the evidence, from commands run on its exact HEAD.

Rollback boundary: revert this commit. No tag, template, mirror, catalog entry or book release
changes here.
