# Change 0093 — Star follow-ups and the Quarto-dependent tests in CI

Implementer: oc7 (OpenCode). Reviewer and merger: a different agent. Branch
`fix/0093-stars-and-quarto-ci` from `main` `65d9921`. No version bump, tag or release.

This change closes hub issues 148 (follow-ups of the PR 146 review of change `0085`) and 137
(Quarto-dependent tests skipped in CI). It changes only the web chrome and CI; no manuscript,
PDF or Word edition changes.

## Issue 148

### 1. Navbar star is a 44 px target (Minor)

The reading-site and portal navbars rendered the star link as a Bootstrap `.nav-link` 36 to 39 px
tall at 992 px and wider. A navbar item cannot carry a class, but Quarto parses its `text` as
Markdown, so `stars.navbar_markup()` emits `[★ Star · 1.2k]{.star-link}` and the label becomes
`<span class="menu-text"><span class="star-link">…</span></span>`. The shared `handbook.css` now
targets `#quarto-header .navbar .nav-link:has(.star-link)` with `min-width` and `min-height`
44 px and centers the label. The negative block margin returns the extra height to the flex line,
so the navbar keeps its height instead of growing: measured at 1280 px the portal navbar is 56 px
(unchanged) and the reading-site navbar 58 px (58.125 px before, sub-pixel). The box measures
65.3 × 44 px without a count and 109.8 × 44 px with one, and the page never overflows.

`book-metric-37` (44 px) and `book-metric-38` (-2.5 px) carry the numbers in the design metrics.

Proof: `test_reading_site.NavbarStarBrowserTests` renders the reading-site navbar with a real
Quarto render and `test_portal.QuartoPortalTests.test_navbar_star_is_a_44_pixel_target_without_overflow_or_shift`
renders the portal. Both measure `getBoundingClientRect()` at 320, 390 and 1280 px, opening the
collapsed menu below 992 px, and assert `width ≥ 44`, `height ≥ 44`, and
`document.documentElement.scrollWidth ≤ width`. The portal test also builds the same site with a
count and asserts the navbar height is unchanged, so writing the count cannot shift the layout.

### 2. Redirect test sockets (Optional)

`test_stars.test_a_redirect_is_refused…` now calls `server_close()` on both `HTTPServer` instances
after `shutdown()`, so the listening sockets do not leak. Run with
`python -W error::ResourceWarning -m unittest test_stars -v`: 13 tests, OK, no ResourceWarning.

### 3. Concurrent portal star lookups (Optional)

`stars.prefetch_counts(repositories)` reads distinct repositories with
`ThreadPoolExecutor(max_workers=8)` (bounded by the number of repositories). It compares keys
case-insensitively, keeps the first-seen order for a deterministic result, and delegates each
request to `star_count`, so a failure or timeout is still just `None`. `stars.TIMEOUT` drops from
10 s to 5 s. The Quarto portal prefetches the hub and every book repository before rendering the
cards; the rollback-only legacy engine does the same before `_card`.

Tests in `test_stars.py`:
- `test_prefetch_reads_each_distinct_repository_once_and_keeps_order`: five inputs, three distinct
  repositories (one duplicate spelling), one failing; the opener sees each repository once, the
  failing one is `None`, the others keep their counts, and the result order is the input order.
- `test_prefetch_looks_up_repositories_concurrently`: a `threading.Barrier(3)` in the opener only
  releases if all three requests are in flight; a sequential implementation would break the
  barrier and return no counts.
- `test_prefetch_is_a_no_op_unless_the_build_asks_for_counts`.

### 4. Legacy portal overflow (Optional, fixed)

The rollback-only legacy portal overflowed to 552 px at both 320 and 390 px because
`.links` was `flex-wrap: nowrap` with `white-space: nowrap`; the star link ran past the viewport.
Changing `.links` to `flex-wrap: wrap` is the whole fix (the links keep `white-space: nowrap`
individually). Proof: `test_portal.PortalTests.test_legacy_engine_does_not_overflow_at_phone_widths`
asserts `scrollWidth ≤ width` at 320, 390 and 1280 px. This is a small stylesheet change inside
the legacy generator, so it was fixed rather than deferred.

## Issue 137

Chosen option: **extend `publication-build`**, not `checks`.

`checks` is the fast job (`make check` is documented as "suitable for every commit"), and it
already runs the whole suite with Quarto absent. Adding Quarto, LibreOffice and Playwright there
would duplicate every real build that `publication-build` already runs (`test_build`,
`test_render_resources`, `test_table_fit`, `test_tables_figures_build`, `test_template`), roughly
doubling the build time on every pull request and changing the job's purpose. `publication-build`
already installs Quarto `1.11.9`, poppler, qpdf and LibreOffice; it only lacked five test files
and a browser.

Changes to `.github/workflows/ci.yml` (`publication-build`):
- installs `tools/scripts/requirements-edition-preview.txt` and
  `python -m playwright install --with-deps chromium`, so the portal browser tests run;
