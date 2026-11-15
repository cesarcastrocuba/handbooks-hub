# Change 0043 — Verification evidence

Implementation source: `78a587be4a3ab7ff64ca44a3046e8916cc095e5d` (toolkit 0.10.4, inherited
from main). The handoff commit also contains this evidence. No release, tag or self-review is made.

## Inputs and environment

- Frozen origin/main baseline: `efc4c40c9c22fb5e5d2f50bf4cde189f304d0146`, checked out separately
  under `/tmp/motion-baseline-toolkit`; its toolkit built the before previews.
- The template comparison uses the same exported book commit before and after:
  `f1a1330b5cef3904925767edcbaafd51d05007e8`, `/tmp/motion-evidence/fixtures/template-book`.
- Fresh sample clone: `/tmp/motion-sample-source`, commit
  `778ebdba065dc668a43284354d3af0698503c580`.
- Quarto 1.11.9; Playwright 1.60.0 / Chromium 148.0.7778.0. Dependencies were installed in the
  assigned worktree's `.venv` from `requirements-dev.txt` and
  `tools/scripts/requirements-edition-preview.txt`; Chromium was installed with Playwright.
- Main `9a15882` is merged (its latest change only updates the catalog). The previews were built before that catalog-only merge, at implementation commit `78a587b`, with main `5cef9f6` already merged, including the publishable `handbook-render` directory and toolkit
  0.10.4. No toolkit version, STATUS or decisions change is authored here.

## Commands and results

Results below come from the executed logs. The final browser receipt is still running.

| Check | Command | Result |
| --- | --- | --- |
| Repository | `make full` | 421 tests passed; fast 5/0 and full 7/0 validators |
| Real editions | `python3 -m unittest discover -s tools/tests -p test_build.py -v` | 32 passed (326.800 s) |
| Browser contract | `python3 -m unittest discover -s tools/tests -p test_reading_site.py -v` | 15 passed |
| Token contract | `python3 -m unittest discover -s tools/tests -p test_design.py -v` | 21 passed |
| Conformance | `python3 -m unittest discover -s tools/tests -p test_design_conformance.py -v` | 13 passed |
| Template | `python3 tools/scripts/edition_preview.py --template --output /tmp/motion-acceptance/template-required` | Passed; 7 files, 6 matching checksums, LibreOffice PDF, 4 HTML pages |
| Frozen template comparison | `python3 tools/scripts/edition_preview.py --repo /tmp/motion-evidence/fixtures/template-book --output /tmp/motion-acceptance/template-after` | Passed; 7 files, 6 matching checksums, 4 HTML pages |
| Sample | `python3 tools/scripts/edition_preview.py --repo /tmp/motion-sample-source --output /tmp/motion-acceptance/sample-after` | Passed; 7 files, 6 matching checksums, LibreOffice PDF, 18 HTML pages |
| Portal | `python3 -m handbook_toolkit.portal catalog/catalog.json --output /tmp/motion-acceptance/portal-after --engine quarto` | Passed; 7 HTML pages |
| Visual receipt | `python3 tools/scripts/motion_evidence.py --root /tmp/motion-acceptance --output /tmp/motion-acceptance/inspection` | In progress; partial strict pixel mismatch disclosed below |

Logs: `/tmp/motion-acceptance-{full,build,template,required,sample,portal,inspection}.log`.
The preview outputs include the unpacked HTML sites, LibreOffice PDFs, screenshots and PREVIEW.md.
Checksums are verified for all six hashed files in each seven-file edition directory.

## Browser proof

The visual harness compares 72 before/after viewport pairs: three pages of each of the template,
sample and Quarto portal, at 1440 and 390 CSS px, light/dark, with no-preference/reduced motion.
Height is 1000 px, device scale is 1. Each scenario has a fresh browser and each before/after
image a fresh page, so this comparison does not accidentally navigate between two different
builds. No animation disabling, image normalization, changed-pixel tolerance or fabricated
intermediate frames is used. The report records actual Chromium launch arguments.

The compiled motion stylesheet must byte-match the current factory. Every generated HTML page is
parsed for unique named regions and the native render-blocking marker; script inventories must
match the baseline exactly. The same compiled-page checks also run in the real book/portal CI tests.
All observed asset requests must remain local.

Separately, the default Chromium compositor captures 24 actual navigation contact sheets. Each has
before, native frames at ready-relative 0–400 ms in 40 ms steps, and settled. Frame timestamps and
the browser's actual animation timing are retained in report.json. Reduced-motion navigation must
not create a native transition. The authored title/body animation budget is 220 ms; browser-ready
to finished wall time also includes scheduling/compositor latency and is reported separately.

Directory: `/tmp/motion-acceptance/inspection/contact-sheets`.
Report and full-size resting screenshots: `/tmp/motion-acceptance/inspection/`.

Navigation pairs:

- Template: List of Figures to Example Chapter (the canonical template has only one authored chapter).
- Sample: Chapter 1 to Chapter 2.
- Portal: How it works to Create your handbook.

The native browser tests also check actual button displacement/arrow color, intermediate details
heights in both directions, first-load card delays, switch-driven theme interpolation on the body,
navbar, footer, heading and card, actual painted initial content, once-only reveal with a return to
static positioning, back-scroll without replay, and progress scaleX(1) at the end. A static pixel
fixture checks outside list markers at both widths/schemes. The peak cover highlight retains
calculated dark-mode contrast 4.71:1; a regression rejects the previous 14% overlay (4.03:1).

## Refinements and limits

New reading reveals use native view-timeline triggers with `play-once`, rather than a reversible
`animation-timeline: view()` animation. Unsupported browsers get static content. The original cover
entrance is retained. Result-count feedback follows CSS-observable focus/filter state; arbitrary
text replacements are not animated by a new script. Quarto/Bootstrap vendor assets are unchanged;
the guard covers every toolkit-authored/generated stylesheet, not a rewritten vendor bundle.

The default-compositor receipt is in progress. Its first 12 pairs include a strict mismatch of 15 pixels on the dark desktop template cover, within [345, 438, 460, 440]. Sampled computed styles and geometry are equal. This is a disclosed acceptance gap, not a pixel-identity pass. The PR remains draft pending the completed receipt and coordinator decision.
