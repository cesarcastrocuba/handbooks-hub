# Change 0093 — Star follow-ups and the Quarto-dependent tests in CI

Implementer: oc7 (OpenCode). Reviewer and merger: a different agent. Branch
`fix/0093-stars-and-quarto-ci` from `main` `65d9921`. No version bump, tag or release.

This change closes hub issues 148 (follow-ups of the PR 146 review of change `0085`) and 137
(Quarto-dependent tests skipped in CI). It changes only the web chrome and CI; no manuscript,
PDF or Word edition changes.

## Review follow-up (oc8, PR 159)

- **Major:** the first revision grew the portal navbar from 56 to 57 px at 992/1000/1280 px
  because the star's negative margin (-2.5 px) still left a larger margin box than the base link.
  The margin is now -4 px and the rule is scoped to the expanded navbar; the portal is 56 px
  again and the tests assert the absolute base heights so a drift is caught.
- **Minor:** the CHANGELOG no longer claims that no Quarto-gated test is skipped anywhere in CI;
  it says they now run in `publication-build` while `checks` and `quickstart` skip them by design.
- **Optional 1:** the star rule is split at 992 px. Below it the collapsed menu keeps its base
  full-width row (the portal row was already 44 px; the reading-site row is 44 px high and keeps
  its base width). From 992 px the 44 × 44 target applies with the margin that preserves the base
  navbar height.
- **Optional 2:** the CI evidence below names the run of the reviewed head.
- **Optional 3:** the record says that `NavbarStarBrowserTests` runs only in the non-required
  `edition-preview (template)` job, and why.

## Issue 148

### 1. Navbar star is a 44 px target (Minor)

The reading-site and portal navbars rendered the star link as a Bootstrap `.nav-link` 36 to 39 px
tall at 992 px and wider. A navbar item cannot carry a class, but Quarto parses its `text` as
Markdown, so `stars.navbar_markup()` emits `[★ Star · 1.2k]{.star-link}` and the label becomes
`<span class="menu-text"><span class="star-link">…</span></span>`. From 992 px the shared
`handbook.css` targets `#quarto-header .navbar .nav-link:has(.star-link)` with `min-width` and
`min-height` 44 px, centers the label, and applies a negative block margin that returns the extra
height to the flex line, so the navbar keeps its base height. Below 992 px the rule keeps the
collapsed menu row at its base full width and at least 44 px high.

Measured in Chromium on the final head, with counts present:

| Page | 320 px | 390 px | 992 px | 1000 px | 1280 px | Navbar at ≥ 992 |
| --- | --- | --- | --- | --- | --- | --- |
| Portal star | 246.0 × 44 | 316.0 × 44 | 95.6 × 44 | 95.6 × 44 | 95.6 × 44 | 56.0 px (base 56.0) |
| Reading-site star | 243.5 × 44 | 313.5 × 44 | 109.8 × 44 | 109.8 × 44 | 109.8 × 44 | 58.125 px (base 58.125) |

`book-metric-37` (44 px) and `book-metric-38` (-4 px) carry the numbers in the design metrics.

Proof: `test_reading_site.NavbarStarBrowserTests` renders the reading-site navbar with a real
Quarto render and `test_portal.QuartoPortalTests.test_navbar_star_is_a_44_pixel_target_without_overflow_or_shift`
renders the portal. Both measure `getBoundingClientRect()` at 320, 390, 992, 1000 and 1280 px,
opening the collapsed menu below 992 px, and assert `width ≥ 44`, `height ≥ 44`, and
`document.documentElement.scrollWidth ≤ width`. From 992 px they assert the absolute base navbar
height (56 px for the portal, 58.12 ± 0.5 px for the reading site), so a drift against base
`65d9921` fails. The portal test also builds the same site with a count and asserts the navbar
height is unchanged, so writing the count cannot shift the layout.

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
a required job depend on the flaky one. Consequence: `NavbarStarBrowserTests` runs only in the
non-required `edition-preview (template)` job. That is an accepted risk, recorded at closure; the
portal half of the same rule runs in the required `publication-build` job through `test_portal`.

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
| `make check` | `Ran 681 tests in 1182.462s` — `OK` (no skips); `VERIFY: 5 check(s), 0 problem(s)`; `site-check: 1 page(s), 3 asset(s), all 200` |
| `make verify-full` | `VERIFY (full): 7 check(s), 0 problem(s)` |

## CI evidence

Pull request 159, CI run `46166634655`, all jobs pass. Every line below is `OK` with no
`skipped=` suffix, so the Quarto-gated skip count is 0.

`publication-build`, step "Run the remaining Quarto-dependent test files" (job
`141045510023`):

```
test_numbering_parity                Ran 16 tests in 25.965s   OK
test_appendices_document_control     Ran 9 tests in 37.261s    OK
test_artifact_optimize               Ran 18 tests in 74.968s   OK
test_glossary_build                  Ran 1 test in 12.089s     OK
test_portal                          Ran 32 tests in 37.009s   OK
```

`publication-build` also keeps its existing files green: `test_build` (35 tests, OK),
`test_render_resources` (6, OK), `test_table_fit` and `test_tables_figures_build` (20, OK) and
`test_template` (30, OK). `test_portal` runs with Playwright, so
`test_legacy_engine_does_not_overflow_at_phone_widths` and
`test_navbar_star_is_a_44_pixel_target_without_overflow_or_shift` executed instead of skipping.

`edition-preview (template)`, step "Verify native CSS motion behavior in Chromium" (job
`141045509956`):

```
test_navbar_star_is_a_44_pixel_target_without_overflow ... ok
Ran 15 tests in 18.030s
OK
```

`checks` (1m3s) and `quickstart` (57s) still skip the Quarto-gated tests by design; the goal is
met in `publication-build`, a required check. No job failed and no test was re-skipped; the known
`NativeMotionBrowserTests` flake did not reproduce in this run.

Measured browser evidence from the same tests: the portal star is 59.6 × 44 px at 320, 390 and
1280 px and the portal navbar stays 56 px at 1280; the reading-site star is 109.8 × 44 px with a
count and the reading-site navbar stays 58 px (58.125 px before). `scrollWidth` never exceeds the
viewport width.

## Known gaps

- `checks` and `quickstart` still have no Quarto, so their copy of the suite still skips the
  Quarto-gated tests. The choice above is deliberate: the tests run in `publication-build` (a
  required check) instead of duplicating the full build in the fast job.
- `NativeMotionBrowserTests` remains a known local flake. If it flakes in `edition-preview`, the
  log will be reported rather than hidden.
- The black-box mobile layout is proven at 320, 390 and 1280 px in Chromium only, as the existing
  browser tests are.
