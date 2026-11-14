# WP5 evidence

## Environment and source

Initial main dcfd8c86a616c931ae68450c60dbd220cfd49a08 (toolkit-v0.10.0); integrated main's
print-path fix d4480f9 and retained toolkit 0.10.1. The final pre-PR main merge/version is reported
in the PR. No edits were made to the other writer's print/staging files. Quarto 1.11.9, Python 3.12,
Playwright Chromium; the real catalog lists sample v0.4.2 at the time of these measurements.

Created and activated a local .venv; installed requirements-dev.txt and the edition-preview browser
requirements; installed Chromium. Pillow/ruff were used only as local inspection aids.

## Commands and observed results

- Built the original generator before editing: /tmp/wp5-baseline. A later legacy build at
  /tmp/wp5-legacy-final passed cmp against its index.html. All shared font/notice bytes are unchanged.
- `python3 -m unittest discover -s tools/tests -p test_portal.py -v`: 18 tests passed in 38.564 s
  at this stage; final focused count/result is reported in the PR. Tests parse HTML/YAML and render
  malicious text, empty catalogs, a standalone Design page and repeated real Quarto output.
- `python3 -m unittest discover -s tools/tests -p test_portal_pages_workflow.py -v`: 7 passed.
  The trigger, permissions, deploy condition and verification token remain unchanged. The pinned
  Quarto setup and non-deployed candidate render are covered.
- `python3 -m handbook_toolkit.catalog_verification catalog/catalog.json`: **release verification: OK**.
  No release checks were bypassed or weakened. This is distinct from the offline generator.
- `make full`: initial integrated run passed 384 tests in 204.107 s, fast verify 5/0 and full
  verify 7/0. Subsequent final tests/HEAD and CI results are reported in the PR.
- `python3 tools/scripts/portal_preview.py --output /tmp/wp5-acceptance-preview`: succeeded.
  Both engines, the two-book fixtures, Design, guide pages and native guide-search navigation
  were rendered and inspected in light/dark at 1440 and 390. The script records parity.json,
  PREVIEW.md, complete site trees and screenshots; CI runs the same sibling script.
- The installed-wheel CI check stages a full portal outside the checkout, exercising packaged QMD,
  templates, JavaScript, CSS, all fonts, generated Design data and native configuration.

The first repeat-build proof differed only in sitemap lastmod values derived from staging mtimes;
parsed omission of those optional fields made every file repeat exactly. The first browser proof
caught a Cosmo Google Fonts request. Explicit shared Sass web-font-path:false removes it; the
final browser guard allows loopback inspection only and records no external requests.

## Weight measurements

Uncompressed bytes of every published HTML/CSS/JS/font file; image/JSON/XML/notice bytes are not
hidden in the font total. Initial-load bytes are the union of successful local HTML/CSS/JS/font
responses from a fresh desktop Chromium context. No compression difference is used to mask growth.

| Type | Legacy | Quarto candidate |
| --- | ---: | ---: |
| HTML | 25,538 | 306,257 |
| CSS | 0 (inline in HTML) | 1,127,882 |
| JavaScript | 0 (inline in HTML) | 355,447 |
| WOFF2 | 456,120 | 456,120 |
| WOFF | 0 | 180,288 |
| TTF/OTF | 0 | 0 |
| **Total** | **481,658** | **2,425,994** |
| Initial library load | 253,846 | 1,925,403 |

**Result: FAIL.** The deployed default remains legacy. The new generator is opt-in, not a
replacement approved by screenshots alone.

## Browser evidence and inspection

All library vectors pass in both engines: cafe/CAFÉ, zurich security, missing, clear; category-only
and category+query; reverse title and latest order. Fixtures are invented test data with distinct
URLs, not approved release entries. The native guide search also finds withdrawal and reaches
publishing.html. Old external links, guide fragments, OFL notices and llms.txt retain their targets.

Computed contrast (light/dark): body 13.14/14.13; summary 5.91/7.00; card link 7.52/8.51; selected
filter 7.65/5.28; footer 5.34/7.87. Keyboard Tab reaches an outlined skip link first. Candidate phone
scrollWidth is 390/viewport 390; the unchanged legacy is 460/390. One/two-book layout captures and
Design component/control captures are in the preview tree; inspection is recorded with the PR.

All authored motion comes from the same guarded reading.css tested by WP4. No motion script or
remote dependency was added. Existing catalogue library filtering remains a shared inline script.
