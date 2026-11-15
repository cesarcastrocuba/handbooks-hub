# Change 0046 — Inspection evidence

The local portal and template reading site are built with the branch toolkit and served read-only:

- Portal: <http://127.0.0.1:8766/>; Design page: <http://127.0.0.1:8766/design.html>.
- Template book: <http://127.0.0.1:8767/>.
- Owner reference: <http://127.0.0.1:8765/>, supplied outside the repository.

No release, deployment, tag or merge was performed. The servers bind only to loopback and are left
running. Their PIDs and logs are under `.venv/inspection/server-8766.*` and `server-8767.*`.
Generated sites, raw screenshots and PDFs remain untracked under `.venv/` in this worktree.

## Commands and results

All commands run from `/home/ubuntu/github/handbooks-hub.worktrees/preview-align`.

| Command | Result |
| --- | --- |
| `python3 -m venv .venv` and `.venv/bin/pip install -r requirements-dev.txt -r tools/scripts/requirements-edition-preview.txt` | Installed toolkit/development dependencies and Playwright 1.60.0 |
| `.venv/bin/python -m handbook_toolkit --root . verify` | 5 checks, 0 problems |
| `.venv/bin/python -m unittest discover -s tools/tests -p test_portal.py -v` | 22 tests passed, 56.257 s; includes real Quarto render, byte determinism and Chromium computed-style/focus/target/scroll checks |
| `.venv/bin/python -m unittest discover -s tools/tests -p test_reading_site.py -v` | 13 tests passed, 11.502 s; once-only reveals, reduced motion, theme feedback and exact resting callout pixels retained |
| `.venv/bin/python -m unittest discover -s tools/tests -p test_docx_native.py -v` | 36 tests passed, 0.307 s |
| `.venv/bin/python -m unittest discover -s tools/tests -p test_design_conformance.py -v` | 13 tests passed, 0.036 s; no literal geometry in packaged layout CSS |
| `.venv/bin/python -m unittest discover -s tools/tests -p test_reference_docx.py -v` | 2 tests passed, 0.101 s; reference DOCX is byte-identical to its generator |
| `.venv/bin/python -m unittest discover -s tools/tests -p test_render_resources.py -v` | 4 tests passed, 2.520 s; actual themed rounded 100-row PDF retained every row and repeated header across eight pages |
| `make full PYTHON=.venv/bin/python` | 432 tests in 339.486 s: 429 passed, 3 failed, all solely from the three coordinator-owned STATUS statements |
| `.venv/bin/python -m handbook_toolkit --root . verify --full` | 7 checks, 3 problems, all stale toolkit statements in STATUS.md lines 10, 37, 47 |
| `git diff --check` | Passed |

An early exploratory `make check` ran while sources were still changing and failed. A subsequent
`make full` ran 431 tests in 329.514 s with four failures: three currency checks, plus the browser
check using a pre-refactor imported metric map against the concurrently changed CSS template.
Its repository check also saw this evidence file before it existed. The isolated stable-source
portal run passed all 22 tests; the final full run is performed after all source files are stable.
No failure is represented as a passing check.

## Built editions

```bash
.venv/bin/python -m handbook_toolkit.portal catalog/catalog.json --output .venv/portal-corrected --engine quarto
.venv/bin/python tools/scripts/edition_preview.py --template --output .venv/editions-corrected --require-tools
.venv/bin/python tools/scripts/edition_preview.py --repo /home/ubuntu/github/handbook-sample-01 --output .venv/sample --require-tools
.venv/bin/python sdd/changes/0046-preview-alignment/capture.py
```

All three builds succeeded. The template preview has all seven publication files, four HTML pages,
Typst PDF and a LibreOffice conversion. The sample preview is built from source commit
`a75046b4407383fddbbee02eeb47d4fbc68bc59b`, version `0.5.1-preview`, with seven publication files,
18 HTML pages, a 61-page Typst PDF and a 71-page LibreOffice conversion. Both builds required cached
DOCX page-number probing; neither skipped a required tool. The sample repository was read only.

The sample DOCX was also inspected as parsed XML: **33 data tables, 389 body cells and 96 header
cells**. Every inspected body cell had direct surface shading and the print border-color bottom
rule; every header retained accent-solid shading. Existing DOCX validation and cached index/page
checks ran during the builds. The Owner's desktop Word F9 test remains pending.

