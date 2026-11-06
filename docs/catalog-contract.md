# Catalog contract

The catalog is the only data source for the hub portal. It is deliberately small: it lists books and
their approved releases; it does not mirror manuscript content.

Machine-readable contract: [`catalog/catalog.json`](../catalog/catalog.json) and
[`schemas/catalog.schema.json`](../schemas/catalog.schema.json). Current state: **empty**, because no
book release has been approved.

## Entry model

```json
{
  "schema_version": "1.0",
  "books": [
    {
      "id": "handbook-authoring-and-publishing",
      "slug": "handbook-authoring-and-publishing",
      "title": "Handbook Authoring and Publishing",
      "summary": "A practical guide to writing, reviewing and publishing a handbook.",
      "categories": ["authoring", "publishing"],
      "status": "published",
      "latest_release": {
        "version": "1.0.0",
        "tag": "v1.0.0",
        "url": "https://github.com/OWNER/REPO/releases/tag/v1.0.0",
        "published_at": "2026-12-01",
        "manifest_url": "https://github.com/OWNER/REPO/releases/download/v1.0.0/publication-manifest.json",
        "checksums_url": "https://github.com/OWNER/REPO/releases/download/v1.0.0/SHA256SUMS.txt"
      }
    }
  ]
}
```

The example is illustrative and is not listed in the catalog.

## Required invariants

The toolkit enforces these deterministically:

| Invariant | Reason |
| --- | --- |
| `id` and `slug` are unique and match `^[a-z][a-z0-9-]{1,63}$` | Stable URLs and joins |
| `status` is `published` or `archived` | No drafts in the public catalog |
| `latest_release.version` is exact semver `MAJOR.MINOR.PATCH` | Immutable, comparable releases |
| `tag` is exactly `v` + `version` | One naming rule across books |
| Release, manifest and checksums URLs are HTTPS and share the same tag | No mutable or mixed-release links |
| `published_at` is an ISO date (`YYYY-MM-DD`) | Deterministic rendering |
| Categories are unique lowercase slugs | Stable portal grouping |
| The JSON document is valid against the catalog schema | One validated interface |

A catalog entry is rejected if it points to a branch, a pull request, a draft release or a build
artifact that is not attached to the release.

## Update flow

1. The book owner approves a release and the book publishes the artifact set.
2. The book release is verified: tag, manifest, checksums and artifact hashes.
3. A hub change updates `catalog/catalog.json` and the change record.
4. `handbook-toolkit validate-catalog` and `handbook-toolkit verify --full` pass.
5. An independent reviewer verifies the links and the release evidence.
6. The owner merges; the portal rebuilds from the catalog.

The catalog is append-mostly. Removing an entry is reserved for withdrawal (for example a licensing
or integrity defect) and must be recorded with the reason and the replacement version.

## Categories

Categories are portal facets, not a taxonomy of every topic. Start with a small controlled set and
extend it only when a book cannot be described by the existing values:

`architecture`, `authoring`, `cloud`, `data`, `engineering`, `governance`, `publishing`, `security`.

The catalog schema currently accepts lowercase slugs; Phase 4 adds a vocabulary check and a portal
test that every category has at least one book or is explicitly marked as a planned facet.

## Portal behavior

- One card per book: title, summary, categories, latest version and links to the reading site and
  release downloads.
- Filter/sort by category and title; no client-side search in the first vertical slice.
- The portal is static HTML generated from the catalog and deployed to Pages.
- The portal never proxies or hosts book downloads; it links to immutable release assets.
- Broken or missing release assets fail the portal build, not the reader's browser.

## Non-goals

- Full-text search across books.
- Hosting canonical manuscript content in the hub.
- Automatic ingestion from a branch or a pull request.
- Ratings, comments or user accounts.
