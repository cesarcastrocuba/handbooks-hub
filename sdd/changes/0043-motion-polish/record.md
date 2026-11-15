# Change 0043 — Native motion polish

- Role: Implementer. Coordinator audit and a different Reviewer are required; no self-review,
  merge or tag.
- Scope: the shared native CSS layer used by the book and Quarto portal, its token contract,
  browser checks and reproducible inspection evidence. No product script, library or external
  resource is added. No change to the toolkit version, STATUS or decisions is authored here.
- Baseline: origin/main `efc4c40c9c22fb5e5d2f50bf4cde189f304d0146`, frozen before implementation.
  Main `9a15882` is merged before handoff; its publishable render-directory rename and toolkit
  0.10.4 are retained. No version bump is authored by this change.

## Behavior

Cross-document view transitions name the top bar, sidebar, margin contents and footer separately,
only while `:active-view-transition` matches. Permanent names changed resting glyph rasterization.
A shared native `link rel="expect" blocking="render"`, conditional on no reduced-motion preference,
waits for Quarto's existing
`quarto-html-after-body` marker: without it, streaming HTML could reveal before the named incoming
title/body had been parsed. A deliberately streamed HTTP fixture proves both incoming animations
are captured. This adds HTML metadata, with no new script or rendered-HTML rewrite.
The new chrome is shown without blending or movement. The old reading content leaves in 90 ms;
its replacement title rises 4 px over 160 ms, and the body rises 6 px over 180 ms after a 40 ms
lead. Group geometry interpolation is disabled, so the browser does not infer a horizontal slide.
The page-change budget is 220 ms of authored animation.

Reading progress uses the accent-solid to accent ramp and reaches scaleX(1) at the end of the root
scroll timeline. Links retain their existing semantic underline and grow a decorative underline;
buttons lift and reveal a decorative arrow on hover or keyboard focus. Native details interpolate
open/closed height where supported; search focus and sidebar states transition. Theme colors
cross-fade while the existing native switch is hovered or focused, avoiding an incidental palette
fade during startup. Automatic preference initialization remains static.
Portal cards have a bounded first-load stagger (276 ms maximum), token-derived lift/shadow,
contained cover highlight, chip transitions and a finite result-count pulse on filter/search focus.
The count pulse responds to CSS-observable interaction, not arbitrary script text replacements.

Every authored animation, transition, trigger and named transition region is inside the
no-preference reduced-motion query. Feature guards preserve static readable content in older
browsers. Native Quarto/Bootstrap vendor assets are unchanged; the motion-guard test covers the
entire toolkit-authored packaged CSS set, not a rewritten vendor stylesheet.

## Reveal refinement and browser proof

A reversible `animation-timeline: view()` cannot remember that a reader has already seen an
entry. Chromium 148 supports native view-timeline triggers (`timeline-trigger`, `trigger-scope`,
`animation-trigger: ... play-once`); these start a finite token-driven animation once on entry.
The trigger covers the element's visible interval so content already visible at load also plays
and settles. An early entry-only trigger missed that content and could leave a compositor snapshot
invisible despite computed opacity one; a painted-pixel regression now covers it. Reveals complete
in 180 ms and never reverse or replay on back-scroll. Unsupported browsers remain static, rather
than receiving a reversible fallback. This deliberately refines the brief's literal view-timeline
animation/range syntax to satisfy its once-only behavior without JavaScript.

The cover keeps its established early view-timeline entrance (8 px, entry 0–15%) to preserve its
resting compositor; only its interactive controls are refined. Existing section/guide-card final
transform fill is retained for baseline stacking behavior;
new object targets animate registered opacity/offset values, with relative positioning only
during entry. Permanent relative positioning made outside list markers disappear in mobile
callouts. Returning to the original static position fixes that paint defect; a browser regression
compares complete callout pixels at both widths/schemes, and the live once-only test checks the
position returns to static. Buttons and covers generate decorative pseudo-elements only during
interaction; otherwise positioning/pseudo paint changed resting glyphs. Format pills retain their
original underline and use the button lift, avoiding a rounded-border paint change from an extra
background underline. Motion tokens include all authored durations,
easings, distances, stagger bounds and shadow geometry/color. The schema requires the complete
contract, rejects unknown fields and enforces the page/stagger budgets. The peak cover highlight
is limited to 6%; its calculated dark-scheme text contrast is 4.71:1. The validator rejects a
stronger highlight that would fail the existing 4.5:1 floor.

## Evidence and acceptance boundary

See evidence.md for executed commands, browser contact sheets and the pixel-comparison result.
At-rest pixel identity is checked using unmodified browser screenshots, with no tolerance, forced
animation completion or hidden normalization. Early mismatches were treated as defects, not
waived as renderer noise; the paint and marker fixes above resulted from that comparison.

The completed receipt has 69 exact pixel matches and three non-identical pairs (15 template
pixels; 16 and 14 portal pixels), with equal sampled styles/geometry for those pairs. The coordinator
accepted the 15-pixel template case as rendering noise and directed the PR to be marked ready;
the additional portal cases remain explicitly disclosed in evidence.md. No comparison tolerance
or normalization was introduced. All sample and reduced-motion pairs are pixel-identical.

## Documentation impact

- CHANGELOG: adds the behavior to main's current toolkit entry; no separate release is created.
- This record and evidence.md: implementation rationale, reproducible gates and raw visual proof.
- README and operations runbook: public installation, preview and release commands are unchanged.
- STATUS and decisions: explicitly outside the write set. Changes 0027/0032 remain historical;
  this record documents the refinement rather than changing their past results.

## Evidence limits and deliberate refinements

The template has one authored chapter: its navigation sheet uses the native List of Figures to
Example Chapter link. The fresh sample uses Chapter 1 to Chapter 2. No second canonical template
chapter was invented just to label the proof differently. View-triggered play-once replaces the
brief's reversible view-timeline/range syntax, as explained above. The result-count pulse follows
CSS-observable filter/search state; no JavaScript is added to animate every text replacement.

Native references: [view-timeline triggers](https://developer.chrome.com/blog/scroll-triggered-animations)
and [cross-document render blocking](https://developer.chrome.com/docs/web-platform/view-transitions/cross-document).