A bare clipped-table experiment retained 100 rows across seven pages. The regression probe using
the actual toolkit preamble/theme retained rows 0–99 and a repeated header across **eight pages**.
This supports keeping PDF rounding instead of accepting square corners. Word has square table
geometry; no unsupported rounding is claimed. Poppler prints `Suspects object is wrong type
(boolean)` for the standalone Typst probe's PDF metadata but extracts all pages/rows successfully.

## Initial computed styles (5ae35ca)

Chromium 148, executable `~/.cache/ms-playwright/chromium-1223/chrome-linux/chrome`, launched with
`--headless=new --no-sandbox`. Viewports: **1280 × 1000** and **390 × 1000**, both light and dark.
The following values were measured after local fonts loaded, without overriding product styles.

| Element | Preview 1280 / 390 px | Portal 1280 / 390 px | Radius: preview / portal |
| --- | --- | --- | --- |
| body | 15px / 15px | 15px / 15px | 0px / 0px |
| h1 | 48px / 32px | 48px / 32px | 0px / 0px |
| h2 | 24px / 24px | 24px / 24px | 0px / 0px |
| card title | 20px / 20px | 20px / 20px | 0px / 0px |
| button | 14px / 14px | 14px / 14px | 6px / 6px |
| tag | 11px / 11px | 11px / 11px | 5px / 5px |
| format | 12px / 12px | 12px / 12px | 6px / 6px |
| summary | 14px / 14px | 14px / 14px | 0px / 0px |
| links | 13px / 13px | 13px / 13px | 0px / 0px |

The same font sizes/radii were measured in dark mode. Body line-height is **23.25 px** on both
surfaces. Buttons are **700** weight with **10 × 16 px** padding, **21.7 px** line-height and
**43.6875 px** measured height on both surfaces. Tags have **2 × 8 px** padding and are static text
labels. Format links have **3 × 10 px** padding and **26.59375 px** height. Filter controls are
**29.6875 px** high. Cover corners are **4 / 10 / 10 / 4 px**, book and guide cards **8 px**.
Section heading line-height differs deliberately: preview 37.2 px, Quarto 28.8 px; both are 24 px.
Card-title line-height is preview 31 px versus Quarto 24 px, preserving the compact reading rhythm.
The preview's embedded mock hero uses a separate smaller scale; the table compares its top-level
page-title clamp with the real portal page-title clamp required by the brief.

Design-page table body cells are **14 px** with **21.7 px** line-height and **8 px / 12 px** padding;
the reference uses **10 px / 12 px**. Web table radius is **8 px**. All sampled body rows use the
same surface color: light **rgb(255, 253, 248)**, dark **rgb(28, 37, 38)**. Headers use accent-solid
and on-solid; body row borders use **#DDD3C0** / **#33403F**. Both widths retain horizontal scrolling
where a table is wider than its container. All portal/Design viewport samples have document width
equal to viewport width: **1280** or **390 px**, with no page-wide horizontal overflow.

The existing palette is preserved. Declared text contrast and the brightest cover highlight are
validated at the existing 4.5:1 floor. Keyboard focus has a visible **3 px** outline; buttons,
filters, search, sort, edition links and whole-card guide links meet the 24 px target-height check.
Inline prose links retain the inline-text exception; category tags are not controls.

## Screenshots

Raw captures and `computed.json` are under `.venv/inspection-final/`: preview reference frames,
portal home, Design page and template chapter, in both themes at both widths (24 reference/site
captures), plus four full sample-chapter captures and four sample-table crops. The sample capture
is chapter 1, `manuscript/chapters/ch01-why-handbooks-fail.html`, which contains genuine data tables.

Compact contact sheets are committed for review:

- [Desktop light](comparison-1280-light.webp) and [desktop dark](comparison-1280-dark.webp).
- [Phone light](comparison-390-light.webp) and [phone dark](comparison-390-dark.webp).
- [PDF and LibreOffice tables](print-tables.webp): sample PDF page 12, DOCX converted page 13,
  and the first page of the eight-page table probe.

The PDF and LibreOffice pages were rasterized with `pdftoppm -f PAGE -singlefile -scale-to 1400
-png FILE OUTPUT` and visually inspected. They show equal body fills and horizontal rules; the PDF
has rounded table corners and the DOCX has square corners. No screenshot is a desktop Word oracle.
The full-sized captures remain local; the committed WebP sheets are reduced review aids.

## Known gates

The coordinator must update the three stale STATUS toolkit statements; this Implementer did not
modify STATUS, decisions, any reference handbook, released pins or validator policy. Independent
review and Owner acceptance of the preview and Word behavior remain pending. CI edition artifact
identities are recorded in the PR body at handoff.

