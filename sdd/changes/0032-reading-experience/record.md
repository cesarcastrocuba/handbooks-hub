# Change 0032 — Native book reading experience

- Decision: HUB-DEC-038; work package WP4 of change 0027.
- Role: Implementer; independent review and coordinator audit required. No self-review or merge.
- Started stacked on WP3 / PR 55. Integrated its updated branch and origin/main with merge commits,
  never rebasing published work. PR 55 final HEAD is 78c2db96afe05152725ae2781464adac4c305c7a;
  its independent merge is 48816803069f38148de6bbfc4ef32c85bb38045f. This PR targets main.
- Toolkit remains 0.10.0. Released template heading/pin remain 1.4.2/0.9.2 until the release PR.

## Behavior

The HTML cover is generated from the descriptor and publication metadata. It includes title,
subtitle when supplied, author, summary, edition/date/status/licence and Start reading. Known
release/edition URLs must be explicit metadata, never inferred from a future version; preview
builds omit them. Document Control follows the cover as a separate page. Reading-order groups
become native Quarto parts, with nonempty caption lists in front matter. Native page-footer carries
edition identity on every page. Print and Markdown staging precede these HTML-only additions and
retain their existing title/index behavior.

Quarto's unnumbered title grammar is used for the cover so chapter and caption numbers do not
shift. A canonical root index.qmd is preserved under a generated, root-level source alias; a native
Lua Link filter preserves direct links to it. Ordinary sources retain their own paths. There are
no edits of rendered HTML and no new script. Native site-url/canonical, description, Open Graph,
Twitter and the token-derived original SVG favicon supply metadata. GitHub Pages follows the
pipeline convention; custom publication domains can be explicit metadata/configuration.

The template includes an original SVG, caption, alt text and cross-reference. Its packaged drawing
source generates the template asset deterministically from tokens; conformance checks that parity.
It appears in HTML, PDF, DOCX and the Markdown caption. SVG system colors were rejected by the
Typst proof (a black rectangle); concrete generated token values work across renderers.

## Accessibility and motion

Focus is visible on interactive elements; native Quarto supplies the skip link and tab order.
All authored motion is native CSS inside the no-preference reduced-motion query: view transitions,
view-timeline section/card reveals, scroll progress and focus/control/details transitions. Unsupported
features leave visible static content. Duration/easing tokens drive the stylesheet. No script,
library, hosted font or external image is added.

Actual computed callout title/tint, table link/header and footer pairs were checked in both schemes.
The light/print warning title accent changed minimally to meet AA (4.57:1, previously 4.24:1); the
reference DOCX was regenerated from the same token. Other callout roles remain unchanged.

## Figure-path defect found during inspection

LibreOffice exposed a teal figure container with a white/bold caption: the DOCX post-processor
mistook Quarto's one-cell figure layout table for a data header. It now honors Pandoc's explicit
firstRow flag, preserving unshaded figure containers, normal italic captions and native drawing
alignment. A unit test and the real template SVG build assert this distinction; genuine data
headers retain shading, white/bold runs and repetition. This fix is part of proving the required
figure path, not a Word architecture migration.

## Evidence and limits

See evidence.md. No requested feature is deferred. Download links are intentionally absent when
unknown or when previewing. Desktop Word is unavailable; native fields, validators and LibreOffice
are verified, while Word's pagination/field update remains a human publication check.

## Refinements after the coordinator's acceptance audit

The coordinator built the template and the sample with this branch and inspected the screenshots.
Four visible defects were corrected in follow-up commits by the coordinator, who is therefore a
co-implementer of this change and does not review or merge it:

- **One statement of the summary.** When the catalog summary and the subtitle say the same thing
  (the sample's do), the cover printed it twice. The summary paragraph is omitted in that case.
- **No one-item groups.** A reading-order group with a single page ("References" holding only
  "References", "Back matter" holding only the notices, a one-chapter book) was rendered as a part
  with one child. A group is a part only when it has several pages; a single page stands on its own.
- **The cover keeps the page grid.** The cover disabled the table of contents, which made Quarto
  drop the margin column and shift the sidebar and the text away from the header's alignment. The
  cover no longer disables it, so moving from the cover to a chapter does not move the sidebar.
- **No progress bar on a page that does not scroll.** Without an active scroll timeline the bar was
  drawn at full width. It now starts at zero width and only the timeline extends it.
