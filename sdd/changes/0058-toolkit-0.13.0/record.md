# Change 0058 — Toolkit 0.13.0

Prepare toolkit `0.13.0`, the platform features the Solutions Architecture Handbook needs for its
first complete edition `v3.1.0` (`HUB-DEC-043`: no section is lost). It releases the toolkit work merged
since `0.12.0` (PR 89, `0824ddf`):

- change `0052` (PR 88): opt-in cross-reference links (G8);
- change `0053` (PR 93): opt-in glossary definition pointers and the analytic Index (G9, G4);
- change `0055` (PR 90): lossless artifact size optimization, **on by default**.

Change `0057` (PR 92) changed the template release workflow only; it ships with the next template
release, which pins this toolkit in a separate change.

## Write set

`tools/pyproject.toml`, `tools/src/handbook_toolkit/__init__.py`, `tools/tests/test_cli.py`,
`tools/tests/test_build.py` (the fixture book's toolkit pin must match the builder) and `CHANGELOG.md`.
The CHANGELOG also drops a reference to `HUB-DEC-045` from the `0055` entry: no such decision exists.

## Owner gates before the tag `toolkit-v0.13.0`

1. Desktop Word check of a DOCX built with this commit and the book opted in (links, Index,
   glossary pointers, recompressed images).
2. Decisions for the Owner: optimization on by default for every book (`--no-optimize` opts out);
   whether the PDF also gets `qpdf` (21.4 → 15.4 MB, a new binary in CI and in the release workflows);
   the two Optional points of PR 88's review (range ends such as "Chapters 1–18" link their ends;
   Document Control and Conclusions get more links than v3.0.0).
3. Approval of the tag in the chat, after `toolkit-v0.12.0`.

## Verification evidence

In the pull request, from commands run on its exact HEAD.

Rollback boundary: revert this commit. No tag, template, mirror, catalog entry or book release changes here.