The served `design-tokens.css`, `handbook.css`, `portal.css` and `reading.css` were compared byte for
byte with the current source factories: all matched. Local `site_check` passed for the portal
(3 pages, 24 assets, all 200) and template book (2 pages, 26 assets, all 200).

## Initial stable-source full run (5ae35ca)

`make full PYTHON=.venv/bin/python` ran **432 tests in 339.486 s**: **429 passed, 3 failed**.
All failures are `test_verify_full`, `test_the_repository_itself_is_current` and
`test_repository_full_verification`, each reporting only the same three stale STATUS statements.
There were no other failures, errors or skips. All browser, PDF, DOCX, reference-byte and rendered
asset checks passed. Make stops at the test prerequisite, so the standalone fast and full
validators were also run separately: **5 checks / 0 problems** and **7 checks / 3 currency problems**.

The coordinator-owned synchronization is the only remaining mechanical repository gate. This is
not a green full-gate receipt; independent review, Owner preview acceptance and desktop Word
acceptance remain separate outstanding gates.

## Coordinator review correction evidence

All four findings in the global review of `5ae35ca` were fixed on the same branch. The five
committed WebP sheets were regenerated; the preceding initial measurements remain historical.
Current raw captures and SVG/OOXML probes are under `.venv/review77-inspection/`.

| Finding | Measured correction |
| --- | --- |
| Print border colors | Both print roles now `#DDD3C0`. Sample DOCX document XML has **650** explicit `w:color="DDD3C0"` attributes and **0** `D9E2EC`. All **389** body-cell bottom borders in **33** data tables are `DDD3C0`. |
| PDF justification | `par(justify: false)` is scoped to table cells. Sample PDF page **12** was rasterized and visually inspected: “README / or short / guide” is left aligned with natural word spaces; running prose stays justified. |
| Planned topics | Desktop: **20 px** actual gap from book grid to note, **20 px** top margin, **13 px** font, muted **rgb(85, 102, 106)**. The browser regression checks both themes and widths. |
| Home hero | At 1280 px: **40 px**, weight **700**, width **476.953125 px**, height **129.5625 px** (three lines). At 390 px: **28 px**, width **333.859375 px**, height **90.703125 px** (three lines). Other page h1 stays **48 / 32 px**. |

The new sample PDF remains **61 pages**; the LibreOffice conversion remains **71 pages**, with the
inspected DOCX table on page **13**. Poppler's SVG for PDF page 12 reports the actual 0.5 pt table
strokes and running 0.4 pt furniture as `rgb(86.66687%, 82.745361%, 75.294495%)`, which rounds to
**rgb(221, 211, 192)**. Token `chrome_rule` is used by web Sass, emitted CSS roles and the Typst
preamble; print furniture currently consumes `hb-border`, now the same cream color. No other
print consumer retains the old blue-grey rule token. The reference DOCX was regenerated using
`tools/scripts/generate_reference_docx.py` and passes its byte-parity test.

Correction builds (all with required tools):

```bash
.venv/bin/python tools/scripts/generate_reference_docx.py
.venv/bin/python -m handbook_toolkit.portal catalog/catalog.json --output .venv/review77-portal --engine quarto
.venv/bin/python tools/scripts/edition_preview.py --template --output .venv/review77-template --require-tools
.venv/bin/python tools/scripts/edition_preview.py --repo /home/ubuntu/github/handbook-sample-01 --output .venv/review77-sample --require-tools
.venv/bin/python sdd/changes/0046-preview-alignment/capture.py --output .venv/review77-inspection
make full PYTHON=.venv/bin/python
```

The portal, template and sample builds succeeded. Focused design tests: **23 passed in 0.107 s**;
reference-DOCX tests: **2 passed in 0.121 s**. The standalone full validator reports **7 checks,
3 currency problems**, exclusively the reserved STATUS statements. The full suite result follows
below. No STATUS or decisions file was changed.

Both localhost previews are rebuilt again after the correction commit, into
`.venv/review77-head-portal/` and `.venv/review77-head-template/site/`, and left serving on their
original ports. The current stylesheets are compared byte-for-byte with the source factories.

Correction full run: **433 tests in 306.515 s; 430 passed, 3 failed**, no errors or skips. The only
failures remain the CLI full-verification, repository-currency and repository-full wrappers, all
reporting the same STATUS.md lines 10, 37 and 47. Every browser/layout, print, DOCX, cached-index,
reference-byte and contrast check passed. The coordinator will synchronize STATUS and add the
new decision after this push, as directed in the review. The full gate is not claimed green here.

