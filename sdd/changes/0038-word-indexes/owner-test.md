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

## Second test — 2026-11-14, the CI-built DOCX of toolkit `0.10.2` (pull request 65)

The Owner opened the `book.docx` of the `edition-preview-sample` artifact of CI run 43619890917 in
desktop Word:

| Check | Result |
| --- | --- |
| Contents, List of Tables and List of Figures on open | Entries with correct page numbers; Word asks nothing |
| "Update page numbers only" on each index | Correct |
| "Update entire table" on Contents | Correct |
| "Update entire table" on List of Tables and List of Figures | **The list is emptied**: Word finds no entries |
| Banding of captioned tables | Shown |

Three variants of that file, differing only in the caption markers, were then tested by the Owner
with "Update entire table" on both lists:

| Variant | Markers | Result |
| --- | --- | --- |
| E | A hidden `SEQ <name> \h` in each caption and `TOC \h \z \c "<name>"` | Emptied |
| F | `TC "<caption>" \f <letter> \l "1"` at the start of the caption, **not formatted as hidden text** | **Entries kept, with pages** |
| G | The original hidden `TC`, moved to a hidden paragraph outside the wrapping table | Emptied |

Conclusion: desktop Word skips a caption marker formatted as hidden text when it rebuilds the whole
list. The fix emits the markers exactly as in variant F; a validator rejects any field run
formatted as hidden text. A `TC` field has no result, so it shows nothing in Word, in LibreOffice
or in the converted PDF.
