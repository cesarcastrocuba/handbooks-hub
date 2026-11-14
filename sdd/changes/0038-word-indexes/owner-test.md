# Owner desktop Word test of the published DOCX — 2026-11-14

This record is the Owner's observation, not an agent test. It is the first time an edition of this
work was opened in desktop Word, and it is the input that change `0038` fixes.

## What the Owner observed

The Owner opened the published sample `v0.5.0` DOCX in desktop Word on Windows:

- **Contents, List of Tables and List of Figures are empty on open** ("No table of contents entries
  found") until the reader updates the field with F9 / Update entire table. F9 then populates the
  Contents correctly.
- **Captioned tables show no banding.** The alternating row shading is absent.
- **Callout titles are bold, as intended.**

The same defect applies to `v0.4.2`, the previous published edition.

## Consequence recorded here

`v0.4.2` and `v0.5.0` carry this defect. No tag or release follows until the Owner opens the
CI-built edition preview `book.docx` and confirms the indexes, F9 on each and the banding; the fix
is on `main` as toolkit `0.10.2` (change `0038`), which is not tagged.
