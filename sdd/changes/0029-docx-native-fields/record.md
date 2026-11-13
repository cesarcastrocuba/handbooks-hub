# WP1 — Native Word fields, style definitions and structural gates

This implements W1–W8 and H1 from change 0027, under HUB-DEC-037. Toolkit version: 0.9.2.
The coordinator owns release pins, template publication, STATUS.md and docs/decisions.md.
This pull request neither releases nor deploys anything. A different agent must review it.

## Change and rationale

- First, move the existing DOCX post-processing from build.py into docx_post.py without changing
  behavior (commit 2ee437c). The two focused helper tests passed at that boundary.
- Obtain human-readable callout style names from one design function shared by the reference
  generator and staged Lua filter. Remove the direct callout-title color repair.
- Use one caption registry for tables, figures and listings. Hidden TC fields index captions;
  native TOC fields contain linked cached entries and nested PAGEREF fields. Contents preserves
  Pandoc's instruction and caches headings 1–3. Unknown page results stay empty and dirty.
  Empty caption lists are omitted, and an explicitly disabled Contents is respected.
- Normalize bookmark names to Word's ASCII/40-character contract, preserving internal hyperlink
  and REF/PAGEREF targets. A digest suffix prevents normalized identifiers from colliding.
- Put horizontal bands in reference table styles. Plain callout tables have no bands, and no
  row-level shading is emitted. Register namespaces and order authored properties by their schema
  sequences, including settings. Keep callout boxes inside the text column.
- Declare font alternate-name chains (one name per altName), without embedding binaries.
  Viewer substitution remains outside the structural guarantee.
- Validate styles, authored property children/order/uniqueness, field nesting and bookmark targets
  at the artifact boundary. Tests include passing and failing fixtures for each gate.
- Include an original generated PNG in the real build. It exposed first-page relative image paths
  when that source becomes index.qmd; a native Pandoc Image filter rebases them before writing,
  preserving canonical manuscript paths. Conditional Typst outlines now include figures.
- Convert the real DOCX to PDF with LibreOffice in a smoke test. Publication-build CI installs
  LibreOffice Writer and Poppler; the test explicitly skips if those tools are absent locally.
- Remove the second rule, padding and margin at the top of the HTML caption-list section.
  build.py is reduced from 1,606 to 1,121 lines.

## Engineering boundary and rollback

New OOXML processing uses an XML parser, not regular expressions or concatenated XML strings.
The existing HTML table-index implementation remains for WP3. The two review units are the
behavior-preserving extraction and the native-field/style/validator behavior with its tests.
Reverting the behavior unit restores the previous renderer while retaining the isolated module;
reverting the extraction then restores the original module location.

The released template remains 1.4.1 with its 0.9.1 pin. Runtime template-build tests install the
current builder and update only a temporary copy's descriptor to 0.9.2; the separate template-install
CI job still checks the real released pin. Advancing template 1.4.2 belongs to the coordinator.

## Limits

Desktop Word was not opened. OpenXmlValidator, parsed assertions and LibreOffice are evidence
of structure and cached content, not proof of Word's duplicate-style resolution or field-update UI.
Word or another capable viewer must calculate missing page numbers, possibly after confirmation.
The built-in validator is deliberately bounded to the OOXML containers/invariants the toolkit owns;
the Open XML SDK supplies independent full-schema evidence, not a runtime dependency.
No architecture migration, portal rewrite or reference-handbook edit is included.
