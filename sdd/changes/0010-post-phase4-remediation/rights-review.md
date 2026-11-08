# Third-party rights review — bundled render resources

**Status:** Proposed; the owner decides through `HUB-DEC-020`.
**Date:** 2026-11-08
**Scope:** files under `tools/src/handbook_toolkit/render_data/` added after the Phase 4 close, and
what the `v0.2.0` sample release carries from them. This is an engineering record, not legal advice.

## Findings

| ID | Resource | Evidence | Result |
| --- | --- | --- | --- |
| R1 | Selawik 1.01 | The three TTF files are byte-identical to `Selawik_Release.zip` on upstream release `1.01`. `OFL.txt` is byte-identical to upstream `LICENSE.txt`. | No open question. |
| R2 | Cascadia Code 2407.24 | The three TTF files are byte-identical to `ttf/static/` in upstream `CascadiaCode-2407.24.zip`. `OFL.txt` matches upstream `LICENSE` apart from line endings. | **Open.** See below. |
| R3 | `docx/reference.docx` | 14 of its 16 package parts are byte-identical to the default of Pandoc 3.10; only `word/document.xml` and `word/styles.xml` differ. | **Open.** See below. |
| R4 | `html/handbook.css` | Imported byte-identical from `publishing/styles/handbook.css` in the reference handbook, same author. This change edits only its first comment line. | No open question; recorded in `NOTICE.md`. |
| R6 | `typst/handbook-typst.typ` | Adapted from `publishing/styles/handbook-typst.typ` in the reference handbook, same author; the files differ. | No open question; recorded in `NOTICE.md`. |
| R7 | `typst/typst-show.typ` | Added in `988773c`; not in the reference handbook. It shares distinctive template lines with the Quarto `typst-show` partial, for example `#show: doc => article(`, so Quarto is the probable source. Quarto 1.11.9 is MIT, © 2020-2024 Posit Software, PBC. | Resolved: the MIT notice is now in the file header and `NOTICE.md`. |
| R5 | `v0.2.0` sample artifacts | `pdffonts` shows embedded subsets of Selawik, Cascadia Code and Liberation Sans. `book-html.zip` carries Quarto's `bootstrap-icons.woff`. | Selawik and Cascadia are covered by OFL section 5 for documents. **Liberation Sans is open:** `handbook-typst.typ` and `typst-show.typ` request it, it is not bundled, so it came from the build environment, and its license was not reviewed. |

## Open questions for the owner

1. **Cascadia Code metadata (R2).** The license field inside each TTF (name ID 13) opens with
   "Microsoft supplied font... Any other use is prohibited" and then gives a license "based on the SIL
   Open Font license". The upstream repository licenses the same files under plain OFL 1.1. The record
   assumes the upstream license governs. The alternative is to replace the font.
2. **`reference.docx` provenance (R3).** Pandoc is GPL-2.0-or-later, and its `COPYRIGHT` file grants
   the dual license only to `data/templates`, so it does not name this file. Whether the GPL reaches a
   style-only document is not resolved here. The alternatives are to accept it or to replace it with a
   reference document authored from scratch.
3. **Liberation Sans (R5).** Either review its license or configure builds so that only bundled fonts
   are embedded.

## File hashes (SHA-256)

| File | Hash |
| --- | --- |
| `fonts/cascadia-code/CascadiaCode-Bold.ttf` | `58197c5c3ba2967d4780b0ef8aee72d0cbbfa42885ddede9ec96fa7a1df5aead` |
| `fonts/cascadia-code/CascadiaCode-Italic.ttf` | `1f0676937792fe550effeafb7f4622080c2a5d62715d1245d471258fa1a23b8c` |
| `fonts/cascadia-code/CascadiaCode-Regular.ttf` | `c33ef522cdfeff99907fb54f3e97152bb18bfb9b56ec2fef4d4ceec51c8974a4` |
| `fonts/cascadia-code/OFL.txt` | `82c05d6c53dfa0c9025985c19e371810020b74ed2c61d51d370f2a8ab2506d52` |
| `fonts/selawik/OFL.txt` | `77b7c2506d4efb22e09c8ccf10159f4956eab3ef7c007fef95de136bcf45300c` |
| `fonts/selawik/selawk.ttf` | `e9d98518d8ac2817782a9a382430463a2e0793ea68350b695bb727d9a830ee1c` |
| `fonts/selawik/selawkb.ttf` | `f0db5e174a90e0956ad7d2844bdca1d5e6da92ec65b2c04e57ba9b180668c904` |
| `fonts/selawik/selawksb.ttf` | `0a9e9d0549a10f24bef9b3a29e06fe6e0b5c21e7a784c503b048a307841a7783` |
| `docx/reference.docx` | `216414b23b44e81fb4b8d6ecf4fe1fda1491228edd2922d9985ecf179d724918` |
