# Change 0038 — Word index caches and direct cell banding (toolkit 0.10.2)

Implementer change; coordinator audit and an independent reviewer are required. No self-review,
merge, tag or release. STATUS.md, docs/decisions.md and reference repositories are not edited.

## Owner's desktop Word observations

The Owner opened the published sample v0.5.0 DOCX in desktop Word on Windows. Callout titles were
correct, but Contents and both caption lists were empty on open, and captioned table banding was
absent. F9 / Update entire table populated Contents correctly. In a test copy without dirty flags,
with tab/PAGEREF caches set to 1, Word displayed every cached entry at page 1 without recalculating.
These are Owner observations, not agent desktop Word tests.

The prior writer marked field starts dirty and requested updateFields. That asks Word to replace
otherwise visible caches at load time, before usable entries are available. Conditional table
banding also did not display. The new mechanism keeps valid native fields, provides complete caches,
and leaves Word's field update under reader control.

## Method

- Remove dirty attributes from every Word XML part and remove updateFields. TC fields have
  begin/instruction/end only (the first build formatted them as hidden text; see the Owner's second
  test in `owner-test.md`). Each index ends in a separate final paragraph.
- Cache entries as history=1 anchored hyperlinks containing the title and, only for known pages,
  a tab and native PAGEREF with numeric result. Contents keeps Pandoc's selected heading depth;
  caption indexes come from the existing shared registry.
- Author point bookmarks inside each actual heading/caption paragraph, preserving manuscript
  anchors. LibreOffice omits at least one Pandoc body-level bookmark after a table in the published
  sample; a missing destination is an error, never a reason to search caption text.
- Convert with a private LibreOffice profile and private fontconfig configuration using only staged
  toolkit fonts. Export bookmark destinations and read pdfinfo -dests. Derive each encoded PDF name
  from the exact authored bookmark; detect missing, conflicting and ambiguous names.
- Establish placeholder digit widths, write real numbers and verify with another conversion.
  Page differences or unstable widths fail every build. Single-digit documents use two conversions.
  Multi-digit results need an additional width-establishment conversion: final width is unknowable
  before the first pagination. This bounded extra pass is an explicit refinement of the two-pass
  brief; it does not relax final verification or guess pagination.
- Handle decimal section numbering and restarts using section-start bookmarks. Non-decimal or
  chapter-prefixed page formats fail a required probe; optional builds warn and keep title-only
  caches rather than confuse physical and displayed pages.
- Optional unavailable/failed probes warn on stderr and record stable title-only status and the
  LibreOffice version (or unavailable) in manifest tool_versions. --require-page-numbers blocks
  those cases. Release and preview CI require it. Nonconvergence never falls back silently.
- Write alternating body cell fills directly from docx_values(). Keep header fills; skip float
  wrappers and TablePlain callout tables. Remove reference-document band conditionals. Ensure
  every table cell ends with a paragraph, including callouts ending in a nested table.

## Boundaries and acceptance

Cached pages are LibreOffice pagination with packaged fonts, not guaranteed Word pagination.
The Owner must open the PR's edition-preview-sample DOCX before any tag: all three indexes must
show numbers without a prompt; F9 must regenerate each; table banding must be visible. Agents
cannot perform that desktop Word acceptance. No manuscript/profile edit is required, but a book
must install LibreOffice Writer and pass the strict flag in its release workflow.

Checks, sample entries and the independent Open XML SDK result are recorded in evidence.md and the
PR handoff. The 0.10.2 changelog also records the unversioned Quarto portal/design-preview addition
already merged after 0.10.1; this Word fix does not change portal deployment.
