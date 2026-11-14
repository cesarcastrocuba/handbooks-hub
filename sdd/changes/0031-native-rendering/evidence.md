# WP3 evidence

Baseline: toolkit 0.9.2 at origin/main 2e294388ea4e4039744b14e4164301f6c085f587.
Sample source, read-only: 70383d125841006b8a73c5906cfa6dda4741300b.
Quarto 1.11.9, Pandoc 3.10, Typst 0.15.1; Python 3.12; LibreOffice 24.2.

## Commands

- python3 -m venv .venv; activate; pip install -r requirements-dev.txt
  -r tools/scripts/requirements-edition-preview.txt; python3 -m playwright install chromium:
  succeeded. Pillow was installed only for local side-by-side screenshot contact sheets.
- edition_preview.py --repo /home/ubuntu/github/handbook-sample-01 --output /tmp/wp3-before:
  succeeded before source changes, seven edition files, LibreOffice PDF, 12 light/dark desktop/phone
  screenshots. The source pin was explicitly overridden by preview mode only.
- quarto render /tmp/wp3-poc --to html: succeeded for brand and Sass variants; three native
  cross-references resolve to Table/Figure/Listing 1.1 in chapter.html.
- Behavior-preserving split: test_build.py, 24 tests passed in 59.663 s before commit aa1373e.
- make full: final result recorded below.
- test_build.py and test_template.py: final results recorded below.
- edition_preview.py sample after: /tmp/wp3-final-preview; result recorded below.

## Visual comparison

Before and candidate contact sheets for index, chapter 2 and tables were inspected side by side
in light and dark. /tmp/wp3-style-comparison.json records computed geometry/type/color. The first
candidate exposed a 17 px dark-navbar height difference from replacing Darkly; scheme-specific Sass padding
variables now preserve that spacing. A chrome_rule token preserves the prior inherited Quarto
outline colors (the first same-base candidate had bright outlines in dark mode). First-page and chapter typography, content widths and token
colors match. Native lists replace the cloned page's stale navigation and now have native next/
previous links; this structural change is intentional. Final inspection is recorded below.

Toolkit-authored !important count: before 25, after 0 (generated CSS plus layout and Sass). The
packaged source stylesheet contains substitutions for dimensions; staging expands every one.

## Final results

- make full: 362 tests passed in 133.620 s; fast verify 5 checks/0 problems; full verify
  7 checks/0 problems. The subsequently extended resource conformance suite passed 13 tests;
  Markdown parser suite passed 6 tests. CI will include the additional conformance test.
- Focused test_build.py: 23 tests passed in 118.069 s (the obsolete regex-replacement test was
  replaced by native-page integration assertions). The real fixture includes a table, figure and
  listing; the chapter-only fixture asserts all empty lists are omitted.
- Focused test_template.py: 18 tests passed in 42.201 s, including both real seven-file builds and
  initialize-book round trips.
- Final sample preview: /tmp/wp3-handoff-preview, seven edition files, LibreOffice PDF and
  12 screenshots. Browser parsing confirmed all four number/caption links in tables.html reach
  existing target IDs and the list page appears in search.json.
- Inspected side-by-side index, chapter 2 and Tables in light/dark at desktop and phone widths.
  The final native list keeps the old title-band margin and full caption links. Quarto adds its
  native previous/next controls and issue footer. The shared theme's measured body, navbar,
  sidebar, title, links, callout and table-header properties are identical to baseline on index
  and chapter 2 in both schemes. Navbar heights: light 58.125 px, dark 75.125 px.
- Remaining post-render reading-site HTML edits: none. Fallback items: none.

Local screenshot paths are evidence generated for this run, not committed publication artifacts.
Reviewers can reproduce them with edition_preview.py or inspect the PR's edition-preview artifacts.
