# Record — Check the deployed site, not only the build

**Change:** `0045-deployed-site-check`. **Recorded:** 2026-11-15. Follow-up of change `0042`.

## Problem

`portal-pages` run 43617800145 deployed the Quarto portal on 2026-11-14 and succeeded. Every page
answered 200. Four stylesheets answered 404, because their directory was hidden and the Pages
artifact leaves hidden files out. The coordinator's check after the deployment requested the pages
and looked for the release links; the Owner found the defect by opening the site. Change `0042`
removed the cause and added a build-side rule; nothing yet looked at what was actually served.

## What changed

- `tools/src/handbook_toolkit/site_check.py` (standard library only): fetches each page, collects
  the same-origin targets of `link`, `script` and `img`, requests each once and fails with the
  list of those that do not answer 200. It retries a bounded number of times, because Pages needs
  a few seconds to serve a new deployment. HTTPS only (plain HTTP on loopback for the tests); a
  redirect to another origin is an error.
- `portal-pages.yml`: `deploy` exposes its `page_url`; a new job `verify` (read-only, pinned
  checkout without credentials, same condition as `deploy`) runs the check on the root,
  `design.html` and `create.html`. The URL reaches the shell through `env`.
- `docs/operations-runbook.md`: the manual command and what a failure means.

## Scope

Books are not changed. Before a release is listed, `catalog_verification` already compares every
file of the released HTML archive with the live reading site, so a file that is not served is
reported there. Adding the check to the book template's release workflow needs a template release
that pins a toolkit containing the module; it is left as a follow-up.

## Evidence

- Live, before merge: portal `3 page(s), 27 asset(s), all 200`; sample reading site
  `1 page(s), 25 asset(s), all 200`.
- Unit tests against a local HTTP server: a complete site passes; a missing stylesheet fails and
  is named; a missing page fails; the retry is bounded; plain HTTP is refused off loopback.
- Not observed before merge: the `verify` job, which runs on the next deployment.