- runs the five missing files: `test_numbering_parity`, `test_appendices_document_control`,
  `test_artifact_optimize`, `test_glossary_build` and `test_portal`.

Every file guarded by `BUILD_AVAILABLE` or a Quarto check and the job that now runs it:

| Test file | Quarto guard | CI job |
| --- | --- | --- |
| `test_build.py` | `BUILD_AVAILABLE` | `publication-build` (already) |
| `test_numbering_parity.py` | `BUILD_AVAILABLE` | `publication-build` (new step) |
| `test_appendices_document_control.py` | `BUILD_AVAILABLE` | `publication-build` (new step) |
| `test_artifact_optimize.py` | `BUILD_AVAILABLE` (from `test_build`) | `publication-build` (new step) |
| `test_glossary_build.py` | `BUILD_AVAILABLE` (from `test_build`) | `publication-build` (new step) |
| `test_tables_figures_build.py` | `BUILD_AVAILABLE` | `publication-build` (already) |
| `test_template.py` | `BUILD_AVAILABLE` | `publication-build` (already) |
| `test_render_resources.py` | `skipUnless(quarto)` | `publication-build` (already) |
| `test_table_fit.py` | `skipUnless(quarto)` | `publication-build` (already) |
| `test_portal.py` | `skipUnless(quarto)` | `publication-build` (new step, Playwright added) |
| `test_reading_site.py` | `skipUnless(quarto)` on `NavbarStarBrowserTests` | `edition-preview` (already runs the file with Playwright) |

`test_reading_site.py` is not added to `publication-build`: its `NativeMotionBrowserTests` is a
known intermittent browser test and `edition-preview` already runs that file with Quarto and
Playwright on every pull request, so the new reading-site target test has a CI home without making
a required job depend on the flaky one.

## Files

| File | Change |
| --- | --- |
| `tools/src/handbook_toolkit/stars.py` | `TIMEOUT` 5 s, `WORKERS`, `prefetch_counts`, `navbar_markup`. |
| `tools/src/handbook_toolkit/reading_site.py` | Navbar star text uses `navbar_markup`. |
| `tools/src/handbook_toolkit/portal_quarto.py` | Navbar star text uses `navbar_markup`; prefetch before staging. |
| `tools/src/handbook_toolkit/portal.py` | Legacy prefetch; `.links` wraps at phone widths. |
| `tools/src/handbook_toolkit/render_data/html/handbook.css` | 44 px navbar star rule. |
| `tools/src/handbook_toolkit/design.py` | `book-metric-37`, `book-metric-38`. |
| `tools/tests/test_stars.py` | Markup assertions, `server_close()`, three prefetch tests. |
| `tools/tests/test_reading_site.py` | `NavbarStarBrowserTests` (Quarto + Playwright). |
| `tools/tests/test_portal.py` | Navbar target test, legacy overflow test. |
| `.github/workflows/ci.yml` | `publication-build`: Playwright and the five missing files. |
| `CHANGELOG.md` | `[Unreleased]` entries. |
| `docs/operations-runbook.md` | Concurrent, bounded, 5 s star lookups. |

## Commands and results

Run in the hub venv (`source …/hubvenv/bin/activate`, `pip install -e tools`), from the worktree:

| Command | Result |
| --- | --- |
| `python -W error::ResourceWarning -m unittest test_stars -v` | 13 tests, OK, no ResourceWarning |
| `python -m unittest test_reading_site -v` | 15 tests, OK (exit 0) |
| `python -m unittest test_portal -v` | 32 tests, OK |
| `python -m unittest test_design test_workflow_pins test_docs_commands test_workflow_system_dependencies test_portal_pages_workflow -v` | 41 tests, OK |
| `make check` | `Ran 681 tests in 1268.205s` — `OK` (no skips); `VERIFY: 5 check(s), 0 problem(s)`; `site-check: 1 page(s), 3 asset(s), all 200` |
| `make verify-full` | `VERIFY (full): 7 check(s), 0 problem(s)` |

## CI evidence

Filled from the pull-request run after the first push:

- `publication-build`: the five new files report `Ran N tests … OK (skipped=K)`; every Quarto-gated
  skip is 0. (Pending.)
- `checks` and `quickstart`: their Quarto tests still skip by design; the goal is met in
  `publication-build`, which runs every Quarto-gated file.
- `edition-preview`: `test_reading_site` including `NavbarStarBrowserTests`.

## Known gaps

- `checks` and `quickstart` still have no Quarto, so their copy of the suite still skips the
  Quarto-gated tests. The choice above is deliberate: the tests run in `publication-build` (a
  required check) instead of duplicating the full build in the fast job.
- `NativeMotionBrowserTests` remains a known local flake. If it flakes in `edition-preview`, the
  log will be reported rather than hidden.
- The black-box mobile layout is proven at 320, 390 and 1280 px in Chromium only, as the existing
  browser tests are.
