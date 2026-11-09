# Evidence — Release `v0.2.2` and catalog listing

**Decision:** `HUB-DEC-023`. **Sample commit:** `c1485183ca1c52e28bdbd28c92c1f382b6603d55`.
**Catalog automation commit:** `69513cf952baf1f0a3cb102945961df2682458fb`. **Recorded:** 2026-11-09.

## Owner decision

On 2026-11-09 the Owner accepted P5-GATE: the operations runbook, the clean-clone evidence and their
documented limits, including the 1-hour reading-site and 30-minute replacement limits. The Owner also
authorized publishing sample `v0.2.2`, updating the catalog, and withdrawing `v0.2.1` by deleting its
release page and assets while keeping its tag, once the portal shows `v0.2.2`.

The Owner merged hub PR 7 (`ecd1878`) and sample PR 4 (`c148518`) directly.

## Released

Sample release `v0.2.2` was published by run 42621799383 from `c148518`. The release has six assets:
`book-html.zip`, `book-source.zip`, `book.docx`, `book.pdf`, `publication-manifest.json` and
`SHA256SUMS.txt`. The manifest records toolkit `0.5.0`.

The PDF author is Franz César Castro Cuba. The third-party notices page is at
`manuscript/back-matter/third-party-notices.html` and is live with HTTP 200 at
<https://cesarcastrocuba.github.io/handbook-sample-01/manuscript/back-matter/third-party-notices.html>.

## Catalog automation

| Run | Result |
| --- | --- |
| Dry run 42622072835 | Success; reported `updated: handbook-authoring-and-publishing v0.2.1 -> v0.2.2 (published 2026-11-09)` and `release verification: OK`; publish skipped |
| Real run 42622209774 | Success; pushed `catalog/handbook-authoring-and-publishing-v0.2.2` at `69513cf`; the first real run of the automation |

## Verified

- `sha256sum -c SHA256SUMS.txt`: five entries OK; the sixth release asset is `SHA256SUMS.txt` itself.
- `pdfinfo`: author Franz César Castro Cuba.
- `pdffonts`: only Selawik, JetBrains Mono and Liberation Sans subsets.
- Notices page and reading site: HTTP 200.
- `make check`: 203 tests, 5 repository checks, 0 problems.
- `make full`: 203 tests, 6 repository checks, documentation links OK.

## Still to happen

1. Merge this catalog branch and run `portal-pages`; confirm the portal shows `v0.2.2`.
2. Delete the `v0.2.1` release page and assets on GitHub Releases, keeping its Git tag.

## Not run

- The portal deployment for `v0.2.2` has not been run from this change.
- The `v0.2.1` withdrawal has not been run.
- No new sample artifact build was run in this catalog change; release run 42621799383 built `v0.2.2`.
