# Change 0080 — Reproducible `book-html.zip`: no render times in the sitemap

Fixes hub issue 98. Implementer Claude; reviewer and merger a different agent. Branch
`fix/html-sitemap-lastmod` from main `57e7350`. No version bump or tag: the toolkit fix ships with
the next toolkit release, which needs its own Owner approval.

## Defect

Two builds of the same book commit gave identical PDF, DOCX, Markdown and source bundles, but a
different `book-html.zip`. A member-by-member comparison of two local builds of Solutions
Architecture Handbook commit `ef3b16b` (toolkit `0.14.2`, Quarto 1.11.9) found one differing member
out of 209: `sitemap.xml` (7,689 bytes in both builds; archives 15,002,483 and 15,002,478 bytes).
Every `<lastmod>` held the time Quarto rendered that page, for example `2026-11-21T14:23:43.106Z`
against `2026-11-21T14:50:46.758Z`. Quarto ignores `SOURCE_DATE_EPOCH` for this field. A book gets
a sitemap whenever its reading site has a `site-url`, which every GitHub-hosted book has.

The portal already removed these times (`portal_quarto._omit_sitemap_times`). The book HTML build did
not. The existing test `test_build_book_reproducible_bytes` missed the problem because its fixture
has `repository.url: null`, so it had no `site-url` and no sitemap.

## Fix

| File | Change |
| --- | --- |
| `tools/src/handbook_toolkit/artifacts.py` | New `omit_sitemap_times(site)`, moved from the portal unchanged in behaviour: removes every `lastmod` from `sitemap.xml`, keeps every `loc`, no-op without a sitemap, `ValueError` on a malformed one. `lastmod` is optional in the sitemap protocol, and a render time is not a page's modification date. |
| `tools/src/handbook_toolkit/build_html.py` | Calls it on the reading site before `archive_tree`; a malformed sitemap fails the build with `BuildError`. |
| `tools/src/handbook_toolkit/portal_quarto.py` | Uses the shared function; its private copy and the `ElementTree` import are removed. |

## Tests

- `test_artifacts.test_sitemap_render_times_are_omitted`: no sitemap, a sitemap with and without
  `lastmod`, and a malformed sitemap.
- `test_artifact_optimize.test_build_book_reproducible_bytes`: the fixture now has a GitHub
  repository, so Quarto writes a sitemap. The test asserts the sitemap is archived with its `loc`
  entries and without `lastmod`, and still compares every payload of two builds byte by byte.
  Without the `build_html.py` change it fails with `'lastmod' unexpectedly found`.

## Verification evidence

The pull request records the commands and results on its exact HEAD, including two full local
builds of Solutions Architecture `ef3b16b` with this toolkit.

Rollback boundary: revert this commit.
