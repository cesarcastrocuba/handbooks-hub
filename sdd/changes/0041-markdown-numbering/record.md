# Change 0041 — Consistent float labels in the Markdown edition

Implementer change for toolkit 0.10.2, already on main but not tagged. Coordinator audit and a
different reviewer are required. No self-review, merge, tag or release. STATUS.md, decisions.md
and the toolkit version are not changed. The Owner's desktop Word acceptance gate still applies.

## Cause and native-render proof

The Markdown stage renders a concatenated source as a default GFM document, with no chapter
cross-reference setting. Quarto therefore uses sequential float counters. It also captured source
before the shared chapter wrapper had promoted pilot headings and assigned automatic table IDs.

A standalone Quarto 1.11.9 proof with number-sections:true and crossref.chapters:true produced
Table 1 in an unnumbered Introduction, Figure 1.1 in chapter one and Table/Listing 2.1 in chapter
two, including matching resolved references. A separate book-project/GFM experiment failed with
"The gfm format is not supported by book projects". The supported single-file render is retained.
No fallback label computation, rendered-label substitution or HTML/XML regex is necessary.

## Change

The GFM render enables native section/chapter cross-referencing and receives the book's crossref
options and edition language. Its source uses the same chapter wrapper/table-ID assignment as the
other editions. The shared wrapper can retain the canonical heading text for GFM, because that
writer does not print section numbers into heading text. Explicit .unnumbered classes survive;
no new interpretation of file metadata is invented. Quarto resolves labels and forward/cross-file
references from the combined AST, including appendix content in the canonical reading order.

Listing references exposed a source-validation gap: opening-fence IDs were omitted from reference
validation, although list pages already collected them. The source visibility helper now optionally
exposes opening-fence attributes; reference declarations and list pages share it, while code bodies
remain excluded. The duplicated fence scan is removed. Reference uses inside literal code remain
ignored, and fake labels in that code still fail when referenced from prose.

## Verification and rollback

A real book fixture has an unnumbered front-matter table and numbered chapter/appendix tables,
figures and listings, with forward and cross-file references. The test parses the reading site
using the existing HTML helper, parses book.md through Pandoc GFM and compares every caption and
reference sentence. Separate source tests cover wrapper/title preservation and code-fence labels.
Evidence includes the required full checks and a fresh sample clone's before/after labels.

The rollback boundary is the Markdown source wrapper/native render configuration and the shared
opening-fence declaration collection, together with their tests and documentation. No native
HTML/PDF/DOCX numbering rules are changed; labels remain Quarto's responsibility in every writer.
