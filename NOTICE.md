# Licensing and attribution

This repository uses two licenses. The split follows the existing handbook's `DEC-007` pattern, but
this hub is a new work; the scope below is the hub's own.

| Material | License | File |
| --- | --- | --- |
| Documentation, editorial profiles, templates, schemas, catalog metadata and repository governance | Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0) | [`LICENSE`](LICENSE) |
| Software: `tools/`, CI workflows and executable build configuration | MIT License | [`LICENSE-CODE`](LICENSE-CODE) |

Copyright © 2026 Franz César Castro Cuba.

## Attribution

When you share or adapt the hub documentation, credit "Handbook Hub, Franz César Castro Cuba", link
to CC BY-SA 4.0, state whether you made changes and license your adaptations under CC BY-SA 4.0.

## Derivation and reference material

The standard profile and the plan record editorial lessons observed in the existing
`Solutions Architecture Handbook` (CC BY-SA 4.0, Franz César Castro Cuba), inspected read-only at
commit `6a15cc211f65e148afdaa75c71a063a8084d1910`. No manuscript text, diagram or checklist data was
copied into this repository. The packaged HTML stylesheet, Typst style and DOCX reference document
were adapted from that handbook's publishing styles by the same author. The reference repository
remains unchanged and is not a dependency.

## Bundled render resources

The toolkit ships third-party files under `tools/src/handbook_toolkit/render_data/` so that builds
are reproducible. They are not covered by this repository's MIT or CC BY-SA licenses.

| Resource | Version and upstream | License |
| --- | --- | --- |
| Selawik Regular, Semibold and Bold | 1.01, <https://github.com/microsoft/Selawik/releases/tag/1.01> | SIL Open Font License 1.1, `fonts/selawik/OFL.txt` |
| JetBrains Mono Regular, Bold and Italic | 2.304, <https://github.com/JetBrains/JetBrainsMono/releases/tag/v2.304> | SIL Open Font License 1.1, `fonts/jetbrains-mono/OFL.txt` |
| Liberation Sans Regular, Bold, Italic and Bold Italic | 2.1.5, <https://github.com/liberationfonts/liberation-fonts/releases/tag/2.1.5> | SIL Open Font License 1.1, `fonts/liberation-sans/OFL.txt` |
| `typst/typst-show.typ` | Portions adapted from the Quarto `typst-show` partial, © 2020-2024 Posit Software, PBC | MIT, notice kept in the file header |

Selawik is © Microsoft Corporation and a trademark of its owner; JetBrains Mono is © The JetBrains Mono
Project Authors; Liberation is © Google Corporation and Red Hat, Inc. The fonts are used unmodified, as
typography only, and imply no endorsement. `docx/reference.docx` is written from scratch by
`tools/scripts/generate_reference_docx.py` and contains no third-party template parts.
The review, file hashes and open questions are in
[`sdd/changes/0010-post-phase4-remediation/rights-review.md`](sdd/changes/0010-post-phase4-remediation/rights-review.md).

## Not covered

- Third-party standards, regulations, books and trademarks referenced in documentation remain the
  property of their owners.
- Any future book content is licensed in that book's own repository; the hub licenses only the
  material stored here.
- Dependencies installed from package indexes keep their own licenses.
- The bundled render resources listed above keep their own licenses.

## Planned content license for books

Unless a book's owner records an exception, handbook content defaults to CC BY-SA 4.0 and book
software defaults to MIT. Every book must carry its own `LICENSE`, `LICENSE-CODE` and `NOTICE` before
publication, and must complete a third-party rights review for imported material.