## Owner acceptance follow-up

The Owner reviewed the portal, template and sample previews and accepted the sample DOCX in
Word on 2026-11-15. [owner-acceptance.md](owner-acceptance.md) records the exact feedback and the
accepted artifact identity. The two requested corrections remove generated button hover arrows
and apply the neutral review role to the template checklist. No template version or pin is bumped.

A fresh sample build with required tools was compared with the actual accepted CI artifact:

```bash
gh run download 43734028505 --repo cesarcastrocuba/handbooks-hub --name edition-preview-sample --dir .venv/owner-accepted-sample
.venv/bin/python tools/scripts/edition_preview.py --repo /home/ubuntu/github/handbook-sample-01 --output .venv/owner77-sample --require-tools
sha256sum .venv/owner-accepted-sample/edition/book.docx .venv/owner77-sample/edition/book.docx
```

**The sample DOCX did not change: every byte matches.** Both SHA-256 hashes are
`744deb27b1837fe64956e69ee1c7464a9e1bfbca7869303a00dc8dba90a56a83`.
The accepted file is from run 43734028505, artifact 14169259876, source book commit
`a75046b4407383fddbbee02eeb47d4fbc68bc59b`. The follow-up does not change the sample manuscript or
DOCX processing; its HTML archive changes because the shared button CSS changes.

The template DOCX was compared with `.venv/review77-head-template/edition/book.docx` from before
this follow-up. Visible `w:t` text is identical. In `word/document.xml` only three attributes differ:
checklist left border `5C2D91` → `55666A`, fill `F5F0FA` → `F2F1ED`, and title paragraph style
`CalloutImportantTitle` → `CalloutReviewTitle`. `docProps/core.xml` also changes the normal created/
modified timestamps of the separately exported template build; every other ZIP member is identical.
Thus the content change is the checklist's callout style only, with ordinary build timestamp changes.
The template version remains 1.5.1 and its toolkit pin remains 0.10.3, pending the separate release PR.

The updated template preview was built with:

```bash
.venv/bin/python tools/scripts/edition_preview.py --template --output .venv/owner77-template --require-tools
.venv/bin/python -m handbook_toolkit.portal catalog/catalog.json --output .venv/owner77-portal --engine quarto
```

All three editions were inspected. HTML computed review colors are light **rgb(85, 102, 106)**
accent/title on **rgb(242, 241, 237)**, dark **rgb(163, 176, 176)** on **rgb(29, 38, 40)**.
The PDF retains the full suffixed title on page **4**, using the neutral accent/tint; Poppler's SVG
contains `rgb(94.902039%, 94.509888%, 92.941284%)` (`#F2F1ED`) and neutral title text. The existing
`"Review Checklist" in label` matcher already handles the suffix and was preserved. The DOCX box
uses `CalloutReviewTitle`, border `55666A` and fill `F2F1ED`; its LibreOffice conversion was inspected
on page **5**. This records an Implementer's inspection, not a new desktop Word acceptance claim.

At 1280 and 390 px in both schemes, hovering each home button produces `::after` content **none**
and retains **translateY(-2px)**. All five guide-arrow spans and the explicit “Read handbook →”
text remain. The focus-outline rule is unchanged. Raw screenshots and computed data are in
`.venv/owner77-inspection/`; the compact [owner follow-up sheet](owner-followup.webp) accompanies this record.

An isolated motion test run during simultaneous edition/browser builds hit the existing 30 ms
mid-reveal timing assertion (`position` had already returned to static after a separate running-state
read). The final full-suite run on stable sources is recorded below; the motion behavior or its timing
assertions were not weakened to hide that result.

Owner follow-up final gate: `make full PYTHON=.venv/bin/python` **passed**: **434 tests in
487.846 s**, no failures, errors or skips; fast validator **5 checks / 0 problems**; full
validator **7 checks / 0 problems**, including documentation currency. The final run includes the
updated hover/no-arrow regression, original motion checks and the real template HTML/DOCX
neutral-review assertions. `git diff --check` passed. STATUS/decisions were not modified by this
follow-up; the coordinator's preceding `b1cac26` commit fixed their earlier currency failures.

After committing and pushing this follow-up, the portal and template previews are rebuilt from
that HEAD into `.venv/owner77-head-portal/` and `.venv/owner77-head-template/site/`, served on
127.0.0.1:8766 and :8767. Their authored CSS is compared with current source factories, and the
local asset checks are rerun. The Owner's sample preview on port 8768 is not changed.
