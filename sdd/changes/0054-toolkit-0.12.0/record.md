# Change 0054 — Toolkit 0.12.0

Prepare toolkit `0.12.0` for the onboarding of `handbook-solutions-architecture` (Phase 6,
`HUB-DEC-043`, `HUB-DEC-044`). It releases the toolkit work merged since `toolkit-v0.11.0`:

- change `0050` (PR 85): standard profile `1.1.0`, gaps G2 and G3 plus the unit relaxations;
- change `0051` (PR 87): figure and table numbering follows the displayed chapters, gap G12.

Change `0049` (PR 84) changed the template and the documentation only; it ships with template
`1.7.0`, which pins this toolkit in a separate change. Cross-reference links (`0052`) and the
glossary pointers and analytic Index (`0053`) are not part of this release; they are planned for
toolkit `0.13.0`, before the book's first complete edition `v3.1.0`.

## Write set

`tools/pyproject.toml`, `tools/src/handbook_toolkit/__init__.py`, `tools/tests/test_cli.py` (the
version the CLI prints), `tools/tests/test_build.py` (the fixture book's toolkit pin must match the
builder) and `CHANGELOG.md` (the `0050` and `0051` entries move from `[Unreleased]`
under `[0.12.0]`; the template entries of `0049` stay under `[Unreleased]` for template `1.7.0`).
`STATUS.md` changes in the status PR after the tag, not here.

## Owner gates before the tag `toolkit-v0.12.0`

1. Desktop Word check of a DOCX built with this commit. The DOCX table and figure labels change
   (front matter `0.N`, appendix letters, back matter `BM.N`); the sample's front-matter `Table 1`
   becomes `Table 0.1`.
2. Confirmation of the fourth relaxation of profile `1.1.0` (change `0050` record, line 54): a bold
   paragraph label inside a heading section of the same name is body prose.
3. Approval of the tag itself in the chat.

The coordinator creates the annotated tag on the merge commit only after all three.

## Verification evidence

See the pull request; every command is run on the exact HEAD and its output pasted there.

Rollback boundary: revert this commit. No tag, template, mirror, catalog entry or book release is
changed here.
