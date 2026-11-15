# Record — Site resources in a path a static host publishes

**Change:** `0042-publishable-site-paths`. **Recorded:** 2026-11-15. **Toolkit:** `0.10.3`.

## Problem

On 2026-11-14 the Quarto portal was deployed (`HUB-DEC-041`, `portal-pages` run 43617800145). The
Owner reported that the live portal showed no styles. Every page answered 200, which is all the
deployment check looked at; four of its stylesheets answered 404:

```text
404 .handbook-render/html/design-tokens.css
404 .handbook-render/html/handbook.css
404 .handbook-render/html/portal.css
404 .handbook-render/html/reading.css
```

The toolkit stages its render resources in `.handbook-render/` inside the rendered project, and
Quarto copies the referenced stylesheets, fonts and favicon into the site under that same hidden
path. `actions/upload-pages-artifact` v4 and later leave hidden files out of the Pages artifact.
The portal workflow uses v5.0.0, so the directory never reached the server.

The book reading site has the same layout. The published sample is styled only because its release
workflow still uses `upload-pages-artifact@v3`; the book template's `release.yml` uses v5.0.0, so
**a new book created from the template would have been published without styles**. No test saw
it: the tests read the built directory, where the hidden files exist.

## What changed

- `render_resources.RENDER_DIRECTORY = "handbook-render"` is the single name of the staged
  directory; `build.py`, `build_html.py`, `reading_site.py` and `portal_quarto.py` use it.
- `artifacts.hidden_site_paths` lists the paths of a site that have a component starting with a
  dot. The HTML payload inspection of `build-book` fails on any, and `build_portal` refuses to
  return such a site, for both engines.
- Tests: an HTML archive with a hidden stylesheet is rejected; the rendered Quarto portal has no
  hidden path and every local stylesheet, script and image of every page exists in the site.

## Consequences

- Toolkit `0.10.2` is tagged but, like `0.10.0`, is not pinned by any template or book. Template
  `1.5.1` and sample `v0.5.1` pin `0.10.3`.
- The portal is redeployed from this change. After a deployment the check is now that the
  stylesheets of the live page answer 200, not only the page.

## Evidence

- Before: `curl` of the four stylesheet URLs of the live portal returned 404 (above).
- After: the sample built with this change has no hidden path in `book-html.zip`; its pages
  reference `handbook-render/html/*.css`. The Quarto portal built with this change has no hidden
  path and passes the new asset test.
- `make full`: see the pull request.
- Not verified before merge: the live portal, which is redeployed and checked after it.
