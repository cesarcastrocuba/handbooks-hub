# Record — Authenticated release verification

**Change:** `0035-verification-api-auth`. **Recorded:** 2026-11-14. Follow-up of the `v0.4.2`
release in change `0034`.

## Problem

`portal-pages` run 43579566245 failed twice with `remote asset returned HTTP 403` before a third
attempt deployed `v0.4.2`; the same happened once for `v0.4.1`. The same verification passed
locally three times in a row and in `catalog-update` minutes earlier. It was recorded as a
"transient asset 403" and retried.

The cause is not the asset. `catalog_verification` reads release metadata from `api.github.com`
without credentials, so its requests count against the anonymous rate limit of the runner's shared
address. When that limit is exhausted the API answers 403, and the error message named neither the
host nor the reason.

## What changed

- `catalog_verification` sends `Authorization: Bearer $GITHUB_TOKEN` when the variable is set, and
  only to `api.github.com`. Headers are computed for each request from its host, so a redirect to
  another host carries no token.
- The failure message names the host, and says that the rate limit is exhausted when the response
  says so (`X-RateLimit-Remaining: 0` on a 403 or 429).
- `portal-pages.yml` and `catalog-update.yml` pass the workflow token to the verification step.
  Their permissions do not change: `contents: read` is enough for public release metadata.
- The operations runbook describes the token and the new message.

## Why not a retry

A retry hides the cause and does not help while the limit stays exhausted. Authenticated requests
have their own, much higher limit, so the failure does not occur.

## Limits

- Without `GITHUB_TOKEN` (a local run) the verification still works anonymously and can still hit
  the anonymous limit; the message now says what to do.
- Not observed after the change: a `portal-pages` run on `main`. The next catalog change proves it.
