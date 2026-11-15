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

## Computed styles

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

## Final stable-source full run

`make full PYTHON=.venv/bin/python` ran **432 tests in 339.486 s**: **429 passed, 3 failed**.
All failures are `test_verify_full`, `test_the_repository_itself_is_current` and
`test_repository_full_verification`, each reporting only the same three stale STATUS statements.
There were no other failures, errors or skips. All browser, PDF, DOCX, reference-byte and rendered
asset checks passed. Make stops at the test prerequisite, so the standalone fast and full
validators were also run separately: **5 checks / 0 problems** and **7 checks / 3 currency problems**.

The coordinator-owned synchronization is the only remaining mechanical repository gate. This is
not a green full-gate receipt; independent review, Owner preview acceptance and desktop Word
acceptance remain separate outstanding gates.
